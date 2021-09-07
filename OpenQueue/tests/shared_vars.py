import argparse

cli = argparse.ArgumentParser()

cli.add_argument("--db_username", type=str, default="")
cli.add_argument("--db_password", type=str, default="")
cli.add_argument("--db_server", type=str, default="")
cli.add_argument("--db_port", type=int, default=3306)
cli.add_argument("--db_database", type=str, default="")

cli.add_argument("--b2_key_id", type=str, default="")
cli.add_argument("--b2_application_key", type=str, default="")
cli.add_argument("--b2_bucket_id", type=str, default="")
cli.add_argument("--b2_cdn_url", type=str, default="")

cli.add_argument("--dathost_email", type=str, default="")
cli.add_argument("--dathost_password", type=str, default="")
cli.add_argument("--dathost_clone_id", type=str, default="")
cli.add_argument("--dathost_timeout", type=int, default=240)

cli.add_argument("--steam_api_key", type=str, default="")
cli.add_argument("--steam_steam_id", type=str, default="")

cli.add_argument("--smtp_hostname", type=str, default="")
cli.add_argument("--smtp_port", type=int, default=25)
cli.add_argument("--smtp_email", type=str, default="")
cli.add_argument("--smtp_username", type=str, default="")
cli.add_argument("--smtp_password", type=str, default="")

cli.add_argument("--webhook_key", type=str, default="")
cli.add_argument(
    "--webhook_global_webhook_url", type=str, default=""
)

args = vars(cli.parse_args())


DATABASE = {
    "username": args["db_username"],
    "password": args["db_password"],
    "server": args["db_server"],
    "port": args["db_port"],
    "database": args["db_database"]
}

BACKBLAZE = {
    "key_id": args["b2_key_id"],
    "application_key": args["b2_application_key"],
    "bucket_id": args["b2_bucket_id"],
    "cdn_url": args["b2_cdn_url"]
}

DATHOST = {
    "email": args["dathost_email"],
    "password": args["dathost_password"],
    "clone_id": args["dathost_clone_id"],
    "timeout": args["dathost_timeout"]
}

STEAM = {
    "api_key": args["steam_api_key"],
    "steam_id": args["steam_steam_id"]
}

WEBHOOK = {
    "key": args["webhook_key"],
    "global_webhook_url": args["webhook_global_webhook_url"]
}

SMTP = {
    "hostname": args["smtp_hostname"],
    "port": args["smtp_port"],
    "email": args["smtp_email"],
    "username": args["smtp_username"],
    "password": args["smtp_password"]
}
