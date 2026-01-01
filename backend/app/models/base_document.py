"""Base document class for MongoDB models."""

from typing import Optional
from bson import ObjectId


class BaseDocument:
    """Base class for MongoDB documents."""

    def __init__(self, **data):
        self._id = data.get("_id")
        for key, value in data.items():
            if key != "_id":
                setattr(self, key, value)

    @property
    def id(self):
        """Get string representation of ObjectId."""
        return str(self._id) if self._id else None

    def to_dict(self):
        """Convert document to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if key == "_id" and value:
                result[key] = str(value)
            elif not key.startswith("_"):
                result[key] = value
        return result
