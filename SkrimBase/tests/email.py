from .base_test import TestBase
from ..resources import Config

from ..email import send_email


class TestEmail(TestBase):
    async def test_send_email(self) -> None:
        await send_email(
            to="wpearce6@gmail.com",
            subject="Skrim.gg | Please confirm your email!",
            header="Welcome to Skrim.gg, {}!".format("Ward"),
            body="""Thanks for joining Skrim.gg!
            Please click the button to confirm your email.

            If you didn't sign up to Skrim.gg, please
            ignore this email.""",
            button="Confirm my email",
            url=Config.smtp.confirmation + "someRadom_codawd"
        )
