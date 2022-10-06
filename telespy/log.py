"""Setup logging"""
import sys
import logging
from typing import Any


class RedactingFilter(logging.Filter):
	"""Filter that redacts secret values"""

	def __init__(self: "RedactingFilter", replace_map: dict[str, str]):
		super().__init__()
		self._patterns = {str(k): str(v) for k, v in replace_map.items()}

	def filter(  # noqa: A003
		self: "RedactingFilter", record: logging.LogRecord
	) -> bool:
		record.msg = self.redact(record.msg)
		if isinstance(record.args, dict):
			new_args = {}
			for k in record.args.keys():
				new_args[k] = self.redact(record.args[k])
			record.args = new_args
		elif record.args:
			record.args = tuple(self.redact(arg) for arg in record.args)
		return True

	def redact(self: "RedactingFilter", msg: Any) -> Any:
		"""Redact a message"""
		if isinstance(msg, int):
			if str(msg) in self._patterns:
				return 0
			return msg
		if isinstance(msg, float):
			if str(msg) in self._patterns:
				return 0.0
			return msg
		msg = msg if isinstance(msg, str) else str(msg)
		for pattern, replace_val in self._patterns.items():
			msg = msg.replace(pattern, f"--REDACTED--{replace_val}--")
		return msg


def init_logging(
	level: int = logging.INFO,
	log_file: str = "telespy.log",
	secret_values: dict[str, str] | None = None,
) -> None:
	"""Initialize logging"""
	# Import coloredlogs if available and setup logging to log_file
	try:
		coloredlogs = __import__("coloredlogs")
	except ImportError:
		coloredlogs = None

	formatter = logging.Formatter(
		"[%(asctime)s] %(name)s (%(levelname)s) -> %(message)s"
	)
	if not secret_values:
		secret_values = {}

	console_handler = logging.StreamHandler(sys.stdout)
	console_handler.setLevel(level)
	console_handler.setFormatter(formatter)
	console_handler.addFilter(RedactingFilter(secret_values))

	file_handler = logging.FileHandler(log_file, mode="a")
	file_handler.setLevel(logging.DEBUG)
	file_handler.setFormatter(formatter)
	file_handler.addFilter(RedactingFilter(secret_values))

	logging.getLogger().handlers = []
	logging.getLogger().setLevel(logging.DEBUG)
	logging.getLogger().addHandler(console_handler)
	logging.getLogger().addHandler(file_handler)

	# If coloredlogs is available, use it to color the log output
	if coloredlogs:
		coloredlogs.install(
			level=level,
			fmt="[%(asctime)s] %(name)s (%(levelname)s) -> %(message)s",
			datefmt="%H:%M:%S",
			field_styles={"asctime": {"color": "green"}},
		)
	logging.info("--- new launch ---")