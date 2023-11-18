from __future__ import absolute_import

from threading import Event

from staring.schedulers.base import BaseScheduler, STATE_STOPPED
from staring.util import TIMEOUT_MAX


class BlockingScheduler(BaseScheduler):
    """
    A scheduler that runs in the foreground
    (:meth:`~staring.schedulers.base.BaseScheduler.start` will block).
    """
    _event = None

    def start(self, *args, **kwargs):
        if self._event is None or self._event.is_set():
            self._event = Event()

        super(BlockingScheduler, self).start(*args, **kwargs)
        self._main_loop()

    def shutdown(self, wait=True):
        super(BlockingScheduler, self).shutdown(wait)
        self._event.set()

    def _main_loop(self):
        wait_seconds = TIMEOUT_MAX
        while self.state != STATE_STOPPED:
            self._event.wait(wait_seconds)
            self._event.clear()
            wait_seconds = self._process_jobs()

    def wakeup(self):
        self._event.set()