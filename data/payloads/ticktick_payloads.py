from datetime import datetime


class TicktickPayloads:

    @staticmethod
    def get_habits_checkins(habit_list: dict, after_stamp: int) -> dict:
        return {
                "habitIds": list(habit_list.keys()),
                "afterStamp": after_stamp
                }

    @classmethod
    def complete_task(cls, task_id: str, project_id: str) -> dict:
        return {
                "update": [
                    {
                        "completedUserId": 114478622,
                        "status": 2,
                        "projectId": project_id,
                        "completedTime": f"{datetime.utcnow()}+0000",
                        "id": task_id
                    }
                ]
            }
