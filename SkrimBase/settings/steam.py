# -*- coding: utf-8 -*-

from datetime import timedelta


class SteamSettings:
    def __init__(self, api_key: str, steam_id: str,
                 api_url: str = "https://api.steampowered.com",
                 token_expires: timedelta = timedelta(days=31)) -> None:
        """Settings for steam.

        Parameters
        ----------
        api_key : str
        steam_id : str
        api_url : str, optional
            by default "https://api.steampowered.com"
        token_expires : timedelta, optional
            by default timedelta(days=31)
        """

        self.api_key = api_key
        self.token_expires = token_expires
        self.steam_id = steam_id

        if api_url[0] == "/":
            self.api_url = api_url[1:]
        else:
            self.api_url = api_url
