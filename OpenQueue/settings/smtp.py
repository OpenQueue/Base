import validators


class SmtpSettings:
    def __init__(self, hostname: str, port: int, email: str,
                 use_tls: bool = False, username: str = None,
                 password: str = None,
                 confirmation: str = "https://skrim.gg/api/auth/site/confirmation/"  # noqa: E501
                 ) -> None:
        """SMTP Connection settings.

        Parameters
        ----------
        hostname : str
        port : int
        use_tls : bool, optional
            by default False
        username : str, optional
        password : str, optional
        confirmation : str, optional
            URL for confirmation
        """

        self.hostname = hostname
        self.port = port
        self.use_tls = use_tls
        self.username = username
        self.password = password

        if validators.email(email):
            self.email = email
        else:
            raise Exception("Invalid email!")

        if not validators.url(confirmation):
            raise Exception("Invalid confirmation url!")

        self.confirmation = (
            confirmation if confirmation[-1:] == "/" else confirmation + "/"
        )
