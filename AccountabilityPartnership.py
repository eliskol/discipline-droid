import json
import random
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
        stake_level: str = "low",
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
        self.stake_level: str = stake_level
        self.started_by: int | None = started_by
        self.paused: bool = paused
        if new:
            print("Saving new Accountability Partnership")
            self.save_partnership()

    @classmethod
    def from_member_id(cls, member_id: int):
        """
        This method gets the AP instance for the other member in the Partnership.

        :param cls: self parameter; AccountabilityPartnership class.
        :param member_id: Discord member's id to search for.
        :type member_id: int
        :return: None if there is no AP for member_id, or the AP object if there is one.
        :rtype: AccountabilityPartnership | None
        """
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
            partnership["stakes"],
            partnership["started_by"],
            False,
            partnership["paused"]
        )

    def get_other_member_ap(self) -> "None | AccountabilityPartnership":
        """
        Docstring for get_other_member_ap

        :param self: Instance of AccountabilityPartnership
        :return: Returns the AP instance belonging to the other person in the Accountability Partnership.
        :rtype: AccountabilityPartnership | None
        """
        return self.from_member_id(self.other_member)

    def save_partnership(self):
        """
        This method saves the self instance of the AccountabilityPartnership class to cogs/accountability.json
        """
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
            "stakes": self.stake_level,
            "started_by": self.started_by,
            "paused": self.paused
        }
        with open("cogs/accountability.json", "w") as write:
            json.dump(partnerships_dict, write, indent=2)

    def log_today(self) -> Literal["paused", "already logged", "successful", "missing log"]:
        """
        This method logs for today in the AP instance.
        It returns a status string depending on the execution of the log.

        :return: Returns 'paused' if the Partnership is currently paused; 'already logged' if today was already logged; 'successful' if successful; or 'missing log' if yesterday was not logged.
        :rtype: Literal['paused', 'already logged', 'successful', 'missing log']
        """
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

    def log_yesterday(self) -> Literal["paused", "already logged", "successful", "missing log"]:
        """
        Analog to log_today, but for the previous day.

        :return: Returns 'paused' if the Partnership is currently paused; 'already logged' if yesterday was already logged; 'successful' if successful; 'missing log' if the day before last was not logged (which shouldn't be possible, since partnerships are eliminated if not logged for 2 days).
        :rtype: Literal['paused', 'already logged', 'successful', 'missing log']
        """
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
        """
        Docstring for date_obj_from_str

        :param string: string representing a date in isoformat, or None.
        :type string: str | None
        :return: returns the date 1/1/1 if None is passed in, or the date as a date object otherwise.
        :rtype: date
        """
        if string is None: return datetime.date(1, 1, 1)
        return date.fromisoformat(string)

    def update_last_date_completed(self):
        """
        This method updates the last_date_completed attribute in both members' AP objects and saves them to the json file.
        """
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
        """
        This method should only be called after a successful log.
        It adds 2 points to both members of a Partnership if they have completed a new day.
        """
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
        """
        This method adds a given amount of points to a member with given id.

        :param member_id: member to add points to
        :type member_id: int
        :param points_to_add: number of points to add
        :type points_to_add: int | float
        """
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
        This method pauses a Partnership, modifies both AP instances, and saves them.
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
        This method resumes a Partnership, modifies both AP instances, and saves them.
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

    def fail_partnership(self) -> int:
        """
        Fails the partnership, deleting it from accountability.json and removing a random amount of points based on the stakes of the partnership.
        It returns the amount of points lost.
        """
        with open("cogs/accountability.json", "r") as read:
            all_partnerships = json.load(read)
            read.close()
            print(f"Read accountability.json: {all_partnerships}")
        del all_partnerships[str(self.primary_member)]
        print(f"Deleted this partnership, now all_partnerships is {all_partnerships}.")
        with open("cogs/accountability.json", "w") as write:
            print("Dumping accountability.json now.")
            json.dump(all_partnerships, write, indent=2)
            write.close()

        stake = self.calculate_stake()
        self.remove_points_from_primary_member(stake)

        other_ap = self.get_other_member_ap()
        if other_ap is not None:
            other_ap.fail_partnership()
            other_ap.remove_points_from_primary_member(stake)

        return stake


    def calculate_stake(self) -> int:
        """
        Helper method for failing the partnership.
        Returns the amount of points to remove for the stake.
        """
        point_ranges = {"low": [20, 40], "medium": [40, 60], "high": [50, 200]}
        return random.randrange(*point_ranges[self.stake_level], 1)

    def remove_points_from_primary_member(self, points_to_remove):
        """
        Removes a given amount of points from the primary member of the partnership.
        Returns the amount of points removed.
        :param points_to_remove: Amount of points to remove
        """
        with open("cogs/eco.json", "r") as f:
            user_eco = json.load(f)
        if str(self.primary_member) not in user_eco:
            user_eco[str(self.primary_member)] = {}
            user_eco[str(self.primary_member)]["Growth Points"] = 0
        user_eco[str(self.primary_member)]["Growth Points"] -= points_to_remove
        with open("cogs/eco.json", "w") as f:
            json.dump(user_eco, f, indent=2)