# -*- coding: utf-8 -*-

from typing import Dict, Union
from datetime import datetime

from .base import ApiSchema


class LeagueModel(ApiSchema):
    def __init__(self, league_id: str, league_name: str,
                 kill: float,
                 death: float, round_won: float,
                 round_lost: float, match_won: float,
                 match_lost: float, assist: float,
                 mate_blinded: float, headshot: float,
                 mate_killed: float, score: float,
                 timestamp: datetime,
                 disabled: bool, banned: bool,
                 allow_api_access: str,
                 user_id: str,
                 dathost_id: Union[str, None],
                 email: str,
                 region: str,
                 tickrate: int, demo_tickrate: int,
                 webhooks: Dict[str, str] = None) -> None:

        self.league_id = league_id
        self.league_name = league_name
        self.user_id = user_id
        self.kill = kill
        self.death = death
        self.round_won = round_won
        self.round_lost = round_lost
        self.match_won = match_won
        self.match_lost = match_lost
        self.assist = assist
        self.headshot = headshot
        self.score = score
        self.mate_blinded = mate_blinded
        self.mate_killed = mate_killed
        self.timestamp = timestamp
        self.disabled = disabled
        self.banned = banned
        self.allow_api_access = allow_api_access
        self.dathost_id = dathost_id
        self.email = email
        self.region = region
        self.webhooks = webhooks
        self.tickrate = tickrate
        self.demo_tickrate = demo_tickrate

    def api_schema(self, public: bool = True
                   ) -> Dict[str, Union[str, int, float, dict, list, None]]:
        """Used to get a model's API schema.

        Parameters
        ----------
        public : bool, optional
            If public safe data should only be shown, by default True

        Returns
        -------
        Dict[str, Union[str, int, float, list, dict, None]]
        """

        schema = {
            "league_id": self.league_id,
            "league_name": self.league_name,
            "identifiers": {
                "user": self.user_id
            },
            "timestamp": self.timestamp.timestamp(),
            "disabled": self.disabled,
            "banned": self.banned,
            "allow_api_access": self.allow_api_access,
            "region": self.region,
            "tickrate": {
                "game": self.tickrate,
                "demo": self.demo_tickrate
            },
        }

        if public:
            return schema

        schema["identifiers"]["dathost"] = self.dathost_id
        schema["identifiers"]["email"] = self.email

        return {
            "webhooks": self.webhooks,
            "elo": {
                "kill": self.kill,
                "death": self.death,
                "round_won": self.round_won,
                "round_lost": self.round_lost,
                "match_won": self.match_won,
                "match_lost": self.match_lost,
                "assist": self.assist,
                "mate_blinded": self.mate_blinded,
                "mate_killed": self.mate_killed,
                "headshot": self.headshot,
                "score": self.score
            },
            **schema
        }
