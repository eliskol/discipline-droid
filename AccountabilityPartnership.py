import json
import datetime
from pytz import timezone

class AccountabilityPartnership:
    def __init__(self, primary_member : int, other_member : int, date_started : str | None = None, last_date_logged : str | None = None, last_date_completed : str | None = None, started_by : int | None = None, new = True):
        self.date_started : str = date_started if date_started else str(datetime.datetime.now(timezone('US/Pacific')).date())
        self.primary_member : int = primary_member
        self.other_member : int = other_member
        self.last_date_logged = last_date_logged
        self.last_date_completed = last_date_completed
        self.started_by = started_by
        if new: self.save_partnership()

    @classmethod
    def from_member_id(cls, member_id : int):
        with open("cogs/accountability.json", "r") as read:
            partnerships_dict = json.load(read)
        partnership = partnerships_dict[str(member_id)]
        return cls(member_id, int(partnership.other_member), partnership.date_started, partnership.last_date_logged, partnership.last_date_completed, partnership.started_by, False)

    def save_partnership(self):
        with open("cogs/accountability.json", "r") as read:
            partnerships_dict = json.load(read)
        partnerships_dict[str(self.primary_member)] = {"other_member": self.other_member, "date_started" : self.date_started, "last_date_logged" : None, "last_date_completed": None, "started_by" : self.started_by}
        with open("cogs/accountability.json", "w") as write:
            json.dump(partnerships_dict, write)


    def log_today(self):
        if self.last_date_logged == (datetime.datetime.now(timezone("US/Pacific")) - datetime.timedelta(1)).date(): # if last date logged was yesterday
            pass


    def log_yesterday(self):
        pass