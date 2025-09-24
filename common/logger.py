import logging
import functools
from datetime import datetime
from queue import Queue
from PySide6.QtCore import QObject, Signal


class ColouredConsoleHandler(logging.StreamHandler):
    """Custom handler to add colours to console output."""
    COLORS = {
        "DEBUG": "\033[37m",     # White / Light gray
        "INFO": "\033[36m",      # Cyan
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[95m",  # Bright Magenta
        "RESET": "\033[0m",
    }

    def format(self, record):
        base = super().format(record)
        color = self.COLORS.get(record.levelname, "")
        reset = self.COLORS["RESET"]
        return f"{color}{base}{reset}"


class Logger(QObject):
    """Singleton Qt Logger with queue-based storage, coloured console output, and export feature."""
    _instance = None
    log_updated = Signal(str)  # Qt signal emitted when a new log entry is added

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, name: str = "Application", level=logging.DEBUG):
        if getattr(self, "_initialized", False):
            return

        super().__init__()
        self.name = name
        self.level = level
        self.logs = Queue()

        # Python logging setup
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        self._logger.propagate = False

        console_handler = ColouredConsoleHandler()
        console_handler.setLevel(level)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        console_handler.setFormatter(formatter)

        if not self._logger.handlers:
            self._logger.addHandler(console_handler)

        self._initialized = True

    def _store_log(self, level_name: str, msg: str):
        """Store log in queue and emit update signal."""
        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        formatted = f"{timestamp} | {level_name} | {msg}"
        self.logs.put(formatted)

        # if level_name != "DEBUG":
        self.log_updated.emit(msg)

        return formatted

    # Public logging API (unchanged)
    def debug(self, msg, *args, **kwargs):
        formatted = self._store_log("DEBUG", msg)
        self._logger.debug(msg, *args, **kwargs)
        return formatted

    def info(self, msg, *args, **kwargs):
        formatted = self._store_log("INFO", msg)
        self._logger.info(msg, *args, **kwargs)
        return formatted

    def warning(self, msg, *args, **kwargs):
        formatted = self._store_log("WARNING", msg)
        self._logger.warning(msg, *args, **kwargs)
        return formatted

    def error(self, msg, *args, **kwargs):
        formatted = self._store_log("ERROR", msg)
        self._logger.error(msg, *args, **kwargs)
        return formatted

    def critical(self, msg, *args, **kwargs):
        formatted = self._store_log("CRITICAL", msg)
        self._logger.critical(msg, *args, **kwargs)
        return formatted

    def log_function(self, level=logging.DEBUG):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if self._logger.isEnabledFor(level):
                    arg_list = [repr(a) for a in args] + [f"{k}={v!r}" for k, v in kwargs.items()]
                    call_msg = f"Calling {func.__name__}({', '.join(arg_list)})"
                    self._store_log(logging.getLevelName(level), call_msg)
                result = func(*args, **kwargs)
                if self._logger.isEnabledFor(level):
                    self._store_log(logging.getLevelName(level), f"{func.__name__} returned {result!r}")
                return result
            return wrapper

        return decorator

    def export_to_file(self, file_path: str):
        items = list(self.logs.queue)
        with open(file_path, "w", encoding="utf-8") as f:
            for line in items:
                f.write(line + "\n")
