# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import List, Tuple
from random import shuffle
from sqlalchemy import select, or_, and_

from ..tables import statistic_table, user_table
from ..resources import Sessions
from ..decorators import validate_users
from ..exceptions import CaptainsNotInTeam, PlayersNotGiven


class CaptainSettings:
    def __init__(self, upper: MatchSettings) -> None:
        """Used to set captains.

        Parameters
        ----------
        team_1_players : List[str]
            List of user IDs.
        team_2_players : List[str]
            List of user IDs.
        upper: MatchSettings
        """

        self.elo_set = None
        self.upper = upper

    def given(self, captain_1: str, captain_2: str) -> MatchSettings:
        """Uses to set captains.

        Parameters
        ----------
        captain_1 : str
        captain_2 : str

        Raises
        ------
        CaptainsNotInTeam

        Returns
        -------
        MatchSettings
        """

        if (captain_1 not in self.upper.team_1_players or
                captain_2 not in self.upper.team_2_players):
            raise CaptainsNotInTeam()

        self.upper.team_1_captain = captain_1
        self.upper.team_2_captain = captain_2

        return self.upper

    def random(self) -> MatchSettings:
        """Used to select captains at random.

        Returns
        -------
        MatchSettings
        """

        shuffle(self.upper.team_1_players)
        shuffle(self.upper.team_2_players)

        self.upper.team_1_captain = self.upper.team_1_players[0]
        self.upper.team_2_captain = self.upper.team_2_players[0]

        return self.upper

    def elo(self) -> MatchSettings:
        """Used to select captains based off elo.

        Notes
        -----
        If used, __elo must be called before used.

        Returns
        -------
        MatchSettings
        """

        self.elo_set = self.__elo
        return self.upper

    def __create_elo_query(self, league_id: str, players: List[str]) -> select:
        return select([statistic_table.c.user_id]).select_from(
            statistic_table
        ).where(
            and_(
                statistic_table.c.league_id == league_id,
                statistic_table.c.user_id.in_(players)
            )
        ).order_by(
            statistic_table.c.elo.desc()
        ).limit(1)

    async def __elo(self, league_id: str) -> None:
        users = await Sessions.database.fetch_one(
            select([
                self.__create_elo_query(
                    league_id, self.upper.team_1_players
                ).alias("team_1"),
                self.__create_elo_query(
                    league_id, self.upper.team_2_players
                ).alias("team_2")
            ])
        )

        if users:
            if users["team_1"] and users["team_2"]:
                self.upper.team_1_captain = users["team_1"]
                self.upper.team_2_captain = users["team_2"]
            elif users["team_1"]:
                self.upper.team_1_captain = users["team_1"]
                self.upper.team_2_captain = self.upper.team_2_players[0]
            elif users["team_2"]:
                self.upper.team_2_captain = users["team_2"]
                self.upper.team_1_captain = self.upper.team_1_players[0]
            else:
                self.random()
        else:
            self.random()


class PlayerSettings:
    def __init__(self, upper: MatchSettings) -> None:
        self.elo_set = None
        self.__players = None
        self.upper = upper

    @validate_users("team_1", "team_2")
    async def given(self, team_1: List[str],
                    team_2: List[str]) -> MatchSettings:
        """Give team players.

        Parameters
        ----------
        team_1 : List[str]
            List of user IDs.
        team_2 : List[str]
            List of user IDs.

        Raises
        ------
        InvalidUser

        Returns
        -------
        MatchSettings
        """

        self.upper.team_1_players = team_1
        self.upper.team_2_players = team_2

        return self.upper

    @validate_users("players")
    async def random(self, players: List[str]) -> MatchSettings:
        """Used to set teams at random.

        Parameters
        ----------
        players : List[str]
            List of user IDs.

        Raises
        ------
        InvalidUser

        Returns
        -------
        MatchSettings
        """

        shuffle(players)

        for player in players:
            if players.index(player) % 2 == 0:
                self.upper.team_1_players.append(player)
            else:
                self.upper.team_2_players.append(player)

        return self.upper

    @validate_users("players")
    async def elo(self, players: List[str]) -> MatchSettings:
        """Used to set players by elo.

        Parameters
        ----------
        players : List[str]
            List of user IDs.

        Raises
        ------
        InvalidUser

        Returns
        -------
        MatchSettings
        """

        self.__players = players
        self.elo_set = self.__elo
        return self.upper

    async def __elo(self, league_id: str) -> None:
        if not self.__players:
            raise PlayersNotGiven()

        query = select([
            statistic_table.c.user_id
        ]).select_from(
            statistic_table
        ).where(
            and_(
                statistic_table.c.league_id == league_id,
                statistic_table.c.user_id.in_(self.__players)
            )
        ).order_by(
            statistic_table.c.elo.desc()
        )

        iteration = 0
        async for row in Sessions.database.iterate(query):
            if iteration % 2 == 0:
                self.upper.team_1_players.append(row["user_id"])
            else:
                self.upper.team_2_players.append(row["user_id"])

            iteration += 1

        if iteration != len(self.__players):
            for user_id in self.__players:
                if (user_id not in self.upper.team_1_players and
                        user_id not in self.upper.team_2_players):
                    if iteration % 2 == 0:
                        self.upper.team_1_players.append(user_id)
                    else:
                        self.upper.team_2_players.append(user_id)

                    iteration += 1


class MapSettings:
    def __init__(self, maps: List[str], upper: MatchSettings) -> None:
        self.maps = maps
        self.upper = upper

    def random(self) -> MatchSettings:
        """Used to select a random map.

        Returns
        -------
        MatchSettings
        """

        shuffle(self.maps)
        self.upper.map = self.maps[0]
        return self.upper

    def given(self) -> MatchSettings:
        """Used to set map as given, uses 1st index.

        Returns
        -------
        MatchSettings
        """

        self.upper.map = self.maps[0]
        return self.upper


class MatchSettings:
    def __init__(self, team_1_name: str = "One", team_2_name: str = "Two",
                 connection_time: int = 300, knife_round: bool = False,
                 wait_for_spectators: bool = True,
                 warmup_time: int = 15) -> None:
        """Used to create match.

        Parameters
        ----------
        team_1_name : str, optional
            by default "One"
        team_2_name : str, optional
            by default "Two"
        connection_time : int, optional
            by default 300
        knife_round : bool, optional
            by default False
        wait_for_spectators : bool, optional
            by default True
        warmup_time : int, optional
            by default 15
        """

        self.team_1_players = []
        self.team_2_players = []

        self.team_1_captain: str
        self.team_2_captain: str

        self.team_1_name = team_1_name
        self.team_2_name = team_2_name

        self.map: str

        self.connection_time = connection_time
        self.knife_round = knife_round
        self.wait_for_spectators = wait_for_spectators
        self.warmup_time = warmup_time

        self._captains: CaptainSettings
        self._players: PlayerSettings

    async def user_to_steam(self) -> Tuple[List[str], List[str]]:
        """Used to convert user IDs to steam IDs.

        Returns
        -------
        List[str]
            Team 1, player Steam IDs.
        List[str]
            Team 2, player Steam IDs.
        """

        team_1 = []
        team_2 = []

        team_1_append = team_1.append
        team_2_append = team_2.append

        query = select([
            user_table.c.steam_id,
            user_table.c.user_id
        ]).select_from(
            user_table
        ).where(
            or_(
                user_table.c.user_id.in_(self.team_1_players),
                user_table.c.user_id.in_(self.team_2_players)
            )
        )

        async for row in Sessions.database.iterate(query):
            team_append = (
                team_1_append if row["user_id"] in
                self.team_1_players else team_2_append
            )

            team_append(row["steam_id"])

        return team_1, team_2

    def players(self) -> PlayerSettings:
        """Used to set players.

        Returns
        -------
        PlayerSettings
        """

        self._players = PlayerSettings(self)
        return self._players

    def captains(self) -> CaptainSettings:
        """Used to set captains.

        Returns
        -------
        CaptainSettings
        """

        assert self.team_1_players, self.team_2_players
        self._captains = CaptainSettings(self)
        return self._captains

    def maps(self, maps: List[str]) -> MapSettings:
        """Used to set map.

        Parameters
        ----------
        maps : List[str]
            List of full map names.

        Returns
        -------
        MapSettings
        """

        return MapSettings(maps, self)
