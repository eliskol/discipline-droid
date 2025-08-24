# Packages used
import discord
from discord.ext import commands, tasks
import os
import asyncio
from datetime import datetime, timedelta
from datetime import date
import datetime
import pandas as pd

from dotenv import load_dotenv
from pathlib import Path

dotenv_path = Path('test.env')
load_dotenv(dotenv_path=dotenv_path)

bot_token = os.getenv('bot_token')
leaderboard_channel = int(os.getenv('leaderboard_channel'))
habit_hub_channel = int(os.getenv('habit_hub_channel'))


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
    "🌟": "yesterdaypersonal"  # Trigger the "vice" command
}


@client.event
async def on_ready():
    await send_leaderboard_message()
    await send_startup_message()  # Send a message at startup
    daily_message.start()  # Start the daily message loop
    print("Bot is connected and ready!")


async def send_leaderboard_message():
    channell = client.get_channel(leaderboard_channel)
    if channell:
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
    client.embed_message = await channell.send(embed=embed)
{
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

# Function to send the message at startup


async def send_startup_message():
    channelh = client.get_channel(habit_hub_channel)
    if channelh:
        todayr = (datetime.datetime.utcnow() -
                  datetime.timedelta(hours=8)).date()
        today = todayr.isoformat()
        disc = ['coldshower', 'gratitude', 'journal', 'makebed', 'meditation',
                'personal', 'reading', 'sunlight', 'sunriser', 'workout']
        for a in disc:
            record = pd.read_csv(f"cogs/Habits Record/{a}.csv")
            if today != record.columns[-1]:
                record[today] = 0
                record.to_csv(f"cogs/Habits Record/{a}.csv", index=False)

        embed = discord.Embed(
            title="⭐️ Daily Discipline Tracker ⭐️",
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

# Task to send a message every day at 12:01 AM


@tasks.loop(hours=24)
async def daily_message():
    now = datetime.datetime.now()
    midnight = now.replace(hour=8, minute=1, second=0, microsecond=0)
    if now > midnight:
        midnight += timedelta(days=1)
    delay = (midnight - now).total_seconds()
    print(delay)

    await asyncio.sleep(delay)  # Wait until 12:01 AM
    channelh = client.get_channel(habit_hub_channel)
    if channelh:
        todayr = (datetime.datetime.utcnow() -
                  datetime.timedelta(hours=8)).date()
        today = todayr.isoformat()
        disc = ['coldshower', 'gratitude', 'journal', 'makebed', 'meditation',
                'personal', 'reading', 'sunlight', 'sunriser', 'workout']
        for a in disc:
            record = pd.read_csv(f"cogs/Habits Record/{a}.csv")
            if today != record.columns[-1]:
                record[today] = 0
                record.to_csv(f"cogs/Habits Record/{a}.csv", index=False)
        embed = discord.Embed(
            title="⭐️ Daily Discipline Tracker ⭐️",
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


@daily_message.before_loop
async def before_daily_message():
    await client.wait_until_ready()

# Handle reactions to trigger commands


@client.event
async def on_reaction_add(reaction, user):
    if user.bot:  # Ignore bot reactions
        return

    # guild = reaction.message.guild
    # print(guild)
    # member = guild.get_member(user.id)
    # print(member)
    # roler = [role.name for role in member.roles[1:-1]]

    todayr = (datetime.datetime.utcnow()-datetime.timedelta(hours=8)).date()
    today = todayr.isoformat()
    yesterdayr = (datetime.datetime.utcnow() -
                  datetime.timedelta(hours=32)).date()
    yesterday = yesterdayr.isoformat()
    mdate = (reaction.message.created_at-datetime.timedelta(hours=8)).date()
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
        if filename.endswith("Economy.py") or filename.endswith("ping.py"):
            await client.load_extension(f"cogs.{filename[:-3]}")


async def main():
    async with client:
        await load()
        await client.start(bot_token)

asyncio.run(main())
