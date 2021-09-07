from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.integration import IntegrationModel


class IntegrationSettings:
    def __init__(self, defaults: List["IntegrationModel"]) -> None:
        self.defaults = defaults
