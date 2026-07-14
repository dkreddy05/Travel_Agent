"""
wanderai/repositories/base.py
Generic base repository — all CRUD operations using SQLAlchemy.
Domain repositories extend this and add query-specific methods.
"""

from typing import TypeVar, Generic, Type, Optional
from wanderai.extensions import db

T = TypeVar("T", bound=db.Model)


class BaseRepository(Generic[T]):
    """
    Type-safe repository base class.
    Usage: class UserRepository(BaseRepository[User]): ...
    """

    def __init__(self, model_class: Type[T]):
        self.model = model_class

    def get_by_id(self, record_id: str) -> Optional[T]:
        return db.session.get(self.model, record_id)

    def get_all(self) -> list[T]:
        return self.model.query.all()

    def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        db.session.add(instance)
        db.session.flush()  # get ID without committing
        return instance

    def update(self, instance: T, **kwargs) -> T:
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        db.session.flush()
        return instance

    def delete(self, instance: T) -> None:
        db.session.delete(instance)
        db.session.flush()

    def commit(self) -> None:
        db.session.commit()

    def rollback(self) -> None:
        db.session.rollback()
