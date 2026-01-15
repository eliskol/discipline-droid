# Packages used
import discord
from discord.ext import commands, tasks
import os
import asyncio
from datetime import datetime, timedelta
import datetime
import pandas as pd
import json
from AccountabilityPartnership import AccountabilityPartnership
from pytz import timezone

from dotenv import load_dotenv
from pathlib import Path

from csv_fixer import fix_csvs

dotenv_path = Path('main.env')
load_dotenv(dotenv_path=dotenv_path)

bot_token = os.getenv('bot_token')
leaderboard_channel_id = int(os.getenv('leaderboard_channel'))
habit_hub_channel_id = int(os.getenv('habit_hub_channel'))
accountability_channel_id = int(os.getenv('accountability_channel'))


# Initialize the bot with all intents
client = commands.Bot(command_prefix='!', intents=discord.Intents.all())
client.embed_message = None
# List of 10 reactions (you can change these emojis)
REACTIONS = ["🛏️", "😎", "🌅", "🧘", "📝", "🙏", "🏋", "🚿", "📖", "🌟"]

# Reaction triggers for specific actions
TREACTION_COMMANDS = {
    "🛏️": "makebed",
    "😎": "sunlight",
    "🌅": "earlybird",
    "🧘": "meditation",
    "📝": "journal",
    "🙏": "gratitude",
    "🏋": "workout",
    "🚿": "coldshower",
    "📖": "reading",  # Trigger the "reading" command
    "🌟": "personal"  # Trigger the "vice" command
}

YREACTION_COMMANDS = {
    "🛏️": "yesterdaymakebed",
    "😎": "yesterdaysunlight",
    "🌅": "yesterdayearlybird",
    "🧘": "yesterdaymeditation",
    "📝": "yesterdayjournal",
    "🙏": "yesterdaygratitude",
    "🏋": "yesterdayworkout",
    "🚿": "yesterdaycoldshower",
    "📖": "yesterdayreading",  # Trigger the "reading" command
    "🌟": "yesterdaypersonal"
}


@client.event
async def on_ready():
    await send_leaderboard_message()
    print(f"boutta call send_startup_message")
    await send_startup_message()  # Send a message at startup
    daily_loop.start()  # Start the daily message loop
    await check_accountability_partnerships()
    print("Bot is connected and ready!")


async def send_leaderboard_message():
    leaderboard_channel = client.get_channel(leaderboard_channel_id)
    if leaderboard_channel:
        embed = discord.Embed(
            title="🏆Self-Improvement Club Leaders🏆",
            description="Here we commemorate SIC members for their discipline!",
            color=discord.Color.green()
        )
        embed.add_field(name="Total Growth Points",
                        value=f"1. Test\n2. Test\n3. Test\n4. Test\n5. Test", inline=True)
        embed.add_field(name="Monthly Growth Points",
                        value=f"1. Test\n2. Test\n3. Test\n4. Test\n5. Test", inline=True)
        embed.add_field(
            name="🛏️ Make Bed", value=f"1. Test\n2. Test\n3. Test\n4. Test\n5. Test", inline=True)
        embed.add_field(
            name="😎 Sunlight", value=f"1. Test\n2. Test\n3. Test\n4. Test\n5. Test", inline=True)
        embed.add_field(
            name="🌅 Early Bird", value=f"1. Test\n2. Test\n3. Test\n4. Test\n5. Test", inline=True)
        embed.add_field(
            name="🧘 Meditation", value=f"1. Test\n2. Test\n3. Test\n4. Test\n5. Test", inline=True)
        embed.add_field(
            name="📝 Journaling", value=f"1. Test\n2. Test\n3. Test\n4. Test\n5. Test", inline=True)
        embed.add_field(
            name="🙏 Gratitude", value=f"1. Test\n2. Test\n3. Test\n4. Test\n5. Test", inline=True)
        embed.add_field(
            name="🏋 Workouts", value=f"1. Test\n2. Test\n3. Test\n4. Test\n5. Test", inline=True)
        embed.add_field(name="🚿 Cold Showers",
                        value=f"1. Test\n2. Test\n3. Test\n4. Test\n5. Test", inline=True)
        embed.add_field(
            name="📖 Reading", value=f"1. Test\n2. Test\n3. Test\n4. Test\n5. Test", inline=True)
        embed.add_field(name="🌟 Personal Goals",
                        value=f"1. Test\n2. Test\n3. Test\n4. Test\n5. Test", inline=True)

    print(f"last message id is {leaderboard_channel.last_message_id}")
    previous_message = await leaderboard_channel.fetch_message(leaderboard_channel.last_message_id)
    if previous_message.author.id == client.application_id and previous_message.created_at.date() == datetime.datetime.now(datetime.timezone.utc).date():
        await previous_message.delete()

    client.embed_message = await leaderboard_channel.send(embed=embed)

# Function to send the message at startup


async def send_startup_message():
    print(f"inside send_startup_message now")
    habit_channel = client.get_channel(habit_hub_channel_id)
    print(habit_channel)
    if habit_channel:
        print("inside if")
        todayr = (datetime.datetime.now(timezone("US/Pacific"))).date()
        todaytt = todayr.timetuple()
        today = todayr.isoformat()
        disc = ['coldshower', 'gratitude', 'journal', 'makebed', 'meditation',
                'personal', 'reading', 'sunlight', 'sunriser', 'workout']
        for a in disc: # adding current day to csv file if it isn't there already
            record = pd.read_csv(f"cogs/Habits Record/{a}.csv")
            if today != record.columns[-1]:
                record[today] = 0
                record.to_csv(f"cogs/Habits Record/{a}.csv", index=False)

        fix_csvs() # just in case

        print("line 124")

        embed = discord.Embed(
            title=f"⭐️ Daily Discipline Tracker {todaytt[1]}/{todaytt[2]}/{todaytt[0]} ⭐️",
            description="Hello, everyone! It's time to record your 10 Daily Disciplines!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Please click the emoji that represents your completed Discipline.\n"
            "Points will be recorded in the Progress Reporting Chat.",
            value="1. 🛏️ Make your bed. | 0.2 pts\n"
            "2. 😎 Get Sunlight Exposure. | 0.25 pts\n"
            "3. 🌅 Wake up at or before 6 am. | 0.5 pts\n"
            "4. 🧘 Meditate for at least 5 minutes. | 0.5 pts\n"
            "5. 📝 Write a Journal Entry. | 1 pt\n"
            "6. 🙏 Write down at least 3 things you're grateful for. | 0.3 pts\n"
            "7. 🏋️ Get at least 30 minutes of physical exercise. | 1 pt\n"
            "8. 🚿 Take a Cold Shower. | 0.5 pts\n"
            "9. 📖 Read for at least 5 minutes. | 0.5 pts\n"
            "10. 🌟 Complete your personal goal. | 1 pt\n", inline=True
        )

        print("made embed object")

        print(f"boutta get last message in habit hub")
        print(
            f"last message id in habit hub is {habit_channel.last_message_id}")
        previous_message = await habit_channel.fetch_message(habit_channel.last_message_id)
        if previous_message.author.id == client.application_id and previous_message.created_at.date() == datetime.datetime.now(datetime.timezone.utc).date():
            await previous_message.delete()
        print("about to send message")
        message = await habit_channel.send(embed=embed)

        for reaction in REACTIONS:
            await message.add_reaction(reaction)

# Task to send a message every day at 12:01 AM


@tasks.loop(hours=24)
async def daily_loop():
    now = datetime.datetime.now(timezone("US/Pacific"))
    midnight = now.replace(hour=0, minute=1, second=0, microsecond=0)
    if now > midnight:
        midnight += timedelta(days=1)
    delay = (midnight - now).total_seconds()
    print(delay)

    await asyncio.sleep(delay)  # Wait until 12:01 AM
    await check_accountability_partnerships()
    channelh: discord.TextChannel = client.get_channel(habit_hub_channel_id)
    if channelh:
        todayr = datetime.datetime.now(timezone("US/Pacific")).date()
        todaytt = todayr.timetuple()
        today = todayr.isoformat()
        disc = ['coldshower', 'gratitude', 'journal', 'makebed', 'meditation',
                'personal', 'reading', 'sunlight', 'sunriser', 'workout']
        for a in disc:
            record = pd.read_csv(f"cogs/Habits Record/{a}.csv")
            if today != record.columns[-1]:
                record[today] = 0
                record.to_csv(f"cogs/Habits Record/{a}.csv", index=False)
        embed = discord.Embed(
            title=f"⭐️ Daily Discipline Tracker {todaytt[1]}/{todaytt[2]}/{todaytt[0]} ⭐️",
            description="Hello, everyone! It's time to record your 10 Daily Disciplines!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Please click the emoji that represents your completed Discipline.\n"
            "Points will be recorded in the Progress Reporting Chat.",
            value="1. 🛏️ Make your bed. | 0.2 pts\n"
            "2. 😎 Get Sunlight Exposure. | 0.25 pts\n"
            "3. 🌅 Wake up at or before 6 am. | 0.5 pts\n"
            "4. 🧘 Meditate for at least 5 minutes. | 0.5 pts\n"
            "5. 📝 Write a Journal Entry. | 1 pt\n"
            "6. 🙏 Write down at least 3 things you're grateful for. | 0.3 pts\n"
            "7. 🏋️ Get at least 30 minutes of physical exercise. | 1 pt\n"
            "8. 🚿 Take a Cold Shower. | 0.5 pts\n"
            "9. 📖 Read for at least 5 minutes. | 0.5 pts\n"
            "10. 🌟 Complete your personal goal. | 1 pt\n", inline=True
        )
        message = await channelh.send(embed=embed)
        for reaction in REACTIONS:
            await message.add_reaction(reaction)

# Restart the loop to ensure it waits until the next time after restart


@daily_loop.before_loop
async def before_daily_message():
    await client.wait_until_ready()


async def check_accountability_partnerships():
    print("checking accountability partnerships now")
    if os.path.exists("cogs/accountability.json"):
        with open("cogs/accountability.json", "r") as read:
            accountability_partnerships = json.load(read)

        yesterday_date = datetime.datetime.now(
            timezone("US/Pacific")).date() - timedelta(days=1)
        ids_that_failed = []

        accountability_channel = client.get_channel(accountability_channel_id)

        for id in accountability_partnerships:
            if id in ids_that_failed:
                print(f"{id} already in ids_that_failed")
                continue
            print(f"looking at member with id {id}")
            ap = AccountabilityPartnership.from_member_id(int(id))
            if ap is None:
                continue
            elif ap.paused:
                continue

            if ap.last_date_logged is None and (ap.date_obj_from_str(ap.date_resumed if ap.date_resumed else ap.date_started) - yesterday_date).days < -1:
                print("failed! failed to log for new partnership")
                points_lost = ap.fail_partnership()
                await accountability_channel.send(f"<@{id}> and <@{ap.other_member}>, your Accountability Partnership went uncompleted and has ended. You lost {points_lost} points.")
            elif ap.last_date_logged is not None and (ap.date_obj_from_str(ap.last_date_logged) - yesterday_date).days < -1:
                print("failed! failed to log")
                points_lost = ap.fail_partnership()
                await accountability_channel.send(f"<@{id}> and <@{ap.other_member}>, your Accountability Partnership went uncompleted and has ended. You lost {points_lost} points.")
            else: print("still in!")

    else:
        with open("cogs/accountability.json", "w") as write:
            print(f"Dumping empty json since cogs/accountability.json does not exist.")
            json.dump({}, write, index=2)

# Handle reactions to trigger commands


@client.event
async def on_reaction_add(reaction, user):
    if user.bot:  # Ignore bot reactions
        return
    todayr = datetime.datetime.now(timezone("US/Pacific")).date()
    today = todayr.isoformat()
    yesterdayr = todayr - datetime.timedelta(days=1)
    yesterday = yesterdayr.isoformat()
    mdate = (reaction.message.created_at.replace(tzinfo=timezone("US/Pacific"))).date()
    mdate = str(mdate)
    # Check if it's a bot message and the emoji is in the reaction commands
    if reaction.message.author == client.user and reaction.emoji in TREACTION_COMMANDS and today == mdate:
        ctx = await client.get_context(reaction.message)
        ctx.author = user
        command_name = TREACTION_COMMANDS[reaction.emoji]

        # Find the command and invoke it with the context
        command = client.get_command(command_name)
        if command:
            await ctx.invoke(command)

    if reaction.message.author == client.user and reaction.emoji in YREACTION_COMMANDS and yesterday == mdate:
        ctx = await client.get_context(reaction.message)
        ctx.author = user
        command_name = YREACTION_COMMANDS[reaction.emoji]

        # Find the command and invoke it with the context
        command = client.get_command(command_name)
        if command:
            await ctx.invoke(command)


async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith("Economy.py") or filename.endswith("ping.py") or filename.endswith("Accountability.py"):
            await client.load_extension(f"cogs.{filename[:-3]}")


async def main():
    async with client:
        await load()
        await client.start(bot_token)

asyncio.run(main())
