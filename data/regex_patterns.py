

class RegexPatterns:
    
    GET_TASK_ENERGY = r"^\s*(\d)\s*\|"
    GET_TASK_POINTS = r"-\s*(\d+)\s*$"
    GET_TASK_TITLE = r"^\s*\d\s*\|\s*(.+)\s*-\s*\d+\s*$"
    GET_TASK_DATE = r"(.+)T"
    POINTS = "int, Estimated task points"
    DONE = "boolean, is the task done"
    DUE_DATE = "datetime, due date"
