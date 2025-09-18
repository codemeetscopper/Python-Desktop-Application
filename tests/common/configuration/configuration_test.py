import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
from PySide6.QtCore import QSettings

from common.configuration.parser import ConfigurationManager
from common.configuration.exceptions import (
    ConfigurationNotLoadedError,
    SettingNotFoundError,
    ConfigurationJsonNotProvided
)
from common.configuration.models import SettingItem

# -------------------------
# Test Data
# -------------------------
TEST_JSON = {
    "configuration": {
        "user": {
            "sample_text_input": {
                "name": "Sample Text Input",
                "value": "New Value",
                "description": "A sample text input setting.",
                "type": "text",
                "accessibility": "user",
                "group": "Sample Group 1",
                "icon": "images/size.svg"
            },
            "sample_dropdown_input": {
                "name": "Sample DropDown Input",
                "value": ["Option 1", "Option 2"],
                "description": "A sample drop down setting.",
                "type": "dropdown",
                "accessibility": "user",
                "group": "Sample Group 1",
                "icon": "images/size.svg"
            }
        },
        "static": {
            "setting_1": "static_setting_1",
            "setting_2": 0
        }
    },
    "page_mapping": {
        "defaults": {
            "Home": {
                "widget_ref": "frontend.core.pages.home.home_c",
                "enabled": True,
                "index": 1,
                "icon": "images/dashboard.svg",
                "selectable": True,
                "license_required": True
            }
        },
        "plugins": {
            "Sample Plugin": {
                "widget_ref": "frontend.core.pages.plugin.sample_plugin_c",
                "enabled": True,
                "index": 3,
                "icon": "images/plugin.svg",
                "selectable": True,
                "license_required": True
            }
        }
    }
}

# -------------------------
# Helper
# -------------------------
def get_mock_config_manager():
    with patch("builtins.open", mock_open(read_data=json.dumps(TEST_JSON))):
        with patch.object(QSettings, "sync"):
            return ConfigurationManager("dummy_path.json")

# -------------------------
# Tests
# -------------------------

def test_singleton_behavior():
    cm1 = get_mock_config_manager()
    cm2 = get_mock_config_manager()
    assert cm1 is cm2

def test_init_without_json_raises():
    # Reset singleton
    ConfigurationManager._instance = None
    with pytest.raises(ConfigurationJsonNotProvided):
        ConfigurationManager("")

def test_load_parses_json_correctly():
    cm = get_mock_config_manager()
    assert cm.data.configuration.user["sample_text_input"].value == "New Value"
    assert cm.data.configuration.static["setting_1"] == "static_setting_1"
    assert "Home" in cm.data.page_mapping.defaults
    assert "Sample Plugin" in cm.data.page_mapping.plugins

def test_get_value_normal_and_as_string():
    cm = get_mock_config_manager()
    val_obj = cm.get_value("sample_text_input")
    assert isinstance(val_obj, SettingItem)
    assert val_obj.value == "New Value"

    val_str = cm.get_value("sample_text_input", as_string=True)
    assert val_str == "New Value"

def test_set_value_updates_dataclass_and_qsettings():
    cm = get_mock_config_manager()
    with patch.object(QSettings, "setValue") as mock_set, patch.object(QSettings, "sync") as mock_sync:
        cm.set_value("sample_text_input", "Updated Value")
        assert cm.data.configuration.user["sample_text_input"].value == "Updated Value"
        mock_set.assert_called()
        mock_sync.assert_called()

def test_get_value_not_loaded_raises():
    cm = ConfigurationManager.__new__(ConfigurationManager)
    cm.data = None
    with pytest.raises(ConfigurationNotLoadedError):
        cm.get_value("sample_text_input")

def test_set_value_not_loaded_raises():
    cm = ConfigurationManager.__new__(ConfigurationManager)
    cm.data = None
    with pytest.raises(ConfigurationNotLoadedError):
        cm.set_value("sample_text_input", "value")

def test_get_value_not_found_raises():
    cm = get_mock_config_manager()
    with pytest.raises(SettingNotFoundError):
        cm.get_value("nonexistent")

def test_set_value_not_found_raises():
    cm = get_mock_config_manager()
    with pytest.raises(SettingNotFoundError):
        cm.set_value("nonexistent", "value")

@patch("builtins.open", new_callable=mock_open)
def test_save_writes_json(mock_file):
    cm = get_mock_config_manager()
    cm.set_value("sample_text_input", "Saved Value")
    cm.save()
    mock_file().write.assert_called()

def test_serialize_and_deserialize_color():
    from PySide6.QtGui import QColor
    color = QColor("#abcdef")
    serialized = ConfigurationManager._serialize(color)
    assert serialized["__type__"] == "QColor"
    deserialized = ConfigurationManager._deserialize(serialized)
    assert isinstance(deserialized["value"], QColor)
    assert deserialized["value"].name() == "#abcdef"

def test_serialize_dict_nested():
    from PySide6.QtGui import QColor
    input_dict = {"a": {"b": QColor("#000000")}, "c": 5}
    serialized = ConfigurationManager._serialize_dict(input_dict)
    assert isinstance(serialized["a"]["b"], dict)
    assert serialized["c"] == 5
