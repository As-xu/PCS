import datetime
import logging
from tts.common.base import BaseController
from tts.common.sql_condition import Sc
from tts.common.response import Response
from tts.common.enum.system_enum import SchedulerStatus
from tts.common.enum.common_enum import DataChangeMode
from tts.common.common_const import JCK
from tts.common.scheduler import run_scheduler_func
import uuid


logger = logging.getLogger(__name__)


class SchedulerController(BaseController):
    def query_scheduler_info(self, request_data):
        _scheduler = self.scheduler
        data_json = {
            "state": SchedulerStatus.get_name(self.scheduler.state),
            "jobstores": str(self.scheduler._scheduler._jobstores),
            "job_defaults": str(self.scheduler._scheduler._job_defaults),
            "jobs": self.scheduler._scheduler.get_jobs(),
        }
        return Response.json_data(data_json)

    def change_scheduler_status(self, request_data):
        status = request_data.get("status")
        start_after_paused = request_data.get("start_and_need_paused") or False
        stop_need_wait = request_data.get("stop_need_wait") or True
        if status not in SchedulerStatus.names():
            return Response.error(f"未知的状态: {status}")

        status_code = SchedulerStatus.get_value(status)
        if self.scheduler.state == status_code:
            return Response.warning(f"当前状态已经是: {status}")
        if status == SchedulerStatus.paused.name:
            if self.scheduler.state == SchedulerStatus.stopped.value:
                return Response.warning(f"当前状态已经是{status}, 不可暂停")
            self.scheduler.pause()
        elif status == SchedulerStatus.running.name:
            if self.scheduler.state == SchedulerStatus.stopped.value:
                self.scheduler.start(start_after_paused)
            elif self.scheduler.state == SchedulerStatus.paused.value:
                self.scheduler.resume()
        elif status == SchedulerStatus.stopped.name:
            if self.scheduler.state == SchedulerStatus.paused.value:
                return Response.warning(f"当前状态已经是{status}, 不可停止")
            self.scheduler.shutdown(stop_need_wait)

        return Response.success()

    def save_scheduler_job(self, request_data):
        job_id = request_data.get("job_id")
        job_store_id = request_data.get("job_store_id")
        func_name = request_data.get("func_name")
        func_method = request_data.get("func_method")
        args = request_data.get("args") or ()
        kwargs = request_data.get("kwargs") or {}

        job_defaults = self.scheduler._scheduler._job_defaults
        # coalesce: 当由于某种原因导致某个job积攒了好几次没有实际运行（比如说系统挂了5分钟后恢复，有一个任务是每分钟跑一次的，
        # 按道理说这5分钟内本来是“计划”运行5次的，但实际没有执行），如果coalesce为True，下次这个job被submit给executor时，
        # 只会执行1次，也就是最后这次，如果为False，那么会执行5次（不一定，因为还有其他条件，看后面misfire_grace_time的解释）。

        # max_instances: 每个job在同一时刻能够运行的最大实例数, 默认情况下为1个, 可以指定为更大值,
        # 这样即使上个job还没运行完同一个job又被调度的话也能够再开一个线程执行。

        # misfire_grace_time: 单位为秒, 假设有这么一种情况, 当某一job被调度时刚好线程池都被占满, 调度器会选择将该job排队不运行,
        # misfire_grace_time 参数则是在线程池有可用线程时会比对该job的应调度时间跟当前时间的差值, 如果差值 < misfire_grace_time,
        # 调度器会再次调度该job.反之该job的执行状态为EVENT_JOBMISSED了, 即错过运行

        misfire_grace_time = request_data.get("misfire_grace_time") or job_defaults.get("misfire_grace_time")
        coalesce = request_data.get("coalesce") or job_defaults.get("coalesce")

        trigger = request_data.get("trigger")
        max_instances = request_data.get("max_instances") or job_defaults.get("max_instances")
        next_run_time = request_data.get("next_run_time") or datetime.datetime.utcnow()

        modify_code = request_data.pop(JCK.MODIFY_MODE, None)
        if modify_code == DataChangeMode.Create.value:
            job_store_id = uuid.uuid1().hex

        job_t = self.get_table(self.tables.RingStarJobTable)

        scheduler_job_data = {
            'id': job_store_id, 'name': func_name, 'args': args, 'kwargs': kwargs,
            'trigger': trigger, 'executor': 'default', 'func': run_scheduler_func,
            'misfire_grace_time': misfire_grace_time, 'coalesce': coalesce, 'max_instances': max_instances,
            'next_run_time': next_run_time, "seconds": 200
        }
        if modify_code == DataChangeMode.Create.value:
            self.scheduler.add_job(scheduler_job_data)

            # scheduler_job_data = {
            #     'job_store_id': job_store_id, 'name': func_name, 'args': args, 'kwargs': kwargs,
            #     'trigger': trigger, 'executor': executor, 'func': func_method,
            #     'misfire_grace_time': misfire_grace_time, 'coalesce': coalesce, 'max_instances': max_instances,
            #     'next_run_time': next_run_time
            # }
            # job_t.create(scheduler_job_data)
        elif modify_code == DataChangeMode.Update.value:
            pass
        elif modify_code == DataChangeMode.Delete.value:
            pass

        return Response.success()

    def query_all_scheduler_job(self, request_data):
        return Response.success()

    def query_one_scheduler_job(self, request_data):
        return Response.success()

    def change_scheduler_job_status(self, request_data):
        return Response.success()