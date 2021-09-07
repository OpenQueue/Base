# -*- coding: utf-8 -*-

from typing import AsyncGenerator, TYPE_CHECKING, Tuple, Type
from uuid import uuid4
from sqlalchemy import select

from .resources import Sessions

from .tables import (
    event_table,
    league_table,
    user_table
)

from .constants import WEBHOOK_EVENTS

from .models.league import LeagueModel

if TYPE_CHECKING:
    from .league import League


def str_uuid4() -> str:
    """Generate string UUID.

    Returns
    -------
    str
    """

    return str(uuid4())


async def cache_events() -> None:
    """Stores events into database.
    """

    raw = await Sessions.database.fetch_all(event_table.select())
    if raw:
        event_ids = [
            event["event_id"] for event in raw
        ]
    else:
        event_ids = []

    # Isn't coded to be optimal.
    for event_type, event_id in WEBHOOK_EVENTS.items():
        if event_id not in event_ids:
            await Sessions.database.execute(
                event_table.insert().values(
                    event_id=event_id,
                    event_type=event_type
                )
            )


async def leagues(league: Type["League"], user_id: str = None,
                  search: str = None, desc: bool = True
                  ) -> AsyncGenerator[Tuple[LeagueModel, "League"], None]:
    """Used to list leagues.

    Parameters
    ----------
    league: League
    user_id : str, optional
        by default None
    search : str, optional
        by default None
    desc : bool, optional
        by default True

    Yields
    -------
    LeagueModel
    League
    """

    query = select([
        league_table,
        user_table.c.email,
        user_table.c.dathost_id
    ]).select_from(
        league_table.join(
            user_table,
            user_table.c.user_id == league_table.c.user_id
        )
    )

    if user_id:
        query = query.where(
            league_table.c.user_id == user_id
        )

    if search:
        query = query.where(
            league_table.c.league_name.like("%{}%".format(search))
        )

    query = query.order_by(
        league_table.c.timestamp.desc() if desc
        else league_table.c.timestamp.asc()
    )

    async for row in Sessions.database.iterate(query):
        yield LeagueModel(**row), league(row["league_id"])
