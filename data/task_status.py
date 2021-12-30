from enum import Enum


class TaskStatus(Enum):
    
    NO_CHANGE = "no_change"
    NEW = "new"
    UPDATED = "updated"
    COMPLETED = "completed"
    DELETED = "deleted"
