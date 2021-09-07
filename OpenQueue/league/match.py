# -*- coding: utf-8 -*-

from datetime import datetime
from typing import List, TYPE_CHECKING, TypedDict
from sqlalchemy.sql import and_, select, func

from ..tables import (
    scoreboard_total_table,
    scoreboard_table,
    server_table,
    user_table
)
from ..exceptions import (
    InvalidMatchID,
    MatchAlreadyEnded,
    NoDemoToAnalyze,
    LeagueInvalid
)
from ..resources import Config, Sessions
from ..webhook import WebhookSender
from ..demo import Demo
from ..on_conflict import on_scoreboard_conflict, on_statistic_conflict

from ..models.match import (
    MatchModel,
    MatchFinished,
    ScoreboardModel
)

if TYPE_CHECKING:
    from . import League


class PlayerTypings(TypedDict):
    user_id: str
    team: int
    alive: bool
    ping: int
    kills: int
    headshots: int
    assists: int
    deaths: int
    shots_fired: int
    shots_hit: int
    mvps: int
    score: int
    disconnected: bool
    team_blinds: int
    team_kills: int


class Match:
    def __init__(self, upper: "League", match_id: str) -> None:
        self.upper = upper
        self.match_id = match_id

    @property
    def __and_statement(self) -> and_:
        return and_(
            scoreboard_total_table.c.match_id == self.match_id,
            scoreboard_total_table.c.league_id == self.upper.league_id
        )

    async def get(self) -> MatchModel:
        """Used to get match model.

        Returns
        -------
        MatchModel

        Raises
        ------
        InvalidMatchID
        """

        capt_team_1 = user_table.alias("capt_team_1")
        capt_team_2 = user_table.alias("capt_team_2")
        team_1_scoreboard = scoreboard_table.alias("team_1_scoreboard")
        team_2_scoreboard = scoreboard_table.alias("team_2_scoreboard")

        query = select([
            scoreboard_total_table.c.match_id,
            scoreboard_total_table.c.league_id,
            scoreboard_total_table.c.raw_ip,
            scoreboard_total_table.c.game_port,
            scoreboard_total_table.c.server_id,
            scoreboard_total_table.c.b2_id,
            scoreboard_total_table.c.timestamp,
            scoreboard_total_table.c.status,
            scoreboard_total_table.c.demo_status,
            scoreboard_total_table.c.map,
            scoreboard_total_table.c.team_1_name,
            scoreboard_total_table.c.team_2_name,
            scoreboard_total_table.c.team_1_score,
            scoreboard_total_table.c.team_2_score,
            scoreboard_total_table.c.team_1_side,
            scoreboard_total_table.c.team_2_side,
            capt_team_1.c.user_id.label("capt_team_1_user_id"),
            capt_team_2.c.user_id.label("capt_team_2_user_id"),
            capt_team_1.c.pfp_extension.label("capt_team_1_pfp_extension"),
            capt_team_2.c.pfp_extension.label("capt_team_2_pfp_extension"),
            func.group_concat(user_table.c.user_id).label("user_ids"),
            func.group_concat(
                user_table.c.pfp_extension
            ).label("user_pfp_extensions"),
            func.group_concat(user_table.c.name).label("user_names"),
            func.group_concat(scoreboard_table.c.team).label("user_teams")
        ]).select_from(
            scoreboard_total_table.join(
                scoreboard_table,
                scoreboard_table.c.
                match_id == scoreboard_total_table.c.match_id
            ).join(
                team_1_scoreboard.join(
                    capt_team_1,
                    and_(
                        capt_team_1.c.user_id == team_1_scoreboard.c.user_id,
                        team_1_scoreboard.c.team == 0,
                        team_1_scoreboard.c.captain == True  # noqa: E712
                    )
                ),
                team_1_scoreboard.c.match_id ==
                scoreboard_total_table.c.match_id,
                isouter=True
            ).join(
                team_2_scoreboard.join(
                    capt_team_2,
                    and_(
                        capt_team_2.c.user_id == team_2_scoreboard.c.user_id,
                        team_2_scoreboard.c.team == 1,
                        team_2_scoreboard.c.captain == True  # noqa: E712
                    )
                ),
                team_2_scoreboard.c.match_id ==
                scoreboard_total_table.c.match_id,
                isouter=True
            ).join(
                user_table,
                user_table.c.user_id == scoreboard_table.c.user_id
            )
        ).where(
            and_(
                scoreboard_total_table.c.league_id == self.upper.league_id,
                scoreboard_total_table.c.match_id == self.match_id
            )
        )

        row = await Sessions.database.fetch_one(query)

        if row:
            return MatchModel(**row)
        else:
            raise InvalidMatchID()

    async def analyze_demo(self) -> None:
        """Used to analyze demo with playwin.

        Raises
        ------
        NoDemoToAnalyze
        """

        if not Config.playwin:
            return

        if not await self.upper.integration_enabled("playwin"):
            return

        match = await self.get()
        if not match.demo_url:
            raise NoDemoToAnalyze()

        await Sessions.requests.post(
            Config.playwin.route,
            headers={"Authorization": Config.playwin.authorization},
            data={
                "matchId": self.match_id,
                "demoUrl": match.demo_url,
                "webhookUrl": Config.playwin.result_webhook
            }
        )

    async def scoreboard(self) -> ScoreboardModel:
        """Gets scoreboard.

        Returns
        ------
        ScoreboardModel
        """

        query = select([
            scoreboard_total_table,
            user_table.c.name,
            user_table.c.user_id,
            user_table.c.steam_id,
            user_table.c.discord_id,
            user_table.c.pfp_extension,
            user_table.c.timestamp.label("user_timestamp"),
            scoreboard_table.c.team,
            func.ifnull(scoreboard_table.c.alive, True).label("alive"),
            func.ifnull(scoreboard_table.c.ping, 0).label("ping"),
            func.ifnull(scoreboard_table.c.kills, 0).label("kills"),
            func.ifnull(scoreboard_table.c.headshots, 0).label("headshots"),
            func.ifnull(scoreboard_table.c.assists, 0).label("assists"),
            func.ifnull(scoreboard_table.c.deaths, 0).label("deaths"),
            func.ifnull(
                scoreboard_table.c.shots_fired, 0
            ).label("shots_fired"),
            func.ifnull(scoreboard_table.c.shots_hit, 0).label("shots_hit"),
            func.ifnull(scoreboard_table.c.mvps, 0).label("mvps"),
            func.ifnull(scoreboard_table.c.score, 0).label("score"),
            func.ifnull(
                scoreboard_table.c.disconnected, False
            ).label("disconnected")
        ]).select_from(
            scoreboard_total_table.join(
                scoreboard_table,
                scoreboard_table.c.match_id ==
                scoreboard_total_table.c.match_id
            ).join(
                user_table,
                user_table.c.user_id == scoreboard_table.c.user_id
            )
        ).where(self.__and_statement)

        scoreboard_data = {
            "match": None,
            "team_1": [],
            "team_2": []
        }

        team_1_append = scoreboard_data["team_1"].append
        team_2_append = scoreboard_data["team_2"].append

        async for row in Sessions.database.iterate(query=query):
            if not scoreboard_data["match"]:
                scoreboard_data["match"] = {
                    "match_id": self.match_id,
                    "raw_ip": row["raw_ip"],
                    "game_port": row["game_port"],
                    "server_id": row["server_id"],
                    "timestamp": row["timestamp"],
                    "b2_id": row["b2_id"],
                    "status": row["status"],
                    "demo_status": row["demo_status"],
                    "map": row["map"],
                    "team_1_name": row["team_1_name"],
                    "team_2_name": row["team_2_name"],
                    "team_1_score": row["team_1_score"],
                    "team_2_score": row["team_2_score"],
                    "team_1_side": row["team_1_side"],
                    "team_2_side": row["team_2_side"],
                    "league_id": row["league_id"]
                }

            team_append = team_1_append if row["team"] == 0 else team_2_append

            team_append({
                "user_id": row["user_id"],
                "steam_id": row["steam_id"],
                "discord_id": row["discord_id"],
                "pfp_extension": row["pfp_extension"],
                "name": row["name"],
                "timestamp": row["user_timestamp"],
                "team": row["team"],
                "alive": row["alive"],
                "ping": row["ping"],
                "kills": row["kills"],
                "headshots": row["headshots"],
                "assists": row["assists"],
                "deaths": row["deaths"],
                "shots_fired": row["shots_fired"],
                "shots_hit": row["shots_hit"],
                "mvps": row["mvps"],
                "score": row["score"],
                "disconnected": row["disconnected"]
            })

        if scoreboard_data["match"]:
            return ScoreboardModel(**scoreboard_data)
        else:
            raise InvalidMatchID()

    async def update(self, raw_ip: str = None, game_port: int = None,
                     server_id: str = None, b2_id: str = None,
                     timestamp: datetime = None, status: int = None,
                     demo_status: int = None, map: str = None,
                     team_1_name: str = None, team_2_name: str = None,
                     team_1_score: int = None, team_2_score: int = None,
                     team_1_side: int = None, team_2_side: int = None,
                     players: List[PlayerTypings] = None) -> ScoreboardModel:
        """Used to update a match.

        Parameters
        ----------
        raw_ip : str, optional
            by default None
        game_port : int, optional
            by default None
        server_id : str, optional
            by default None
        b2_id : str, optional
            by default None
        timestamp : datetime, optional
            by default None
        status : int, optional
            by default None
        demo_status : int, optional
            by default None
        map : str, optional
            by default None
        team_1_name : str, optional
            by default None
        team_2_name : str, optional
            by default None
        team_1_score : int, optional
            by default None
        team_2_score : int, optional
            by default None
        team_1_side : int, optional
            by default None
        team_2_side : int, optional
            by default None
        players : List[PlayerTypings], optional
            by default None

        Returns
        -------
        ScoreboardModel
        """

        # Steam workshop map pull for map var

        values = {}
        if raw_ip:
            values["raw_ip"] = raw_ip
        if game_port is not None:
            values["game_port"] = game_port
        if server_id:
            values["server_id"] = server_id
        if b2_id:
            values["b2_id"] = b2_id
        if timestamp:
            values["timestamp"] = timestamp
        if status is not None:
            values["status"] = status
        if demo_status is not None:
            values["demo_status"] = demo_status
        if map:
            values["map"] = map
        if team_1_name:
            values["team_1_name"] = team_1_name
        if team_2_name:
            values["team_2_name"] = team_2_name
        if team_1_score is not None:
            values["team_1_score"] = team_1_score
        if team_2_score is not None:
            values["team_2_score"] = team_2_score
        if team_1_side is not None:
            values["team_1_side"] = team_1_side
        if team_2_side is not None:
            values["team_2_side"] = team_2_side

        if values:
            await Sessions.database.execute(
                scoreboard_total_table.update().values(**values).where(
                    self.__and_statement
                )
            )

        if players:
            try:
                league = await self.upper.get()
            except LeagueInvalid:
                raise

            scoreboard = []
            scoreboard_append = scoreboard.append

            statistics = []
            statistics_append = statistics.append

            for player in players:
                scoreboard_append({
                    "match_id": self.match_id,
                    "user_id": player["user_id"],
                    "team": player["team"],
                    "alive": player["alive"],
                    "ping": player["ping"],
                    "kills": player["kills"],
                    "headshots": player["headshots"],
                    "assists": player["assists"],
                    "deaths": player["deaths"],
                    "shots_fired": player["shots_fired"],
                    "shots_hit": player["shots_hit"],
                    "mvps": player["mvps"],
                    "score": player["score"],
                    "disconnected": player["disconnected"]
                })

                round_won = 0.0
                round_lost = 0.0
                if team_1_score and team_2_score:
                    if team_1_side == player["team"]:
                        if team_1_score > team_2_score:
                            round_won = league.round_won
                        else:
                            round_lost = league.round_lost
                    else:
                        if team_2_score > team_1_score:
                            round_won = league.round_won
                        else:
                            round_lost = league.round_lost

                statistics_append({
                    "league_id": self.upper.league_id,
                    "user_id": player["user_id"],
                    "kills": player["kills"],
                    "headshots": player["headshots"],
                    "assists": player["assists"],
                    "deaths": player["deaths"],
                    "shots_fired": player["shots_fired"],
                    "shots_hit": player["shots_hit"],
                    "mvps": player["mvps"],
                    "elo": (
                        (player["kills"] * league.kill) +
                        (player["headshots"] * league.headshot) +
                        (player["assists"] * league.assist) +
                        (player["deaths"] * league.death) +
                        (player["score"] * league.score) +
                        (player["team_blinds"] * league.mate_blinded) +
                        (player["team_kills"] * league.mate_killed) +
                        round_won + round_lost
                    )
                })

            await Sessions.database.execute_many(
                query=on_statistic_conflict(),
                values=statistics
            )

            await Sessions.database.execute_many(
                query=on_scoreboard_conflict(),
                values=scoreboard
            )

        scoreboard = await self.scoreboard()

        await Sessions.scheduler.spawn(
            WebhookSender(scoreboard).match_update()
        )

        return scoreboard

    async def end(self) -> ScoreboardModel:
        """Used to end a match.

        Returns
        -------
        ScoreboardModel

        Raises
        ------
        MatchAlreadyEnded
        """

        # TODO
        # Update player elo for match win / lost.

        try:
            match = await self.scoreboard()
        except InvalidMatchID:
            raise

        if match.status == MatchFinished:
            raise MatchAlreadyEnded()

        server = Sessions.game.server(match.server_id)

        # Incase the match was force ended, the demo can still be saved.
        await server.console_send("tv_stoprecord")

        server_details = await server.get()
        await Sessions.database.execute(
            server_table.update().values(
                month_credits=server_details.month_credits,
                month_reset_at=server_details.month_reset_at
                # ^ Not really needed, but we have the data
            ).where(
                server_table.c.server_id == match.server_id
            )
        )

        match.status = 0
        await self.update(status=match.status)

        await Sessions.scheduler.spawn(
            WebhookSender(match, self.upper.league_id).match_end()
        )
        await Sessions.scheduler.spawn(server.stop())
        await Sessions.scheduler.spawn(Demo(server, self).upload())

        return match
