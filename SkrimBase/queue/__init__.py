# -*- coding: utf-8 -*-

from asyncio import iscoroutinefunction

from ..misc import str_uuid4
from ..user import User
from ..exceptions import (
    InvalidUser,
    UserAlreadyInQueue,
    QueueFull
)
from ..resources import QueueGlobal, Sessions

from ..models.queue import QueueModel


class Queue:
    """Used to handle the queue of a match, does NOT
       handle match creation.
    """

    def __init__(self, capacity: int = 10) -> None:
        self.queue_id = str_uuid4()
        self.waiting = []
        self.map = None

        self.capacity = capacity

    def get(self) -> QueueModel:
        return QueueModel(self.queue_id, self.waiting, self.map)

    async def select_map(self, map: str) -> None:
        """Used to set map

        Parameters
        ----------
        map : str
        """

        self.map = map

        await Sessions.scheduler.spawn(
            self._call_events(QueueGlobal.on_map_select)
        )

    async def _call_events(self, list_: list) -> None:
        """Used to call on queue full events.
        """

        get = self.get()

        for func in list_:
            if iscoroutinefunction(func):
                await func(queue=get)
            else:
                func(queue=get)

    async def join(self, user: User) -> None:
        """Used to enter a user into a queue.

        Parameters
        ----------
        user : User

        Raises
        ------
        UserAlreadyInQueue
        QueueFull
        InvalidUser
        """

        if user.user_id in self.waiting:
            raise UserAlreadyInQueue()

        waiting_len = len(self.waiting)

        if waiting_len == self.capacity:
            raise QueueFull()

        if not await user.exists():
            raise InvalidUser()

        self.waiting.append(user.user_id)

        if waiting_len + 1 == self.capacity:
            await Sessions.scheduler.spawn(
                self._call_events(QueueGlobal.on_queue_full)
            )

    def leave(self, user: User) -> None:
        """Used to remove a player in queue.

        Parameters
        ----------
        user : User
        """

        if user.user_id in self.waiting:
            self.waiting.remove(user.user_id)
