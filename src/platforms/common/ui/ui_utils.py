import logging
import threading

import flet as ft

logger = logging.getLogger(__name__)


def safe_update(control: ft.Control):
    """Safely updates a Flet control, ensuring it is attached to a page."""
    if not control or not hasattr(control, "page") or not control.page:
        return
    try:
        # Flet controls have a private __uid attribute.
        # If it's None, the control isn't rendered yet.
        if getattr(control, "_Control__uid", None) is not None:
            control.update()
    except Exception as e:
        logger.debug(f"UI update skipped for {control.__class__.__name__}: {e}")


class Debouncer:
    """
    Utility to delay execution of a function until after a specified silence period.
    Commonly used for 'Search-as-you-type' to avoid flooding the DB/API with requests.
    """

    def __init__(self, delay=0.4):
        self.delay = delay
        self._timer = None

    def run(self, action, *args, **kwargs):
        """Triggers the action after the delay, cancelling any pending ones."""
        if self._timer is not None:
            self._timer.cancel()
        self._timer = threading.Timer(self.delay, action, args=args, kwargs=kwargs)
        self._timer.start()

    def cancel(self):
        """Cancels any pending action."""
        if self._timer is not None:
            self._timer.cancel()
