from celery import Celery
from config.settings import settings
from celery.schedules import crontab

celery_app = Celery(
    "graphrag_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['src.workers.tasks'] 
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1, 
    task_acks_late=True           
)

celery_app.conf.beat_schedule = {
    'purge-qdrant-graveyard-every-hour': {
        'task': 'sweep_orphaned_vectors',
        'schedule': crontab(minute=0), # Executes at the top of every hour
    },
}