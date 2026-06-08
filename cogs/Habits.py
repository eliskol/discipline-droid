import discord
from discord.ext import commands
import os
import json
from discord.utils import get
import datetime
from table2ascii import table2ascii as t2a, PresetStyle, Merge
import matplotlib as mpl
import matplotlib.patches as patches
# mpl.use('TkAgg', force=True)
from matplotlib import pyplot as plt
import pandas as pd
from pytz import timezone
from dotenv import load_dotenv
from pathlib import Path
dotenv_path = Path('test.env')
load_dotenv(dotenv_path=dotenv_path)

print("Switched to:", mpl.get_backend())

leaderboard_channel = int(os.getenv('leaderboard_channel'))
habit_hub_channel = int(os.getenv('habit_hub_channel'))
progress_reporting_channel = int(os.getenv('progress_reporting_channel'))
main_chat_channel = int(os.getenv('main_chat_channel'))


client = commands.Bot(command_prefix='!', intents=discord.Intents.all())


class Habits(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.discipline_to_leaderboard_json_title = {"makebed": "Makebed", "alarm": "Alarm", "sunriser": "Early", "meditation": "Meditate",
                                                     "journal": "Journal", "gratitude": "Gratitude", "workout": "Workout", "coldshower": "Cold", "reading": "Read", "personal": "Goal"}
        with open('cogs/disciplines.json') as f:
            self.disciplines = json.load(f)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} is online!")

    def is_user_officer(self, ctx):
        roles = ctx.author.roles
        rolen = [role.name for role in roles]
        if 'Officer' in rolen:
            print('Officer')
            return True
        else:
            return False

    def get_member_obj_from_username(self, ctx, username):
        for member in ctx.guild.members:
            if member.name == username:
                return member

    def get_longest_current_streak_for_discipline(self, discipline_name) -> tuple[int]:
        """returns (id, streak)"""
        if discipline_name not in self.disciplines:
            print('Error in get_longest_current_streak_for_discipline')
        discipline_record = pd.read_csv(
            f"cogs/Habits Record/{discipline_name}.csv")
        row_with_max = discipline_record["Streak"].idxmax()
        user_id_with_max = discipline_record.iloc[row_with_max]["Member"]
        max_streak = discipline_record.iloc[row_with_max]["Streak"]
        return (user_id_with_max, max_streak)

    @staticmethod
    def update_all_streaks_for_discipline(discipline_name):
        discipline_record = pd.read_csv(
            f"cogs/Habits Record/{discipline_name}.csv")
        discipline_record["Streak"] = discipline_record.apply(
            Habits.current_streak, axis=1)
        discipline_record.to_csv(
            f"cogs/Habits Record/{discipline_name}.csv", index=False)

    @staticmethod
    def current_streak(row: pd.Series):
        yesterday_date_string = (datetime.datetime.today() - datetime.timedelta(days=1)).astimezone(
            tz=timezone("US/Pacific")).date().isoformat()
        if row[yesterday_date_string] == 0:
            return 0
        row = row.iloc[2:]
        return row[row.index <= yesterday_date_string][::-1].cumprod().sum()

    def get_user_eco(self, ctx):
        with open("cogs/eco.json", "r") as f:
            user_eco = json.load(f)
        if str(ctx.author.id) not in user_eco:
            user_eco[str(ctx.author.id)] = {}
            user_eco[str(ctx.author.id)]["Growth Points"] = 0

            with open("cogs/eco.json", "w") as f:
                json.dump(user_eco, f, indent=4)
        return user_eco

    async def remove_extra_roles(self, ctx):
        officer_role = discord.utils.get(ctx.guild.roles, name="Officer")
        admin_role = discord.utils.get(ctx.guild.roles, name="Admin")
        discipline_roles = [role for role in ctx.author.roles if role !=
                            officer_role and role != admin_role][1:-1]
        if len(discipline_roles) != 0:
            await ctx.author.remove_roles(*discipline_roles)

    async def input_discipline(self, discipline, ctx: commands.Context, yesterday=False):

        print(f'{ctx.author.name} inputted discipline {discipline}!')

        user_eco = self.get_user_eco(ctx)

        self.remove_extra_roles(ctx)

        discipline_record = pd.read_csv(f"cogs/Habits Record/{discipline}.csv")
        # get first column of {discipline}.csv file (user ids)
        user_ids_in_discipline_file = list(discipline_record.iloc[:, 0])
        dates_in_discipline_file = discipline_record.iloc[0, :]  # get the first row (dates)

        # reduced this to a list comp
        dates_in_file_as_strings = [date for date in dates_in_discipline_file.index.values]
        today = datetime.datetime.today().astimezone(
            tz=timezone("US/Pacific")).date()
        today_iso_date = today.isoformat()
        # using the fact that True has an int value of 1
        col_index_of_date_to_input = dates_in_file_as_strings.index(today_iso_date) - yesterday

        if str(ctx.author.id) not in user_ids_in_discipline_file:
            user_ids_in_discipline_file.append((str(ctx.author.id)))
            newr = [0] * (len(dates_in_file_as_strings)-1)
            newr.insert(0, (str(ctx.author.id)))
            newrs = pd.Series(newr, index=discipline_record.columns)
            newrst = newrs.to_frame().T
            discipline_record = pd.concat([discipline_record, newrst], ignore_index=True)
        row_index_for_user = user_ids_in_discipline_file.index(str(ctx.author.id))

        if discipline_record.iloc[row_index_for_user, col_index_of_date_to_input] == 1:
            eco_embed = discord.Embed(title=self.disciplines[discipline]["alr_done"]["title"],
                                      description=f"{self.disciplines[discipline]['alr_done']['description']} {ctx.author.mention}", color=discord.Color.red())
            channelp = self.client.get_channel(progress_reporting_channel)
            await channelp.send(embed=eco_embed)
            return

        points_discipline_is_worth = self.disciplines[discipline]["points"]
        current_points = round(user_eco[str(ctx.author.id)]["Growth Points"], 2)
        new_points = current_points + points_discipline_is_worth
        user_eco[str(ctx.author.id)]["Growth Points"] = round(new_points, 2)

        with open("cogs/eco.json", "w") as f:
            json.dump(user_eco, f, indent=4)

        gp = user_eco[str(ctx.author.id)]["Growth Points"]
        discipline_record.iloc[row_index_for_user, col_index_of_date_to_input] = 1
        streak = discipline_record.iloc[row_index_for_user, 1] + 1

        discipline_record.to_csv(f"cogs/Habits Record/{discipline}.csv", index=False)
        print('discipline csv should have been saved now')

        self.update_all_streaks_for_discipline(discipline)

        new_embed = discord.Embed(
            title="🏆Self-Improvement Club Leaders🏆",
            description="Here we commemorate SIC members for their discipline! Highest current streaks:",
            color=discord.Color.green()
        )
        for discipline in self.disciplines:
            user_id, longest_streak = self.get_longest_current_streak_for_discipline(discipline)
            new_embed.add_field(
                name = f'{self.disciplines[discipline]["emoji"]} {self.disciplines[discipline]["long_name"]}',
                value = f'<@{user_id}>: {int(longest_streak)} Days'
            )
        await self.client.embed_message.edit(embed=new_embed)

        # create confirmation embed
        eco_embed = discord.Embed(
            title=self.disciplines[discipline]["just_done"]["title"], description=f"{self.disciplines[discipline]['just_done']['description']} {ctx.author.mention}", color=discord.Color.green())
        eco_embed.add_field(name="Points Earned:",
                            value=f'{points_discipline_is_worth}', inline=False)
        eco_embed.add_field(name="Total Growth Points:",
                            value=f"{user_eco[str(ctx.author.id)]['Growth Points']}", inline=False)
        eco_embed.add_field(name=f"{self.disciplines[discipline]['long_name']} Streak:",
                            value=f"{streak} Day{'s' if streak > 1 else ''}")
        channelp = self.client.get_channel(progress_reporting_channel)
        await channelp.send(embed=eco_embed)

        r = str(ctx.author.top_role)

        # could do to change this into a json file instead of csv, for ease of use
        roles_df = pd.read_csv("cogs/SID Roles.csv")
        role_names = roles_df.iloc['SID Role'].tolist()
        role_points = roles_df.iloc['Growth Points']

        rp = role_names.index(r)
        next_role_points = role_points[rp - 1]
        next_role_name = role_names[rp - 1]
        if gp >= next_role_points:
            member = ctx.author
            role = get(member.guild.roles, name=f'{next_role_name}')
            await member.add_roles(role)
            channelm = self.client.get_channel(main_chat_channel)
            await channelm.send(f"Congratulations {ctx.author.mention}! You Have Exemplified Discipline and Have Leveled Up to {next_role_name}")

    @commands.command(aliases=["hr"], pass_context=True)
    async def hreload(self, ctx, *args: str):
        if ctx.author.id != 292088878767144964:
            return
        await self.client.unload_extension("cogs.Habits")
        await ctx.send("Unloaded cogs.Habits.")
        await self.client.load_extension("cogs.Habits")
        await ctx.send("Loaded cogs.Habits.")

    @commands.command(aliases=["h"], pass_context=True)
    async def habits(self, context: commands.Context, *args: str):
        if context.channel.id != progress_reporting_channel:
            print(
                f"{context.author} tried to use a habit command outside the proper channel!")
            return

        arg = args[0].lower()

        detected_discipline = [discipline for discipline in self.disciplines if (
            arg in self.disciplines[discipline]["aliases"] or arg == discipline)]

        if detected_discipline != []:
            assert len(detected_discipline) == 1
            print(f"detected {detected_discipline[0]} from {context.author}")
            await self.input_discipline(detected_discipline[0], context)
            return

        detected_yesterday_discipline = [discipline for discipline in self.disciplines if (
            arg in self.disciplines[discipline]["yesterday_aliases"] or arg == "yesterday" + discipline)]
        if detected_yesterday_discipline != []:
            assert len(detected_yesterday_discipline) == 1
            print(
                f"detected {detected_yesterday_discipline[0]} from {context.author}")
            await self.input_discipline(detected_yesterday_discipline[0], context, yesterday=True)
            return

        elif args[0].endswith("week"):
            detected_week_command = [discipline for discipline in self.disciplines if (
                arg.removesuffix("week") in self.disciplines[discipline]["aliases"] or arg.removesuffix("week") == discipline)]
            if detected_week_command != []:
                assert len(detected_week_command) == 1
                print(
                    f"detected {detected_week_command[0]}week from {context.author}")
                await self.disciplineweek(detected_week_command[0], context)
                return

        elif args[0].endswith("month"):
            detected_month_command = [discipline for discipline in self.disciplines if (
                arg.removesuffix("month") in self.disciplines[discipline]["aliases"] or arg.removesuffix("month") == discipline)]
            if detected_month_command != []:
                assert len(detected_month_command) == 1
                print(
                    f"detected {detected_month_command[0]}month from {context.author}")
                await self.disciplinemonth(detected_month_command[0], context)
                return

    @commands.command(aliases=["Alllastmonth"], pass_context=True)
    async def alllastmonth(self, ctx):
        if self.generate_discipline_record_for_member(ctx.author, True):
            await ctx.send(file=discord.File('testfig2.png'))
        else:
            await ctx.send(f"{ctx.author}, you don't have any discipline records for last month!")

    @commands.command(aliases=["Ranks",], pass_context=True)
    async def ranks(self, ctx):
        rolesf = pd.read_csv("cogs/SID Roles.csv")
        rolesf = pd.DataFrame(rolesf)
        output = t2a(
            header=["Rank", "Points"],
            body=list(list(row) for row in rolesf.to_numpy()),
            style=PresetStyle.thin_compact
        )
        await ctx.send(f"```\n{output}\n```")

    # perhaps use helper functions for this
    async def disciplineweek(self, discipline, ctx):
        # await ctx.send("reading record now")
        record = pd.read_csv(f"cogs/Habits Record/{discipline}.csv")
        names = list(record.iloc[:, 0])
        datef = record.iloc[0, :]
        # await ctx.send("just read the record")

        dateff = [date for date in datef.index.values]
        # await ctx.send("just made date array")
        today = datetime.datetime.today().astimezone(
            tz=timezone("US/Pacific")).date()
        iso_date = today.isoformat()
        weekday = today.isoweekday()
        today_index = dateff.index(iso_date)
        if weekday == 7:
            beginning_index = today_index
        else:
            beginning_index = today_index - weekday

        if str(ctx.author.id) not in names:
            names.append((str(ctx.author.id)))
            new_row = [0] * (len(dateff) - 1)
            new_row.insert(0, (str(ctx.author.id)))
            new_row_series = pd.Series(new_row, index=record.columns)
            new_row_series_transpose = new_row_series.to_frame().T
            record = pd.concat(
                [record, new_row_series_transpose], ignore_index=True)
            record.to_csv(f"cogs/Habits Record/{discipline}.csv", index=False)

        name_index = names.index(str(ctx.author.id))

        # await ctx.send("making week_record and checks rn")
        week_record = record.iloc[name_index, beginning_index:today_index + 1]
        week_record_checks = ["\u2713" if i == 1 else " " for i in week_record]

        weekdays = ["Sunday", "Monday", "Tuesday",
                    "Wednesday", "Thursday", "Friday", "Saturday"]

        weekday_discipline_pairing_list = [
            [weekdays[i], week_record_checks[i]] for i in range(len(week_record_checks))]
        # await ctx.send("just made pairing list")
        output = t2a(
            header=[
                f"This Week's {self.disciplines[discipline]['long_name']}", Merge.LEFT],
            body=weekday_discipline_pairing_list,
            style=PresetStyle.double_thin_box
        )
        # await ctx.send("just made table")
        await ctx.send(f"```\n{output}\n```")

    # use helper functions (shorten this function....)
    async def disciplinemonth(self, discipline, ctx):
        record = pd.read_csv(f"cogs/Habits Record/{discipline}.csv")
        names = list(record.iloc[:, 0])
        datef = record.iloc[0, :]
        dateff = [date for date in datef.index.values]

        today = datetime.datetime.today().astimezone(
            tz=timezone("US/Pacific")).date()
        iso_date = today.isoformat()
        month_days = list(
            range(1, int(iso_date.partition('-')[2].partition('-')[2])+1))
        today_index = dateff.index(iso_date)
        beginning_index = today_index - len(month_days) + 1

        if str(ctx.author.id) not in names:
            names.append((str(ctx.author.id)))
            new_row = [0] * (len(dateff) - 1)
            new_row.insert(0, (str(ctx.author.id)))
            new_row_series = pd.Series(new_row, index=record.columns)
            new_row_series_transpose = new_row_series.to_frame().T
            record = pd.concat(
                [record, new_row_series_transpose], ignore_index=True)
            record.to_csv(f"cogs/Habits Record/{discipline}.csv", index=False)

        name_index = names.index(str(ctx.author.id))

        month_record = record.iloc[name_index,
                                   beginning_index: today_index + 1]
        month_record_checks = ["\u2713" if i ==
                               1 else " " for i in month_record]

        month_record_formatted = []
        i = 1
        if len(month_record_checks) > 7:
            weeks_so_far = int(len(month_record_checks)/7)
            days_so_far_this_week = len(month_record_checks) % 7
            for i in list(range(1, weeks_so_far+1)):
                month_record_formatted.append(
                    month_record_checks[(i-1)*7:(i*7)])
            if days_so_far_this_week != 0:
                last = []
                for i in list(range(1, 8)):
                    if i <= days_so_far_this_week:
                        last.append(month_record_checks[weeks_so_far*7 + i-1])
                    else:
                        last.append(' ')
                month_record_formatted.append(last)
        elif len(month_record_formatted) == 7:
            month_record_formatted = list()
            i = 1
            month_record_formatted.append(month_record_checks[0:7])
        else:
            last = []
            days_so_far_this_week = len(month_record_checks) % 7

            for i in list(range(0, 7)):
                if i < days_so_far_this_week:
                    last.append(month_record_checks[i])
            month_record_formatted.append(last)

        month_day_numbers = list(range(1, 32))
        month_day_numbers_so_far = month_day_numbers[0:len(
            month_record_checks)]

        if len(month_day_numbers_so_far) > 7:
            weeks_so_far = int(len(month_day_numbers_so_far)/7)
            days_so_far_this_week = len(month_day_numbers_so_far) % 7
            month_day_numbers_so_far = list()
            i = 1
            for i in list(range(1, weeks_so_far+1)):
                month_day_numbers_so_far.append(
                    list(range((i-1)*7+1, (i*7)+1)))
            if days_so_far_this_week != 0:
                last = []
                i = 2
                for i in list(range(1, 8)):
                    if i <= days_so_far_this_week:
                        last.append(weeks_so_far*7 + i)
                    else:
                        last.append(' ')
                month_day_numbers_so_far.append(last)
        elif len(month_day_numbers_so_far) == 7:
            month_day_numbers_so_far = list()
            i = 1
            month_day_numbers_so_far.append(list(range((i-1)*7+1, (i*7)+1)))
        else:
            last = []
            days_so_far_this_week = len(month_day_numbers_so_far) % 7
            month_day_numbers_so_far = list()
            for i in list(range(1, 8)):
                if i <= days_so_far_this_week:
                    last.append(i)
            month_day_numbers_so_far.append(last)

        fullm = []

        for i in list(range(0, len(month_record_formatted))):
            fullm.append(month_day_numbers_so_far[i])
            fullm.append(month_record_formatted[i])

        header = [
            f"This Month's {self.disciplines[discipline]['long_name']}"]
        if len(month_record) < 7 and len(month_record) > 1:
            for i in list(range(1, len(month_record))):
                header.append(Merge.LEFT)
        elif len(month_record) > 7:
            for i in list(range(1, 7)):
                header.append(Merge.LEFT)

        output = t2a(
            header=header,
            body=fullm,
            style=PresetStyle.double_thin_box
        )
        await ctx.send(f"```\n{output}\n```")

    @commands.command(pass_context=True)
    async def today(self, ctx: commands.Context):
        user_id = ctx.author.id
        today_string = datetime.datetime.today().astimezone(
            tz=timezone("US/Pacific")).date().isoformat()
        today_results = {}
        for discipline in self.disciplines:
            today_result = pd.read_csv(f"cogs/Habits Record/{discipline}.csv").query(
                f'Member == "{user_id}"').filter(like=today_string, axis=1).iloc[0, 0]
            today_results[discipline] = today_result
        disciplines_row_1  = [discipline.capitalize()
                             for discipline in list(self.disciplines.keys())[::2]]
        disciplines_row_2 = [discipline.capitalize()
                             for discipline in list(self.disciplines.keys())[1::2]]
        table_body = []
        for i in range(len(disciplines_row_1)):
            row_1_indicator = "\u2713" if today_results[disciplines_row_1[i].lower(
            )] == 1 else " "
            row_2_indicator = "\u2713" if today_results[disciplines_row_2[i].lower(
            )] == 1 else " "
            table_body.append(
                [disciplines_row_1[i], row_1_indicator, disciplines_row_2[i], row_2_indicator])
        title = "Today's Disciplines"
        output = t2a(
            header=[title, Merge.LEFT, Merge.LEFT, Merge.LEFT],
            body=table_body,
            style=PresetStyle.double_thin_box
        )
        await ctx.send(f"```\n{output}\n```")

    @commands.command(aliases=["Allmonth"], pass_context=True)
    async def allmonth(self, ctx):
        if self.generate_discipline_record_for_member(ctx.author):
            await ctx.send(file=discord.File('testfig2.png'))
        else:
            await ctx.send(f"{ctx.author}, you don't have any discipline records for this month!")

    @commands.command(aliases=["Show"], pass_context=True)
    async def show(self, ctx, *usernames):
        if not self.is_user_officer(ctx):
            await ctx.send('You must have the officer role to use this command')
            return

        # await ctx.send('Getting member objects now..')
        members = [self.get_member_obj_from_username(
            ctx, username) for username in usernames]

        # await ctx.send('Got member objects, now entering loop..')

        # await ctx.send(f'Members are: {members=}')

        for member in members:
            if self.generate_discipline_record_for_member(member):
                await ctx.send(file=discord.File('testfig2.png'))
            else:
                await ctx.send(f"{ctx.author}, you do not have any discipline records for last month!")

    def generate_discipline_record_for_member(self, member, last_mo=False):
        user_id = member.id
        this_month_time = datetime.datetime.today().astimezone(
            tz=timezone("US/Pacific")).date() if last_mo is False else (datetime.datetime.today().astimezone(
                tz=timezone("US/Pacific")).replace(day=1) - datetime.timedelta(days=1)).date()
        date_prefix = this_month_time.isoformat()[:-3]
        this_month_disciplines = {}
        for discipline in self.disciplines:
            # make this a helper function to deal with missing members?
            dataframe = pd.read_csv(
                f"cogs/Habits Record/{discipline}.csv").query(f'Member == "{user_id}"').filter(like=date_prefix, axis=1)
            this_month_disciplines[discipline] = list(dataframe.iloc[0])
            if dataframe.shape[0] == 0:
                return False

        # logic to actually make the figure

        days_in_month = dataframe.shape[1]

        fig, ax = plt.subplots(figsize=(days_in_month, 10), dpi=150)
        rows = 10
        cols = days_in_month

        ax.set_ylim(-1, rows + 1)
        ax.set_xlim(0, cols + .5)

        discipline_dataframe = pd.DataFrame.from_dict(this_month_disciplines).T
        plt.cla()
        for col in range(cols):
            for row in range(rows):
                if int(discipline_dataframe.iloc[row, col]) == 1:
                    ax.text(x=col, y=row, s='\u2713',
                            va='center', ha='center', fontsize=24)

        for col in range(cols):
            ax.text(col, 9.75, col+1, weight='bold', ha='center', fontsize=20)
            ax.plot([col - .5, col - .5], [-0.5, rows+0.5],
                    ls='solid', lw='1', c='grey')
            if col % 10 == 0:
                ax.plot([col - .5, col - .5], [-0.5, rows+0.5],
                        ls='solid', lw='2.4', c='black')

        discf = ["Makebed", "Earlybird", "Alarm", "Reading", "Gratitude",
                 "Journal", "Meditate", "Workout", "Coldshower", "Personal"]

        bb = -4.25
        for row in range(rows):
            ax.text(x=-0.75, y=row, s=discf[9-row], va='center',
                    ha='right', fontsize=20, weight='bold')
            ax.plot([bb, cols-.5], [row - .5, row - .5],
                    ls='solid', lw='2.4', c='black')

        ax.text(x=-0.65, y=9.90, s="Disciplines\\Days", va='center',
                ha='right', fontsize=17, weight='bold')
        ax.plot([bb, cols-.5], [9.5, 9.5], ls='solid', lw='2.4', c='black')
        ax.plot([bb, cols-.5], [10.5, 10.5], ls='solid', lw='3', c='black')
        ax.plot([bb, cols-.5], [-.5, -.5], ls='solid', lw='3', c='black')
        ax.plot([bb, bb], [-0.5, rows+0.5], ls='solid', lw='3', c='black')
        ax.plot([cols - .5, cols - .5], [-0.5, rows+0.5],
                ls='solid', lw='3', c='black')

        ax.axis('off')

        this_month_name = this_month_time.strftime("%B")

        ax.set_title(
            f"{member}'s Discipline Record for {this_month_name} {this_month_time.year}",
            loc='left',
            fontsize=30,
            weight='bold'
        )

        fig.savefig('testfig2.png', bbox_inches='tight', pad_inches=1)
        return True

    @commands.command(pass_context=True)
    async def testleaderboard(self, ctx):
        for discipline in self.disciplines:
            self.update_all_streaks_for_discipline(discipline)
            await ctx.send(f"longest for {discipline} is {self.get_longest_current_streak_for_discipline(discipline)}")

# make a monthly discipline challenge handler

async def setup(client):
    await client.add_cog(Habits(client))
