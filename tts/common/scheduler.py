import logging
import werkzeug
import dateutil.parser

from collections import OrderedDict
from flask.helpers import get_debug_flag
from pytz import utc

from ringstar.events import EVENT_ALL
from ringstar.schedulers.background import BackgroundScheduler
from ringstar.executors.pool import ThreadPoolExecutor
from ringstar.jobstores.base import JobLookupError
from ringstar.jobstores.redis import RedisJobStore
from ringstar.triggers.cron import CronTrigger
from ringstar.triggers.date import DateTrigger
from ringstar.triggers.interval import IntervalTrigger

from datetime import datetime


logger = logging.getLogger(__name__)



def job_to_dict(job):
    """Converts a job to an OrderedDict."""

    data = OrderedDict()
    data["id"] = job.id
    data["name"] = job.name
    data["func"] = job.func_ref
    data["args"] = job.args
    data["kwargs"] = job.kwargs

    data.update(trigger_to_dict(job.trigger))

    if not job.pending:
        data["misfire_grace_time"] = job.misfire_grace_time
        data["max_instances"] = job.max_instances
        data["next_run_time"] = None if job.next_run_time is None else job.next_run_time

    return data


def pop_trigger(data):
    """Pops trigger and trigger args from a given dict."""

    trigger_name = data.pop("trigger")
    trigger_args = {}

    if trigger_name == "date":
        trigger_arg_names = ("run_date", "timezone")
    elif trigger_name == "interval":
        trigger_arg_names = ("weeks", "days", "hours", "minutes", "seconds", "start_date", "end_date", "timezone")
    elif trigger_name == "cron":
        trigger_arg_names = ("year", "month", "day", "week", "day_of_week", "hour", "minute", "second", "start_date", "end_date", "timezone")
    else:
        raise Exception(f"Trigger {trigger_name} is not supported.")

    for arg_name in trigger_arg_names:
        if arg_name in data:
            trigger_args[arg_name] = data.pop(arg_name)

    return trigger_name, trigger_args


def trigger_to_dict(trigger):
    """Converts a trigger to an OrderedDict."""

    data = OrderedDict()

    if isinstance(trigger, DateTrigger):
        data["trigger"] = "date"
        data["run_date"] = trigger.run_date
    elif isinstance(trigger, IntervalTrigger):
        data["trigger"] = "interval"
        data["start_date"] = trigger.start_date

        if trigger.end_date:
            data["end_date"] = trigger.end_date

        w, d, hh, mm, ss = extract_timedelta(trigger.interval)

        if w > 0:
            data["weeks"] = w
        if d > 0:
            data["days"] = d
        if hh > 0:
            data["hours"] = hh
        if mm > 0:
            data["minutes"] = mm
        if ss > 0:
            data["seconds"] = ss
    elif isinstance(trigger, CronTrigger):
        data["trigger"] = "cron"

        if trigger.start_date:
            data["start_date"] = trigger.start_date

        if trigger.end_date:
            data["end_date"] = trigger.end_date

        for field in trigger.fields:
            if not field.is_default:
                data[field.name] = str(field)
    else:
        data["trigger"] = str(trigger)

    return data


def fix_job_def(job_def):
    """
    转化为datetime对象
    """
    if isinstance(job_def.get("start_date"), str):
        job_def["start_date"] = dateutil.parser.parse(job_def.get("start_date"))

    if isinstance(job_def.get("end_date"), str):
        job_def["end_date"] = dateutil.parser.parse(job_def.get("end_date"))

    if isinstance(job_def.get("run_date"), str):
        job_def["run_date"] = dateutil.parser.parse(job_def.get("run_date"))

    # it keeps compatibility backward
    if isinstance(job_def.get("trigger"), dict):
        trigger = job_def.pop("trigger")
        job_def["trigger"] = trigger.pop("type", "date")
        job_def.update(trigger)


def extract_timedelta(delta):
    w, d = divmod(delta.days, 7)
    mm, ss = divmod(delta.seconds, 60)
    hh, mm = divmod(mm, 60)
    return w, d, hh, mm, ss


def bytes_to_wsgi(data):
    assert isinstance(data, bytes), "data must be bytes"
    if isinstance(data, str):
        return data
    else:
        return data.decode("latin1")


def wsgi_to_bytes(data):
    """coerce wsgi unicode represented bytes to real ones"""
    if isinstance(data, bytes):
        return data
    return data.encode("latin1")  # XXX: utf8 fallback?


class RingStarScheduler(object):
    """Provides a scheduler integrated to Flask."""

    def __init__(self, scheduler=None):
        self._scheduler = scheduler or BackgroundScheduler()
        self.app = None

    def init_app(self, app):
        """初始化"""

        self.app = app
        self.app.scheduler = self

        self._load_config()
        self._load_jobs()

    def _load_config(self):
        """
        加载配置
        """
        redis_config = {
            'host': '106.75.237.181',
            'port': '6379',
            'db': 0,
            'password': '1756232088'
        }

        # coalesce: 当由于某种原因导致某个job积攒了好几次没有实际运行（比如说系统挂了5分钟后恢复，有一个任务是每分钟跑一次的，
        # 按道理说这5分钟内本来是“计划”运行5次的，但实际没有执行），如果coalesce为True，下次这个job被submit给executor时，
        # 只会执行1次，也就是最后这次，如果为False，那么会执行5次（不一定，因为还有其他条件，看后面misfire_grace_time的解释）。

        # max_instance: 每个job在同一时刻能够运行的最大实例数, 默认情况下为1个, 可以指定为更大值,
        # 这样即使上个job还没运行完同一个job又被调度的话也能够再开一个线程执行。

        # misfire_grace_time: 单位为秒, 假设有这么一种情况, 当某一job被调度时刚好线程池都被占满, 调度器会选择将该job排队不运行,
        # misfire_grace_time参数则是在线程池有可用线程时会比对该job的应调度时间跟当前时间的差值, 如果差值 < misfire_grace_time时,
        # 调度器会再次调度该job.反之该job的执行状态为EVENTJOBMISSED了, 即错过运行

        options = {
            "jobstores":{
                'default': RedisJobStore(**redis_config)
            },
            "executors":{
                'default': ThreadPoolExecutor(20),
            },
            "job_defaults":{
                "coalesce": True,
                "max_instance": 1,
                "misfire_grace_time": None
            },
            "timezone": utc
        }
        self._scheduler.configure(**options)

    def _load_jobs(self):
        """
        加载任务
        """
        pass

    @property
    def state(self):
        """调度器状态"""
        return self._scheduler.state

    @property
    def scheduler(self):
        """获取调度器"""
        return self._scheduler

    @property
    def task(self):
        """获取基本调度程序装饰器"""
        return self._scheduler.scheduled_job

    def start(self, paused=False):
        """
        开始定时任务
        :param bool paused: 如果为True, 那么不会运行job, 直到调用resume方法
        """
        # 调试模式下的 Flask 会生成一个子进程，以便每次代码更改时它都可以重新启动该进程，新的子进程会初始化并启动一个新的 APScheduler，从而导致作业运行两次。
        # is_running_from_reloader 为True 则说明当前程序式主进程,不是子进程

        if get_debug_flag() and not werkzeug.serving.is_running_from_reloader():
            return

        self._scheduler.start(paused=paused)
        logger.info("定时任务已启动")

    def shutdown(self, wait=True):
        """
        关闭调度程序。 但不中断任何当前正在运行的job。

        :param bool wait: wait为True会等待所有当前正在执行的job完成
        如果调度程序尚未启动会引发异常 SchedulerNotRunningError
        """

        self._scheduler.shutdown(wait)
        logger.info("定时任务已关闭")

    def pause(self):
        """
        暂停调度程序中的作业处理。

        This will prevent the scheduler from waking up to do job processing until :meth:`resume`
        is called. It will not however stop any already running job processing.
        """
        self._scheduler.pause()
        logger.info("定时任务已暂停")

    def resume(self):
        """
        恢复调度程序中的作业处理。
        """
        self._scheduler.resume()
        logger.info("定时任务已恢复")

    def add_listener(self, callback, mask=EVENT_ALL):
        """
        添加调度器事件的监听

        当匹配事件发生时，将使用事件对象作为其唯一参数来执行“callback”。 如果未提供“mask”参数，回调将接收所有类型的事件

        :param callback: 回调函数
        :param int mask: 事件掩码
        """
        self._scheduler.add_listener(callback, mask)

    def remove_listener(self, callback):
        """
        移除回调函数
        """
        self._scheduler.remove_listener(callback)

    def add_job(self, job_data):
        """
        将给定作业添加到作业列表中，并唤醒调度程序（如果它已在运行）。
        """

        return self._scheduler.add_job(**job_data)

    def remove_job(self, job_id, jobstore=None):
        """
        删除作业，并防止其再运行。

        :param str job_id: job的id
        :param str jobstore: 包含job的jobstore名字
        """

        self._scheduler.remove_job(job_id, jobstore)

    def remove_all_jobs(self, jobstore=None):
        """
        从指定的jobstore中删除所有lob，如果没有给出，则删除所有jobstore。

        :param str|unicode jobstore: jobstore的别名
        """

        self._scheduler.remove_all_jobs(jobstore)

    def get_job(self, job_id, jobstore=None):
        """
        根据id返回job对象,没有则返回None

        :param str job_id: job的唯一标识符
        :param str jobstore: 最有可能包含该job的jobstore的别名

        """

        return self._scheduler.get_job(job_id, jobstore)

    def get_jobs(self, jobstore=None):
        """
        从特定作业存储或所有作业存储中返回挂起作业（如果计划程序尚未启动）和计划作业的列表。
        :param str jobstore: 作业存储的别名
        :rtype: list[Job]
        """

        return self._scheduler.get_jobs(jobstore)

    def modify_job(self, job_id, jobstore=None, **changes):
        """
        修改单个作业的属性。changes作为额外的关键字参数传递给此方法。

        :param str job_id: job的唯一标识符
        :param str jobstore: 包含作业的作业存储的别名
        """

        fix_job_def(changes)

        if "trigger" in changes:
            trigger, trigger_args = pop_trigger(changes)
            self._scheduler.reschedule_job(job_id, jobstore, trigger, **trigger_args)

        return self._scheduler.modify_job(job_id, jobstore, **changes)

    def pause_job(self, job_id, jobstore=None):
        """
        暂停任务, 可通过resume_job回复

        :param str job_id: job的唯一标识符
        :param str jobstore: 包含作业的作业存储的别名
        """
        self._scheduler.pause_job(job_id, jobstore)

    def resume_job(self, job_id, jobstore=None):
        """
        恢复给定作业的计划，或者在其计划完成时删除该作业。

        :param str job_id: job的唯一标识符
        :param str jobstore: 包含作业的作业存储的别名
        """
        # 待修改

        self._scheduler.resume_job(job_id, jobstore)

    def run_job(self, job_id, jobstore=None):
        """
        不通过调度任务, 直接运行给定的作业
        :param job_id: job的唯一标识符
        :param str jobstore: 包含作业的作业存储的别名
        :return:
        """
        job = self._scheduler.get_job(job_id, jobstore)

        if not job:
            raise JobLookupError(job_id)

        job.func(*job.args, **job.kwargs)

    def print_jobs(self, jobstore=None, out=None):
        self._scheduler.print_jobs(jobstore, out)


def run_scheduler_func(*args, **kwargs):
    logger.info("success")

    return True


