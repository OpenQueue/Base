# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Dict, Tuple, Union
from sqlalchemy import select

from dathost.server.awaiting import ServerAwaiting
from dathost.settings import ServerSettings as DathostServerSettings
from dathost.models.server import ServerModel

from .resources import Sessions, Config

from .tables import (
    server_table,
    scoreboard_total_table,
)


async def generate_game_token(memo: str, app_id: int = 730) -> Tuple[str, str]:
    """Used to generate a API key.

    Parameters
    ----------
    memo : str
    app_id : int, optional
        by default 730

    Returns
    -------
    str
        Game token
    str
        Game token ID
    """

    url = "{}/{}".format(
        Config.steam.api_url,
        "/IGameServersService/CreateAccount/v1/"
    )

    params = {
        "key": Config.steam.api_key,
        "appid": app_id,
        "memo": memo
    }

    async with Sessions.requests.post(url, params=params) as resp:
        resp.raise_for_status()
        json = (await resp.json())["response"]
        return json["login_token"], json["steam_id"]


async def delete_game_token(game_token_id: str) -> None:
    """Used to delete a game token.

    Parameters
    ----------
    game_token_id : str
        Steam token to delete.
    """

    url = "{}/{}".format(
        Config.steam.api_url,
        "/IGameServersService/DeleteAccount/v1/"
    )

    # It says steamid, but it isn't a steam user id.
    params = {
        "key": Config.steam.api_key,
        "steamid": game_token_id
    }

    await Sessions.requests.post(url, params=params)


async def get_server(server_name: str, region: str, tickrate: int
                     ) -> Tuple[ServerModel, ServerAwaiting]:
    """Used to get a server for a match.
    If no servers are free, it just clones a new one.

    Parameters
    ----------
    server_name : str
    region : str
    tickrate : int

    Returns
    -------
    ServerModel
    ServerAwaiting
    """

    sub_query = select([
        scoreboard_total_table.c.server_id
    ]).select_from(
        scoreboard_total_table
    ).where(
        scoreboard_total_table.c.status != 0
    ).alias("sub_query")

    row = await Sessions.database.fetch_one(
        select([
            server_table.c.server_id,
            server_table.c.game_token_expires,
            server_table.c.game_token_id,
            server_table.c.month_reset_at
        ]).select_from(
            server_table
        ).where(
            server_table.c.server_id.notin_(sub_query)
        ).order_by(
            server_table.c.month_credits.desc(),
            server_table.c.month_reset_at.asc()
        )
    )

    now = datetime.now()
    token_expires = now + Config.steam.token_expires

    if row:
        server = Sessions.game.server(row["server_id"])
        model = await server.get()

        server_update: Dict[str, Union[str, float, datetime]] = {
            "game_token_expires": token_expires
        }

        if now >= row["game_token_expires"]:
            await delete_game_token(row["game_token_id"])

            game_token, token_id = await generate_game_token(server.server_id)
            server_update["game_token"] = game_token
            server_update["game_token_id"] = token_id
        else:
            game_token = None

        if now >= row["month_reset_at"]:
            server_update["month_credits"] = model.month_credits
            server_update["month_reset_at"] = model.month_reset_at

        await Sessions.database.execute(
            server_table.update().values(
                **server_update
            ).where(
                server_table.c.server_id == row["server_id"]
            )
        )
    else:
        model, server = await (
            Sessions.game.server(Config.clone_id)
        ).duplicate(sync=True)

        game_token = await generate_game_token(server.server_id)

        await Sessions.database.execute(
            server_table.insert().values(
                server_id=model.server_id,
                month_credits=model.month_credits,
                month_reset_at=model.month_reset_at,
                game_token=game_token,
                game_token_expires=token_expires
            )
        )

    await server.update(
        DathostServerSettings(
            server_name, region
        ).csgo(
            game_token=game_token,
            tickrate=tickrate
        )
    )

    return model, server
