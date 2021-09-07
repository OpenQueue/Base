import aiosmtplib

from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader, select_autoescape
from os import path

from ..resources import Config


jinja2 = Environment(
    loader=FileSystemLoader(path.dirname(path.realpath(__file__))),
    autoescape=select_autoescape(["html", "xml"])
)


def render_html(file: str, params: dict) -> str:
    return (jinja2.get_template(file)).render(**params)


async def send_email(to: str, subject: str, header: str, body: str,
                     button: str = None, url: str = None) -> None:
    """Used to send mail.

    Parameters
    ----------
    to : str
    subject : str
    header : str
    body : str
    button : str, optional
        by default None
    url : str, optional
        by default None
    """

    message = MIMEText(render_html(
        "template.html",
        {
            "header": header,
            "body": body,
            "button_text": button,
            "url": url
        }
    ), "html", "utf-8")
    message["From"] = Config.smtp.email
    message["To"] = to
    message["Subject"] = subject

    await aiosmtplib.send(
        message,
        hostname=Config.smtp.hostname,
        port=Config.smtp.port,
        use_tls=Config.smtp.use_tls,
        password=Config.smtp.password,
        username=Config.smtp.username
    )
