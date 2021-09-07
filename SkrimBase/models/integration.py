from typing import Dict, Union
from .base import ApiSchema


class IntegrationModel(ApiSchema):
    def __init__(self, name: str, logo: str, auth_url: Union[str, None],
                 globally_required: bool) -> None:
        self.name = name
        self.logo = logo
        self.auth_url = auth_url
        self.globally_required = globally_required

    def api_schema(self, public: bool = True
                   ) -> Dict[str, Union[str, bool, None]]:
        return {
            "name": self.name,
            "logo": self.logo,
            "auth_url": self.auth_url,
            "globally_required": self.globally_required
        }
