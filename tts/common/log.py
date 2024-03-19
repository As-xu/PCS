import logging
from queue import Empty, Queue
import threading
import atexit
import os
import abc
import io
import time
from logging.handlers import WatchedFileHandler
if os.name == 'nt':
    import win32con
    import win32file
    import pywintypes

    LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
    LOCK_SH = 0  # The default value
    LOCK_NB = win32con.LOCKFILE_FAIL_IMMEDIATELY
    _overlapped = pywintypes.OVERLAPPED()  # noqa
else:
    import fcntl


RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"
COLOR_PATTERN = "%s%s%%s%s" % (COLOR_SEQ, COLOR_SEQ, RESET_SEQ)
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, _NOTHING, DEFAULT = range(10)
LEVEL_COLOR_MAPPING = {
    logging.DEBUG: (BLUE, DEFAULT),
    logging.INFO: (GREEN, DEFAULT),
    logging.WARNING: (YELLOW, DEFAULT),
    logging.ERROR: (RED, DEFAULT),
    logging.CRITICAL: (WHITE, RED),
}


class TTSFormatter(logging.Formatter):
    def format(self, record):
        fg_color, bg_color = LEVEL_COLOR_MAPPING.get(record.levelno, (GREEN, DEFAULT))
        record.levelname = COLOR_PATTERN % (30 + fg_color, 40 + bg_color, record.levelname)
        return logging.Formatter.format(self, record)


class BaseLock(metaclass=abc.ABCMeta):
    def __init__(self, lock_file_path: str):
        self.f = open(lock_file_path, 'a')

    @abc.abstractmethod
    def __enter__(self):
        raise NotImplemented

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplemented


class WindowsFileLock(BaseLock):
    # windows文件锁
    def __enter__(self):
        self.hfile = win32file._get_osfhandle(self.f.fileno())  # noqa
        win32file.LockFileEx(self.hfile, LOCK_EX, 0, 0xffff0000, _overlapped)

    def __exit__(self, exc_type, exc_val, exc_tb):
        win32file.UnlockFileEx(self.hfile, 0, 0xffff0000, _overlapped)


class LinuxFileLock(BaseLock):
    # Linux文件锁
    def __enter__(self):
        fcntl.flock(self.f, fcntl.LOCK_EX)

    def __exit__(self, exc_type, exc_val, exc_tb):
        fcntl.flock(self.f, fcntl.LOCK_UN)


FileLock = WindowsFileLock if os.name == 'nt' else LinuxFileLock


class SuperFileHandler(logging.Handler):
    """多进程日志"""
    process_id_set = set()
    terminator = '\n'

    def _emit_handler(self):
        while True:
            self._write_to_file()
            time.sleep(1)

    def _start_emit_handler(self):
        self.thread = threading.Thread(target=self._emit_handler, daemon=True)
        self.thread.start()

    def __init__(self, file_name: str, mode='a', encoding=None, errors=None):
        super().__init__()
        self.file_name = file_name
        self.mode = mode
        self.encoding = encoding
        self.thread = None
        if "b" not in mode:
            self.encoding = io.text_encoding(encoding)
        self.errors = errors

        self.max_buffer = 2 ** 23
        self.buffer_msgs_queue = Queue()

        atexit.register(self.stop_emit_handler)
        # 注册

        if os.getpid() not in self.process_id_set:
            self._start_emit_handler()
            self.__class__.process_id_set.add(os.getpid())

    def stop_emit_handler(self):
        self._write_to_file()
        self.buffer_msgs_queue.put(Empty)
        self.thread.join()

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            self.buffer_msgs_queue.put(msg)
        except RecursionError:
            raise
        except Exception:
            self.handleError(record)

    def _write_to_file(self):
        buffer_msgs = ''
        while True:
            try:
                msg = self.buffer_msgs_queue.get(block=False)
                buffer_msgs += msg + self.terminator
                if len(buffer_msgs) > self.max_buffer:
                    break
            except Empty:
                break

        if buffer_msgs:
            with FileLock(self.file_name + '.lock'):
                with open(self.file_name, mode=self.mode, encoding=self.encoding) as f:
                    f.write(buffer_msgs)
                    f.flush()

if __name__ == '__main__':
    from multiprocessing import Process


    def worker_process():
        logging.getLogger().addHandler((SuperFileHandler("odoo.log")))
        logger = logging.getLogger(__name__)
        for i in range(15):
            logger.error('Message no %d | %s|%d' % (i, time.time(), os.getpid()))
            time.sleep(0.5)

    if __name__ == '__main__':
        from multiprocessing import Process

        workers = []
        for i in range(10):
            wp = Process(target=worker_process, name='worker %d' % (i + 1))
            workers.append(wp)
            wp.start()

        for wp in workers:
            wp.join()

    workers = []

    for i in range(10):
        wp = Process(target=worker_process, name='worker %d' % (i + 1))
        workers.append(wp)
        wp.start()

    for wp in workers:
        wp.join()

