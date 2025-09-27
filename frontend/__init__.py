from dataclasses import dataclass
from typing import Optional

from common.configuration.parser import ConfigurationManager
from common.fontmanager import FontManager
from common.logger import Logger
from common.backendclient import BackendClient
from common.stylemanager import StyleManager
from common.threadmanager import ThreadManager
from common.data import AppData


# noinspection PyCompatibility
@dataclass
class AppContext:
    name: str = "Python-Desktop-Application"
    version: str = "1.0.0.2"
    config_path: str = "config/configuration.json"
    logger: Optional[Logger] = None
    settings: Optional[ConfigurationManager] = None
    styler: Optional[StyleManager] = None
    font: Optional[FontManager] = None
    threader: Optional[ThreadManager] = None
    backend: Optional[BackendClient] = None
    data:Optional[AppData] = None

# Create a single instance to share across your app
AppCntxt = AppContext()
