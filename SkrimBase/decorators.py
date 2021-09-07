# -*- coding: utf-8 -*-

from functools import wraps

from .users import Users
from .exceptions import InvalidUser, InvalidRegion
from .resources import Config
from .exceptions import DemoTickRateAboveGame, InvalidTickRate
from .constants import REGIONS


def validate_users(*params):
    """Decorator what validates Nexus League's user IDs.
    """

    def decorator(func_):
        @wraps(func_)
        async def _validate(*args, **kwargs):
            user_ids = []

            for param in params:
                if isinstance(kwargs[param], list):
                    user_ids += kwargs[param]
                else:
                    user_ids.append(kwargs[param])

            try:
                await Users(user_ids).validate()
            except InvalidUser:
                raise
            else:
                return await func_(*args, **kwargs)

        return _validate

    return decorator


def validate_region(key: str):
    """Decorator what validates region.
    """

    def decorator(func):
        @wraps(func)
        def _validate(*args, **kwargs):
            if (key in kwargs and kwargs[key] is not None
                    and kwargs[key] not in REGIONS):
                raise InvalidRegion()

            return func(*args, **kwargs)

        return _validate

    return decorator


def validate_tickrate(game_key: str, demo_key: str):
    """Used to ensure tickrate is valid.
    """

    def decorator(func):
        @wraps(func)
        def _validate(*args, **kwargs):
            if (game_key in kwargs and kwargs[game_key] and demo_key in kwargs
                    and kwargs[demo_key]):

                if kwargs[demo_key] > kwargs[game_key]:
                    raise DemoTickRateAboveGame()

                if (kwargs[game_key] not in Config.game_tick.game or
                        kwargs[demo_key] not in Config.game_tick.demo):
                    raise InvalidTickRate()

            return func(*args, **kwargs)

        return _validate

    return decorator
