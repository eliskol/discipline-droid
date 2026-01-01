import json
import datetime
from datetime import date
from typing import Literal
from pytz import timezone



class AccountabilityPartnership:
    def __init__(
        self,
        primary_member: int,
        other_member: int,
        date_started: str | None = None,
        date_resumed: str | None = None,
        last_date_logged: str | None = None,
        log_streak: int = 0,
        last_date_completed: str | None = None,
        completion_streak: int = 0,
        started_by: int | None = None,
        new=True,
        paused=False
    ):
        self.primary_member: int = primary_member
        self.other_member: int = other_member
        self.date_started: str = (
            date_started
            if date_started
            else str(datetime.datetime.now(timezone("US/Pacific")).date())
        )
        self.date_resumed: str | None = date_resumed
        self.last_date_logged: str | None = last_date_logged
        self.log_streak: int = log_streak
        self.last_date_completed: str | None = last_date_completed
        self.completion_streak: int = completion_streak
        self.started_by: int | None = started_by
        self.paused: bool = paused
        if new:
            print("Saving new Accountability Partnership")
            self.save_partnership()

    @classmethod
    def from_member_id(cls, member_id: int):
        print(f"Fetching AccountabilityPartnership object for member with id {member_id}")
        with open("cogs/accountability.json", "r") as read:
            partnerships_dict = json.load(read)
        if str(member_id) not in partnerships_dict.keys():
            return None
        partnership = partnerships_dict[str(member_id)]
        print("Stored AP:", partnership)
        return cls(
            member_id,
            int(partnership["other_member"]),
            partnership["date_started"],
            partnership["date_resumed"],
            partnership["last_date_logged"],
            int(partnership["log_streak"]),
            partnership["last_date_completed"],
            int(partnership["completion_streak"]),
            partnership["started_by"],
            False,
            partnership["paused"]
        )

    def get_other_member_ap(self):
        return self.from_member_id(self.other_member)

    def save_partnership(self):
        with open("cogs/accountability.json", "r") as read:
            partnerships_dict = json.load(read)
        partnerships_dict[str(self.primary_member)] = {
            "other_member": self.other_member,
            "date_started": self.date_started,
            "date_resumed": self.date_resumed,
            "last_date_logged": self.last_date_logged,
            "log_streak": self.log_streak,
            "last_date_completed": self.last_date_completed,
            "completion_streak": self.completion_streak,
            "started_by": self.started_by,
            "paused": self.paused
        }
        with open("cogs/accountability.json", "w") as write:
            json.dump(partnerships_dict, write, indent=2)

    def log_today(self) -> str:
        if self.paused: return "paused"
        today = datetime.datetime.now(timezone("US/Pacific")).date()
        yesterday = today - datetime.timedelta(1)
        if self.last_date_logged == str(today):  # if today already logged
            return "already logged"
        if self.last_date_logged == str(yesterday) or self.date_started == str(today) or self.date_resumed == str(today):
            self.last_date_logged = str(today)
            self.log_streak += 1

            other_ap = self.get_other_member_ap()
            if self.last_date_logged == other_ap.last_date_logged:
                self.completion_streak += 1
                other_ap.completion_streak += 1
            self.save_partnership() # possibly redundant since disburse_points calls update_last_date_completed which saves partnership
            other_ap.save_partnership()

            print(f"Saved partnership after updating last_date_logged")
            self.disburse_points()
            return "successful"
        return "missing log"

    def log_yesterday(self) -> str:
        if self.paused: return "paused"
        today = datetime.datetime.now(timezone("US/Pacific")).date()
        yesterday = today - datetime.timedelta(1)
        last_date_logged = self.date_obj_from_str(self.last_date_logged)
        if last_date_logged >= yesterday:
            return "already logged"
        if last_date_logged == yesterday - datetime.timedelta(1) or self.date_started == str(yesterday) or self.date_resumed == str(yesterday):
            self.last_date_logged = str(yesterday)
            self.log_streak += 1

            other_ap = self.get_other_member_ap()
            if date.fromisoformat(self.last_date_logged) <= self.date_obj_from_str(other_ap.last_date_logged):
                self.completion_streak += 1
                other_ap.completion_streak += 1

            self.save_partnership()
            other_ap.save_partnership()
            print(f"Saved partnership after updating last_date_logged")
            self.disburse_points()
            return "successful"
        return "missing log"

    def date_obj_from_str(self, string: str | None) -> datetime.date:
        if string is None: return datetime.date(1, 1, 1)
        return date.fromisoformat(string)

    def update_last_date_completed(self):
        other_ap = self.get_other_member_ap()
        if other_ap is None:
            print(f"There has been an error in update_last_date_completed inside the AP for user {self.primary_member}.")
            return
        elif self.last_date_logged is None or other_ap.last_date_logged is None:
            return
        else: # neither self.last_date_logged nor other_ap.last_date_logged are None
            self.last_date_completed = min(self.last_date_logged, other_ap.last_date_logged)
            other_ap.last_date_completed = min(self.last_date_logged, other_ap.last_date_logged)
        print(f"self.last_date_completed is now {self.last_date_completed}")
        self.save_partnership()
        other_ap.save_partnership()

    def disburse_points(self): # should only be called when a log is successful
        print("inside disburse_points now ")
        points_to_add = 0
        old_last_date_completed = str(self.last_date_completed)
        self.update_last_date_completed()
        self.added_points = False
        if str(self.last_date_completed) != old_last_date_completed: # str() is necessary because it might be None
            points_to_add = 2
            self.added_points = True
        self.add_points_to_member(self.primary_member, points_to_add)
        self.add_points_to_member(self.other_member, points_to_add)
        print(f"Added {points_to_add} point to {self.primary_member} and {self.other_member}")

    def add_points_to_member(self, member_id: int, points_to_add : int | float):
        with open("cogs/eco.json", "r") as f:
            user_eco = json.load(f)
        if str(member_id) not in user_eco:
            user_eco[str(member_id)] = {}
            user_eco[str(member_id)]["Growth Points"] = 0
        user_eco[str(member_id)]["Growth Points"] += points_to_add
        with open("cogs/eco.json", "w") as f:
            json.dump(user_eco, f, indent=2)

    def pause_partnership(self) -> bool:
        """
        Docstring for pause_partnership

        :return: False if already paused, True if now paused.
        :rtype: bool
        """
        if not self.paused:
            self.paused = True
            self.save_partnership()
            self.get_other_member_ap().pause_partnership()
            return True
        return False

    def resume_partnership(self) -> bool:
        """
        Docstring for resume_partnership

        :return: False if already active, True if now active.
        :rtype: bool
        """
        if self.paused:
            self.paused = False
            self.date_resumed = str(datetime.datetime.now(timezone("US/Pacific")).date())
            self.save_partnership()
            self.get_other_member_ap().resume_partnership()
            return True
        return False