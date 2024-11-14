class SingletonMeta(type):
    """A thread-safe implementation of Singleton."""
    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            # Create a new instance if it doesn't exist
            cls._instance = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instance