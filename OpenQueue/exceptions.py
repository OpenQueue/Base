# -*- coding: utf-8 -*-


from typing import Any, List


class OpenQueueException(Exception):
    """Base exception for Nexus League.
    """

    def __init__(self, msg: str = "Internal error", status_code: int = 500,
                 *args: object) -> None:

        self.msg = msg
        self.status_code = status_code

        super().__init__(*args)


class UserTaken(OpenQueueException):
    """Raised when a user ID is taken.
    """

    def __init__(self, msg: str = "User taken", status_code: int = 400,
                 *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)


class InvalidUser(OpenQueueException):
    """Raised when User ID is invalid.
    """

    def __init__(self, msg: str = "Invalid user ID", status_code: int = 404,
                 invalid_users: List[str] = [], *args: object) -> None:
        self.invalid_users = invalid_users
        super().__init__(msg=msg, status_code=status_code, *args)


class CaptainsNotInTeam(OpenQueueException):
    """Raised when given captain not in team.
    """

    def __init__(self, msg: str = "Captain not in teams",
                 status_code: int = 400, *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)


class LeagueTaken(OpenQueueException):
    """Raised when league is taken.
    """

    def __init__(self, msg: str = "League taken", status_code: int = 400,
                 *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)


class LeagueInvalid(OpenQueueException):
    """Raised when a league ID is invalid.
    """

    def __init__(self, msg: str = "Invalid League ID", status_code: int = 404,
                 *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)


class InvalidRegion(OpenQueueException):
    """Raised when region is incorrect.
    """

    def __init__(self, msg: str = "Region not supported",
                 status_code: int = 400, *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)


class InvalidMatchID(OpenQueueException):
    """Raised when match ID is invalid.
    """

    def __init__(self, msg: str = "Match ID not found", status_code: int = 404,
                 *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)


class MatchAlreadyEnded(OpenQueueException):
    """Raised when match already ended.
    """

    def __init__(self, msg: str = "Match already ended",
                 status_code: int = 400, *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)


class InvalidBan(OpenQueueException):
    """Raised when ban ID is invalid.
    """

    def __init__(self, msg: str = "Ban ID not found", status_code: int = 404,
                 *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)


class UserAlreadyInQueue(OpenQueueException):
    """Raised when a user is already in queue.
    """

    def __init__(self, msg: str = "User already in queue",
                 status_code: int = 400, *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)


class QueueFull(OpenQueueException):
    """Raised when queue is full.
    """

    def __init__(self, msg: str = "Queue is full",
                 status_code: int = 400, *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)


class MatchCancelled(OpenQueueException):
    """Base for match cancelled.
    """

    def __init__(self, msg: str = "Match cancelled",
                 status_code: int = 400, *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)


class UsersBanned(MatchCancelled):
    """Raised when users banned for match.
    """

    def __init__(self, bans: List[Any], msg: str = "Users banned",
                 status_code: int = 400, *args: object) -> None:
        self.bans = bans
        super().__init__(msg=msg, status_code=status_code, *args)


class DemoTickRateAboveGame(OpenQueueException):
    """Raised when demo tickrate above game tickrate.
    """

    def __init__(self, msg: str = "Demo tickrate above game tickrate",
                 status_code: int = 400, *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)


class InvalidTickRate(OpenQueueException):
    def __init__(self, msg: str = "Invalid tickrate provided",
                 status_code: int = 400, *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)


class NoDemoToAnalyze(OpenQueueException):
    def __init__(self, msg: str = "No demo saved", status_code: int = 400,
                 *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)


class InvalidPfpUrl(OpenQueueException):
    def __init__(self, msg: str = "Invalid pfp url",
                 status_code: int = 400, *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)


class PlayersNotGiven(OpenQueueException):
    def __init__(self, msg: str = "Players must be given",
                 status_code: int = 400, *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)


class ExternalInUse(OpenQueueException):
    def __init__(self, msg: str = "External ID in use",
                 status_code: int = 400, *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)


class LoginException(OpenQueueException):
    def __init__(self, msg: str = "Login error",
                 status_code: int = 500, *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)


class IncorrectLoginDetails(LoginException):
    def __init__(self, msg: str = "Password or email incorrect",
                 status_code: int = 401, *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)


class InvalidDathostDetails(LoginException):
    def __init__(self, msg: str = "Raised when dathost login incorrect",
                 status_code: int = 401, *args: object) -> None:
        super().__init__(msg=msg, status_code=status_code, *args)
