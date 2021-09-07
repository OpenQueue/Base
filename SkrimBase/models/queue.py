# -*- coding: utf-8 -*-

from typing import Dict, List, Union

from .base import ApiSchema


class QueueModel(ApiSchema):
    def __init__(self, queue_id: str, waiting: List[str],
                 map: Union[str, None]) -> None:
        """Queue Model.

        Parameters
        ----------
        queue_id : str
            Unique queue ID.
        waiting : List[str]
            List of user IDs.
        map : Union[str, None]
        """

        self.queue_id = queue_id
        self.waiting = waiting
        self.map = map

    def api_schema(self, public: bool = True
                   ) -> Dict[str, Union[str, List[str], None]]:
        """Used to get a model's API schema.

        Parameters
        ----------
        public : bool, optional
            If public safe data should only be shown, by default True

        Returns
        -------
        Dict[str, Union[str, List[str]]]
        """

        return {
            "queue_id": self.queue_id,
            "waiting": self.waiting,
            "map": self.map
        }
