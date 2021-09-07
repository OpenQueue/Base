# -*- coding: utf-8 -*-

class DatabaseSettings:
    def __init__(
                self,
                username: str,
                password: str,
                server: str,
                database: str,
                port: int = 3306,
                engine: str = "mysql"
                ) -> None:
        """Database settings.

        Parameters
        ----------
        username : str
        password : str
        server : str
        database : str
        port : int, optional
            by default 3306
        engine : str, optional
            by default "mysql"

        Raises
        ------
        UnSupportedEngine
        """

        self.username = username
        self.password = password
        self.server = server
        self.port = port
        self.database = database
        self.engine = engine

        if engine == "mysql":
            self.alchemy_engine = "pymysql"
        elif engine == "sqlite":
            self.alchemy_engine = "sqlite3"
        elif engine == "postgresql":
            self.alchemy_engine = "psycopg2"
        else:
            raise Exception("Unsupported databae engine")

        self.url = "://{}:{}@{}:{}/{}?charset=utf8mb4".format(
            self.username,
            self.password,
            self.server,
            self.port,
            self.database
        )
