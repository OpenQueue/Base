# -*- coding: utf-8 -*-

from datetime import timedelta


class BanSettings:
    def __init__(self, reason: str, expires: timedelta,
                 banner_id: str) -> None:
        """Used to give users a ban reason.

        Parameters
        ----------
        reason : str
        expires : timedelta
        banner_id : str
        """

        self.reason = reason
        self.expires = expires
        self.banner_id = banner_id
