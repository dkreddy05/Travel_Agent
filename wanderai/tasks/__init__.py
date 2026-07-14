"""
wanderai/tasks/__init__.py
Re-exports the shared Celery app from extensions so task modules can simply:
    from wanderai.tasks import celery
"""

from wanderai.extensions import celery_app as celery  # noqa: F401
