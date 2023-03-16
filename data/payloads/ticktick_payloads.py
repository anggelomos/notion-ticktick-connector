
class TicktickPayloads:

    @staticmethod
    def get_habits_checkins(habit_list: dict, after_stamp: int) -> dict:
        return {
                "habitIds": list(habit_list.keys()),
                "afterStamp": after_stamp
                }
