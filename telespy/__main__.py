"""Entry point"""
import sys
import argparse
import logging
from dotenv import load_dotenv  # type: ignore

from telespy.config import Config, load_config_from_env
from telespy.log import init_logging

logger = logging.getLogger(__name__)
__version__ = "1"


def main(argv: list[str]) -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        prog="telespy",
        description="Telegram spy bot",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level",
    )
    args = parser.parse_args(argv)

    load_dotenv()

    config = Config()
    config.set_config(load_config_from_env())

    init_logging(
        level=logging.getLevelName(args.log_level),
        secret_values={
            config["TRACK_APP_ID"]: "TRACK_APP_ID",
            config["TRACK_APP_HASH"]: "TRACK_APP_HASH",
            config["TRACK_BOT_TOKEN"]: "TRACK_BOT_TOKEN",
        },
    )

    from telespy.main import main as main_entry_point  # type: ignore

    assert isinstance(config["TRACK_APP_ID"], int), "TRACK_APP_ID must be an int"  # nosec
    assert isinstance(config["TRACK_APP_HASH"], str), "TRACK_APP_HASH must be a str"  # nosec
    assert isinstance(config["TRACK_BOT_TOKEN"], str), "TRACK_BOT_TOKEN must be a str"  # nosec
    assert isinstance(config["TRACK_ADMINS"], list), "TRACK_ADMINS must be a list"  # nosec

    return main_entry_point(config)


if __name__ == "__main__":
    if __package__ != "telespy":
        print("[X] Error: run track with `python -m telespy`")
        sys.exit(1)
    main(sys.argv[1:])
