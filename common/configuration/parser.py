import json
import logging
import time
from dataclasses import asdict
from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor

from .exceptions import ConfigurationNotLoadedError, SettingNotFoundError, ConfigurationJsonNotProvided
from .models import PageMapping, AppSettings, Configuration, SettingItem, PageInfo
from ..logger import Logger

LOGGER = Logger()

class ConfigurationManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, json_path: str = "", org: str = "Default Organisation", app: str = "Default Application Name"):

        if json_path == "":
            if hasattr(self, "_initialized") and self._initialized:
                return
            else:
                raise ConfigurationJsonNotProvided()

        self._initialized = True

        self.json_path = json_path
        self.settings = QSettings(org, app)
        self.data: AppSettings | None = None

        self.load()

    # --------------------------
    # Public API
    # --------------------------
    @LOGGER.log_function(level=logging.DEBUG)
    def load(self):
        """Load JSON into dataclasses and QSettings."""
        if self.json_path == "":
            raise ConfigurationJsonNotProvided()
        LOGGER.info(f"Loading configuration from {self.json_path}")
        with open(self.json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        self.data = AppSettings(
            configuration=Configuration(
                user={k: SettingItem(**self._deserialize(v)) for k, v in raw["configuration"]["user"].items()},
                static=raw["configuration"]["static"]
            ),
            page_mapping=PageMapping(
                defaults={k: PageInfo(**v) for k, v in raw["page_mapping"]["defaults"].items()},
                plugins={k: PageInfo(**v) for k, v in raw["page_mapping"]["plugins"].items()}
            )
        )
        LOGGER.info(f"Loaded configuration from {self.json_path}")
        self._save_to_q_settings(raw)

    @LOGGER.log_function(level=logging.DEBUG)
    def get_value(self, setting_key: str, as_string: bool = False):
        """Get a user or static setting by key."""
        if not self.data:
            raise ConfigurationNotLoadedError()

        setting_obj = self.data.configuration.user.get(setting_key)
        is_user_setting = setting_obj is not None

        if not is_user_setting:
            setting_obj = self.data.configuration.static.get(setting_key)

        if setting_obj is None:
            raise SettingNotFoundError(setting_key)

        value = getattr(setting_obj, 'Value', setting_obj)
        return self._serialize(value) if as_string else value

    @LOGGER.log_function(level=logging.DEBUG)
    def set_value(self, setting_key: str, value):
        """Update a user setting in both QSettings and dataclass."""
        if not self.data:
            raise ConfigurationNotLoadedError()

        setting_obj = self.data.configuration.user.get(setting_key)
        if not setting_obj:
            raise SettingNotFoundError(setting_key)

        # Update dataclass
        setting_obj.value = value

        # Update QSettings
        q_settings_key = f"configuration/user/{setting_key}/value"
        self.settings.setValue(q_settings_key, self._serialize(value))
        self.settings.sync()

    @LOGGER.log_function(level=logging.DEBUG)
    def save(self):
        """Save current dataclasses to JSON."""
        if not self.data:
            raise ConfigurationNotLoadedError()

        json_dict = {
            "configuration": {
                "user": {k: self._serialize_dict(asdict(v)) for k, v in self.data.configuration.user.items()},
                "static": self.data.configuration.static
            },
            "page_mapping": {
                "defaults": {k: asdict(v) for k, v in self.data.page_mapping.defaults.items()},
                "plugins": {k: asdict(v) for k, v in self.data.page_mapping.plugins.items()},
            }
        }
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(json_dict, f, indent=4)

    # --------------------------
    # Internal Helpers
    # --------------------------
    @LOGGER.log_function(level=logging.DEBUG)
    def _save_to_q_settings(self, raw_dict):
        """Recursively save a dictionary to QSettings."""
        def recursive_save(prefix, obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    recursive_save(f"{prefix}/{k}" if prefix else k, v)
            else:
                self.settings.setValue(prefix, self._serialize(obj))
        recursive_save("", raw_dict)
        self.settings.sync()

    @staticmethod
    def _serialize(value):
        """Convert special objects to JSON-safe values."""
        if isinstance(value, QColor):
            return {"__type__": "QColor", "value": value.name()}
        # Add other types like QFont, QPoint, etc.
        return value

    @staticmethod
    def _deserialize(value):
        """Convert stored JSON-safe values back to objects."""
        if isinstance(value, dict) and "__type__" in value:
            if value["__type__"] == "QColor":
                return {**value, "value": QColor(value["value"])}
        return value

    @staticmethod
    def _serialize_dict(d):
        """Recursively serialize dictionary values."""
        for k, v in d.items():
            if isinstance(v, dict):
                d[k] = ConfigurationManager._serialize_dict(v)
            else:
                d[k] = ConfigurationManager._serialize(v)
        return d
