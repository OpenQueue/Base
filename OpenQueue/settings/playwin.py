# -*- coding: utf-8 -*-


class PlaywinSettings:
    def __init__(self, token: str, result_webhook: str,
                 route: str = "https://anticheat.playwin.me/v1/csgo") -> None:
        """Used to configure Playwin

        Parameters
        ----------
        token : str
        result_webhook : str
        route : str, optional
            by default "https://anticheat.playwin.me/v1/csgo"
        """

        self.authorization = "Bearer " + token
        self.result_webhook = result_webhook
        self.route = route
