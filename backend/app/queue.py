from __future__ import annotations

import os

from redis import Redis
from rq import Queue

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
connection = Redis.from_url(redis_url)
task_queue = Queue("evvents-tasks", connection=connection)
