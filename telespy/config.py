"""Config parser"""
import os
import json
from types import GenericAlias, NoneType, UnionType
from typing import Type, TypeVar
from telespy.utils import Singleton

ParseableTypes = str | int | float | bool | list["ParseableTypes"]
ParseableMap = dict[str, "ParseableTypes"]

sentinel = object()

T = TypeVar("T")

REQUIRED_CONFIG = {
	"TRACK_APP_ID": int,
	"TRACK_APP_HASH": str,
	"TRACK_USERS": list[str],
}


def resolve_type(x: UnionType | Type[T]) -> tuple[bool, Type[T]]:
	"""
	Returns may_be_none and base_type
	"""
	if isinstance(x, UnionType):
		if len(x.__args__) > 2 or len(x.__args__) == 0 or NoneType not in x.__args__:
			raise TypeError(f"Invalid UnionType: {x}")
		args = list(x.__args__)
		args.remove(NoneType)
		return True, args[0]
	return False, x


def parse_value(key: str, value: str | None, _type: T) -> T:
	"""
	Parses the value to the given type.
	"""
	may_be_none, base_type = resolve_type(_type)
	if value is None:
		if may_be_none:
			return None
		raise ValueError(f"{key} is None, but valid type is {base_type}")
	if isinstance(base_type, GenericAlias):
		child_types = base_type.__args__
		base_type = base_type.__origin__
		if base_type is list:
			return [
				parse_value(key + " child", val, child_types[0])
				for val in value.split(",")
			]
		if base_type is dict:
			parsed_json = json.loads(value)
			if not isinstance(parsed_json, dict):
				raise ValueError(f"{key} is not a valid JSON object")
			# ensure types
			for ch_key, val in parsed_json.items():
				if not isinstance(ch_key, child_types[0]):
					raise ValueError(f"{ch_key} is not a valid {child_types[0]}")
				if not isinstance(val, child_types[1]):
					raise ValueError(f"{val} is not a valid {child_types[1]}")
	return base_type(value)


def load_config_from_env() -> ParseableMap:
	"""
	Loads the config from the environment variables.
	"""
	config: ParseableMap = {}
	for key, _type in REQUIRED_CONFIG.items():
		config[key] = parse_value(key, os.environ.get(key), _type)
	return config


class Config(Singleton):
	"""
	Config parser
	"""

	def __init__(self: "Config") -> None:
		self.config = {}

	def set_config(self: "Config", config: ParseableMap) -> None:
		"""
		Sets the config.
		"""
		self.config = config

	def get(self: "Config", key: str, default: ParseableTypes = None) -> ParseableTypes:
		"""
		Returns the value of the key or the default value.
		"""
		if not self.config:
			raise ValueError("Config not loaded")
		return self.config.get(key, default)

	def __getitem__(self: "Config", key: str) -> ParseableTypes:
		"""
		Returns the value of the key.
		"""
		return self.get(key)