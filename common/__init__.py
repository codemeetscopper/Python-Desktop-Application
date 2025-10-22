from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from common.configuration.parser import ConfigurationManager
from common.appearance.fontmanager import FontManager
from common.logger import Logger
from common.tcpinterface.backendclient import BackendClient
from common.appearance.stylemanager import StyleManager
from common.threadmanager import ThreadManager
from common.data import AppData

# noinspection PyCompatibility
@dataclass
class AppContext:
    name: str = "Python-Desktop-Application"
    version: str = "1.0.0.2"
    # keep default relative path; it will be resolved at initialise time
    config_path: str = "config/configuration.json"
    logger: Optional[Logger] = None
    settings: Optional[ConfigurationManager] = None
    styler: Optional[StyleManager] = None
    font: Optional[FontManager] = None
    threader: Optional[ThreadManager] = None
    backend: Optional[object] = None
    data: Optional[AppData] = None

# create a global app context instance that other modules import
AppCntxt = AppContext()


def initialise_context():
    """
    Initialise the global AppCntxt. This was previously done in frontend.app._initialise_context.
    Imports inside the function minimise import-time side-effects / cycles.
    """
    # local imports to avoid circular import at module import time
    import hashlib
    import time
    import common.threadmanager as threadmanager_module
    from common.tcpinterface.backendclient import BackendClient

    # Resolve config path relative to project root (module location), not current working directory
    project_root = Path(__file__).resolve().parent.parent  # <project_root>/common -> parent is project root
    cfg_path = Path(AppCntxt.config_path)
    if not cfg_path.is_absolute():
        cfg_path = project_root / cfg_path
    # normalize and store absolute string back to context for later use
    AppCntxt.config_path = str(cfg_path.resolve())

    # Logger
    AppCntxt.logger = Logger()

    # Thread manager instance
    AppCntxt.threader = threadmanager_module.get_instance()

    # AppData
    AppCntxt.data = AppData()

    # Start thread manager
    AppCntxt.threader.start()

    # Settings / Configuration
    AppCntxt.settings = ConfigurationManager(AppCntxt.config_path)

    # Backend client
    ip = AppCntxt.settings.get_value('sdk_ip_address')
    port = AppCntxt.settings.get_value('sdk_tcp_port')
    timeout = AppCntxt.settings.get_value('sdk_tcp_timeout')
    # key = AppCntxt.settings.get_value('sdk_aes_key')
    key = hashlib.sha256(b"sample key").digest()
    AppCntxt.backend = BackendClient(ip, port, timeout, secret_key=key)

    # Style manager initialisation
    AppCntxt.styler = StyleManager()
    try:
        accent = AppCntxt.settings.get_value('accent')
        support = AppCntxt.settings.get_value('support')
        neutral = AppCntxt.settings.get_value('neutral')
        theme = AppCntxt.settings.get_value('theme')
    except Exception:
        # fallback defaults if configuration missing or malformed
        accent = "#0c4d35"
        support = "#bb1133"
        neutral = "#7d8be0"
        theme = "light"
    AppCntxt.styler.initialise(accent, support, neutral, theme)

    # Font manager and preload some fonts (keep the previous behaviour)
    AppCntxt.font = FontManager()
    try:
        # make font paths relative to project root as well (optional)
        resources = project_root / "resources" / "fonts"
        AppCntxt.font.load_font(str(resources / "RobotoCondensed-VariableFont_wght.ttf"), "h1", 18)
        AppCntxt.font.load_font(str(resources / "RobotoCondensed-VariableFont_wght.ttf"), "h2", 14)
        AppCntxt.font.load_font(str(resources / "Roboto-VariableFont_wdth,wght.ttf"), "p", 11)
        AppCntxt.font.load_font(str(resources / "RobotoCondensed-VariableFont_wght.ttf"), "pc", 11)
        AppCntxt.font.load_font(str(resources / "Inconsolata-VariableFont_wdth,wght.ttf"), "log", 11)
    except Exception:
        # non-fatal; log and continue
        if AppCntxt.logger:
            AppCntxt.logger.warning("Some fonts could not be loaded during initialisation.")
    # allow caller to process events if needed
    return AppCntxt
