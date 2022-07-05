from enum import Enum

from data.task_data import TaskData


class FilterTagsRegex(Enum):

    POINTS = fr"^{TaskData.POINTS.value}-\d+$"
    ENERGY = fr"^{TaskData.ENERGY.value}-\d+$"
