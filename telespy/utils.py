class SingletonMeta(type):
	"""Metaclass for singletons"""

	_instance = None

	def __call__(cls: "SingletonMeta", *args: any, **kwargs: any) -> "SingletonMeta":
		if cls._instance is None:
			cls._instance = super().__call__()
		return cls._instance

class Singleton(metaclass=SingletonMeta):
	"""Singleton base class"""