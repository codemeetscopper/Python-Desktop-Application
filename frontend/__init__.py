from dataclasses import dataclass
from typing import Optional

from common.configuration.parser import ConfigurationManager
from common.logger import Logger
from common.backendmanager import BackendManager
from common.threadmanager import ThreadManager


@dataclass
class AppContext:
    name: str = "Python Desktop App Template"
    version: str = "v0.1"
    config_path: str = "config/configuration.json"
    logger: Optional[Logger] = None
    settings: Optional[ConfigurationManager] = None
    thread_manager: Optional[ThreadManager] = None
    sdk_manager: Optional[BackendManager] = None

# Create a single instance to share across your app
ApplicationContext = AppContext()
