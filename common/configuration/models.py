from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class SettingItem:
    name: str
    value: Any
    values: Any
    description: str
    type: str
    accessibility: str
    group: str
    icon: str


@dataclass
class Configuration:
    user: Dict[str, SettingItem]
    static: Dict[str, Any]


@dataclass
class PageInfo:
    widget_ref: str
    enabled: bool
    index: int
    icon: str
    selectable: bool
    license_required: bool


@dataclass
class PageMapping:
    defaults: Dict[str, PageInfo]
    plugins: Dict[str, PageInfo]


@dataclass
class AppSettings:
    configuration: Configuration
    page_mapping: PageMapping
