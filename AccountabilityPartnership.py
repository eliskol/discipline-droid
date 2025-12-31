import json
import datetime
from datetime import date
from pytz import timezone



class AccountabilityPartnership:
    def __init__(
        self,
        primary_member: int,
        other_member: int,
        date_list: list[str] | None = None,
        last_date_completed: str | None = None,
        paused: bool = False,
        started_by: int | None = None,
        new=True,
    ):
        self.date_list: list[str] = (
            date_list
            if date_list
            else [str(datetime.datetime.now(timezone("US/Pacific")).date())]
        )
        self.last_date_completed = last_date_completed
        self.paused = paused
        self.primary_member: int = primary_member
        self.other_member: int = other_member
        self.started_by = started_by
        if new:
            print(f"Saving new Accountability Partnership between {self.primary_member} and {self.other_member}")
            self.save_partnership()

    @classmethod
    def from_member_id(cls, member_id: int):
        print(f"Fetching AccountabilityPartnership object for member with id {member_id}.")
        with open("cogs/accountability.json", "r") as read:
            partnerships_dict = json.load(read)
        if str(member_id) not in partnerships_dict.keys():
            print(f"Could not find an AccountabilityPartnership object for member with id {member_id}.")
            return None
        partnership = partnerships_dict[str(member_id)]
        print(f"Found an AccountabilityPartnership object for member with id {member_id}.")
        return cls(
            member_id,
            int(partnership["other_member"]),
            partnership["date_list"],
            partnership["last_date_completed"],
            partnership["paused"],
            partnership["started_by"],
            False,
        )

    def get_other_member_ap(self):
        print(f"Getting other member AccountabilityPartnership object from object of member id {self.primary_member}.")
        return self.from_member_id(self.other_member)

    def save_partnership(self):
        print(f"Saving partnership of member {self.primary_member}.")
        with open("cogs/accountability.json", "r") as read:
            print(f"Opening accountability.json.")
            partnerships_dict = json.load(read)
        print(f"Adding partnership to json object.")
        partnerships_dict[str(self.primary_member)] = {
            "other_member": self.other_member,
            "date_list": self.date_list,
            "last_date_completed": self.last_date_completed,
            "paused": self.paused,
            "started_by": self.started_by,
        }
        with open("cogs/accountability.json", "w") as write:
            print(f"Saving json object.")
            json.dump(partnerships_dict, write, indent=2)

    def get_last_date_logged(self) -> str | None:
        if len(self.date_list) == 0:
            return None
        elif len(self.date_list) % 3 == 0:
            return "Paused"
        elif len(self.date_list) % 3 == 1:
            return None
        elif len(self.date_list) % 3 == 2:
            return self.date_list[-1]

    def get_date_resumed(self) -> str | None:
        if self.date_list == []: return None
        elif len(self.date_list) < 3: return self.date_list[0]
        return self.date_list[-(len(self.date_list) % 3) - 1]

    def log_today(self) -> str:
        print(f"Logging today for {self.primary_member}.")
        today = datetime.datetime.now(timezone("US/Pacific")).date()
        yesterday = today - datetime.timedelta(1)
        print("Getting last date logged:")
        last_date_logged = self.get_last_date_logged()
        print(last_date_logged)
        print("Now getting date resumed:")
        date_resumed = self.get_date_resumed()
        print(date_resumed)
        if last_date_logged == "Paused":
            return "Paused"
        elif last_date_logged == str(today):  # if today already logged
            print("Found that it was already logged.")
            return "already logged"
        elif last_date_logged == str(yesterday) or date_resumed == str(today):
            print("Successful log, saving last_date_logged now.")
            if len(self.date_list) % 3 == 2:
                print("Updating today's date in date_list.")
                self.date_list[-1] = str(today)
            elif len(self.date_list) % 3 == 1:
                print("Adding today's date to date_list.")
                self.date_list.append(str(today))
            self.save_partnership() # possibly redundant since disburse_points calls update_last_date_completed which saves partnership
            print(f"Saved partnership after updating last_date_logged")
            self.disburse_points()
            return "successful"
        return "missing log"

    def log_yesterday(self) -> str:
        today = datetime.datetime.now(timezone("US/Pacific")).date()
        yesterday = today - datetime.timedelta(1)
        last_date_logged = self.date_obj_from_str(self.get_last_date_logged())
        if last_date_logged >= yesterday:
            return "already logged"
        if last_date_logged == yesterday - datetime.timedelta(1) or self.get_date_resumed() == str(yesterday):
            if len(self.date_list) % 3 == 2:
                print("Updating yesterday's date in date_list.")
                self.date_list[-1] = str(yesterday)
            elif len(self.date_list) % 3 == 1:
                print("Adding yesterday's date to date_list.")
                self.date_list.append(str(yesterday))
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

        elif self.get_last_date_logged() is None or other_ap.get_last_date_logged() is None:
            return
        # elif self.last_date_logged is None: # other_ap.last_date_logged cannot possibly be None now
        #     self.last_date_completed = other_ap.last_date_logged
        #     other_ap.last_date_completed = other_ap.last_date_logged
        # elif other_ap.last_date_logged is None: # self.last_date_logged cannot possibly be None now
        #     self.last_date_completed = self.last_date_logged
            # other_ap.last_date_completed = self.last_date_logged
        else: # neither self.last_date_logged nor other_ap.last_date_logged are None
            self.last_date_completed = min(self.get_last_date_logged(), other_ap.get_last_date_logged())
            other_ap.last_date_completed = min(self.get_last_date_logged(), other_ap.get_last_date_logged())
        print(f"self.last_date_completed is now {self.last_date_completed}")
        self.save_partnership()
        other_ap.save_partnership()

    def disburse_points(self): # should only be called when a log is successful
        print("Inside disburse_points()")
        # date_started = self.date_obj_from_str(self.date_started)
        print("Calculating amount of points to add")
        points_to_add = 0
        old_last_date_completed = str(self.last_date_completed)
        self.update_last_date_completed()
        self.added_points = False
        if str(self.last_date_completed) != old_last_date_completed: # str() is necessary because it might be None
            print("Found that we should add 2 points.")
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
        if self.get_last_date_logged() is None:
            return 0
        elif len(self.date_list) < 3:
            return (date.fromisoformat(self.date_list[1]) - date.fromisoformat(self.date_list[0])).days + 1
        every_third_index = range(0, len(self.date_list), 3)
        if len(self.date_list) % 3 == 1:
            streak = 0
            for index in every_third_index[::-1][1:]:
                if self.date_list[index + 1] != self.date_list[index + 2]: # i + 1 gives a last date logged, and i + 2 gives a date paused
                    return streak
                streak += (date.fromisoformat(self.date_list[index + 1]) - date.fromisoformat(self.date_list[index + 2])).days + 1
            return streak

        streak = 0
        for index in every_third_index[::-1]:
            if self.date_list[index + 1] != self.date_list[index + 2]:
                return streak
            streak += (date.fromisoformat(self.date_list[index + 1]) - date.fromisoformat(self.date_list[index + 2])).days + 1
        return streak


    def get_completion_streak(self) -> int:
        print("Calculating completion streak.")
        return min(self.get_log_streak(), self.get_other_member_ap().get_log_streak())
        # if self.get_last_date_logged() is None:
        #     print("Returning streak since no logs yet.")
        #     return 0

        # other_partner_date_list = self.get_other_member_ap().date_list
        # print(f"Other partner's date list was {other_partner_date_list}")
        # if len(self.date_list) < 2 or len(other_partner_date_list) < 2:
        #     print("Returning streak since small lists.")
        #     return 0

        # every_third_index = range(0, len(self.date_list), 3)
        # every_third_index = every_third_index[::-1]
        # print(f"Every third index: {[i for i in every_third_index]}")
        # streak = 0
        # if len(self.date_list) % 3 == 1:
        #     print("inside if")
        #     every_third_index = every_third_index[1:]

        # recent_completion_streak = (date.fromisoformat(self.date_list[every_third_index[0] + 1]) - date.fromisoformat(self.date_list[every_third_index[0] + 2])).days + 1
        # print("recent", recent_completion_streak)
        # other_recent_completion_streak = (date.fromisoformat(other_partner_date_list[every_third_index[0] + 1]) - date.fromisoformat(other_partner_date_list[every_third_index[0] + 2])).days + 1
        # print("other recent", other_recent_completion_streak)
        # streak += min(recent_completion_streak, other_recent_completion_streak)

        # print(f"Streak is now {streak}")

        # for index in every_third_index[1:]:
        #     if self.date_list[index + 1] != other_partner_date_list[index + 1]:
        #         return streak
        #     streak += (date.fromisoformat(self.date_list[index + 1]) - date.fromisoformat(self.date_list[index + 2])).days + 1
        # print(f"Streak is now {streak}")
        # return streak


    def pause_partnership(self):
        if not self.paused:
            self.paused = True
            if len(self.date_list) % 3 == 1:
                self.date_list.append(None)
                self.date_list.append(str(datetime.datetime.now(timezone("US/Pacific")).date()))
            else:
                self.date_list.append(str(datetime.datetime.now(timezone("US/Pacific")).date()))
            self.save_partnership()

            self.get_other_member_ap().pause_partnership()

    def resume_partnership(self):
        if self.paused:
            self.paused = False
            self.date_list.append(str(datetime.datetime.now(timezone("US/Pacific")).date()))
            self.save_partnership()
            self.get_other_member_ap().resume_partnership()