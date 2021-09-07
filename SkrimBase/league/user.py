# -*- coding: utf-8 -*-


from typing import Tuple, AsyncGenerator, TYPE_CHECKING, List, cast
from datetime import datetime
from sqlalchemy import select, and_, func, or_

from ..tables import (
    ban_table,
    statistic_table,
    user_table,
    scoreboard_table,
    scoreboard_total_table
)

from ..resources import Sessions

from ..ban import Ban

from ..webhook import WebhookSender

from ..exceptions import InvalidUser

from ..models.ban import BanModel
from ..models.user import StatisticModel, UserMapTying
from ..models.match import MatchModel, MatchFinished, STATUS_CODES

from ..settings.ban import BanSettings

from ..misc import str_uuid4

from .match import Match
from .misc import matches

if TYPE_CHECKING:
    from . import League


class User:
    def __init__(self, upper: "League", user_id: str) -> None:
        """Used to interact with user within league ID.

        Parameters
        ----------
        upper : League
        user_id : str
        """

        self.upper = upper
        self.user_id = user_id

    @property
    def __and_statement(self) -> and_:
        return and_(
            user_table.c.user_id == self.user_id,
            or_(
                statistic_table.c.league_id == self.upper.league_id,
                statistic_table.c.league_id.is_(None)
            )
        )

    async def get(self) -> StatisticModel:
        """Used to get user.

        Returns
        -------
        StatisticModel

        Raises
        ------
        InvalidUser
        """

        row = await Sessions.database.fetch_one(
            select([
                user_table,
                func.ifnull(statistic_table.c.elo, 0.0).label("elo"),
                func.ifnull(statistic_table.c.kills, 0).label("kills"),
                func.ifnull(statistic_table.c.headshots, 0).label("headshots"),
                func.ifnull(statistic_table.c.assists, 0).label("assists"),
                func.ifnull(statistic_table.c.deaths, 0).label("deaths"),
                func.ifnull(
                    statistic_table.c.shots_fired, 0
                ).label("shots_fired"),
                func.ifnull(statistic_table.c.shots_hit, 0).label("shots_hit"),
                func.ifnull(statistic_table.c.mvps, 0).label("mvps")
            ]).select_from(
                user_table.join(
                    statistic_table,
                    user_table.c.user_id == statistic_table.c.user_id,
                    isouter=True
                )
            ).where(
                self.__and_statement
            )
        )

        if row:
            wins = func.sum(
                func.IF(or_(
                    and_(
                        scoreboard_total_table.c.team_1_score >
                        scoreboard_total_table.c.team_2_score,
                        scoreboard_table.c.team == 0
                    ),
                    and_(
                        scoreboard_total_table.c.team_2_score >
                        scoreboard_total_table.c.team_1_score,
                        scoreboard_table.c.team == 1
                    )
                ), 1, 0)
            ).label("wins")

            losses = func.sum(
                func.IF(or_(
                    and_(
                        scoreboard_total_table.c.team_1_score >
                        scoreboard_total_table.c.team_2_score,
                        scoreboard_table.c.team == 1
                    ),
                    and_(
                        scoreboard_total_table.c.team_2_score >
                        scoreboard_total_table.c.team_1_score,
                        scoreboard_table.c.team == 0
                    )
                ), 1, 0)
            ).label("losses")

            ties = func.sum(
                func.IF(
                    scoreboard_total_table.c.team_1_score ==
                    scoreboard_total_table.c.team_2_score, 1, 0
                )
            ).label("ties")

            maps_rows = await Sessions.database.fetch_all(
                select([
                    func.sum(scoreboard_table.c.kills).label("kills"),
                    func.sum(scoreboard_table.c.deaths).label("deaths"),
                    wins, losses, ties,
                    scoreboard_total_table.c.map
                ]).select_from(
                    scoreboard_total_table.join(
                        scoreboard_table,
                        scoreboard_total_table.c.match_id ==
                        scoreboard_table.c.match_id
                    )
                ).where(
                    and_(
                        scoreboard_table.c.user_id == self.user_id,
                        scoreboard_total_table.c.league_id ==
                        self.upper.league_id,
                        scoreboard_total_table.c.status ==
                        STATUS_CODES.index(MatchFinished)
                    )
                ).group_by(
                    scoreboard_total_table.c.map
                ).order_by(
                    wins.desc(), ties.desc()
                )
            )

            return StatisticModel(
                league_id=self.upper.league_id,
                maps=cast(List[UserMapTying], maps_rows),
                **row
            )
        else:
            raise InvalidUser()

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

        async for model, match in matches(match=self.upper.match,
                                          league_id=self.upper.league_id,
                                          user_id=self.user_id,
                                          search=search, page=page,
                                          limit=limit, desc=desc):
            yield model, match

    def ban(self, ban_id: str) -> Ban:
        """Used to interact with ban.

        Parameters
        ----------
        ban_id : str

        Returns
        -------
        Ban
        """

        return Ban(ban_id, self.user_id, self.upper.league_id)

    async def create_ban(self, ban_settings: BanSettings
                         ) -> Tuple[BanModel, Ban]:
        """Used to ban user.

        Parameters
        ----------
        ban_settings : BanSettings

        Returns
        -------
        BanModel
        Ban

        Raises
        ------
        InvalidUser
        """

        now = datetime.now()

        values = {
            "ban_id": str_uuid4(),
            "user_id": self.user_id,
            "global_": False,
            "reason": ban_settings.reason,
            "timestamp": now,
            "expires": now + ban_settings.expires,
            "revoked": False,
            "banner_id": ban_settings.banner_id,
            "league_id": self.upper.league_id
        }

        try:
            await Sessions.database.execute(
                ban_table.insert().values(
                    **values
                )
            )
        except Exception:
            raise InvalidUser()
        else:
            ban_model = BanModel(**values)

            await Sessions.scheduler.spawn(
                WebhookSender(ban_model, self.upper.league_id).user_banned()
            )

            return ban_model, self.ban(values["ban_id"])
