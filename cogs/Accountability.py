import discord
from discord.ext import commands, tasks
import os
import json
import datetime
from dateutil.relativedelta import relativedelta


class AccountabiltyPartnership:
    def __init__(self, original_member, invited_member):
        #dm invited member
        pass

    @staticmethod
    def fetch_accountability_partnership(member_obj):
        pass

client = commands.Bot(command_prefix='!', intents=discord.Intents.all())

class Accountability(commands.Cog):
    def __init__(self, client):
        self.client = client
        with open("cog/open_accountability_invitations.json", "r") as f:
            self.open_invitations = json.load(f)

    @tasks.loop(hours=1)
    def save_open_invitations(self):
        pass

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} is online!")

    @commands.command(aliases=["a"], pass_context=True)
    async def accountability(self, ctx, *args):
        if args[0].lower() == "start" and len(args) > 1:
            print(args)
            invited_member_str = args[1]
            invited_member_obj = ctx.guild.get_member_named(args[1])
            if invited_member_obj is None:
                # check if they mentioned the person
                if invited_member_str.startswith("<@") and invited_member_str.endswith(">"):
                    invited_member_id = invited_member_str[2:-1]
                    invited_member_obj = await ctx.guild.fetch_member(invited_member_id)

            if invited_member_obj is None:
                await ctx.send(f"{ctx.author}, please try your command again.")
                return

            invited_member_id = invited_member_obj.id

            # if invited_member_obj == ctx.author:
                # await ctx.send(f"{ctx.author}, you cannot invite yourself to an Accountability Partnership!")

            if ctx.author.id in self.open_invitations and self.open_invitations[ctx.author.id] == invited_member_id:
                await ctx.send(f"{ctx.author}, you have already invited {invited_member_obj} to an Accountability Partnership.")
            elif invited_member_id in self.open_invitations and self.open_invitations[invited_member_id] == ctx.author.id:
                # members have succesfully invited each other to Accountability Partnership
                self.start_accountability_partnership(invited_member_id, ctx.author.id)
            else:
                await ctx.send(f"{ctx.author} has invited {invited_member_obj} to participate in an Accountability Partnership!")
                self.open_invitations[ctx.author.id] = invited_member_obj.id
                await invited_member_obj.send(f"{invited_member_obj}, {ctx.author} has invited you to an Accountability Partnership!\nType `!accountability start {ctx.author}` in the accountability channel to accept their invitation!\nType `!accountability decline {ctx.author}` if you choose to decline.")
        else:
            await ctx.send("You forgot to input arguments!")

    def start_accountability_partnership(self, original_member, invited_member):
        pass

async def setup(client):
    await client.add_cog(Accountability(client))