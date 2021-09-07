# -*- coding: utf-8 -*-

from typing import AsyncGenerator, List, Tuple, Union
from datetime import datetime
from dathost.server.awaiting import ServerAwaiting
from dathost.settings import MatchSettings as DathostMatchSettings
from sqlalchemy import select, func, or_, and_

from ..tables import (
    league_table,
    scoreboard_total_table,
    scoreboard_table,
    user_table,
    statistic_table,
    league_integration_table,
    integration_table
)

from ..decorators import validate_region, validate_tickrate

from ..resources import Sessions

from ..webhook import WebhookSender

from ..exceptions import LeagueInvalid, UsersBanned

from .match import Match

from .user import User
from .users import Users

from .misc import matches

from ..models.league import LeagueModel
from ..models.match import ScoreboardModel, MatchModel
from ..models.user import UserOverviewModel
from ..models.integration import IntegrationModel

from ..settings.match import MatchSettings

from ..misc import str_uuid4

from ..server import get_server


class League:
    def __init__(self, league_id: str) -> None:
        """Used to interact with league.

        Parameters
        ----------
        league_id : str
        """

        self.league_id = league_id

    def match(self, match_id: str) -> Match:
        """Used to interact with match within league context.

        Parameters
        ----------
        match_id : str

        Returns
        -------
        Match
        """

        return Match(self, match_id)

    def user(self, user_id: str) -> User:
        """Used to interact with user within league context.

        Parameters
        ----------
        user_id : str

        Returns
        -------
        User
        """

        return User(self, user_id)

    def users(self, users: List[str]) -> Users:
        """Used to interact with users within league context.

        Parameters
        ----------
        users : List[str]

        Returns
        -------
        Users
        """

        return Users(self, users)

    async def players(self, search: str = None, page: int = 1,
                      limit: int = 20, desc: bool = True
                      ) -> AsyncGenerator[
                          Tuple[UserOverviewModel, User], None]:
        """Used to list players

        Parameters
        ----------
        search : str, optional
            by default None
        page : int, optional
             by default 1
        limit : int, optional
            by default 10
        desc : bool, optional
            by default True

        Yields
        -------
        UserOverviewModel
        User
        """

        query = select([
            user_table,
            func.ifnull(statistic_table.c.elo, 0.0).label("elo"),
            func.ifnull(statistic_table.c.kills, 0).label("kills"),
            func.ifnull(statistic_table.c.headshots, 0).label("headshots"),
            func.ifnull(statistic_table.c.deaths, 0).label("deaths"),
            func.ifnull(
                statistic_table.c.shots_fired, 0
            ).label("shots_fired"),
            func.ifnull(statistic_table.c.shots_hit, 0).label("shots_hit"),
            select([func.count()]).select_from(
                scoreboard_total_table.join(
                    scoreboard_table,
                    scoreboard_table.c.match_id ==
                    scoreboard_total_table.c.match_id
                )
            ).where(
                scoreboard_table.c.user_id == user_table.c.user_id
            ).label("matches")
        ]).select_from(
            user_table.join(
                statistic_table,
                user_table.c.user_id == statistic_table.c.user_id
            )
        ).where(
            statistic_table.c.league_id == self.league_id
        ).limit(limit).offset((page - 1) * limit if page > 1 else 0).order_by(
            statistic_table.c.elo.desc() if desc else
            statistic_table.c.elo.asc()
        )

        if search:
            query = query.where(
                or_(
                    user_table.c.steam_id == search,
                    user_table.c.discord_id == search,
                    user_table.c.user_id == search,
                    user_table.c.name.like("%{}%".format(search))
                )
            )

        async for player in Sessions.database.iterate(query):
            yield UserOverviewModel(**player), self.user(player["user_id"])

    async def matches(self, search: str = None,
                      page: int = 1, limit: int = 10, desc: bool = True
                      ) -> AsyncGenerator[Tuple[MatchModel, Match], None]:
        """Lists matches.

        Paramters
        ---------
        search: str
        page: int
        limit: int
        desc: bool, optional
            by default True

        Yields
        ------
        MatchModel
            Holds basic match details.
        Match
            Used for interacting with a match.
        """

        async for model, match in matches(match=self.match,
                                          league_id=self.league_id,
                                          search=search, page=page,
                                          limit=limit, desc=desc):
            yield model, match

    async def create_match(self, match_settings: MatchSettings,
                           ) -> Tuple[ScoreboardModel, Match, ServerAwaiting]:
        """Used to create a match.

        Parameters
        ----------
        match_settings : MatchSettings

        Returns
        -------
        ScoreboardModel
        Match
        ServerAwaiting
        """

        try:
            league = await self.get()
        except LeagueInvalid:
            raise

        teams_combined = (match_settings.team_1_players
                          + match_settings.team_2_players)

        # Checking for active bans.
        banned_users = [
            banned_user async for banned_user in
            self.users(teams_combined).active_ban_users()
        ]

        if banned_users:
            raise UsersBanned(banned_users)

        match_id = str_uuid4()

        # Lets get a server uwu.
        server_details, server = await get_server(
            server_name=league.league_name,
            region=league.region,
            tickrate=league.tickrate
        )

        values = {
            "match_id": match_id,
            "server_id": server_details.server_id,
            "league_id": self.league_id,
            "demo_status": 0,
            "status": 2,
            "map": match_settings.map,
            "team_1_score": 0,
            "team_2_score": 0,
            "team_1_side": 0,
            "team_2_side": 1,
            "team_1_name": match_settings.team_1_name,
            "team_2_name": match_settings.team_2_name,
            "timestamp": datetime.now(),
            "raw_ip": server_details.raw_ip,
            "game_port": server_details.ports.game
        }

        await Sessions.database.execute(
            scoreboard_total_table.insert().values(**values)
        )

        # Kinda hackie way, but elo must know the league ID.
        if match_settings._captains.elo_set:
            await match_settings._captains.elo_set(self.league_id)

        if match_settings._players.elo_set:
            await match_settings._players.elo_set(self.league_id)

        players = []
        players_append = players.append
        for user in teams_combined:

            if user in match_settings.team_1_players:
                team = 0
                captain = match_settings.team_1_captain
            else:
                team = 1
                captain = match_settings.team_2_captain

            players_append({
                "match_id": match_id,
                "user_id": user,
                "captain": user == captain,
                "team": team,
                "alive": True,
                "ping": 0,
                "kills": 0,
                "headshots": 0,
                "assists": 0,
                "deaths": 0,
                "shots_fired": 0,
                "shots_hit": 0,
                "mvps": 0,
                "score": 0,
                "disconnected": False
            })

        await Sessions.database.execute_many(
            scoreboard_table.insert(),
            players
        )

        # This may take awhile to complete.
        await server.start()
        await server.console_send(f"map {match_settings.map}")
        await server.console_send("tv_snapshotrate {}".format(
            league.demo_tickrate
        ))

        team_1_players, team_2_players = await match_settings.user_to_steam()

        await server.create_match(
            DathostMatchSettings(
                match_settings.connection_time,
                match_settings.knife_round,
                match_settings.wait_for_spectators,
                match_settings.warmup_time
            ).team_1(team_1_players).team_2(team_2_players)
        )

        match = self.match(match_id)

        # Sometimes the IP / Port can change after boot.
        # We can't do this during get_server or before
        # scoreboard_total_table.insert() because it would allow
        # a server to be selected twice due to timing issues.
        after_start_check = await server.get()
        if (after_start_check.raw_ip != values["raw_ip"] or
                after_start_check.ports.game != values["game_port"]):

            await match.update(
                raw_ip=after_start_check.raw_ip,
                game_port=after_start_check.ports.game
            )

            values["raw_ip"] = after_start_check.raw_ip
            values["game_port"] = after_start_check.ports.game

        scoreboard = await match.scoreboard()

        # Spawn match start webhook with some magic.
        await Sessions.scheduler.spawn(
            WebhookSender(scoreboard, self.league_id).match_start()
        )

        return scoreboard, match, server

    async def exists(self) -> bool:
        """Checks if league exists.

        Returns
        -------
        bool
        """

        return await Sessions.database.fetch_val(select([
            func.count()
        ]).select_from(league_table).where(
            league_table.c.league_id == self.league_id
        )) == 1

    async def integration_enabled(self, name: str) -> bool:
        """Used to check if a league has a integration enabled.

        Parameters
        ----------
        name : str

        Returns
        -------
        bool
        """

        return await Sessions.database.fetch_val(
            select([func.ifnull(func.count(), 0)]).select_from(
                league_integration_table.join(
                    integration_table,
                    integration_table.c.name == league_integration_table.c.name
                )
            ).where(
                or_(
                    integration_table.c.globally_required == True,  # noqa: E712, E501
                    and_(
                        league_integration_table.c.name == name,
                        league_integration_table.c.league_id == self.league_id
                    )
                )
            )
        ) == 1

    async def integrations(self) -> AsyncGenerator[IntegrationModel, None]:
        """Lists all enabled integrations.

        Yields
        -------
        IntegrationModel
        """

        query = select([integration_table]).select_from(
            integration_table.join(
                league_integration_table,
                league_integration_table.c.name ==
                integration_table.c.name
            )
        ).where(
            or_(
                integration_table.c.globally_required == True,  # noqa: E712, E501
                league_integration_table.c.league_id == self.league_id
            )
        )
        async for row in Sessions.database.iterate(query):
            yield IntegrationModel(**row)

    async def get(self) -> LeagueModel:
        """Used to get details on a league.

        Returns
        -------
        LeagueModel

        Raises
        ------
        LeagueInvalid
        """

        row = await Sessions.database.fetch_one(
            select([
                league_table,
                user_table.c.email,
                user_table.c.dathost_id,
            ]).select_from(
                league_table.join(
                    user_table,
                    user_table.c.user_id == league_table.c.user_id
                )
            ).where(
                league_table.c.league_id == self.league_id
            )
        )
        if row:
            return LeagueModel(**row)
        else:
            raise LeagueInvalid()

    @validate_region("region")
    @validate_tickrate("tickrate", "demo_tickrate")
    async def update(self, league_name: str = None,
                     email: str = None,
                     region: str = None, tickrate: int = None,
                     demo_tickrate: int = None,
                     disabled: bool = None, banned: bool = None,
                     match_start_webhook: str = None,
                     round_end_webhook: str = None,
                     match_end_webhook: str = None,
                     allow_api_access: bool = None,
                     kill: float = None,
                     death: float = None, round_won: float = None,
                     round_lost: float = None, match_won: float = None,
                     match_lost: float = None, assist: float = None,
                     mate_blinded: float = None, headshot: float = None,
                     mate_killed: float = None, score: float = None
                     ) -> Union[LeagueModel, None]:
        """Used to update details about a league.

        Parameters
        ----------
        league_name : str, optional
            by default None
        email : str, optional
            by default None
        tickrate : int, optional
            by default None
        demo_tickrate : int, optional
            by default None
        region : str, optional
            by default None
        disabled : bool, optional
            by default None
        banned : bool, optional
            by default None
        match_start_webhook : str, optional
            by default None
        round_end_webhook : str, optional
            by default None
        match_end_webhook : str, optional
            by default None
        allow_api_access : bool, optional
            by default None
        kill : float, optional
            by default None
        death : float, optional
            by default None
        round_won : float, optional
            by default None
        round_lost : float, optional
            by default None
        match_won : float, optional
            by default None
        match_lost : float, optional
            by default None
        headshot : float, optional
            by default None
        score : float, optional
            by default None
        assist : float, optional
            by default None
        mate_blinded : float, optional
            by default None
        mate_killed : float, optional
            by default None

        Returns
        -------
        Union[LeagueModel, None]
        """

        # Long ugly check if value given.
        values = {}
        if league_name:
            values["league_name"] = league_name
        if email:
            values["email"] = email
        if region:
            values["region"] = region
        if disabled is not None:
            values["disabled"] = disabled
        if banned is not None:
            values["banned"] = banned
        if match_start_webhook:
            values["match_start_webhook"] = match_start_webhook
        if round_end_webhook:
            values["round_end_webhook"] = round_end_webhook
        if match_end_webhook:
            values["match_end_webhook"] = match_end_webhook
        if allow_api_access is not None:
            values["allow_api_access"] = allow_api_access
        if kill is not None:
            values["kill"] = kill
        if death is not None:
            values["death"] = death
        if round_won is not None:
            values["round_won"] = round_won
        if round_lost is not None:
            values["round_lost"] = round_lost
        if match_won is not None:
            values["match_won"] = match_won
        if match_lost is not None:
            values["match_lost"] = match_lost
        if assist is not None:
            values["assist"] = assist
        if mate_blinded is not None:
            values["mate_blinded"] = mate_blinded
        if mate_killed is not None:
            values["mate_killed"] = mate_killed
        if headshot is not None:
            values["headshot"] = headshot
        if score is not None:
            values["score"] = score
        if tickrate is not None:
            values["tickrate"] = tickrate
        if demo_tickrate is not None:
            values["demo_tickrate"] = demo_tickrate

        if values:
            await Sessions.database.execute(
                league_table.update().values(
                    **values
                ).where(
                    league_table.c.league_id == self.league_id
                )
            )

            league_model = await self.get()

            await WebhookSender(
                league_model, self.league_id
            ).league_updated()

            return league_model
