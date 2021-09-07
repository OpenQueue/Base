from .base_test import TestBase

from ..models.user import UserModel
from ..user import User

from ..models.league import LeagueModel
from ..models.integration import IntegrationModel
from ..exceptions import LoginException


class TestUser(TestBase):
    async def test_user(self) -> None:
        """Tests
            1. User creation
            2. Returned model
            3. User.exists
            4. User.get returned model
        """

        model, user = await self.skrim.create_user(
            name="Ward",
            email="wardpearce@protonmail.com",
            password="epicpassword123"
        )

        self.assertIsInstance(model, UserModel)
        self.assertIsInstance(user, User)

        self.assertTrue(await user.exists())

        self.assertIsInstance(await user.get(), UserModel)

        await user.update(
            email_confirmed=True
        )

        model, user = await self.skrim.login(
            email="wardpearce@protonmail.com",
            password="epicpassword123"
        ).check()

        self.assertIsInstance(model, UserModel)
        self.assertIsInstance(user, User)

    async def test_invalid_login(self) -> None:
        """Test invalid logins.
        """

        with self.assertRaises(LoginException):
            await self.skrim.login(
                email="wardpearce@protonmail.com",
                password="123"
            ).check()

        with self.assertRaises(LoginException):
            await self.skrim.login(
                email="fake@protonmail.com",
                password="123"
            ).check()

        with self.assertRaises(LoginException):
            await self.skrim.login(
                email="fake@protonmail.com",
                password="epicpassword123"
            ).check()

    async def test_create_league(self) -> None:
        """Tests
            1. Create League
            2. Returned model
            3. League.get returned model
            4. UserModel.league_ids
            5. User.leagues
        """

        _, user = await self.skrim.create_user(
            name="Lubricant Jam",
            email="lubeboi@pp.com",
            password="epicpassword123"
        )

        model, league = await user.create_league(
            league_id="nexos",
            league_name="nexos league",
            region="new_york_city"
        )

        self.assertFalse(await league.integration_enabled("playwin"))

        self.assertIsInstance(model, LeagueModel)
        self.assertIsInstance(await league.get(), LeagueModel)

        user_model = await user.get()
        self.assertListEqual(user_model.league_ids, [model.league_id])

        league_ids = [
            league_.league_id async for league_, _ in user.leagues()
        ]

        self.assertListEqual(league_ids, [model.league_id])

        self.assertTrue(await league.exists())

        global_league_ids = [
            league_.league_id async for league_, _ in self.skrim.leagues()
        ]

        self.assertListEqual(global_league_ids, [model.league_id])

        async for integration in league.integrations():
            self.assertIsInstance(integration, IntegrationModel)
