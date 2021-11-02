from enum import Enum

class RegexPatterns(Enum):
    
    GET_TASK_POINTS = r"\s*\|\s*(\w+)\s*$"
    POINTS = "int, Estimated task points"
    DONE = "boolean, is the task done"
    DUE_DATE = "datetime, due date"