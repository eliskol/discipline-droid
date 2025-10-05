import json
import datetime
from datetime import date
from pytz import timezone



class AccountabilityPartnership:
    def __init__(
        self,
        primary_member: int,
        other_member: int,
        date_started: str | None = None,
        last_date_logged: str | None = None,
        last_date_completed: str | None = None,
        started_by: int | None = None,
        new=True,
    ):
        self.date_started: str = (
            date_started
            if date_started
            else str(datetime.datetime.now(timezone("US/Pacific")).date())
        )
        self.primary_member: int = primary_member
        self.other_member: int = other_member
        self.last_date_logged: str | None = last_date_logged
        self.last_date_completed: str | None = last_date_completed
        self.started_by = started_by
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
        return cls(
            member_id,
            int(partnership["other_member"]),
            partnership["date_started"],
            partnership["last_date_logged"],
            partnership["last_date_completed"],
            partnership["started_by"],
            False,
        )

    def get_other_member_ap(self):
        return self.from_member_id(self.other_member)

    def save_partnership(self):
        with open("cogs/accountability.json", "r") as read:
            partnerships_dict = json.load(read)
        partnerships_dict[str(self.primary_member)] = {
            "other_member": self.other_member,
            "date_started": self.date_started,
            "last_date_logged": self.last_date_logged,
            "last_date_completed": self.last_date_completed,
            "started_by": self.started_by,
        }
        with open("cogs/accountability.json", "w") as write:
            json.dump(partnerships_dict, write, indent=2)

    def log_today(self) -> str:
        today = datetime.datetime.now(timezone("US/Pacific")).date()
        yesterday = today - datetime.timedelta(1)
        if self.last_date_logged == str(today):  # if today already logged
            return "already logged"
        if self.last_date_logged == str(yesterday) or self.date_started == str(today):
            self.last_date_logged = str(today)
            self.save_partnership() # possibly redundant since disburse_points calls update_last_date_completed which saves partnership
            print(f"Saved partnership after updating last_date_logged")
            self.disburse_points()
            return "successful"
        return "missing log"

    def log_yesterday(self) -> str:
        today = datetime.datetime.now(timezone("US/Pacific")).date()
        yesterday = today - datetime.timedelta(1)
        last_date_logged = self.date_obj_from_str(self.last_date_logged)
        if last_date_logged >= yesterday:
            return "already logged"
        if last_date_logged == yesterday - datetime.timedelta(1) or self.date_started == str(yesterday):
            self.last_date_logged = str(yesterday)
            self.save_partnership()
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
        # elif self.last_date_logged is None: # other_ap.last_date_logged cannot possibly be None now
        #     self.last_date_completed = other_ap.last_date_logged
        #     other_ap.last_date_completed = other_ap.last_date_logged
        # elif other_ap.last_date_logged is None: # self.last_date_logged cannot possibly be None now
        #     self.last_date_completed = self.last_date_logged
            # other_ap.last_date_completed = self.last_date_logged
        else: # neither self.last_date_logged nor other_ap.last_date_logged are None
            self.last_date_completed = min(self.last_date_logged, other_ap.last_date_logged)
            other_ap.last_date_completed = min(self.last_date_logged, other_ap.last_date_logged)
        print(f"self.last_date_completed is now {self.last_date_completed}")
        self.save_partnership()
        other_ap.save_partnership()

    def disburse_points(self): # should only be called when a log is successful
        print("inside disburse_points now ")
        date_started = self.date_obj_from_str(self.date_started)
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

    def get_log_streak(self) -> int:
        if self.last_date_logged is None: return 0
        return (date.fromisoformat(self.last_date_logged) - date.fromisoformat(self.date_started)).days + 1

    def get_completion_streak(self) -> int:
        if self.last_date_completed is None: return 0
        return (date.fromisoformat(self.last_date_completed) - date.fromisoformat(self.date_started)).days + 1