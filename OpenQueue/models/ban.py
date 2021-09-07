# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Dict, Union

from .base import ApiSchema


class BanModel(ApiSchema):
    def __init__(self, ban_id: str, user_id: str,
                 global_: bool, reason: str,
                 timestamp: datetime, expires: datetime,
                 revoked: bool, banner_id: str,
                 league_id: str) -> None:
        self.ban_id = ban_id
        self.user_id = user_id
        self.global_ = global_
        self.reason = reason
        self.timestamp = timestamp
        self.expires = expires
        self.revoked = revoked
        self.banner_id = banner_id
        self.is_expired = datetime.now() >= self.expires or self.revoked
        self.league_id = league_id

    def api_schema(self, public: bool = True
                   ) -> Dict[str, Union[str, int]]:
        """Used to get API schema.

        Parameters
        ----------
        public : bool, optional
            by default True

        Returns
        -------
        Dict[str, Union[str, int]]
        """

        schema = {
            "league_id": self.league_id,
            "ban_id": self.ban_id,
            "user_id": self.user_id,
            "global": self.global_,
            "reason": self.reason,
            "timestamp": self.timestamp.timestamp(),
            "expires": self.expires.timestamp(),
            "revoked": self.revoked,
            "is_expired": self.is_expired
        }

        if not public:
            schema["banner_id"] = self.banner_id

        return schema


class BanRevokedModel(ApiSchema):
    def __init__(self, user_id: str, ban_id: str, revoked: bool,
                 league_id: str = None) -> None:
        self.user_id = user_id
        self.ban_id = ban_id
        self.revoked = revoked
        self.league_id = league_id

    def api_schema(self, public: bool = True
                   ) -> Dict[str, Union[str, bool, None]]:
        """Used to get API schema.

        Parameters
        ----------
        public : bool, optional
            by default True

        Returns
        -------
        Dict[str, Union[str, bool, None]]
        """

        return {
            "user_id": self.user_id,
            "league_id": self.league_id,
            "ban_id": self.ban_id,
            "revoked": self.revoked
        }
