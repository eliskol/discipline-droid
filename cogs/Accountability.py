import discord
from discord.ext import commands, tasks
import os
import json
import datetime
from dateutil.relativedelta import relativedelta
from AccountabilityPartnership import AccountabilityPartnership


client = commands.Bot(command_prefix='!', intents=discord.Intents.all())

class Accountability(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.open_invitations = {}
        with open("cogs/open_accountability_invitations.json", "r") as f:
            weird_dict = json.load(f)
            for key in weird_dict: # json stores keys as strings no matter what, when our datatype for the keys is really int.
                self.open_invitations[int(key)] = weird_dict[key]
        print(f"just loaded open invitations, we have {self.open_invitations}")

    # @tasks.loop(hours=1)
    def save_open_invitations(self):
        with open("cogs/open_accountability_invitations.json", "w") as f:
            json.dump(self.open_invitations, f)
        print(f"just saved open invitations, we have {self.open_invitations}")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} is online!")

    @commands.command(aliases=["a"], pass_context=True)
    async def accountability(self, ctx, *args: str):
        if args[0].lower() == "start" and len(args) > 1:
            print(args)
            invited_member_obj = await get_member_obj_from_arg(ctx, args[1])

            if invited_member_obj is None:
                await ctx.send(f"{ctx.author}, please try your command again.")
                return

            invited_member_id = invited_member_obj.id

            # if invited_member_obj == ctx.author:
                # await ctx.send(f"{ctx.author}, you cannot invite yourself to an Accountability Partnership!")
                # return

            if int(ctx.author.id) in self.open_invitations and self.open_invitations[int(ctx.author.id)] == invited_member_id:
                await ctx.send(f"{ctx.author}, you have already invited {invited_member_obj} to an Accountability Partnership.")
            elif invited_member_id in self.open_invitations and self.open_invitations[int(invited_member_id)] == int(ctx.author.id):
                # members have succesfully invited each other to Accountability Partnership
                await ctx.send(f"<@{invited_member_id}> and <@{ctx.author.id}>, you have begun an Accountability Partnership!")
                del self.open_invitations[invited_member_id]
                self.save_open_invitations()
                self.start_accountability_partnership(invited_member_id, ctx.author.id)
            else:
                await ctx.send(f"{ctx.author} has invited {invited_member_obj} to participate in an Accountability Partnership!")
                self.open_invitations[int(ctx.author.id)] = invited_member_obj.id
                self.save_open_invitations()
                await invited_member_obj.send(f"{invited_member_obj}, {ctx.author} has invited you to an Accountability Partnership!\nType `!accountability start {ctx.author}` in the accountability channel to accept their invitation!\nType `!accountability decline {ctx.author}` if you choose to decline.")

        elif args[0].lower() == "decline" and len(args) > 1:
            original_member = await get_member_obj_from_arg(ctx, args[1])
            if original_member is None:
                ctx.send("Please try your command again.")
            if ctx.author.id not in self.open_invitations.values() or (ctx.author.id in self.open_invitations.values() and self.open_invitations[original_member.id] != ctx.author.id):
                await ctx.send("Sorry, you do not have an accountability invitation from this person.")
            elif self.open_invitations[original_member.id] == ctx.author.id:
                del self.open_invitations[original_member.id]
                await ctx.send(f"{ctx.author}, you have declined the accountability invitation from {original_member}.")
                self.save_open_invitations()

        elif args[0].lower() == "log":
            if len(args) == 1:
                await ctx.send("You forgot to input arguments!")
                return
            ap = AccountabilityPartnership.from_member_id(ctx.author.id)
            print(f"Got AP object {ap}")
            if ap is None:
                await ctx.send("Couldn't find your Accountability Partnership! Are you sure you're in an active one?")
                return
            if args[1] == "today":
                await self.log_today(ctx, ap, *args)
            elif args[1] == "yesterday":
                await self.log_yesterday(ctx, ap, *args)
            else:
                await ctx.send("Please try your command again!")

        else:
            await ctx.send("You forgot to input arguments!")

    def start_accountability_partnership(self, original_member, second_member):
        AccountabilityPartnership(original_member, second_member, started_by = original_member)
        AccountabilityPartnership(second_member, original_member, started_by = original_member)

    async def log_today(self, ctx, ap, *args):
        print(f"\nReceived log today command from {ctx.author}")
        status = ap.log_today()
        print(f"Status was {status}")
        if status == "already logged":
            await ctx.send("You have already logged for today!")
        elif status == "successful":
            await ctx.send("You have successfully logged your Accountability Partnership for today!")
            other_ap = ap.get_other_member_ap()
            if other_ap is None: await ctx.send("There's been a glitch. Please contact Elias.")
            elif ap.date_obj_from_str(ap.last_date_logged) > ap.date_obj_from_str(other_ap.last_date_logged):
                # send reminder
                print(f"Other partner last_date_logged is {other_ap.last_date_logged}")
                other_member_obj : discord.User = ctx.guild.get_member(ap.other_member)
                await other_member_obj.send(f"{other_member_obj}, your Accountability Partner has logged for today!\nPlease log today to complete the day and extend your streak!")
        else:
            await ctx.send("You forgot to log yesterday!")

    async def log_yesterday(self, ctx, ap, *args):
        print(f"\nReceived log yesterday command from {ctx.author}")
        status = ap.log_yesterday()
        print(f"Status was {status}")
        if status == "already logged":
            await ctx.send("You have already logged for yesterday!")
        elif status == "successful":
            await ctx.send("You have successfully logged your Accountability Partnership for yesterday!")
            other_ap = ap.get_other_member_ap()
            if other_ap is None: await ctx.send("There's been a glitch. Please contact Elias.")
            elif ap.date_obj_from_str(ap.last_date_logged) > ap.date_obj_from_str(other_ap.last_date_logged):
                # send reminder
                print(f"Other partner last_date_logged is {other_ap.last_date_logged}")
                other_member_obj : discord.User = ctx.guild.get_member(ap.other_member)
                await other_member_obj.send(f"{other_member_obj}, your Accountability Partner has logged for yesterday!\nPlease log yesterday to complete the day and extend your streak!")
        else:
            await ctx.send("You forgot to log the day before yesterday!")

async def setup(client):
    await client.add_cog(Accountability(client))

async def get_member_obj_from_arg(ctx, arg):
    invited_member_obj = ctx.guild.get_member_named(arg)
    if invited_member_obj is None:
        # check if they mentioned the person
        if arg.startswith("<@") and arg.endswith(">"):
            invited_member_id = arg[2:-1]
            invited_member_obj = await ctx.guild.fetch_member(invited_member_id)
    return invited_member_obj