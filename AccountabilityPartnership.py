import json
import datetime
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
            self.save_partnership()

    @classmethod
    def from_member_id(cls, member_id: int):
        print(f"Fetching AccountabilityPartnership object for member with id {member_id}")
        with open("cogs/accountability.json", "r") as read:
            partnerships_dict = json.load(read)
            print(f"Just read accountablity.json and got the following:\n{partnerships_dict}")
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
            json.dump(partnerships_dict, write)

    def log_today(self) -> str:
        today = datetime.datetime.now(timezone("US/Pacific")).date()
        yesterday = today - datetime.timedelta(1)
        if self.last_date_logged == str(today):  # if today already logged
            return "already logged"
        if self.last_date_logged == str(yesterday) or self.date_started == str(today):
            self.last_date_logged = str(today)
            self.save_partnership()
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
            return "successful"
        return "missing log"

    def date_obj_from_str(self, string: str | None) -> datetime.date:
        if string is None: return datetime.date(1, 1, 1)
        split = string.split("-")
        return datetime.date(*map(int, split))
