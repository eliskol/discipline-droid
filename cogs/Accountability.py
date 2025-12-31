import discord
from discord.ext import commands, tasks
import os
import json
import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from AccountabilityPartnership import AccountabilityPartnership


accountability_channel_id = int(os.getenv('accountability_channel'))
client = commands.Bot(command_prefix='!', intents=discord.Intents.all())

class Accountability(commands.Cog):
    def __init__(self, client, accountability_channel_id):
        self.client = client
        self.accountability_channel_id = accountability_channel_id
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

    @commands.command(aliases=["r"], pass_context=True)
    async def reload(self, ctx, *args: str):
        if ctx.author.id != 292088878767144964: return
        await self.client.unload_extension("cogs.Accountability")
        await ctx.send("Unloaded cogs.Accountability.")
        await self.client.load_extension("cogs.Accountability")
        await ctx.send("Loaded cogs.Accountability.")

    @commands.command(aliases=["a"], pass_context=True)
    async def accountability(self, ctx, *args: str):
        if ctx.channel.id != self.accountability_channel_id:
            print(f"{ctx.author} tried to use an accountability command outside the proper channel!")
            return

        if len(args) == 0:
            await self.help(ctx, *args)

        elif args[0].lower() == "start":
            await self.start(ctx, *args)

        elif args[0].lower() == "decline" and len(args) > 1:
            await self.decline(ctx, *args)

        elif args[0].lower() == "log":
            await self.log(ctx, *args)

        elif args[0].lower() == "info":
            await self.info(ctx, *args)

        elif args[0].lower() == "help":
            await self.help(ctx, *args)

        elif args[0].lower() == "end":
            await self.end_partnership(ctx, *args)

        elif args[0].lower() == "pause":
            await self.pause(ctx, *args)

        elif args[0].lower() == "resume":
            await self.resume(ctx, *args)


    async def start(self, ctx, *args):
        if len(args) == 1:
            await ctx.send(f"{ctx.author}, you have an argument missing.")
            return
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

    async def decline(self, ctx, *args):
        original_member = await get_member_obj_from_arg(ctx, args[1])
        if original_member is None:
            ctx.send("Please try your command again.")
        if ctx.author.id not in self.open_invitations.values() or (ctx.author.id in self.open_invitations.values() and self.open_invitations[original_member.id] != ctx.author.id):
            await ctx.send("Sorry, you do not have an accountability invitation from this person.")
        elif self.open_invitations[original_member.id] == ctx.author.id:
            del self.open_invitations[original_member.id]
            await ctx.send(f"{ctx.author}, you have declined the accountability invitation from {original_member}.")
            self.save_open_invitations()

    async def log(self, ctx, *args):
        if len(args) == 1:
            await ctx.send("You forgot to input arguments!")
            return
        ap = AccountabilityPartnership.from_member_id(ctx.author.id)
        print(f"Got AP object {ap}")
        if ap is None:
            await ctx.send("Couldn't find your Accountability Partnership! Are you sure you're in an active one?")
        elif args[1] == "today":
            await self.log_today(ctx, ap, *args)
        elif args[1] == "yesterday":
            await self.log_yesterday(ctx, ap, *args)
        else:
            await ctx.send("Please try your command again!")

    def start_accountability_partnership(self, original_member, second_member):
        AccountabilityPartnership(original_member, second_member, started_by = original_member)
        AccountabilityPartnership(second_member, original_member, started_by = original_member)

    async def help(self, ctx, *args):
        print(f"help command invoked by {ctx.author}")
        help_embed = discord.Embed(title="Accountability Partnership Commands", description="These commands can only be used inside the accountability channel!", color=discord.Color.green())
        help_embed.add_field(name="help", value="What you are seeing now. Shows info for accountability commands.", inline=False)
        help_embed.add_field(name="start (user)", value="Invite someone to participate in an Accountability Partnership by typing their username after this command.", inline=False)
        help_embed.add_field(name="decline", value="Decline someone's Accountability Partnership invitation.", inline=False)
        help_embed.add_field(name="log today/yesterday", value="Log today or yesterday for your Accountability Partnership.", inline=False)
        help_embed.add_field(name="info", value="Get information about your current Accountability Partnership.", inline=False)
        help_embed.add_field(name="end", value="Ends your current Accountability Partnership if you are in one.", inline=False)
        await ctx.send(embed=help_embed)

    async def info(self, ctx, *args):
        ap = AccountabilityPartnership.from_member_id(ctx.author.id)
        if ap is None:
            await ctx.send(f"{ctx.author.mention}, you are not in an active Accountability Partnership!")
        else:
            ap_embed = discord.Embed(title="Accountability Partnership", description=f"{ctx.author.mention} and {(await ctx.guild.fetch_member(ap.other_member)).mention}", color=discord.Color.blue())
            ds_tt = date.fromisoformat(ap.get_date_resumed()).timetuple()
            ldl_tt = date.fromisoformat(ap.get_last_date_logged()).timetuple() if type(ap.get_last_date_logged()) is str else [None] * 3
            ldc_tt = date.fromisoformat(ap.last_date_completed).timetuple() if type(ap.last_date_completed) is str else [None] * 3
            ap_embed.add_field(name=f"Date {'Started' if len(ap.date_list) < 3 else 'Resumed'}:", value=f"{ds_tt[1]}/{ds_tt[2]}/{ds_tt[0]}")
            ap_embed.add_field(name="Your Last Day Logged:", value=f"{ldl_tt[1]}/{ldl_tt[2]}/{ldl_tt[0]}")
            ap_embed.add_field(name="Last Day Completed by Both Partners:", value=f"{ldc_tt[1]}/{ldc_tt[2]}/{ldc_tt[0]}")
            await ctx.send(embed=ap_embed)

    async def log_today(self, ctx, ap: AccountabilityPartnership, *args):
        print(f"\nReceived log today command from {ctx.author}")
        status = ap.log_today()
        print(f"Status was {status}")
        log_embed = discord.Embed(title="Accountability Partnership", description=f"<@{ap.primary_member}> and <@{ap.other_member}>")
        if status == "Paused":
            print("Building paused embed now.")
            log_embed.color = discord.Color.red()
            log_embed.add_field(name=f"Partnership Status:", value="Your Partnership is Currently Paused! Use !a resume to resume your partnership.", inline=False)
        elif status == "already logged":
            print("Building already logged embed now.")
            # await ctx.send("You have already logged for today!")
            log_embed.color = discord.Color.red()
            log_embed.add_field(name=f"Log Status:", value="Already Logged", inline=False)
            log_embed.add_field(name=f"Days Logged by You:", value=ap.get_log_streak(), inline=False)
            # log_embed.add_field(name=f"Days Completed by Both Partners:", value=ap.get_completion_streak(), inline=False)
            # embed.add_field(name=f"Points Gained:", value=0, inline=False)
        elif status == "successful":
            print("Building success embed now.")
            log_embed.color = discord.Color.green()
            # await ctx.send("You have successfully logged your Accountability Partnership for today!")
            log_embed.add_field(name=f"Log Status:", value="Successful", inline=False)
            log_embed.add_field(name=f"Days Logged by You:", value=ap.get_log_streak(), inline=False)
            print(f"Log streak was {ap.get_log_streak()}")
            log_embed.add_field(name=f"Days Completed by Both Partners:", value=ap.get_completion_streak(), inline=False)
            print(f"Completed streak was {ap.get_completion_streak()}")
            # embed.add_field(name=f"Points Gained:", value={True: 2, False: 0}[ap.added_points], inline=False)
            if ap.added_points:
                completed_embed = discord.Embed(title=f"Accountability Day {ap.get_completion_streak()} Completed!", description=f"<@{ap.primary_member}> and <@{ap.other_member}>", color=discord.Color.gold())
                completed_embed.add_field(name=f"Points Gained by Both Partners Today:", value=2)
                completed_embed.add_field(name=f"{ctx.author} Total Points:", value=f"{get_points_by_id(ctx.author.id)}")
                completed_embed.add_field(name=f"{await ctx.guild.fetch_member(ap.other_member)} Total Points:", value=f"{get_points_by_id(ap.other_member)}")
            other_ap = ap.get_other_member_ap()
            if other_ap is None: await ctx.send("There's been a glitch. Please contact Elias.")
            elif ap.date_obj_from_str(ap.get_last_date_logged()) > ap.date_obj_from_str(other_ap.get_last_date_logged()):
                # send reminder
                print(f"Other partner last_date_logged is {other_ap.get_last_date_logged()}")
                other_member_obj : discord.User = ctx.guild.get_member(ap.other_member)
                await other_member_obj.send(f"{other_member_obj}, your Accountability Partner has logged for today!\nPlease log today to complete the day and extend your streak!")
        else:
            log_embed.color = discord.Color.red()
            log_embed.add_field(name=f"{ctx.author} Log Status:", value="You forgot to log yesterday!", inline=False)
            log_embed.add_field(name=f"Days Logged by You:", value=ap.get_log_streak(), inline=False)
            log_embed.add_field(name=f"Days Completed by Both Partners:", value=ap.get_completion_streak(), inline=False)
            log_embed.add_field(name=f"Points Gained:", value=0, inline=False)
        print("Sending log_embed now.")
        await ctx.send(embed=log_embed)
        try:
            await ctx.send(embed=completed_embed)
        except:
            print("completed_embed not built.")

    async def log_yesterday(self, ctx, ap: AccountabilityPartnership, *args):
        print(f"\nReceived log yesterday command from {ctx.author}")
        status = ap.log_yesterday()
        print(f"Status was {status}")
        log_embed = discord.Embed(title="Accountability Partnership", description=f"<@{ap.primary_member}> and <@{ap.other_member}>")
        if status == "Paused":
            print("Building paused embed now.")
            log_embed.color = discord.Color.red()
            log_embed.add_field(name=f"Partnership Status:", value="Your Partnership is Currently Paused! Use !a resume to resume your partnership.", inline=False)
        elif status == "already logged":
            log_embed.color = discord.Color.red()
            log_embed.add_field(name=f"Log Status:", value="Already Logged", inline=False)
            log_embed.add_field(name=f"Days Logged by You:", value=ap.get_log_streak(), inline=False)
            log_embed.add_field(name=f"Days Completed by Both Partners:", value=ap.get_completion_streak(), inline=False)
        elif status == "successful":
            log_embed.color = discord.Color.green()
            log_embed.add_field(name=f"Log Status:", value="Successful", inline=False)
            log_embed.add_field(name=f"Days Logged by You:", value=ap.get_log_streak(), inline=False)
            log_embed.add_field(name=f"Days Completed by Both Partners:", value=ap.get_completion_streak(), inline=False)
            # embed.add_field(name=f"Points Gained:", value={True: 2, False: 0}[ap.added_points], inline=False)
            if ap.added_points:
                completed_embed = discord.Embed(title=f"Accountability Day {ap.get_completion_streak()} Completed!", description=f"<@{ap.primary_member}> and <@{ap.other_member}>", color=discord.Color.gold())
                completed_embed.add_field(name=f"Points Gained by Both Partners Yesterday:", value=2)
                completed_embed.add_field(name=f"{ctx.author} Total Points:", value=f"{get_points_by_id(ctx.author.id)}")
                completed_embed.add_field(name=f"{await ctx.guild.fetch_member(ap.other_member)} Total Points:", value=f"{get_points_by_id(ap.other_member)}")
            # await ctx.send("You have successfully logged your Accountability Partnership for yesterday!")
            other_ap = ap.get_other_member_ap()
            if other_ap is None: await ctx.send("There's been a glitch. Please contact Elias.")
            elif ap.date_obj_from_str(ap.get_last_date_logged()) > ap.date_obj_from_str(other_ap.get_last_date_logged()):
                # send reminder
                print(f"Other partner last_date_logged is {other_ap.get_last_date_logged()}")
                other_member_obj : discord.User = ctx.guild.get_member(ap.other_member)
                await other_member_obj.send(f"{other_member_obj}, your Accountability Partner has logged for yesterday!\nPlease log yesterday to complete the day and extend your streak!")
        await ctx.send(embed=log_embed)
        try:
            await ctx.send(embed=completed_embed)
        except:
            pass

    async def end_partnership(self, ctx, *args):
        ap = AccountabilityPartnership.from_member_id(ctx.author.id)
        if ap is None:
            await ctx.send("You're not currently in an Accountability Partnership!")
        else:
            await ctx.send(f"<@{ap.primary_member}> and <@{ap.other_member}>, your Accountability Partnership has ended.")

            with open("cogs/accountability.json", "r") as read:
                accountability_partnerships = json.load(read)
            print("before deletion", accountability_partnerships)
            del accountability_partnerships[str(ap.primary_member)]
            del accountability_partnerships[str(ap.other_member)]
            print("after deletion", accountability_partnerships)
            with open("cogs/accountability.json", "w") as write:
                json.dump(accountability_partnerships, write, indent=2)

    async def pause(self, ctx, *args):
        ap = AccountabilityPartnership.from_member_id(ctx.author.id)
        if ap:
            ap.pause_partnership()
            await ctx.send(f"{ctx.author}, your Accountability Partnership has been paused.")
            other_member_obj : discord.User = ctx.guild.get_member(ap.other_member)
            await other_member_obj.send(f"{ctx.author} has paused your Accountability Partnership.")

    async def resume(self, ctx, *args):
        ap = AccountabilityPartnership.from_member_id(ctx.author.id)
        if ap:
            ap.resume_partnership()
            await ctx.send(f"{ctx.author}, your Accountability Partnership has been resumed!")
            other_member_obj : discord.User = ctx.guild.get_member(ap.other_member)
            await other_member_obj.send(f"{ctx.author} has resumed your Accountability Partnership!")


async def setup(client):
    await client.add_cog(Accountability(client, accountability_channel_id))

async def get_member_obj_from_arg(ctx, arg):
    invited_member_obj = ctx.guild.get_member_named(arg)
    if invited_member_obj is None:
        # check if they mentioned the person
        if arg.startswith("<@") and arg.endswith(">"):
            invited_member_id = arg[2:-1]
            invited_member_obj = await ctx.guild.fetch_member(invited_member_id)
    return invited_member_obj

def get_points_by_id(member_id) -> int:
    with open("cogs/eco.json", "r") as f:
        user_eco = json.load(f)
    if str(member_id) not in user_eco:
        user_eco[str(member_id)] = {}
        user_eco[str(member_id)]["Growth Points"] = 0

        with open("cogs/eco.json", "w") as f:
            json.dump(user_eco, f, indent=4)
    return user_eco[str(member_id)]["Growth Points"]