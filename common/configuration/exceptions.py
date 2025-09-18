class ConfigurationError(Exception):
    """Base class for all configuration-related exceptions."""
    pass


class ConfigurationNotLoadedError(ConfigurationError):
    """Raised when attempting to access settings before loading."""
    def __init__(self):
        super().__init__("Settings not loaded. Call load() first.")


class ConfigurationJsonNotProvided(ConfigurationError):
    """Raised when attempting to access settings before loading."""
    def __init__(self):
        super().__init__("A configuration JSON was not provided for loading configuration.")


class SettingNotFoundError(ConfigurationError):
    """Raised when a requested setting key is not found."""
    def __init__(self, key: str):
        super().__init__(f"Setting '{key}' not found.")


class SerializationError(ConfigurationError):
    """Raised when an object cannot be serialized to a supported format."""
    def __init__(self, value):
        super().__init__(f"Cannot serialize value: {repr(value)}")
