import functools
import logging
import socket
import werkzeug

from ringstar.events import EVENT_ALL
from ringstar.schedulers.background import BackgroundScheduler
from ringstar.jobstores.base import JobLookupError
from flask import make_response
from flask.helpers import get_debug_flag

LOGGER = logging.getLogger(__name__)



import dateutil.parser

from ringstar.triggers.cron import CronTrigger
from ringstar.triggers.date import DateTrigger
from ringstar.triggers.interval import IntervalTrigger
from collections import OrderedDict


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
    Replaces the datetime in string by datetime object.
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

    def __init__(self, scheduler=None, app=None):
        self._scheduler = scheduler or BackgroundScheduler()
        self._authentication_callback = None

        self.auth = None
        self.api_enabled = False
        self.api_prefix = "/scheduler"
        self.endpoint_prefix = "scheduler."
        self.app = None

        if app:
            self.init_app(app)

    @property
    def running(self):
        """Get true whether the scheduler is running."""
        return self._scheduler.running

    @property
    def state(self):
        """Get the state of the scheduler."""
        return self._scheduler.state

    @property
    def scheduler(self):
        """Get the base scheduler."""
        return self._scheduler

    @property
    def task(self):
        """Get the base scheduler decorator"""
        return self._scheduler.scheduled_job

    def init_app(self, app):
        """Initialize the APScheduler with a Flask application instance."""

        self.app = app
        self.app.apscheduler = self

        self._load_config()
        self._load_jobs()

        if self.api_enabled:
            self._load_api()

    def start(self, paused=False):
        """
        Start the scheduler.
        :param bool paused: if True, don't start job processing until resume is called.
        """

        # Flask in debug mode spawns a child process so that it can restart the process each time your code changes,
        # the new child process initializes and starts a new APScheduler causing the jobs to run twice.
        if get_debug_flag() and not werkzeug.serving.is_running_from_reloader():
            return

        self._scheduler.start(paused=paused)

    def shutdown(self, wait=True):
        """
        Shut down the scheduler. Does not interrupt any currently running jobs.

        :param bool wait: ``True`` to wait until all currently executing jobs have finished
        :raises SchedulerNotRunningError: if the scheduler has not been started yet
        """

        self._scheduler.shutdown(wait)

    def pause(self):
        """
        Pause job processing in the scheduler.

        This will prevent the scheduler from waking up to do job processing until :meth:`resume`
        is called. It will not however stop any already running job processing.
        """
        self._scheduler.pause()

    def resume(self):
        """
        Resume job processing in the scheduler.
        """
        self._scheduler.resume()

    def add_listener(self, callback, mask=EVENT_ALL):
        """
        Add a listener for scheduler events.

        When a matching event  occurs, ``callback`` is executed with the event object as its
        sole argument. If the ``mask`` parameter is not provided, the callback will receive events
        of all types.

        For further info: https://apscheduler.readthedocs.io/en/latest/userguide.html#scheduler-events

        :param callback: any callable that takes one argument
        :param int mask: bitmask that indicates which events should be listened to
        """
        self._scheduler.add_listener(callback, mask)

    def remove_listener(self, callback):
        """
        Remove a previously added event listener.
        """
        self._scheduler.remove_listener(callback)

    def add_job(self, id, func, **kwargs):
        """
        Add the given job to the job list and wakes up the scheduler if it's already running.

        :param str id: explicit identifier for the job (for modifying it later)
        :param func: callable (or a textual reference to one) to run at the given time
        """

        job_def = dict(kwargs)
        job_def["id"] = id
        job_def["func"] = func
        job_def["name"] = job_def.get("name") or id

        fix_job_def(job_def)

        return self._scheduler.add_job(**job_def)

    def remove_job(self, id, jobstore=None):
        """
        Remove a job, preventing it from being run any more.

        :param str id: the identifier of the job
        :param str jobstore: alias of the job store that contains the job
        """

        self._scheduler.remove_job(id, jobstore)

    def remove_all_jobs(self, jobstore=None):
        """
        Remove all jobs from the specified job store, or all job stores if none is given.

        :param str|unicode jobstore: alias of the job store
        """

        self._scheduler.remove_all_jobs(jobstore)

    def get_job(self, id, jobstore=None):
        """
        Return the Job that matches the given ``id``.

        :param str id: the identifier of the job
        :param str jobstore: alias of the job store that most likely contains the job
        :return: the Job by the given ID, or ``None`` if it wasn't found
        :rtype: Job
        """

        return self._scheduler.get_job(id, jobstore)

    def get_jobs(self, jobstore=None):
        """
        Return a list of pending jobs (if the scheduler hasn't been started yet) and scheduled jobs, either from a
        specific job store or from all of them.

        :param str jobstore: alias of the job store
        :rtype: list[Job]
        """

        return self._scheduler.get_jobs(jobstore)

    def modify_job(self, id, jobstore=None, **changes):
        """
        Modify the properties of a single job. Modifications are passed to this method as extra keyword arguments.

        :param str id: the identifier of the job
        :param str jobstore: alias of the job store that contains the job
        """

        fix_job_def(changes)

        if "trigger" in changes:
            trigger, trigger_args = pop_trigger(changes)
            self._scheduler.reschedule_job(id, jobstore, trigger, **trigger_args)

        return self._scheduler.modify_job(id, jobstore, **changes)

    def pause_job(self, id, jobstore=None):
        """
        Pause the given job until it is explicitly resumed.

        :param str id: the identifier of the job
        :param str jobstore: alias of the job store that contains the job
        """
        self._scheduler.pause_job(id, jobstore)

    def resume_job(self, id, jobstore=None):
        """
        Resume the schedule of the given job, or removes the job if its schedule is finished.

        :param str id: the identifier of the job
        :param str jobstore: alias of the job store that contains the job
        """
        self._scheduler.resume_job(id, jobstore)

    def run_job(self, id, jobstore=None):
        """
        Run the given job without scheduling it.
        :param id: the identifier of the job.
        :param str jobstore: alias of the job store that contains the job
        :return:
        """
        job = self._scheduler.get_job(id, jobstore)

        if not job:
            raise JobLookupError(id)

        job.func(*job.args, **job.kwargs)

    def authenticate(self, func):
        """
        A decorator that is used to register a function to authenticate a user.
        :param func: The callback to authenticate.
        """
        self._authentication_callback = func
        return func

    def _load_config(self):
        """
        Load the configuration from the Flask configuration.
        """
        options = dict()

        job_stores = self.app.config.get("SCHEDULER_JOBSTORES")
        if job_stores:
            options["jobstores"] = job_stores

        executors = self.app.config.get("SCHEDULER_EXECUTORS")
        if executors:
            options["executors"] = executors

        job_defaults = self.app.config.get("SCHEDULER_JOB_DEFAULTS")
        if job_defaults:
            options["job_defaults"] = job_defaults

        timezone = self.app.config.get("SCHEDULER_TIMEZONE")
        if timezone:
            options["timezone"] = timezone

        self._scheduler.configure(**options)

        self.auth = self.app.config.get("SCHEDULER_AUTH", self.auth)
        self.api_enabled = self.app.config.get("SCHEDULER_VIEWS_ENABLED", self.api_enabled)  # for compatibility reason
        self.api_enabled = self.app.config.get("SCHEDULER_API_ENABLED", self.api_enabled)
        self.api_prefix = self.app.config.get("SCHEDULER_API_PREFIX", self.api_prefix)
        self.endpoint_prefix = self.app.config.get("SCHEDULER_ENDPOINT_PREFIX", self.endpoint_prefix)

    def _load_jobs(self):
        """
        Load the job definitions from the Flask configuration.
        """
        jobs = self.app.config.get("SCHEDULER_JOBS")

        if not jobs:
            jobs = self.app.config.get("JOBS")

        if jobs:
            for job in jobs:
                self.add_job(**job)

    def _load_api(self):
        """
        Add the routes for the scheduler API.
        """
        # self._add_url_route("get_scheduler_info", "", api.get_scheduler_info, "GET")
        # self._add_url_route("pause_scheduler", "/pause", api.pause_scheduler, "POST")
        # self._add_url_route("resume_scheduler", "/resume", api.resume_scheduler, "POST")
        # self._add_url_route("start_scheduler", "/start", api.start_scheduler, "POST")
        # self._add_url_route("shutdown_scheduler", "/shutdown", api.shutdown_scheduler, "POST")
        # self._add_url_route("add_job", "/jobs", api.add_job, "POST")
        # self._add_url_route("get_job", "/jobs/<job_id>", api.get_job, "GET")
        # self._add_url_route("get_jobs", "/jobs", api.get_jobs, "GET")
        # self._add_url_route("delete_job", "/jobs/<job_id>", api.delete_job, "DELETE")
        # self._add_url_route("update_job", "/jobs/<job_id>", api.update_job, "PATCH")
        # self._add_url_route("pause_job", "/jobs/<job_id>/pause", api.pause_job, "POST")
        # self._add_url_route("resume_job", "/jobs/<job_id>/resume", api.resume_job, "POST")
        # self._add_url_route("run_job", "/jobs/<job_id>/run", api.run_job, "POST")

    def _add_url_route(self, endpoint, rule, view_func, method):
        """
        Add a Flask route.
        :param str endpoint: The endpoint name.
        :param str rule: The endpoint url.
        :param view_func: The endpoint func
        :param str method: The http method.
        """
        if self.api_prefix:
            rule = self.api_prefix + rule

        if self.endpoint_prefix:
            endpoint = self.endpoint_prefix + endpoint

        self.app.add_url_rule(
            rule,
            endpoint,
            self._apply_auth(view_func),
            methods=[method]
        )

    def _apply_auth(self, view_func):
        """
        Apply decorator to authenticate the user who is making the request.
        :param view_func: The flask view func.
        """
        @functools.wraps(view_func)
        def decorated(*args, **kwargs):
            if not self.auth:
                return view_func(*args, **kwargs)

            auth_data = self.auth.get_authorization()

            if auth_data is None:
                return self._handle_authentication_error()

            if not self._authentication_callback or not self._authentication_callback(auth_data):
                return self._handle_authentication_error()

            return view_func(*args, **kwargs)

        return decorated

    def _handle_authentication_error(self):
        """
        Return an authentication error.
        """
        response = make_response("Access Denied")
        response.headers["WWW-Authenticate"] = self.auth.get_authenticate_header()
        response.status_code = 401
        return response
