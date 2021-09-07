# -*- coding: utf-8 -*-


from typing import List


class GameTickSettings:
    def __init__(self, demo: List[int] = [16, 32, 64, 128],
                 game: List[int] = [64, 128]) -> None:
        """Used to configure gametick.

        Parameters
        ----------
        demo : List[int], optional
            by default [16, 32, 64, 128]
        game : List[int], optional
            by default [64, 128]
        """

        self.demo = demo
        self.game = game
