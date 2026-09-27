import discord
from discord.ext import commands, tasks
import os
import json
import datetime
from icalendar import Calendar
import requests
from datetime import date
import pytz
from dateutil.relativedelta import relativedelta


class Utilities(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["cal, calendar"], pass_context=True)
    async def events(self, ctx):
        calendar_request = requests.get(
            "https://shoreline.ucsb.edu/ical/ucsb/ical_club_72068.ics")
        calendar = Calendar.from_ical(calendar_request.text)
        events = [CalEvent(event) for event in calendar.events]

        today = datetime.datetime.now(tz=pytz.timezone("US/Pacific"))
        events_to_display = [event for event in events if event.date > today][:5] # only display the next 5 events
        embed = discord.Embed()
        for i, event in enumerate(events_to_display):
            embed.add_field(name=f"{i + 1}. {event.date.strftime('%a, %b %d: %I:%M %p')}: {event.title}", value=event.description, inline=False)
        await ctx.send(embed=embed)


class CalEvent:
    def __init__(self, event):
        self.title = event.summary[:-23]
        self.description = event.description
        self.date = event.start.astimezone(pytz.timezone("US/Pacific"))


async def setup(client):
    await client.add_cog(Utilities(client))
