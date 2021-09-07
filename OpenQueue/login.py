import bcrypt

from typing import TYPE_CHECKING, Tuple
from sqlalchemy import select, func

from .exceptions import (
    IncorrectLoginDetails,
    LoginException
)

from .models.user import UserModel
from .user import User

from .tables import (
    user_table,
    league_table
)

from .resources import Sessions

if TYPE_CHECKING:
    from . import OpenQueue


class Login:
    def __init__(self, upper: "OpenQueue", email: str, password: str) -> None:
        self.upper = upper
        self.email = email
        self.password = password

    async def check(self) -> Tuple[UserModel, User]:
        """Used to check login & get user object / model.

        Returns
        -------
        UserModel
        User

        Raises
        ------
        LoginException
        IncorrectLoginDetails
        LoginConfrimNotCompleted
        """

        row = await Sessions.database.fetch_one(
            select([
                user_table,
                func.group_concat(
                    league_table.c.league_id
                ).label("league_ids")
            ]).select_from(
                user_table.join(
                    league_table,
                    league_table.c.user_id == user_table.c.user_id,
                    isouter=True
                )
            ).where(
                user_table.c.email == self.email
            ).group_by(league_table.c.user_id)
        )

        if not row:
            raise IncorrectLoginDetails()

        if bcrypt.checkpw(self.password.encode(), row["password"]):
            return UserModel(**row), self.upper.user(row["user_id"])
        else:
            raise IncorrectLoginDetails()

    async def new_password(self, new_password: str) -> Tuple[UserModel, User]:
        """Used to require a valid login to change password.

        Parameters
        ----------
        new_password : str

        Returns
        -------
        UserModel
        User
        """

        try:
            model, user = await self.check()
        except LoginException:
            raise
        else:
            await Sessions.database.execute(
                user_table.update().values(
                    password=bcrypt.hashpw(
                        new_password.encode(), bcrypt.gensalt()
                    )
                ).where(
                    user_table.c.user_id == model.user_id
                )
            )
            return model, user
