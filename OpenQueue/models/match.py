# -*- coding: utf-8 -*-


from datetime import datetime
from typing import Dict, Generator, List, Union, cast, TypedDict

from ..resources import Config

from .base import _DepthStatsModel, ApiSchema


class MatchLive:
    pass


class MatchFinished:
    pass


class MatchProcessing:
    pass


class DemoNo:
    pass


class DemoProcessing:
    pass


class DemoReady:
    pass


class DemoTooLarge:
    pass


class DemoExpired:
    pass


class CounterTerrorist:
    pass


class Terrorist:
    pass


class TeamOne:
    pass


class TeamTwo:
    pass


STATUS_CODES = [
    MatchFinished,
    MatchLive,
    MatchProcessing
]


DEMO_STATUS_CODE = [
    DemoNo,
    DemoProcessing,
    DemoReady,
    DemoTooLarge,
    DemoExpired
]


TEAM_SIDES = [
    CounterTerrorist,
    Terrorist
]

TEAMS = [
    TeamOne,
    TeamTwo
]


class TeamTyping(TypedDict):
    discord_id: int
    steam_id: str
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
    timestamp: datetime


class MatchTyping(TypedDict):
    match_id: str
    raw_ip: str
    game_port: int
    server_id: str
    timestamp: datetime
    b2_id: Union[None, str]
    status: int
    demo_status: int
    map: str
    team_1_name: str
    team_2_name: str
    team_1_score: int
    team_2_score: int
    team_1_side: int
    team_2_side: int
    league_id: str


class DemoModel(ApiSchema):
    def __init__(self, match_id: str, league_id: str,
                 demo_status: Union[
                     int, DemoNo, DemoReady, DemoTooLarge,
                     DemoProcessing, DemoExpired]) -> None:

        self.match_id = match_id
        self.league_id = league_id
        self.demo_status = (
            DEMO_STATUS_CODE[demo_status]
            if isinstance(demo_status, int) else demo_status
        )
        self.demo_url = (
            "{}/{}".format(
                Config.demo.pathway,
                self.match_id + Config.demo.compressed_extension
            )
            if self.demo_status == DemoReady else None
        )

    def api_schema(self, public: bool = True) -> Dict[str, Union[str, dict]]:
        """Used to get a model's API schema.

        Parameters
        ----------
        public : bool, optional
            If public safe data should only be shown, by default True

        Returns
        -------
        Dict[str, Union[str, dict]]
        """

        return {
            "match_id": self.match_id,
            "league_id": self.league_id,
            "demo": {
                "status": DEMO_STATUS_CODE.index(self.demo_status),
                "url": self.demo_url
            }
        }


class _MatchPlayerModel(ApiSchema):
    def __init__(self, name: str, user_id: str,
                 team: int, pfp_extension: str = None) -> None:
        self.name = name
        self.user_id = user_id
        self.team = TEAMS[team] if isinstance(team, int) else team
        self.pfp = "{}{}/{}{}".format(
            Config.b2.cdn_url, Config.pfp.pathway, user_id, pfp_extension
        ) if pfp_extension else None

    def api_schema(self, public: bool = True
                   ) -> Dict[str, Union[str, dict, int, None]]:
        return {
            "name": self.name,
            "identifiers": {
                "user": self.user_id
            },
            "team": TEAMS.index(self.team),
            "pfp": self.pfp
        }


class _MatchBaseModel(DemoModel, ApiSchema):
    def __init__(self, timestamp: datetime,
                 status: Union[int, MatchLive, MatchFinished, MatchProcessing],
                 server_id: str, map: str, team_1_name: str, team_2_name: str,
                 team_1_score: int, team_2_score: int,
                 team_1_side: Union[int, CounterTerrorist, Terrorist],
                 team_2_side: Union[int, CounterTerrorist, Terrorist],
                 raw_ip: str, game_port: int,
                 b2_id: Union[str, None] = None,
                 *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.b2_id = b2_id
        self.timestamp = timestamp
        self.status = (
            STATUS_CODES[status]
            if isinstance(status, int) else status
        )
        self.server_id = server_id
        self.map = map
        self.team_1_name = team_1_name
        self.team_2_name = team_2_name
        self.team_1_score = team_1_score
        self.team_2_score = team_2_score

        self.team_1_side = (
            TEAM_SIDES[team_1_side]
            if isinstance(team_1_side, int) else team_1_side
        )
        self.team_2_side = (
            TEAM_SIDES[team_2_side]
            if isinstance(team_2_side, int) else team_2_side
        )
        self.raw_ip = raw_ip
        self.game_port = game_port

    def api_schema(self, public: bool = True
                   ) -> Dict[str, Union[dict, str, int, None]]:
        """Used to get a model's API schema.

        Parameters
        ----------
        public : bool, optional
            If public safe data should only be shown, by default True

        Returns
        -------
        Dict[str, Union[dict, str, int]]
        """

        ip_port = "{}:{}".format(self.raw_ip, self.game_port)

        schema = {
            **super().api_schema(public),
            "timestamp": self.timestamp.timestamp(),
            "status": STATUS_CODES.index(self.status),
            "map": self.map,
            "connect": {
                "ip": self.raw_ip,
                "port": self.game_port,
                "ip_port": ip_port,
                "console": "connect " + ip_port,
                "browser_protocol": "steam://connect/" + ip_port
            },
            "team_1": {
                "name": self.team_1_name,
                "score": self.team_1_score,
                "side": TEAM_SIDES.index(self.team_1_side)
            },
            "team_2": {
                "name": self.team_2_name,
                "score": self.team_2_score,
                "side": TEAM_SIDES.index(self.team_2_side)
            },
        }

        if not public:
            schema["b2_id"] = self.b2_id
            schema["server_id"] = self.server_id

        return schema


class MatchModel(_MatchBaseModel, ApiSchema):
    def __init__(self, capt_team_1_user_id: str,
                 capt_team_1_pfp_extension: str,
                 capt_team_2_user_id: str,
                 capt_team_2_pfp_extension: str,
                 user_ids: str, user_pfp_extensions: str, user_names: str,
                 user_teams: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.capt_team_1_user_id = capt_team_1_user_id
        self.capt_team_1_pfp = "{}{}/{}{}".format(
            Config.b2.cdn_url, Config.pfp.pathway,
            capt_team_1_user_id, capt_team_1_pfp_extension
        ) if capt_team_1_pfp_extension else None
        self.capt_team_2_pfp = "{}{}/{}{}".format(
            Config.b2.cdn_url, Config.pfp.pathway,
            capt_team_2_user_id, capt_team_2_pfp_extension
        ) if capt_team_2_pfp_extension else None
        self.capt_team_2_user_id = capt_team_2_user_id
        self.__user_ids = user_ids
        self.__user_pfp_extensions = user_pfp_extensions
        self.__user_names = user_names
        self.__user_teams = user_teams

    def players(self) -> Generator[_MatchPlayerModel, None, None]:
        user_ids = self.__user_ids.split(",")
        user_names = self.__user_names.split(",")
        user_teams = self.__user_teams.split(",")
        user_pfp_extensions = self.__user_pfp_extensions.split(",")

        for index in range(0, len(user_ids)):
            yield _MatchPlayerModel(
                user_names[index],
                user_ids[index],
                int(user_teams[index]),
                user_pfp_extensions[index]
            )

    def api_schema(self, public: bool = True
                   ) -> Dict[str, Union[dict, str, int, None]]:
        """Used to get a model's API schema.

        Parameters
        ----------
        public : bool, optional
            If public safe data should only be shown, by default True

        Returns
        -------
        Dict[str, Union[dict, str, int, None]]
        """

        schema = super().api_schema(public)
        team_1 = cast(dict, schema["team_1"])
        team_2 = cast(dict, schema["team_2"])

        team_1["players"] = []
        team_2["players"] = []

        team_1_append = team_1["players"].append
        team_2_append = team_2["players"].append

        for player in self.players():
            team_append = (team_1_append if player.team == TeamOne
                           else team_2_append)

            team_append(player.api_schema(public))

        team_1["captain_id"] = self.capt_team_1_user_id
        team_1["pfp"] = self.capt_team_1_pfp
        team_2["captain_id"] = self.capt_team_2_user_id
        team_2["pfp"] = self.capt_team_2_pfp

        if not public:
            schema["b2_id"] = self.b2_id
            schema["server_id"] = self.server_id

        return schema


class _ScoreboardPlayerModel(_DepthStatsModel, _MatchPlayerModel, ApiSchema):
    def __init__(self, discord_id: int, steam_id: str,
                 alive: bool, ping: int,
                 kills: int, headshots: int,
                 assists: int, deaths: int, shots_fired: int,
                 shots_hit: int, mvps: int, score: int,
                 disconnected: bool, timestamp: datetime,
                 *args, **kwargs) -> None:
        _MatchPlayerModel.__init__(self, *args, **kwargs)
        _DepthStatsModel.__init__(
            self, kills, deaths, headshots, shots_hit, shots_fired
        )

        self.steam_id = steam_id
        self.discord_id = discord_id
        self.alive = alive
        self.ping = ping
        self.assists = assists
        self.mvps = mvps
        self.score = score
        self.disconnected = disconnected
        self.timestamp = timestamp

    def api_schema(self, public: bool = True
                   ) -> Dict[str, Union[dict, int, str, float, bool, None]]:
        """Used to get a model's API schema.

        Parameters
        ----------
        public : bool, optional
            If public safe data should only be shown, by default True

        Returns
        -------
        Dict[str, Union[dict, int, str, float, bool, None]]
        """

        return {
            "identifiers": {
                "discord": str(self.discord_id),
                "steam": self.steam_id
            },
            "timestamp": self.timestamp.timestamp(),
            "alive": self.alive,
            "ping": self.ping,
            "assists": self.assists,
            "mvps": self.mvps,
            "score": self.score,
            "disconnected": self.disconnected,
            **_DepthStatsModel.api_schema(self, public),
            **_MatchPlayerModel.api_schema(self, public)
        }


class ScoreboardModel(_MatchBaseModel, ApiSchema):
    def __init__(self, team_1: List[TeamTyping],
                 team_2: List[TeamTyping], match: MatchTyping) -> None:
        super().__init__(**match)

        self.__team_1 = team_1
        self.__team_2 = team_2

    def team_1(self) -> Generator[_ScoreboardPlayerModel, None, None]:
        """Lists players in team 1.
        Yields
        ------
        _ScoreboardPlayerModel
            Holds player data.
        """

        for player in self.__team_1:
            yield _ScoreboardPlayerModel(**player)

    def team_2(self) -> Generator[_ScoreboardPlayerModel, None, None]:
        """Lists players in team 2.
        Yields
        ------
        _ScoreboardPlayerModel
            Holds player data.
        """

        for player in self.__team_2:
            yield _ScoreboardPlayerModel(**player)

    def api_schema(self, public: bool = True
                   ) -> Dict[str, Union[dict, str, int, None]]:
        """Used to get a model's API schema.

        Parameters
        ----------
        public : bool, optional
            If public safe data should only be shown, by default True

        Returns
        -------
        Dict[str, Union[dict, str, int]]
        """

        schema = super().api_schema(public)
        team_1 = cast(dict, schema["team_1"])
        team_2 = cast(dict, schema["team_2"])

        team_1["players"] = [
            model.api_schema(public) for model in self.team_1()
        ]
        team_2["players"] = [
            model.api_schema(public) for model in self.team_2()
        ]

        return schema
