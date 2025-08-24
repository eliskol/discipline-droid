import discord
from discord.ext import commands
import os
import json
import random
import numpy as np
from discord.utils import get
from datetime import date
import datetime
from table2ascii import table2ascii as t2a, PresetStyle, Merge
import matplotlib as mpl
import matplotlib.patches as patches
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from pathlib import Path
dotenv_path = Path('test.env')
load_dotenv(dotenv_path=dotenv_path)

mpl.use('TkAgg', force=True)
print("Switched to:", mpl.get_backend())

leaderboard_channel = int(os.getenv('leaderboard_channel'))
habit_hub_channel = int(os.getenv('habit_hub_channel'))
progress_reporting_channel = int(os.getenv('progress_reporting_channel'))
main_chat_channel = int(os.getenv('main_chat_channel'))


client = commands.Bot(command_prefix='!', intents=discord.Intents.all())


class Economy(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.discipline_values = {"makebed": 0.2, "sunlight": 0.25, "sunriser": 0.5, "meditation": 0.5,
                                  "journal": 1, "gratitude": 0.3, "workout": 1, "coldshower": 0.5, "reading": 0.5, "personal": 1}
        with open('cogs/discipline_embed_info.json') as f:
            self.discipline_embed_info = json.load(f)
        self.discipline_to_leaderboard_json_title = {"makebed": "Makebed", "sunlight": "Sunlight", "sunriser": "Early", "meditation": "Meditate",
                                                     "journal": "Journal", "gratitude": "Gratitude", "workout": "Workout", "coldshower": "Cold", "reading": "Read", "personal": "Goal"}

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

    def update_leaderboard_for_discipline(self, ctx, discipline_name):
        pass

    def get_user_eco(self, ctx):
        with open("cogs/eco.json", "r") as f:
            user_eco = json.load(f)
        if str(ctx.author.id) not in user_eco:
            user_eco[str(ctx.author.id)] = {}
            user_eco[str(ctx.author.id)]["Growth Points"] = 0

            with open("cogs/eco.json", "w") as f:
                json.dump(user_eco, f, indent=4)
        return user_eco

    async def input_discipline(self, discipline, ctx, yesterday=False):

        print(f'{ctx.author.name} inputted discipline {discipline}!')

        user_eco = self.get_user_eco(ctx)

        rolek1 = discord.utils.get(ctx.guild.roles, name="Officer")
        rolek2 = discord.utils.get(ctx.guild.roles, name="Admin")
        roleo = [role for role in ctx.author.roles if role !=
                 rolek1 and role != rolek2][1:-1]
        if len(roleo) != 0:
            await ctx.author.remove_roles(*roleo)

        amount = self.discipline_values[discipline]
        cur = round(user_eco[str(ctx.author.id)]["Growth Points"], 2)
        new = cur + amount
        user_eco[str(ctx.author.id)]["Growth Points"] = round(new, 2)

        record = pd.read_csv(f"cogs/Habits Record/{discipline}.csv")
        # get first column of {discipline}.csv file (user ids)
        recordn = list(record.iloc[:, 0])
        datef = record.iloc[0, :]  # get the first row (dates)

        # reduced this to a list comp
        dateff = [date for date in datef.index.values]
        today = (datetime.datetime.utcnow()-datetime.timedelta(hours=8)).date()
        iso_date = today.isoformat()
        # using the fact that True has an int value of 1
        tl = dateff.index(iso_date) - yesterday

        if str(ctx.author.id) not in recordn:
            recordn.append((str(ctx.author.id)))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, (str(ctx.author.id)))
            newrs = pd.Series(newr, index=record.columns)
            newrst = newrs.to_frame().T
            record = pd.concat([record, newrst], ignore_index=True)
        nl = recordn.index(str(ctx.author.id))

        if record.iloc[nl, tl] == 1:
            eco_embed = discord.Embed(title=self.discipline_embed_info[discipline]["alr_done"]["title"],
                                      description=f"{self.discipline_embed_info[discipline]['alr_done']['description']} {ctx.author.mention}", color=discord.Color.red())
            channelp = self.client.get_channel(progress_reporting_channel)
            await channelp.send(embed=eco_embed)
            return
        with open("cogs/eco.json", "w") as f:
            json.dump(user_eco, f, indent=4)

        gp = user_eco[str(ctx.author.id)]["Growth Points"]
        record.iloc[nl, tl] = 1
        idrec = record.iloc[nl, 2:tl+1]
        idrec0 = idrec == 0
        idrec0 = idrec0.reset_index(drop=True)
        sorl = idrec0[idrec0].index.max()
        streak = len(idrec0.iloc[sorl+1:])
        lead = pd.read_csv("cogs/Habits Record/leaderboard.csv")
        col_index = list(lead.columns).index(
            self.discipline_to_leaderboard_json_title[discipline])
        print(f'col_index is {col_index}')
        leadhp = lead.iloc[0:5, col_index]
        leadhn = lead.iloc[5:, col_index]
        leadtp = lead.iloc[0:5, 2]
        leadtn = lead.iloc[5:, 2]
        leadmp = lead.iloc[0:5, 3]
        leadmn = lead.iloc[5:, 3]
        id = int(ctx.author.id)
        if streak > min(leadhp):
            if id in leadhn.values:
                leadhn.index = list(range(5))
                ind = leadhn.index[leadhn == id][0]
                leadhp[ind] = streak
            else:
                leadhp[5] = streak
                leadhn.index = list(range(5))
                leadhn[5] = str(ctx.author.id)
            leadhp = leadhp.sort_values(ascending=False).iloc[0:5]
            ind = leadhp.index
            leadhn = leadhn.reindex(ind)
            leadhn.index = list(range(5, 10))
            lead.iloc[:5, col_index] = leadhp
            lead.iloc[5:, col_index] = leadhn
            ids = []
            score = []
            for a in list(range(1, 13)):
                for b in lead.iloc[5:, a]:
                    ids.append(b)
            idsf = ["<@" + str(a) + ">" for a in ids]
            for a in list(range(1, 13)):
                print(1)
                for b in lead.iloc[:5, a]:
                    score.append(b)

            new_embed = discord.Embed(
                title="🏆Self-Improvement Club Leaders🏆",
                description="Here we commemorate SIC members for their discipline!",
                color=discord.Color.green()
            )
            new_embed.add_field(name="Total Growth Points",
                                value=f"🥇 {idsf[0]} | {score[0]} Points\n🥈 {idsf[1]} | {score[1]} Points\n🥉 {idsf[2]} | {score[2]} Points\n4. {idsf[3]} | {score[3]} Points\n5. {idsf[4]} | {score[4]} Points", inline=True)
            new_embed.add_field(name="Monthly Growth Points",
                                value=f"🥇 {idsf[5]} | {score[5]} Points\n🥈 {idsf[6]} | {score[6]} Points\n🥉 {idsf[7]} | {score[7]} Points\n4. {idsf[8]} | {score[8]} Points\n5. {idsf[9]} | {score[9]} Points", inline=True)
            new_embed.add_field(
                name="🛏️ Make Bed", value=f"🥇 {idsf[10]} | {score[10]} Days\n🥈 {idsf[11]} | {score[11]} Days\n🥉 {idsf[12]} | {score[12]} Days\n4. {idsf[13]} | {score[13]} Days\n5. {idsf[14]} | {score[14]} Days", inline=True)
            new_embed.add_field(
                name="😎 Sunlight", value=f"🥇 {idsf[15]} | {score[15]} Days\n🥈 {idsf[16]} | {score[16]} Days\n🥉 {idsf[17]} | {score[17]} Days\n4. {idsf[18]} | {score[18]} Days\n5. {idsf[19]} | {score[19]} Days", inline=True)
            new_embed.add_field(
                name="🌅 Early Bird", value=f"🥇 {idsf[20]} | {score[20]} Days\n🥈 {idsf[21]} | {score[21]} Days\n🥉 {idsf[22]} | {score[22]} Days\n4. {idsf[23]} | {score[23]} Days\n5. {idsf[24]} | {score[24]} Days", inline=True)
            new_embed.add_field(
                name="🧘 Meditation", value=f"🥇 {idsf[25]} | {score[25]} Days\n🥈 {idsf[26]} | {score[26]} Days\n🥉 {idsf[27]} | {score[27]} Days\n4. {idsf[28]} | {score[28]} Days\n5. {idsf[29]} | {score[29]} Days", inline=True)
            new_embed.add_field(
                name="📝 Journaling", value=f"🥇 {idsf[30]} | {score[30]} Days\n🥈 {idsf[31]} | {score[31]} Days\n🥉 {idsf[32]} | {score[32]} Days\n4. {idsf[33]} | {score[33]} Days\n5. {idsf[34]} | {score[34]} Days", inline=True)
            new_embed.add_field(
                name="🙏 Gratitude", value=f"🥇 {idsf[35]} | {score[35]} Days\n🥈 {idsf[36]} | {score[36]} Days\n🥉 {idsf[37]} | {score[37]} Days\n4. {idsf[38]} | {score[38]} Days\n5. {idsf[39]} | {score[39]} Days", inline=True)
            new_embed.add_field(
                name="🏋 Workouts", value=f"🥇 {idsf[40]} | {score[40]} Days\n🥈 {idsf[41]} | {score[41]} Days\n🥉 {idsf[42]} | {score[42]} Days\n4. {idsf[43]} | {score[43]} Days\n5. {idsf[44]} | {score[44]} Days", inline=True)
            new_embed.add_field(
                name="🚿 Cold Showers", value=f"🥇 {idsf[45]} | {score[45]} Days\n🥈 {idsf[46]} | {score[46]} Days\n🥉 {idsf[47]} | {score[47]} Days\n4. {idsf[48]} | {score[48]} Days\n5. {idsf[49]} | {score[49]} Days", inline=True)
            new_embed.add_field(
                name="📖 Reading", value=f"🥇 {idsf[50]} | {score[50]} Days\n🥈 {idsf[51]} | {score[51]} Days\n🥉 {idsf[52]} | {score[52]} Days\n4. {idsf[53]} | {score[53]} Days\n5. {idsf[54]} | {score[54]} Days", inline=True)
            new_embed.add_field(
                name="🌟 Personal Goals", value=f"🥇 {idsf[55]} | {score[55]} Days\n🥈 {idsf[56]} | {score[56]} Days\n🥉 {idsf[57]} | {score[57]} Days\n4. {idsf[58]} | {score[58]} Days\n5. {idsf[59]} | {score[59]} Days", inline=True)
            await self.client.embed_message.edit(embed=new_embed)
            lead.to_csv("cogs/Habits Record/leaderboard.csv", index=False)
        record.to_csv(f"cogs/Habits Record/{discipline}.csv", index=False)
        print('discipline csv should have been saved now')

        gp = user_eco[str(ctx.author.id)]["Growth Points"]

        eco_embed = discord.Embed(
            title=self.discipline_embed_info[discipline]["just_done"]["title"], description=f"{self.discipline_embed_info[discipline]['just_done']['description']} {ctx.author.mention}", color=discord.Color.green())
        eco_embed.add_field(name="Points Earned:",
                            value=f'{amount}', inline=False)
        eco_embed.add_field(name="Total Growth Points:",
                            value=f"{user_eco[str(ctx.author.id)]['Growth Points']}", inline=False)
        eco_embed.add_field(name=f"{self.discipline_embed_info[discipline]['long_name']} Streak:",
                            value=f"{streak} Day{'s' if streak > 1 else ''}")
        channelp = self.client.get_channel(progress_reporting_channel)
        await channelp.send(embed=eco_embed)
        print("embed should have been sent")

        r = str(ctx.author.top_role)

        rolesf = pd.read_csv("cogs/SID Roles.csv")
        # rolesf = rolesf.tolist()
        rolesfn = rolesf.iloc[:, 0]
        rolesfp = rolesf.iloc[:, 1]
        rolesfn = rolesfn.tolist()

        rp = rolesfn.index(r)
        next_rolep = rolesfp[rp-1]
        next_rolen = rolesfn[(rp-1)]
        if gp >= next_rolep:
            # join_role = discord.utils.get(ctx.guild.roles, name = f'{next_rolen}')
            # await ctx.add_roles(join_role)
            member = ctx.author
            role = get(member.guild.roles, name=f'{next_rolen}')
            await member.add_roles(role)
            # role = discord.utils.get(ctx.guild.roles, name=f'{next_rolen}')
            channelm = self.client.get_channel(main_chat_channel)
            await channelm.send(f"Congratulations {ctx.author.mention}! You Have Exemplified Discipline and Have Leveled Up to {next_rolen}")

    @commands.command(aliases=["Vice"], pass_context=True)
    async def ice(self, ctx):
        with open("cogs/eco.json", "r") as f:
            user_eco = json.load(f)

        if str(ctx.author.id) not in user_eco:

            user_eco[str(ctx.author.id)] = {}
            user_eco[str(ctx.author.id)]["Growth Points"] = 0

            with open("cogs/eco.json", "w") as f:
                json.dump(user_eco, f, indent=4)

        r = str(ctx.author.top_role)

        print(r)

        rolesf = pd.read_csv("cogs/SID Roles.csv")
        # rolesf = rolesf.tolist()
        rolesfn = rolesf.iloc[:, 0]
        rolesfp = rolesf.iloc[:, 1]
        rolesfn = rolesfn.tolist()

        rp = rolesfn.index(r)
        cur_rolep = rolesfp[rp]
        next_rolep = rolesfp[rp+1]
        next_rolen = rolesfn[(rp+1)]
        print(r)
        print(next_rolen)
        print(next_rolep)

        cur = round(user_eco[str(ctx.author.id)]["Growth Points"], 2)
        amount = next_rolep - cur_rolep
        print(amount)
        new = cur + amount
        amount = -amount
        user_eco[str(ctx.author.id)]["Growth Points"] = round(new, 2)

        with open("cogs/eco.json", "w") as f:
            json.dump(user_eco, f, indent=4)

        gp = user_eco[str(ctx.author.id)]["Growth Points"]
        eco_embed = discord.Embed(
            title="Vice Recorded", description=f"Remember, Failure Isn't Falling Down. Failure Is Not Getting Back Up After Such A Fall, {ctx.author.mention}", color=discord.Color.red())
        eco_embed.add_field(name="Points Deducted:",
                            value=f'{amount}', inline=False)
        eco_embed.add_field(name="Total Growth Points:",
                            value=f"{user_eco[str(ctx.author.id)]['Growth Points']}")
        channelp = self.client.get_channel(progress_reporting_channel)
        print(type(channelp))
        await channelp.send(embed=eco_embed)

        if gp == gp:
            # join_role = discord.utils.get(ctx.guild.roles, name = f'{next_rolen}')
            # await ctx.add_roles(join_role)
            print(gp)
            member = ctx.author
            role = get(member.guild.roles, name=f'{r}')
            print(role)
            await member.remove_roles(role)
            # role = discord.utils.get(ctx.guild.roles, name=f'{next_rolen}')
            channelm = self.client.get_channel(main_chat_channel)
            print(channelm)
            await channelm.send(f"{ctx.author.mention}! Due To Your Participation In Your Vice, You Have Been Demoted From {r} to {next_rolen}")

    @commands.command(aliases=["Makebed", "Madebed", "madebed", "Bed", "bed"], pass_context=True)
    async def makebed(self, context):
        await self.input_discipline("makebed", context)

    @commands.command(aliases=["Sunlight", "Sun", "sun", "Morninglight", "morninglight", 'Morningsun', 'morningsun', 'light', 'Light'], pass_context=True)
    async def sunlight(self, ctx):
        await self.input_discipline("sunlight", ctx)

    @commands.command(aliases=["Sunriser", "earlybird", "Earlybird", "firstwatch", "Firstwatch", "6am", "6AM", "6a.m.", "6A.M.", "early", "Early"], pass_context=True)
    async def sunriser(self, ctx):
        await self.input_discipline("sunriser", ctx)

    @commands.command(aliases=["Meditation", "Mindfulness", "mindfulness", "Peace", "peace", "Namaste", "namaste", "meditate", "Meditate"], pass_context=True)
    async def meditation(self, ctx):
        await self.input_discipline("meditation", ctx)

    @commands.command(aliases=["Journal", "Diary", "diary", "Log", "log"], pass_context=True)
    async def journal(self, ctx):
        await self.input_discipline("journal", ctx)

    @commands.command(aliases=["Gratitude", "Grateful", "grateful", "Gratefulness", "gratefulness", "Thankful", "thankful"], pass_context=True)
    async def gratitude(self, ctx):
        await self.input_discipline("gratitude", ctx)

    @commands.command(aliases=["Workout", "Gym", "gym", "Exercise", "exercise", "Gains", "gains"], pass_context=True)
    async def workout(self, ctx):
        await self.input_discipline("workout", ctx)

    @commands.command(aliases=["Coldshower", "Cold", "cold", 'Coldexposure', 'coldexposure'], pass_context=True)
    async def coldshower(self, ctx):
        await self.input_discipline("coldshower", ctx)

    @commands.command(aliases=["Reading", "Read", "read", "Book", "book"], pass_context=True)
    async def reading(self, ctx):
        await self.input_discipline("reading", ctx)

    @commands.command(aliases=["Personal", "goal", "Goal"], pass_context=True)
    async def personal(self, ctx):
        await self.input_discipline("personal", ctx)

    @commands.command(aliases=["yesterdayRead", "yesterdayread", "yesterdayBook", "yesterdaybook"], pass_context=True)
    async def yesterdayreading(self, ctx):
        await self.input_discipline("reading", ctx, True)

    @commands.command(aliases=["yesterdayWorkout", "yesterdayGym", "yesterdaygym", "yesterdayExercise", "yesterdayexercise", "yesterdayGains", "yesterdaygains"], pass_context=True)
    async def yesterdayworkout(self, ctx):
        await self.input_discipline("workout", ctx, True)

    @commands.command(aliases=["yesterdayMeditation", "yesterdayMindfulness", "yesterdaymindfulness", "yesterdayPeace", "yesterdaypeace", "yesterdayNamaste", "yesterdaynamaste", "yesterdaymeditate", "yesterdayMeditate"], pass_context=True)
    async def yesterdaymeditation(self, ctx):
        await self.input_discipline("meditation", ctx, True)

    @commands.command(aliases=["yesterdayJournal", "yesterdayDiary", "yesterdaydiary", "yesterdayLog", "yesterdaylog"], pass_context=True)
    async def yesterdayjournal(self, ctx):
        await self.input_discipline("journal", ctx, True)

    @commands.command(aliases=["yesterdayGratitude", "yesterdayGrateful", "yesterdaygrateful", "yesterdayGratefulness", "yesterdaygratefulness", "yesterdayThankful", "yesterdaythankful"], pass_context=True)
    async def yesterdaygratitude(self, ctx):
        await self.input_discipline("gratitude", ctx, True)

    @commands.command(aliases=["yesterdayMakebed", "yesterdayMadebed", "yesterdaymadebed", "yesterdayBed", "yesterdaybed"], pass_context=True)
    async def yesterdaymakebed(self, ctx):
        await self.input_discipline("makebed", ctx, True)

    @commands.command(aliases=["yesterdayPersonal", "yesterdaygoal", "yesterdayGoal"], pass_context=True)
    async def yesterdaypersonal(self, ctx):
        await self.input_discipline("personal", ctx, True)

    @commands.command(aliases=["yesterdaySunriser", "yesterdayearlybird", "yesterdayEarlybird", "yesterdayfirstwatch", "yesterdayFirstwatch", "yesterday6am", "yesterday6AM", "yesterday6a.m.", "yesterday6A.M.", "yesterdayearly", "yesterdayEarly"], pass_context=True)
    async def yesterdaysunriser(self, ctx):
        await self.input_discipline("sunriser", ctx, True)

    @commands.command(aliases=["yesterdaySunlight", "yesterdayMorninglight", "yesterdaymorninglight", 'yesterdayMorningsun', 'yesterdaymorningsun', 'yesterdaylight', 'yesterdayLight', "yesterdaysun", "yesterdaySun",], pass_context=True)
    async def yesterdaysunlight(self, ctx):
        await self.input_discipline("sunlight", ctx, True)

    @commands.command(aliases=["yesterdayColdshower", "yesterdayCold", "yesterdaycold", 'yesterdayColdexposure', 'yesterdaycoldexposure'], pass_context=True)
    async def yesterdaycoldshower(self, ctx):
        await self.input_discipline("coldshower", ctx, True)

    @commands.command(aliases=["Alllastmonth"], pass_context=True)
    async def alllastmonth(self, ctx):
        recordc = pd.read_csv("cogs/Habits Record/personal.csv")
        datef = recordc.iloc[0, :]
        dateff = list()
        type(dateff)
        for i in list(datef.index.values):
            dateff.append(i)

        recordn = recordc.iloc[:, 0]

        recordn = list(recordn)

        names = datef.str.extract('([A-Za-z]+) ([A-Za-z]+)')
        dateffn = names.index.tolist()

        today = (datetime.datetime.utcnow()-datetime.timedelta(hours=8)).date()
        today = today - relativedelta(months=1)
        iso_date = today.isoformat()
        datem = iso_date.split('-')
        datemf = datem[0] + '-' + datem[1]

        indices = [item for item in dateffn if datemf in item]
        indice = indices[-1].split('-')[2]
        monthn = int(indice)

        fl = dateff.index(indices[0])
        ll = dateff.index(indices[-1])
        tl = dateff.index(iso_date)
        recordcn = list(recordc.iloc[:, 0])

        if str(ctx.author.id) not in recordcn:
            recordcn.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordc.columns)
            newrst = newrs.to_frame().T
            recordc = pd.concat([recordc, newrst], ignore_index=True)
            recordc.to_csv("cogs/Habits Record/personal.csv", index=False)
        nlc = recordcn.index(str(ctx.author.id))
        cc = recordc.iloc[nlc, fl:ll+1]
        recordma = pd.read_csv("cogs/Habits Record/makebed.csv")
        recordman = list(recordma.iloc[:, 0])
        if str(ctx.author.id) not in recordman:
            recordman.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordma.columns)
            newrst = newrs.to_frame().T
            recordma = pd.concat([recordma, newrst], ignore_index=True)
            recordma.to_csv("cogs/Habits Record/makebed.csv", index=False)
        nlma = recordman.index(str(ctx.author.id))
        cma = recordma.iloc[nlma, fl:ll+1]
        recordj = pd.read_csv("cogs/Habits Record/journal.csv")
        recordjn = list(recordj.iloc[:, 0])
        if str(ctx.author.id) not in recordjn:
            recordjn.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordj.columns)
            newrst = newrs.to_frame().T
            recordj = pd.concat([recordj, newrst], ignore_index=True)
            recordj.to_csv("cogs/Habits Record/journal.csv", index=False)
        nlj = recordjn.index(str(ctx.author.id))
        cj = recordj.iloc[nlj, fl:ll+1]
        recordg = pd.read_csv("cogs/Habits Record/gratitude.csv")
        recordgn = list(recordg.iloc[:, 0])
        if str(ctx.author.id) not in recordgn:
            recordgn.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordg.columns)
            newrst = newrs.to_frame().T
            recordg = pd.concat([recordg, newrst], ignore_index=True)
            recordg.to_csv("cogs/Habits Record/gratitude.csv", index=False)
        nlg = recordgn.index(str(ctx.author.id))
        cg = recordg.iloc[nlg, fl:ll+1]
        recordr = pd.read_csv("cogs/Habits Record/reading.csv")
        recordrn = list(recordr.iloc[:, 0])
        if str(ctx.author.id) not in recordrn:
            recordrn.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordr.columns)
            newrst = newrs.to_frame().T
            recordr = pd.concat([recordr, newrst], ignore_index=True)
            recordr.to_csv("cogs/Habits Record/reading.csv", index=False)
        nlr = recordrn.index(str(ctx.author.id))
        cr = recordr.iloc[nlr, fl:ll+1]
        recordw = pd.read_csv("cogs/Habits Record/workout.csv")
        recordwn = list(recordw.iloc[:, 0])
        if str(ctx.author.id) not in recordwn:
            recordwn.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordw.columns)
            newrst = newrs.to_frame().T
            recordw = pd.concat([recordw, newrst], ignore_index=True)
            recordw.to_csv("cogs/Habits Record/workout.csv", index=False)
        nlw = recordwn.index(str(ctx.author.id))
        cw = recordw.iloc[nlw, fl:ll+1]
        recordme = pd.read_csv("cogs/Habits Record/meditation.csv")
        recordmen = list(recordme.iloc[:, 0])
        if str(ctx.author.id) not in recordmen:
            recordmen.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordme.columns)
            newrst = newrs.to_frame().T
            recordme = pd.concat([recordme, newrst], ignore_index=True)
            recordme.to_csv("cogs/Habits Record/meditation.csv", index=False)
        nlme = recordmen.index(str(ctx.author.id))
        cme = recordme.iloc[nlme, fl:ll+1]

        recordsr = pd.read_csv("cogs/Habits Record/sunriser.csv")
        recordsrn = list(recordsr.iloc[:, 0])
        if str(ctx.author.id) not in recordsrn:
            recordsrn.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordsr.columns)
            newrst = newrs.to_frame().T
            recordsr = pd.concat([recordsr, newrst], ignore_index=True)
            recordsr.to_csv("cogs/Habits Record/sunriser.csv", index=False)
        nlsr = recordsrn.index(str(ctx.author.id))
        csr = recordsr.iloc[nlsr, fl:ll+1]
        recordsl = pd.read_csv("cogs/Habits Record/sunlight.csv")
        recordsln = list(recordsl.iloc[:, 0])
        if str(ctx.author.id) not in recordsln:
            recordsln.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordsl.columns)
            newrst = newrs.to_frame().T
            recordsl = pd.concat([recordsl, newrst], ignore_index=True)
            recordsl.to_csv("cogs/Habits Record/sunlight.csv", index=False)
        nlsl = recordsln.index(str(ctx.author.id))
        csl = recordsl.iloc[nlsl, fl:ll+1]
        recordcs = pd.read_csv("cogs/Habits Record/coldshower.csv")
        recordcsn = list(recordcs.iloc[:, 0])
        if str(ctx.author.id) not in recordcsn:
            recordcsn.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordcs.columns)
            newrst = newrs.to_frame().T
            recordcs = pd.concat([recordcs, newrst], ignore_index=True)
            recordcs.to_csv("cogs/Habits Record/coldshower.csv", index=False)
        nlcs = recordcsn.index(str(ctx.author.id))
        ccs = recordcs.iloc[nlcs, fl:ll+1]

        fig, ax = plt.subplots(figsize=(monthn, 10), dpi=150)
        rows = 10
        cols = monthn

        ax.set_ylim(-1, rows + 1)
        ax.set_xlim(0, cols + .5)

        df = pd.DataFrame({'mb10': list(cc), 'mb9': list(ccs), 'mb8': list(cw), 'mb7': list(cme), 'mb6': list(
            cj), 'mb5': list(cg), 'mb4': list(cr), 'mb3': list(csl), 'mb2': list(csr), 'mb1': list(cma)}).T

        plt.cla()
        for col in range(cols):
            for row in range(rows):
                if int(df.iloc[row, col]) == 1:
                    ax.text(x=col, y=row, s='\u2713',
                            va='center', ha='center', fontsize=24)

        for col in range(cols):
            ax.text(col, 9.75, col+1, weight='bold', ha='center', fontsize=20)
            ax.plot([col - .5, col - .5], [-0.5, rows+0.5],
                    ls='solid', lw='1', c='grey')
            if col % 10 == 0:
                ax.plot([col - .5, col - .5], [-0.5, rows+0.5],
                        ls='solid', lw='2.4', c='black')

        discf = ["Makebed", "Earlybird", "Sunlight", "Reading", "Gratitude",
                 "Journal", "Meditate", "Workout", "Coldshower", "Personal"]
        # disce = ["$\U0001F601$","$\U0001F426$","$\U0001F305$","$\U0001F4DA$","$\U0001F60A$","$\U0001F4DD$","$\U0001F9D8$","$\U0001F3CB$","$\U0001F6BF$","$\U0001F9CD$"]

        bb = -4.25
        for row in range(rows):
            ax.text(x=-0.75, y=row, s=discf[9-row], va='center',
                    ha='right', fontsize=20, weight='bold')
            # ax.text(x=-3.25, y=row, s=disce[9-row], va='center', ha='right',fontsize=9.5, weight='bold')
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

        # rect = patches.Rectangle((int(iso_date.split("-")[2])-1.5, -.5),1,11,ec='none',fc='grey',alpha=.2,zorder=-1)
        # ax.add_patch(rect)

        ax.axis('off')

        now = datetime.datetime.now() - relativedelta(months=1)
        curmon = now.strftime("%B")

        ax.set_title(
            f"{ctx.author.global_name}'s Discipline Record Last Month: {curmon}, {now.year}",
            loc='left',
            fontsize=30,
            weight='bold'
        )
        # plt.figure(figsize=(10,20))

        fig.savefig('testfig2.png', bbox_inches='tight', pad_inches=1)

        await ctx.send(file=discord.File('testfig2.png'))

        # await ctx.send(f"```\n{output}\n```")

    @commands.command(aliases=["Ranks",], pass_context=True)
    async def ranks(self, ctx):
        rolesf = pd.read_csv("cogs/SID Roles.csv")
        rolesf = pd.DataFrame(rolesf)
        output = t2a(
            header=["Rank", "Points"],
            body=[["Dominus", "2000+"], ["Ultra Instinct", 1650], ["Augustus", 1400], ["Saiyan", 1200],
                  ["Sultan", 1000], ["Knight", 850], [
                  "Strategos", 700], ["Full Cowl", 550],
                  ["Novarch", 400], ["Legatus", 300], [
                "Spartan", 220], ["Jonin", 160],
                ["Samurai", 115], ["Sohei", 85], [
                    "Medjay", 65], ["Gurkha", 50],
                ["Chunin", 38], ["Kenin", 28], [
                "Janissary", 18], ["Hapolite", 12],
                ["Genin", 6], ["Recruit", 0]],
            style=PresetStyle.thin_compact
        )
        await ctx.send(f"```\n{output}\n```")

    async def disciplineweek(self, discipline, ctx):
        # await ctx.send("reading record now")
        record = pd.read_csv(f"cogs/Habits Record/{discipline}.csv")
        names = list(record.iloc[:, 0])
        datef = record.iloc[0, :]
        # await ctx.send("just read the record")

        dateff = [date for date in datef.index.values]
        # await ctx.send("just made date array")
        today = (datetime.datetime.utcnow()-datetime.timedelta(hours=8)).date()
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
                f"This Week's {self.discipline_embed_info[discipline]['long_name']}", Merge.LEFT],
            body=weekday_discipline_pairing_list,
            style=PresetStyle.double_thin_box
        )
        # await ctx.send("just made table")
        await ctx.send(f"```\n{output}\n```")

    async def disciplinemonth(self, discipline, ctx):
        record = pd.read_csv(f"cogs/Habits Record/{discipline}.csv")
        names = list(record.iloc[:, 0])
        datef = record.iloc[0, :]
        dateff = [date for date in datef.index.values]

        today = (datetime.datetime.utcnow()-datetime.timedelta(hours=8)).date()
        iso_date = today.isoformat()
        month_days = list(range(1, int(iso_date.partition('-')[2].partition('-')[2])+1))
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

        month_record = record.iloc[name_index, beginning_index: today_index + 1]
        month_record_checks = ["\u2713" if i == 1 else " " for i in month_record]

        month_record_formatted = []
        i = 1
        if len(month_record_checks) > 7:
            weeks_so_far = int(len(month_record_checks)/7)
            days_so_far_this_week = len(month_record_checks) % 7
            for i in list(range(1, weeks_so_far+1)):
                month_record_formatted.append(month_record_checks[(i-1)*7:(i*7)])
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
        month_day_numbers_so_far = month_day_numbers[0:len(month_record_checks)]

        if len(month_day_numbers_so_far) > 7:
            weeks_so_far = int(len(month_day_numbers_so_far)/7)
            days_so_far_this_week = len(month_day_numbers_so_far) % 7
            month_day_numbers_so_far = list()
            i = 1
            for i in list(range(1, weeks_so_far+1)):
                month_day_numbers_so_far.append(list(range((i-1)*7+1, (i*7)+1)))
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

        header = [f"This Month's {self.discipline_embed_info[discipline]['long_name']}"]
        if len(month_record) < 7 and len(month_record) > 1:
            for i in list(range(1, len(month_record))):
                header.append(Merge.LEFT)
        elif len(month_record) > 7:
            for i in list(range(1, 7)):
                header.append(Merge.LEFT)

        output = t2a(
            header = header,
            body = fullm,
            style = PresetStyle.double_thin_box
        )
        await ctx.send(f"```\n{output}\n```")


    @commands.command(aliases=["Personalweek", "Goalweek", "goalweek"], pass_context=True)
    async def personalweek(self, ctx):
        await self.disciplineweek("personal", ctx)

    @commands.command(aliases=["Personalmonth", "Goalmonth", "goalmonth"], pass_context=True)
    async def personalmonth(self, ctx):
        await self.disciplinemonth("personal", ctx)

    @commands.command(aliases=["Meditationweek", "Mindfulnessweek", "mindfulnessweek", "Peaceweek", "peaceweek", "Namasteweek", "namasteweek", "meditateweek", "Meditateweek"], pass_context=True)
    async def meditationweek(self, ctx):
        await self.disciplineweek("meditation", ctx)

    @commands.command(aliases=["Meditationmonth", "Mindfulnessmonth", "mindfulnessmonth", "Peacemonth", "peacemonth", "Namastemonth", "namastemonth", "meditatemonth", "Meditatemonth"], pass_context=True)
    async def meditationmonth(self, ctx):
        await self.disciplinemonth("meditation", ctx)

    @commands.command(aliases=["Workoutweek", "Gymweek", "gymweek", "Exerciseweek", "exerciseweek", "Gainsweek", "gainsweek"], pass_context=True)
    async def workoutweek(self, ctx):
        await self.disciplineweek("workout", ctx)

    @commands.command(aliases=["Workoutmonth", "Gymmonth", "gymmonth", "Exercisemonth", "exercisemonth", "Gainsmonth", "gainsmonth"], pass_context=True)
    async def workoutmonth(self, ctx):
        await self.disciplinemonth("workout", ctx)

    @commands.command(aliases=["Readingweek", "Readweek", "readweek", "Bookweek", "bookweek"], pass_context=True)
    async def readingweek(self, ctx):
        await self.disciplineweek("reading", ctx)

    @commands.command(aliases=["Readingmonth", "Readmonth", "readmonth", "Bookmonth", "bookmonth"], pass_context=True)
    async def readingmonth(self, ctx):
        await self.disciplinemonth("reading", ctx)

    @commands.command(aliases=["Gratitudeweek", "Gratefulweek", "gratefulweek", "Gratefulnessweek", "gratefulnessweek", "Thankfulweek", "thankfulweek"], pass_context=True)
    async def gratitudeweek(self, ctx):
        await self.disciplineweek("gratitude", ctx)

    @commands.command(aliases=["Gratitudemonth", "Gratefulmonth", "gratefulmonth", "Gratefulnessmonth", "gratefulnessmonth", "Thankfulmonth", "thankfulmonth"], pass_context=True)
    async def gratitudemonth(self, ctx):
        await self.disciplinemonth("gratitude", ctx)

    @commands.command(aliases=["Journalweek", "Diaryweek", "diaryweek", "Logweek", "logweek"], pass_context=True)
    async def journalweek(self, ctx):
        await self.disciplineweek("journal", ctx)

    @commands.command(aliases=["Journalmonth", "Diarymonth", "diarymonth", "Logmonth", "logmonth"], pass_context=True)
    async def journalmonth(self, ctx):
        await self.disciplinemonth("journal", ctx)

    @commands.command(aliases=["Makebedweek", "Madebedweek", "madebedweek"], pass_context=True)
    async def makebedweek(self, ctx):
        await self.disciplineweek("makebed", ctx)

    @commands.command(aliases=["Makebedmonth", "Madebedmonth", "madebedmonth"], pass_context=True)
    async def makebedmonth(self, ctx):
        await self.disciplinemonth("makebed", ctx)

    @commands.command(aliases=["Sunriserweek", "earlybirdweek", "Earlybirdweek", "firstwatchweek", "Firstwatchweek"], pass_context=True)
    async def sunriserweek(self, ctx):
        await self.disciplineweek("sunriser", ctx)

    @commands.command(aliases=["Sunrisermonth", "earlybirdmonth", "Earlybirdmonth", "firstwatchmonth", "Firstwatchmonth"], pass_context=True)
    async def sunrisermonth(self, ctx):
        await self.disciplinemonth("sunriser", ctx)

    @commands.command(aliases=["Sunlightweek", "Morninglightweek", "morninglightweek", "morningsunweek", "Morningsunweek"], pass_context=True)
    async def sunlightweek(self, ctx):
        await self.disciplineweek("sunlight", ctx)

    @commands.command(aliases=["Sunlightmonth", "Morninglightmonth", "morninglightmonth", "morningsunmonth", "Morningsunmonth"], pass_context=True)
    async def sunlightmonth(self, ctx):
        await self.disciplinemonth("sunlight", ctx)

    @commands.command(aliases=["Coldshowerweek", "Coldweek", "coldweek", 'Coldexposureweek', 'coldexposureweek'], pass_context=True)
    async def coldshowerweek(self, ctx):
        await self.disciplineweek("coldshower", ctx)

    @commands.command(aliases=["Coldshowermonth", "Coldmonth", "coldmonth", 'Coldexposuremonth', 'coldexposuremonth'], pass_context=True)
    async def coldshowermonth(self, ctx):
        await self.disciplinemonth("coldshower", ctx)

    @commands.command(aliases=["Today"], pass_context=True)
    async def today(self, ctx):
        recordc = pd.read_csv("cogs/Habits Record/personal.csv")
        datef = recordc.iloc[0, :]
        dateff = list()
        type(dateff)
        for i in list(datef.index.values):
            dateff.append(i)

        today = (datetime.datetime.utcnow()-datetime.timedelta(hours=8)).date()
        iso_date = today.isoformat()
        tl = dateff.index(iso_date)
        recordcn = list(recordc.iloc[:, 0])
        if str(ctx.author.id) not in recordcn:
            recordcn.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordc.columns)
            newrst = newrs.to_frame().T
            recordc = pd.concat([recordc, newrst], ignore_index=True)
            recordc.to_csv("cogs/Habits Record/personal.csv", index=False)
        nlc = recordcn.index(str(ctx.author.id))
        cc = recordc.iloc[nlc, tl]
        recordma = pd.read_csv("cogs/Habits Record/makebed.csv")
        recordman = list(recordma.iloc[:, 0])
        if str(ctx.author.id) not in recordman:
            recordman.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordma.columns)
            newrst = newrs.to_frame().T
            recordma = pd.concat([recordma, newrst], ignore_index=True)
            recordma.to_csv("cogs/Habits Record/makebed.csv", index=False)
        nlma = recordman.index(str(ctx.author.id))
        cma = recordma.iloc[nlma, tl]
        recordj = pd.read_csv("cogs/Habits Record/journal.csv")
        recordjn = list(recordj.iloc[:, 0])
        if str(ctx.author.id) not in recordjn:
            recordjn.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordj.columns)
            newrst = newrs.to_frame().T
            recordj = pd.concat([recordj, newrst], ignore_index=True)
            recordj.to_csv("cogs/Habits Record/journal.csv", index=False)
        nlj = recordjn.index(str(ctx.author.id))
        cj = recordj.iloc[nlj, tl]
        recordg = pd.read_csv("cogs/Habits Record/gratitude.csv")
        recordgn = list(recordg.iloc[:, 0])
        if str(ctx.author.id) not in recordgn:
            recordgn.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordg.columns)
            newrst = newrs.to_frame().T
            recordg = pd.concat([recordg, newrst], ignore_index=True)
            recordg.to_csv("cogs/Habits Record/gratitude.csv", index=False)
        nlg = recordgn.index(str(ctx.author.id))
        cg = recordg.iloc[nlg, tl]
        recordr = pd.read_csv("cogs/Habits Record/reading.csv")
        recordrn = list(recordr.iloc[:, 0])
        if str(ctx.author.id) not in recordrn:
            recordrn.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordr.columns)
            newrst = newrs.to_frame().T
            recordr = pd.concat([recordr, newrst], ignore_index=True)
            recordr.to_csv("cogs/Habits Record/reading.csv", index=False)
        nlr = recordrn.index(str(ctx.author.id))
        cr = recordr.iloc[nlr, tl]
        recordw = pd.read_csv("cogs/Habits Record/workout.csv")
        recordwn = list(recordw.iloc[:, 0])
        if str(ctx.author.id) not in recordwn:
            recordwn.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordw.columns)
            newrst = newrs.to_frame().T
            recordw = pd.concat([recordw, newrst], ignore_index=True)
            recordw.to_csv("cogs/Habits Record/workout.csv", index=False)
        nlw = recordwn.index(str(ctx.author.id))
        cw = recordw.iloc[nlw, tl]
        recordme = pd.read_csv("cogs/Habits Record/meditation.csv")
        recordmen = list(recordme.iloc[:, 0])
        if str(ctx.author.id) not in recordmen:
            recordmen.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordme.columns)
            newrst = newrs.to_frame().T
            recordme = pd.concat([recordme, newrst], ignore_index=True)
            recordme.to_csv("cogs/Habits Record/meditation.csv", index=False)
        nlme = recordmen.index(str(ctx.author.id))
        cme = recordme.iloc[nlme, tl]

        recordsr = pd.read_csv("cogs/Habits Record/sunriser.csv")
        recordsrn = list(recordsr.iloc[:, 0])
        if str(ctx.author.id) not in recordsrn:
            recordsrn.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordsr.columns)
            newrst = newrs.to_frame().T
            recordsr = pd.concat([recordsr, newrst], ignore_index=True)
            recordsr.to_csv("cogs/Habits Record/sunriser.csv", index=False)
        nlsr = recordsrn.index(str(ctx.author.id))
        csr = recordsr.iloc[nlsr, tl]
        recordsl = pd.read_csv("cogs/Habits Record/sunlight.csv")
        recordsln = list(recordsl.iloc[:, 0])
        if str(ctx.author.id) not in recordsln:
            recordsln.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordsl.columns)
            newrst = newrs.to_frame().T
            recordsl = pd.concat([recordsl, newrst], ignore_index=True)
            recordsl.to_csv("cogs/Habits Record/sunlight.csv", index=False)
        nlsl = recordsln.index(str(ctx.author.id))
        csl = recordsl.iloc[nlsl, tl]
        recordcs = pd.read_csv("cogs/Habits Record/coldshower.csv")
        recordcsn = list(recordcs.iloc[:, 0])
        if str(ctx.author.id) not in recordcsn:
            recordcsn.append(str(ctx.author.id))
            newr = [0] * (len(dateff)-1)
            newr.insert(0, str(ctx.author.id))
            newrs = pd.Series(newr, index=recordcs.columns)
            newrst = newrs.to_frame().T
            recordcs = pd.concat([recordcs, newrst], ignore_index=True)
            recordcs.to_csv("cogs/Habits Record/coldshower.csv", index=False)
        nlcs = recordcsn.index(str(ctx.author.id))
        ccs = recordcs.iloc[nlcs, tl]

        discf1 = ["Makebed", "Earlybird", "Sunlight", "Reading", "Gratitude"]
        discf2 = ["Journal", "Meditate", "Workout", "Cold", "Personal"]

        discc1 = [cma, csr, csl, cr, cg]
        discc2 = [cj, cme, cw, ccs, cc]

        discd1 = []
        discd2 = []
        full = []
        for i in list(range(0, len(discf1))):
            if discc1[i] == 1:
                discd1 = "\u2713"
            else:
                discd1 = (' ')

            if discc2[i] == 1:
                discd2 = "\u2713"
            else:
                discd2 = (' ')

            full.append([discf1[i], discd1, discf2[i], discd2])

        todayd = "Today's Disciplines"

        if all(discc1):
            if all(discc2):
                todayd = "\u2605 Today's Disciplines \u2605"

        output = t2a(
            header=[todayd, Merge.LEFT, Merge.LEFT, Merge.LEFT],
            body=full,
            style=PresetStyle.double_thin_box
        )
        await ctx.send(f"```\n{output}\n```")

    @commands.command(aliases=["Allmonth"], pass_context=True)
    async def allmonth(self, ctx):
        self.generate_discipline_record_for_member(ctx.author)
        await ctx.send(file=discord.File('testfig2.png'))

    @commands.command(aliases=["Show"], pass_context=True)
    async def show(self, ctx, *usernames):
        if not self.is_user_officer(ctx):
            await ctx.send('You must have the officer role to use this command')
            return

        await ctx.send('Getting member objects now..')
        members = [self.get_member_obj_from_username(
            ctx, username) for username in usernames]

        await ctx.send('Got member objects, now entering loop..')

        await ctx.send(f'Members are: {members=}')

        for member in members:
            self.generate_discipline_record_for_member(member)
            await ctx.send(file=discord.File('testfig2.png'))
            print('inside loop!!!!!')
            # await ctx.send('Sending discipline record for ', member.name)

    def generate_discipline_record_for_member(self, member):
        print(f"generating discipline record for user {member.name=}")
        personn = str(member.name)
        person = str(member.id)

        print('test1')
        recordc = pd.read_csv("cogs/Habits Record/personal.csv")
        datef = recordc.iloc[0, :]
        dateff = list()
        type(dateff)
        for i in list(datef.index.values):
            dateff.append(i)

        recordn = recordc.iloc[:, 0]

        recordn = list(recordn)

        names = datef.str.extract('([A-Za-z]+) ([A-Za-z]+)')
        dateffn = names.index.tolist()

        today = (datetime.datetime.utcnow()-datetime.timedelta(hours=8)).date()
        iso_date = today.isoformat()
        datem = iso_date.split('-')
        datemf = datem[0] + '-' + datem[1]

        indices = [item for item in dateffn if datemf in item]
        indice = indices[-1].split('-')[2]
        monthn = int(indice)

        fl = dateff.index(indices[0])
        ll = dateff.index(indices[-1])
        tl = dateff.index(iso_date)
        recordcn = list(recordc.iloc[:, 0])
        if person not in recordcn:
            recordcn.append(person)
            newr = [0] * (len(dateff)-1)
            newr.insert(0, person)
            newrs = pd.Series(newr, index=recordc.columns)
            newrst = newrs.to_frame().T
            recordc = pd.concat([recordc, newrst], ignore_index=True)
            recordc.to_csv("cogs/Habits Record/personal.csv", index=False)
        nlc = recordcn.index(person)
        cc = recordc.iloc[nlc, fl:ll+1]
        recordma = pd.read_csv("cogs/Habits Record/makebed.csv")
        recordman = list(recordma.iloc[:, 0])
        if person not in recordman:
            recordman.append(person)
            newr = [0] * (len(dateff)-1)
            newr.insert(0, person)
            newrs = pd.Series(newr, index=recordma.columns)
            newrst = newrs.to_frame().T
            recordma = pd.concat([recordma, newrst], ignore_index=True)
            recordma.to_csv("cogs/Habits Record/makebed.csv", index=False)
        nlma = recordman.index(person)
        cma = recordma.iloc[nlma, fl:ll+1]
        recordj = pd.read_csv("cogs/Habits Record/journal.csv")
        recordjn = list(recordj.iloc[:, 0])  # get 1st row of df
        if person not in recordjn:
            recordjn.append(person)
            newr = [0] * (len(dateff)-1)
            newr.insert(0, person)
            newrs = pd.Series(newr, index=recordj.columns)
            newrst = newrs.to_frame().T
            recordj = pd.concat([recordj, newrst], ignore_index=True)
            recordj.to_csv("cogs/Habits Record/journal.csv", index=False)
        nlj = recordjn.index(person)
        cj = recordj.iloc[nlj, fl:ll+1]
        recordg = pd.read_csv("cogs/Habits Record/gratitude.csv")
        recordgn = list(recordg.iloc[:, 0])  # gets the first column
        if person not in recordgn:
            recordgn.append(person)
            newr = [0] * (len(dateff)-1)
            newr.insert(0, person)
            newrs = pd.Series(newr, index=recordg.columns)
            newrst = newrs.to_frame().T
            recordg = pd.concat([recordg, newrst], ignore_index=True)
            recordg.to_csv("cogs/Habits Record/gratitude.csv", index=False)
        nlg = recordgn.index(person)
        cg = recordg.iloc[nlg, fl:ll+1]
        recordr = pd.read_csv("cogs/Habits Record/reading.csv")
        recordrn = list(recordr.iloc[:, 0])
        if person not in recordrn:
            recordrn.append(person)
            newr = [0] * (len(dateff)-1)
            newr.insert(0, person)
            newrs = pd.Series(newr, index=recordr.columns)
            newrst = newrs.to_frame().T
            recordr = pd.concat([recordr, newrst], ignore_index=True)
            recordr.to_csv("cogs/Habits Record/reading.csv", index=False)
        nlr = recordrn.index(person)
        cr = recordr.iloc[nlr, fl:ll+1]
        recordw = pd.read_csv("cogs/Habits Record/workout.csv")
        recordwn = list(recordw.iloc[:, 0])
        if person not in recordwn:
            recordwn.append(person)
            newr = [0] * (len(dateff)-1)
            newr.insert(0, person)
            newrs = pd.Series(newr, index=recordw.columns)
            newrst = newrs.to_frame().T
            recordw = pd.concat([recordw, newrst], ignore_index=True)
            recordw.to_csv("cogs/Habits Record/workout.csv", index=False)
        nlw = recordwn.index(person)
        cw = recordw.iloc[nlw, fl:ll+1]
        recordme = pd.read_csv("cogs/Habits Record/meditation.csv")
        recordmen = list(recordme.iloc[:, 0])
        if person not in recordmen:
            recordmen.append(person)
            newr = [0] * (len(dateff)-1)
            newr.insert(0, person)
            newrs = pd.Series(newr, index=recordme.columns)
            newrst = newrs.to_frame().T
            recordme = pd.concat([recordme, newrst], ignore_index=True)
            recordme.to_csv("cogs/Habits Record/meditation.csv", index=False)
        nlme = recordmen.index(person)
        cme = recordme.iloc[nlme, fl:ll+1]

        recordsr = pd.read_csv("cogs/Habits Record/sunriser.csv")
        recordsrn = list(recordsr.iloc[:, 0])
        if person not in recordsrn:
            recordsrn.append(person)
            newr = [0] * (len(dateff)-1)
            newr.insert(0, person)
            newrs = pd.Series(newr, index=recordsr.columns)
            newrst = newrs.to_frame().T
            recordsr = pd.concat([recordsr, newrst], ignore_index=True)
            recordsr.to_csv("cogs/Habits Record/sunriser.csv", index=False)
        nlsr = recordsrn.index(person)
        csr = recordsr.iloc[nlsr, fl:ll+1]
        recordsl = pd.read_csv("cogs/Habits Record/sunlight.csv")
        recordsln = list(recordsl.iloc[:, 0])
        if person not in recordsln:
            recordsln.append(person)
            newr = [0] * (len(dateff)-1)
            newr.insert(0, person)
            newrs = pd.Series(newr, index=recordsl.columns)
            newrst = newrs.to_frame().T
            recordsl = pd.concat([recordsl, newrst], ignore_index=True)
            recordsl.to_csv("cogs/Habits Record/sunlight.csv", index=False)
        nlsl = recordsln.index(person)
        csl = recordsl.iloc[nlsl, fl:ll+1]
        recordcs = pd.read_csv("cogs/Habits Record/coldshower.csv")
        recordcsn = list(recordcs.iloc[:, 0])
        if person not in recordcsn:
            recordcsn.append(person)
            newr = [0] * (len(dateff)-1)
            newr.insert(0, person)
            newrs = pd.Series(newr, index=recordcs.columns)
            newrst = newrs.to_frame().T
            recordcs = pd.concat([recordcs, newrst], ignore_index=True)
            recordcs.to_csv("cogs/Habits Record/coldshower.csv", index=False)
        nlcs = recordcsn.index(person)
        ccs = recordcs.iloc[nlcs, fl:ll+1]

        fig, ax = plt.subplots(figsize=(monthn, 10), dpi=150)
        rows = 10
        cols = monthn

        ax.set_ylim(-1, rows + 1)
        ax.set_xlim(0, cols + .5)

        all_discipline_records = [cc, ccs, cw, cme, cj, cg, cr, csl, csr, cma]

        df = pd.DataFrame({'mb10': list(cc), 'mb9': list(ccs), 'mb8': list(cw), 'mb7': list(cme), 'mb6': list(
            cj), 'mb5': list(cg), 'mb4': list(cr), 'mb3': list(csl), 'mb2': list(csr), 'mb1': list(cma)}).T

        print("dataframe has been generated")

        plt.cla()
        print("plt.cla() was just called")
        for col in range(cols):
            for row in range(rows):
                print("now we're checking if this discipline was done")
                if int(df.iloc[row, col]) == 1:
                    print("yes, done")
                    ax.text(x=col, y=row, s='\u2713',
                            va='center', ha='center', fontsize=24)
                print(f"row {row+1} of {rows}, col {col+1} of {cols}")
        print("checkmarks have been added to plot")

        for col in range(cols):
            ax.text(x=col, y=-1, s=int(sum((list(discipline)
                    [col] for discipline in all_discipline_records))), va='center', ha='center', fontsize=24)

        print("total disciplines has been added to plot")

        for col in range(cols):
            ax.text(col, 9.75, col+1, weight='bold', ha='center', fontsize=20)
            ax.plot([col - .5, col - .5], [-0.5, rows+0.5],
                    ls='solid', lw='1', c='grey')
            if col % 10 == 0:
                ax.plot([col - .5, col - .5], [-0.5, rows+0.5],
                        ls='solid', lw='2.4', c='black')

        print("cell borders have been added to plot")

        discf = ["Makebed", "Earlybird", "Sunlight", "Reading", "Gratitude",
                 "Journal", "Meditate", "Workout", "Coldshower", "Personal"]
        # disce = ["$\U0001F601$","$\U0001F426$","$\U0001F305$","$\U0001F4DA$","$\U0001F60A$","$\U0001F4DD$","$\U0001F9D8$","$\U0001F3CB$","$\U0001F6BF$","$\U0001F9CD$"]

        bb = -4.25
        for row in range(rows):
            ax.text(x=-0.75, y=row, s=discf[9-row], va='center',
                    ha='right', fontsize=20, weight='bold')
            # ax.text(x=-3.25, y=row, s=disce[9-row], va='center', ha='right',fontsize=9.5, weight='bold')
            ax.plot([bb, cols-.5], [row - .5, row - .5],
                    ls='solid', lw='2.4', c='black')

        print("more stuff added to plot, not sure what")

        ax.text(x=-0.65, y=9.90, s="Disciplines\\Days", va='center',
                ha='right', fontsize=17, weight='bold')
        ax.plot([bb, cols-.5], [9.5, 9.5], ls='solid', lw='2.4', c='black')
        ax.plot([bb, cols-.5], [10.5, 10.5], ls='solid', lw='3', c='black')
        ax.plot([bb, cols-.5], [-.5, -.5], ls='solid', lw='3', c='black')
        ax.plot([bb, bb], [-0.5, rows+0.5], ls='solid', lw='3', c='black')
        ax.plot([cols - .5, cols - .5], [-0.5, rows+0.5],
                ls='solid', lw='3', c='black')

        rect = patches.Rectangle((int(iso_date.split(
            "-")[2])-1.5, -.5), 1, 11, ec='none', fc='grey', alpha=.2, zorder=-1)
        ax.add_patch(rect)

        ax.axis('off')

        now = datetime.datetime.now()
        curmon = now.strftime("%B")

        ax.set_title(
            f"{personn}'s Discipline Record: {curmon}, {now.year}",
            loc='left',
            fontsize=30,
            weight='bold'
        )

        print("title has been added to plot")

        # plt.figure(figsize=(10,20))

        fig.savefig('testfig2.png', bbox_inches='tight', pad_inches=1)

        print(f"discipline record for user {member.name=} has been saved")

        # await ctx.send(f"```\n{output}\n```")

        # await ctx.send(f"```\n{output}\n```")


async def setup(client):
    await client.add_cog(Economy(client))