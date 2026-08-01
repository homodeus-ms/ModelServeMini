from enum import Enum


class ModelVersionRelationType(str, Enum):
    BASE = "BASE"
    RESULT = "RESULT"