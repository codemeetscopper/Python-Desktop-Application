from PySide6.QtCore import QObject, Signal, Slot

from common.logger import Logger


class AppData(QObject):
    """
    Singleton class to act as a global interface between widgets.
    - Controls progress bar updates
    - Holds shared data while tool runs
    """

    # Signals for thread-safe UI updates
    progress_changed = Signal(int, str)  # (value, message)

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AppData, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):  # avoid re-init in singleton
            return
        super().__init__()
        self._initialized = True

        # Active progress bar reference (current window's bar)
        self._progress_bar = None

        # Arbitrary shared data (dict-style store)
        self._data_store = {}

        # Connect signals
        self.progress_changed.connect(self._update_progressbar)
        self._logger = Logger()

    # ---------------------------
    # Progress Handling
    # ---------------------------
    def register_progressbar(self, progressbar):
        """Register the currently active progress bar."""
        self._progress_bar = progressbar

    def unregister_progressbar(self):
        """Clear active progress bar reference."""
        self._progress_bar = None

    def set_progress(self, value: int, message: str = ""):
        """API call to update progress globally."""
        if message != "":
            self._logger.info(message)
        self.progress_changed.emit(value, message)

    @Slot(int, str)
    def _update_progressbar(self, value, message):
        """Internal slot to update UI safely."""
        if self._progress_bar:
            self._progress_bar.setValue(value)
            if message:
                self._progress_bar.setFormat(f"{message} (%p%)")

    # ---------------------------
    # Shared Data Store
    # ---------------------------
    def set_data(self, key, value):
        """Store arbitrary data."""
        self._data_store[key] = value

    def get_data(self, key, default=None):
        """Retrieve data from store."""
        return self._data_store.get(key, default)

    def clear_data(self):
        """Reset data store."""
        self._data_store.clear()
