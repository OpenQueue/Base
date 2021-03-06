# -*- coding: utf-8 -*-

# Base objects to use for other modes.


from typing import Callable, Dict, Union


class ApiSchema:
    api_schema: Callable[
        [bool],
        Dict[str, Union[str, float, int, bool, list, dict, None]]
    ]


class KdrMethod:
    kills: int
    deaths: int

    @property
    def kdr(self) -> float:
        return (
            round(self.kills / self.deaths, 2)
            if self.kills > 0 and self.deaths > 0 else 0.00
        )


class HsPercentageMethod:
    kills: int
    headshots: int

    @property
    def hs_percentage(self) -> float:
        return (
            round((self.headshots / self.kills) * 100, 2)
            if self.kills > 0 and self.headshots > 0 else 0.00
        )


class HitPercentageMethod:
    shots_hit: int
    shots_fired: int

    @property
    def hit_percentage(self) -> float:
        return (
            round((self.shots_hit / self.shots_fired) * 100, 2)
            if self.shots_fired > 0 and self.shots_hit > 0 else 0.00
        )


class _DepthStatsModel(KdrMethod, HsPercentageMethod,
                       HitPercentageMethod, ApiSchema):
    def __init__(self, kills: int, deaths: int,
                 headshots: int, shots_hit: int,
                 shots_fired: int,
                 *args, **kwargs) -> None:
        self.kills = kills
        self.deaths = deaths
        self.headshots = headshots
        self.shots_hit = shots_hit
        self.shots_fired = shots_fired

    def api_schema(self, public: bool = True
                   ) -> Dict[str, Union[float, int]]:
        """Used to get a model's API schema.

        Parameters
        ----------
        public : bool, optional
            If public safe data should only be shown, by default True

        Returns
        -------
        Dict[str, Union[float, int]]
        """

        return {
            "kills": self.kills,
            "deaths": self.deaths,
            "headshots": self.headshots,
            "shots_hit": self.shots_hit,
            "shots_fired": self.shots_fired,
            "kdr": self.kdr,
            "hs_percentage": self.hs_percentage,
            "hit_percentage": self.hit_percentage
        }
