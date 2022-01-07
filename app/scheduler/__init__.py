from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from urllib.parse import urlparse, parse_qs
from redis import UnixDomainSocketConnection

from app.json_rpc.api import JsonRpcAPI

class SchedulerMeta(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SchedulerMeta, cls).__call__(*args, **kwargs)
        return cls._instance

    @property
    def api(cls) -> JsonRpcAPI:
        return cls._instance._api

class Scheduler(object, metaclass=SchedulerMeta):

    _scheduler: AsyncIOScheduler = None
    _instance = None
    _api: JsonRpcAPI

    def __init__(self, scheduler: AsyncIOScheduler, url: str, api: JsonRpcAPI) -> None:
        self._scheduler = scheduler
        self._api = api
        redis_url = urlparse(url)
        redis_url_options = parse_qs(redis_url.query)

        match redis_url.scheme:
            case "redis":
                jobstores = {
                    "default": RedisJobStore(
                        host=redis_url.hostname,
                        db=int(redis_url.path.strip("/")),
                    )
                }
            case "unix":
                jobstores = {
                    "default": RedisJobStore(
                        unix_socket_path=redis_url.path,
                        db=int(redis_url_options.get("db")[0]),
                    )
                }
        self._scheduler.configure(jobstores=jobstores)

    @classmethod
    def start(cls):
        cls._instance._scheduler.start()

    @classmethod
    def add_job(cls, *args, **kwargs):
        return cls._instance._scheduler.add_job(*args, **kwargs)

    @classmethod
    def get_job(cls, id, jobstore=None):
        return cls._instance._scheduler.get_job(id, jobstore)

    @classmethod
    def cancel_jobs(cls, id, jobstore=None):
        return cls._instance._scheduler.remove_job(id, jobstore)

    @classmethod
    def remove_all_jobs(cls, jobstore=None):
        return cls._instance._scheduler.remove_all_jobs(jobstore)

    @classmethod
    def get_jobs(cls, jobstore=None, pending=None):
        return cls._instance._scheduler.get_jobs(jobstore, pending)
