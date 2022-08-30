import json
import uuid
from typing import List, NewType, TypeVar
from dataclasses import dataclass
import time

import jsonpickle

# Model (also types)
REDIS_KEY = "buffer"


@dataclass
class GpsRecord:
    tripId: int
    lat: float
    lon: float
    altitude: float
    speed: float
    timestamp: int = int(time.time() * 1000)
    userId: int = uuid.getnode()

    def __str__(self):
        return str(json.dumps(self.__dict__))

    def to_json(self):
        return jsonpickle.encode(self)


# Types
T = TypeVar("T")
NonEmptyGpsRecordList = NewType("NonEmptyGpsRecordList", List[GpsRecord])
