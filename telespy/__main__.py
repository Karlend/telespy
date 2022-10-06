"""Entry point"""
import sys

if __package__ != "telespy":
	print("[X] Error: run track with `python -m telespy`")
	sys.exit(1)

import argparse
from dotenv import load_dotenv  # type: ignore
from telespy.config import Config, load_config_from_env
from telespy.log import init_logging
import logging

logger = logging.getLogger(__name__)
__version__ = "1"


def main(argv: list[str]):
	"""
	Main function.
	"""
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
		},  # type: ignore
	)

	from telespy.main import main as main_entry_point  # type: ignore

	assert isinstance(config["TRACK_APP_ID"], int), "TRACK_APP_ID must be an int"  # nosec
	assert isinstance(config["TRACK_APP_HASH"], str), "TRACK_APP_HASH must be a str"  # nosec
	assert isinstance(  # nosec
		config["TRACK_USERS"], list
	), "TRACK_USERS must be a list"
	return main_entry_point()

if __name__ == "__main__":
	main(sys.argv[1:])