# -*- coding: utf-8 -*-

from typing import Dict, Generator, TypedDict, Union, List, cast
from datetime import datetime

from ..resources import Config

from .base import HsPercentageMethod, KdrMethod, _DepthStatsModel, ApiSchema


class UserMapTying(TypedDict):
    map: str
    wins: int
    losses: int
    ties: int
    kills: int
    deaths: int


class UserMapModel(ApiSchema):
    def __init__(self, map: str, wins: int, losses: int, ties: int,
                 kills: int, deaths: int) -> None:

        self.map = map
        self.wins = int(wins)
        self.losses = int(losses)
        self.ties = int(ties)
        self.kills = int(kills)
        self.deaths = int(deaths)

    @property
    def kdr(self) -> float:
        return (
            round(self.kills / self.deaths, 2)
            if self.kills > 0 and self.deaths > 0 else 0
        )

    @property
    def win_rate(self) -> float:
        if self.wins and self.losses:
            return round((self.losses / self.wins) * 100, 2)
        elif self.wins:
            return 100
        else:
            return 0

    def api_schema(self, public: bool = True
                   ) -> Dict[str, Union[str, int, float]]:
        """Used to get API schema of model.

        Parameters
        ----------
        public : bool, optional
            by default True

        Returns
        -------
        Dict[str, Union[str, int, float]]
        """

        return {
            "map": self.map,
            "wins": self.wins,
            "losses": self.losses,
            "ties": self.ties,
            "win_rate": self.win_rate,
            "deaths": self.deaths,
            "kills": self.kills,
            "kdr": self.kdr
        }


class UserBaseModel(ApiSchema):
    def __init__(self, name: str, user_id: str,
                 timestamp: datetime,
                 pfp_extension: Union[str, None] = None,
                 steam_id: Union[str, None] = None,
                 discord_id: Union[str, None] = None,
                 *args, **kwargs) -> None:

        # Is encrypted with cryptography's Fernet
        # but lets just make sure it's never saved in the
        # user model.
        kwargs.pop("password", None)

        self.steam_id = steam_id
        self.user_id = user_id
        self.discord_id = discord_id
        self.timestamp = timestamp
        self.name = name
        self.pfp = "{}{}/{}{}".format(
            Config.b2.cdn_url, Config.pfp.pathway, user_id, pfp_extension
        ) if pfp_extension else None

    def api_schema(self, public: bool = True
                   ) -> Dict[str, Union[str, float, dict]]:
        """Used to get API schema of model.

        Parameters
        ----------
        public : bool, optional
            by default True

        Returns
        -------
        Dict[str, Union[str, int, dict]]
        """

        data = {
            "name": self.name,
            "pfp": self.pfp,
            "identifiers": {
                "discord": str(self.discord_id) if self.discord_id else None,
                "steam": self.steam_id,
                "user": self.user_id
            },
            "timestamp": self.timestamp.timestamp(),
        }

        return data


class UserModel(UserBaseModel, ApiSchema):
    def __init__(self, email: str, email_confirmed: bool,
                 league_ids: Union[str, List[str]] = [],
                 dathost_id: Union[str, None] = None,
                 *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.dathost_id = dathost_id
        self.email = email
        self.email_confirmed = email_confirmed

        if isinstance(league_ids, str):
            self.league_ids = league_ids.split(",")
        else:
            self.league_ids = league_ids

    def api_schema(self, public: bool = True
                   ) -> Dict[str, Union[str, float, dict, list]]:
        """Used to get API schema of model.

        Parameters
        ----------
        public : bool, optional
            by default True

        Returns
        -------
        Dict[str, Union[str, float, dict, list]]
        """

        data = cast(dict, super().api_schema(public))

        if not public:
            data["identifiers"]["email"] = self.email
            data["identifiers"]["dathost"] = self.dathost_id

        data = {
            **data,
            "league_ids": self.league_ids,
            "email_confirmed": self.email_confirmed
        }

        return data


class UserOverviewModel(UserBaseModel, KdrMethod,
                        HsPercentageMethod, ApiSchema):
    def __init__(self, kills: int, deaths: int,
                 headshots: int, matches: int, elo: int,
                 *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.kills = kills
        self.deaths = deaths
        self.headshots = headshots
        self.matches = matches
        self.elo = elo

    def api_schema(self, public: bool = True
                   ) -> Dict[str, Union[str, float, dict, list]]:
        return {
            **super().api_schema(public),
            "matches": self.matches,
            "statistics": {
                "kills": self.kills,
                "deaths": self.deaths,
                "headshots": self.headshots,
                "elo": self.elo,
                "kdr": self.kdr,
                "hs_percentage": self.hs_percentage
            }
        }


class StatisticModel(UserBaseModel, _DepthStatsModel, ApiSchema):
    def __init__(self, league_id: str, elo: float,
                 assists: int, mvps: int,
                 maps: List[UserMapTying],
                 *args, **kwargs) -> None:
        UserBaseModel.__init__(self, *args, **kwargs)
        _DepthStatsModel.__init__(self, *args, **kwargs)

        self.league_id = league_id
        self.elo = elo
        self.assists = assists
        self.mvps = mvps

        self.__maps = maps

    def maps(self) -> Generator[UserMapModel, None, None]:
        for map in self.__maps:
            yield UserMapModel(**map)

    def api_schema(self, public: bool = True
                   ) -> Dict[str, Union[dict, str, int, float, list]]:
        """Used to get API schema of model.

        Parameters
        ----------
        public : bool, optional
            by default True

        Returns
        -------
        Dict[str, Union[dict, str, int, float, list]]
        """

        return {
            **UserBaseModel.api_schema(self, public),
            "league_id": self.league_id,
            "statistics": {
                "elo": self.elo,
                "assists": self.assists,
                "mvps": self.mvps,
                **_DepthStatsModel.api_schema(self, public)
            },
            "maps": [
                map.api_schema(public) for map in self.maps()
            ] if self.__maps else []
        }
