# -*- coding: utf-8 -*-


class DathostSettings:
    def __init__(self, email: str, password: str, clone_id: str = None,
                 timeout: float = 60.0) -> None:
        """Dathost settings.

        Parameters
        ----------
        email : str
        password : str
        clone_id : str
            Server to clone if more servers needed.
        timeout : float, optional
            by default 60.0
        """

        self.email = email
        self.password = password
        self.clone_id = clone_id
        self.timeout = timeout
