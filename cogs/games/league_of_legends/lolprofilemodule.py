# *********************************************************************************************************************
# lolprofilemodule.py
# - lol_profile command
# - lol_mastery command
# - lol_rank command
# - lol_champpool command
# - lol_champpooladd command
# - lol_champpoolremove command
# - lol_randomchamp command
# *********************************************************************************************************************

import os
import discord
import random
import cogs.helper.api.league_of_legends_api as lol_api
import cogs.helper.constants.lol_constants as lol_constants
import cogs.helper.helper_functions.beebot_profiles as beebot_profiles

from discord.ext import commands
from discord import Embed
from typing import Optional
from dotenv import load_dotenv
from riotwatcher import LolWatcher, ApiError

# get riot_lol_key from .env file
load_dotenv()
LOL_KEY = os.getenv('RIOT_LOL_KEY')
lol_watcher = LolWatcher(LOL_KEY)
default_region = 'na1'

# role specific names
role_specific_command_name = 'Bot Commander'
admin_specific_command_name = 'Bot Admin'

# Module constants
CHAMP_POOL_KEY = 'champ_pool'

# lolprofilemodule class


class lolprofilemodule(commands.Cog, name="LoLProfileModule", description="lolprofile, lolmastery, lolrank"):
    def __init__(self, bot):
        self.bot = bot

    # *********************************************************************************************************************
    # bot command to show the full profile of a given summoner name (shows rank and mastery)
    # *********************************************************************************************************************
    @commands.command(name='lolprofile', aliases=['profilelol', 'lolp', 'plol', '👤'],
                      help=f"👤 Showcase a summoner\'s league of legends profile.\n\n"
                      f"[Input Region: type \"region:<region>\" (ex: region:kr)]\n"
                      f"[Valid Regions: {', '.join(lol_constants.riot_regions())}]")
    # only specific roles can use this command
    @commands.has_role(role_specific_command_name)
    async def lol_profile(self, ctx, region: Optional[str], *summoner_name):
        summoner_name = list(summoner_name)
        # check region
        region_check = True
        if region == None:
            return await ctx.send("Sorry! You forgot to add any input! :cry: Please try again! :slight_smile:\n")
        if ":" in region:
            region = region[7:]
            if region not in lol_constants.riot_regions():
                region_check = False
                return await ctx.send(f"Sorry! An error has occurred! :cry: Check that you have a valid region! :slight_smile:\n"
                                      f"[Valid Regions: {', '.join(lol_constants.riot_regions())}]")
        else:
            if summoner_name == None:
                summoner_name = region
            else:
                summoner_name = [region] + summoner_name
            region = default_region
        if region_check:
            if not summoner_name:
                return await ctx.send("Sorry! You forgot to add a summoner name! :cry: Please try again! :slight_smile:")
            # check that summoner_name exists
            summoner_check = True
            try:
                # get summoner info
                summoner = lol_watcher.summoner.by_name(
                    region, f"{''.join(summoner_name)}")
            except:
                summoner_check = False
                return await ctx.send("Sorry! The summoner name you inputed doesn't exist! :cry:\n"
                                      "Please try again with a real lol summoner! :slight_smile:")
        if summoner_check:
            # get current lol version for region
            champions_version = lol_api.get_version(region)[
                'n']['champion']
            # get summoner ranks
            ranks = lol_watcher.league.by_summoner(
                region, summoner['id'])
            # get total mastery
            total_mastery = lol_watcher.champion_mastery.scores_by_summoner(
                region, summoner['id'])
            # get top mastery
            top_mastery = lol_watcher.champion_mastery.by_summoner(region, summoner['id'])[
                0]
            # get top mastery champ
            champ_list = lol_api.get_champion_list(
                champions_version)['data']
            top_master_champ_info = ''
            for champion in champ_list:
                if top_mastery['championId'] == int(champ_list[champion]['key']):
                    top_master_champ_info = champion
                    break
            top_master_champ_info = champ_list[top_master_champ_info]
            # *********
            # | embed |
            # *********
            embed = Embed(title=f"{summoner['name']}'s LoL Profile",
                          description=f"Summoner Level: {summoner['summonerLevel']}",
                          colour=ctx.author.colour)
            # embed thumbnail
            thumb_url = f"http://ddragon.leagueoflegends.com/cdn/{champions_version}/img/profileicon/{summoner['profileIconId']}.png"
            embed.set_thumbnail(url=thumb_url)
            # embed fields
            if ranks:
                for rank in ranks:
                    embed.add_field(name=f"{rank['queueType']} Rank:".replace("_", " ").title(),
                                    value=f"{rank['tier'].title()} {rank['rank']} {rank['leaguePoints']}LP\n" +
                                    f"WR: {round((rank['wins']/(rank['wins']+rank['losses']))*100, 2)}% (W{rank['wins']}:L{rank['losses']})", inline=False)
                embed.add_field(
                    name='\u200b', value='\u200b', inline=False)
            fields = [("Total Champion Mastery Score:", f"*{total_mastery}*", False),
                      ("Highest Mastery Champion:",
                       f"*{top_master_champ_info['name']}*", False),
                      ("Mastery Level:",
                       f"*{top_mastery['championLevel']}*", True),
                      ("Mastery Points:", f"*{top_mastery['championPoints']}*", True)]
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
            await ctx.send(embed=embed)

    # *********************************************************************************************************************
    # bot command to show the mastery of a given summoner name
    # *********************************************************************************************************************
    @commands.command(name='lolmastery', aliases=['masterylol', 'lolm', 'mlol', '🎓'],
                      help=f"🎓 Showcase a summoner\'s league of legends mastery.\n\n"
                      f"[Input Region: type \"region:<region>\" (ex: region:kr)]\n"
                      f"[Valid Regions: {', '.join(lol_constants.riot_regions())}]")
    # only specific roles can use this command
    @commands.has_role(role_specific_command_name)
    async def lol_mastery(self, ctx, region: Optional[str], *summoner_name):
        summoner_name = list(summoner_name)
        # check region
        region_check = True
        if region == None:
            return await ctx.send("Sorry! You forgot to add any input! :cry: Please try again! :slight_smile:\n")
        if ":" in region:
            region = region[7:]
            if region not in lol_constants.riot_regions():
                region_check = False
                return await ctx.send(f"Sorry! An error has occurred! :cry: Check that you have a valid region! :slight_smile:\n"
                                      f"[Valid Regions: {', '.join(lol_constants.riot_regions())}]")
        else:
            if summoner_name == None:
                summoner_name = region
            else:
                summoner_name = [region] + summoner_name
            region = default_region
        if region_check:
            if not summoner_name:
                return await ctx.send("Sorry! You forgot to add a summoner name! :cry: Please try again! :slight_smile:")
            # check that summoner_name exists
            summoner_check = True
            try:
                # get summoner info
                summoner = lol_watcher.summoner.by_name(
                    region, f"{''.join(summoner_name)}")
            except:
                summoner_check = False
                return await ctx.send("Sorry! The summoner name you inputed doesn't exist! :cry:\n"
                                      "Please try again with a real lol summoner! :slight_smile:")
        if summoner_check:
            # get current lol version for region
            champions_version = lol_api.get_version()['n']['champion']
            # get total mastery
            total_mastery = lol_watcher.champion_mastery.scores_by_summoner(
                region, summoner['id'])
            # get top mastery
            top_mastery = lol_watcher.champion_mastery.by_summoner(region, summoner['id'])[
                0]
            # get top mastery champ
            champ_list = lol_api.get_champion_list(
                champions_version)['data']
            top_master_champ_info = ''
            for champion in champ_list:
                if top_mastery['championId'] == int(champ_list[champion]['key']):
                    top_master_champ_info = champion
                    break
            top_master_champ_info = champ_list[top_master_champ_info]
            # *********
            # | embed |
            # *********
            embed = Embed(title=f"{summoner['name']}'s LoL Mastery",
                          description=f"Summoner Level: {summoner['summonerLevel']}",
                          colour=ctx.author.colour)
            # embed thumbnail
            thumb_url = f"http://ddragon.leagueoflegends.com/cdn/{champions_version}/img/champion/{top_master_champ_info['id']}.png"
            embed.set_thumbnail(url=thumb_url)
            # embed fields
            fields = [("Total Champion Mastery Score:", f"*{total_mastery}*", False),
                      ("Highest Mastery Champion:",
                       f"*{top_master_champ_info['name']}*", False),
                      ("Mastery Level:",
                       f"*{top_mastery['championLevel']}*", True),
                      ("Mastery Points:", f"*{top_mastery['championPoints']}*", True)]
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
            await ctx.send(embed=embed)

    # *********************************************************************************************************************
    # bot command to show the rank of a given summoner name
    # *********************************************************************************************************************
    @commands.command(name='lolrank', aliases=['ranklol', 'lolr', 'rlol', '🏆'],
                      help=f"🏆 Showcase a summoner\'s league of legends rank.\n\n"
                      f"[Input Region: type \"region:<region>\" (ex: region:kr)]\n"
                      f"[Valid Regions: {', '.join(lol_constants.riot_regions())}]")
    # only specific roles can use this command
    @commands.has_role(role_specific_command_name)
    async def lol_rank(self, ctx, region: Optional[str], *summoner_name):
        summoner_name = list(summoner_name)
        # check region
        region_check = True
        if region == None:
            return await ctx.send("Sorry! You forgot to add any input! :cry: Please try again! :slight_smile:\n")
        if ":" in region:
            region = region[7:]
            if region not in lol_constants.riot_regions():
                region_check = False
                return await ctx.send(f"Sorry! An error has occurred! :cry: Check that you have a valid region! :slight_smile:\n"
                                      f"[Valid Regions: {', '.join(lol_constants.riot_regions())}]")
        else:
            if summoner_name == None:
                summoner_name = region
            else:
                summoner_name = [region] + summoner_name
            region = default_region
        if region_check:
            if not summoner_name:
                return await ctx.send("Sorry! You forgot to add a summoner name! :cry: Please try again! :slight_smile:")
            # check that summoner_name exists
            summoner_check = True
            try:
                # get summoner info
                summoner = lol_watcher.summoner.by_name(
                    region, f"{''.join(summoner_name)}")
            except:
                summoner_check = False
                return await ctx.send("Sorry! The summoner name you inputed doesn't exist! :cry:\n"
                                      "Please try again with a real lol summoner! :slight_smile:")
        if summoner_check:
            # get current lol version for region
            champions_version = lol_api.get_version(region)[
                'n']['champion']
            # get summoner ranks
            ranks = lol_watcher.league.by_summoner(
                region, summoner['id'])
            # *********
            # | embed |
            # *********
            embed = Embed(title=f"{summoner['name']}'s LoL Rank",
                          description=f"Summoner Level: {summoner['summonerLevel']}",
                          colour=ctx.author.colour)
            if ranks:
                riot_ranks = lol_constants.riot_ranks()
                total_rank = 0
                for rank in ranks:
                    embed.add_field(name=f"{rank['queueType']} Rank:".replace("_", " ").title(),
                                    value=f"{rank['tier'].title()} {rank['rank']} {rank['leaguePoints']}LP\n" +
                                    f"WR: {round((rank['wins']/(rank['wins']+rank['losses']))*100, 2)}% (W{rank['wins']}:L{rank['losses']})", inline=False)
                    # get average_rank
                    rank_key = [k for k, v in riot_ranks.items(
                    ) if v == {'tier': rank['tier'], 'rank': rank['rank']}]
                    total_rank = total_rank + sum(rank_key)
                average_rank = round(total_rank/len(ranks), 0)
                final_rank = riot_ranks.get(int(average_rank))

                embed.add_field(
                    name=f"Average Rank:", value=f"{final_rank['tier'].title()} {final_rank['rank']}", inline=False)
                # embed thumbnail
                file = discord.File(
                    f"resource_files/image_files/riot_images/ranked_emblems/Emblem_{final_rank['tier'].title()}.png", filename="image.png")
                embed.set_thumbnail(url='attachment://image.png')
                await ctx.send(file=file, embed=embed)
            else:
                embed.add_field(name="This summoner has nothing for ranked this season.",
                                value="Maybe it's time?... 👀", inline=False)
                # embed thumbnail
                thumb_url = f"http://ddragon.leagueoflegends.com/cdn/{champions_version}/img/map/map11.png"
                embed.set_thumbnail(url=thumb_url)
                await ctx.send(embed=embed)

    # *********************************************************************************************************************
    # bot command to view the calling user's champion pool
    # *********************************************************************************************************************
    @commands.command(name='lolchamppool', aliases=['lolcp', 'cplol', 'pool', 'champpool', '📝'],
                      help=f"📝 Show the list of champions in your champion pool for each role.\n\n"
                           f"[Input Role: type \"<role>\" (ex: mid)]\n"
                           f"[Valid Roles: {', '.join(lol_constants.lol_roles(include_fill=False))}]")
    # only specific roles can use this command
    @commands.has_role(role_specific_command_name)
    async def lol_champpool(self, ctx, role: Optional[str]):
        # Validate provided input, if any
        valid_roles = lol_constants.lol_roles(include_fill=False)
        if role is not None and role not in valid_roles:
            await ctx.send(f"Specified role '{role}' not in list of valid roles ({', '.join(valid_roles)})!")

        # Retrieve persisted champ pools from beebot profiles. Changes don't matter because they're never saved.
        user = str(ctx.message.author)
        beebot_profiles_data = beebot_profiles.get_beebot_profiles_json()
        user_profile = beebot_profiles_data.get(user, {})
        user_champ_pool = user_profile.get(CHAMP_POOL_KEY, {})

        if role is not None:
            user_champ_pool = {role: user_champ_pool.get(role, [])}

        # *********
        # | embed |
        # *********
        embed = Embed(title=user, colour=ctx.author.colour)
        for role, champions in user_champ_pool.items():
            embed.add_field(name=f'{role.title()}:', value=', '.join(champions), inline=False)
        await ctx.send(embed=embed)

    # *********************************************************************************************************************
    # bot command to add champions to the calling user's champion pool for a given role
    # *********************************************************************************************************************
    @commands.command(name='lolchamppooladd', aliases=['lolcpadd', 'cpaddlol', 'pooladd', 'champpooladd', '✏'],
                      help=f"✏ Add champions to your champion pool for a given role.\n\n"
                           f"[Input Role: type \"<role>\" (ex: mid)]\n"
                           f"[Valid Roles: {', '.join(lol_constants.lol_roles(include_fill=False))}]\n"
                           f"[Input Champions: type names of champions to add, separated by a space, using quotes if "
                           f"the champ name is more than one word (ex: \"miss fortune\" cassiopeia).")
    # only specific roles can use this command
    @commands.has_role(role_specific_command_name)
    async def lol_champpooladd(self, ctx, role: str, *champions):
        # Validate inputs
        valid_roles = lol_constants.lol_roles(include_fill=False)
        if role is not None and role not in valid_roles:
            await ctx.send(f"Specified role '{role}' not in list of valid roles ({', '.join(valid_roles)})!")
        if not champions:
            await ctx.send("You must provide a list of champions to add to your pool")

        # Retrieve persisted champ pools from beebot profiles.
        beebot_profiles_data = beebot_profiles.get_beebot_profiles_json()
        user_profile = beebot_profiles_data.get(str(ctx.message.author), {})
        user_champ_pool = user_profile.get(CHAMP_POOL_KEY, {})
        role_champ_pool = user_champ_pool.get(role, [])

        # Validate specified champions and deduplicate entries
        champ_add_success = False
        champ_add_failed_list = []
        champions_version = lol_api.get_version()['n']['champion']
        champ_list = lol_api.get_champion_list(champions_version)['data']
        for champion_name in champions:
            formatted_champ_name = lol_api.champion_string_formatting(champion_name)
            if formatted_champ_name not in champ_list:
                champ_add_failed_list.append(champion_name)
            else:
                role_champ_pool.append(champ_list[formatted_champ_name]['name'])
                champ_add_success = True

        role_champ_pool = sorted(set(role_champ_pool))

        # Persist the updated profile data
        beebot_profiles.set_beebot_profiles_json(beebot_profiles_data)

        if champ_add_failed_list and champ_add_success:
            invalid_champs = ', '.join(champ_add_failed_list)
            await ctx.send(f"Your {role} champion pool has been updated, but {invalid_champs} could not be added.")
        elif champ_add_failed_list and not champ_add_success:
            invalid_champs = ', '.join(champ_add_failed_list)
            await ctx.send(f"Could not update you {role} champion pool - {invalid_champs} could not be added.")
        else:
            await ctx.send(f"Your {role} champion pool has been updated!")

    # *********************************************************************************************************************
    # bot command to remove a champion from the calling user's champion pool for a given role
    # *********************************************************************************************************************
    @commands.command(name='lolchamppoolremove',
                      aliases=['lolcpremove', 'cpremovelol', 'poolremove', 'champpoolremove', '📃'],
                      help=f"📃 Remove champions from your champion pool for a given role.\n\n"
                           f"[Input Role: type \"<role>\" (ex: mid)]\n"
                           f"[Valid Roles: {', '.join(lol_constants.lol_roles(include_fill=False))}]\n"
                           f"[Input Champions: type names of champions to add separated by a space, using quotes if "
                           f"the champ name is more than one word (ex: \"miss fortune\" cassiopeia).")
    # only specific roles can use this command
    @commands.has_role(role_specific_command_name)
    async def lol_champpoolremove(self, ctx, role: str, *champions):
        # Validate inputs
        valid_roles = lol_constants.lol_roles(include_fill=False)
        if role is not None and role not in valid_roles:
            await ctx.send(f"Specified role '{role}' not in list of valid roles ({', '.join(valid_roles)})!")
        if not champions:
            await ctx.send("You must provide a list of champions to add to your pool")

        # Retrieve persisted champ pools from beebot profiles.
        beebot_profiles_data = beebot_profiles.get_beebot_profiles_json()
        user_profile = beebot_profiles_data.get(str(ctx.message.author), {})
        user_champ_pool = user_profile.get(CHAMP_POOL_KEY, {})
        role_champ_pool = user_champ_pool.get(role, [])

        # Remove champions from the specified role's champ pool if they exist
        champ_remove_success = False
        champ_remove_failed_list = []
        for champion_name in champions:
            try:
                role_champ_pool.remove(champion_name)
                champ_remove_success = True
            except ValueError:
                champ_remove_failed_list.append(champion_name)
        role_champ_pool = sorted(role_champ_pool)

        # Persist the updated profile data
        beebot_profiles.set_beebot_profiles_json(beebot_profiles_data)

        if champ_remove_failed_list and champ_remove_success:
            invalid_champs = ', '.join(champ_remove_failed_list)
            await ctx.send(f"Your {role} champion pool has been updated, but {invalid_champs} could not be removed.")
        elif champ_remove_failed_list and not champ_remove_success:
            invalid_champs = ', '.join(champ_remove_failed_list)
            await ctx.send(f"Could not update you {role} champion pool - {invalid_champs} could not be removed.")
        else:
            await ctx.send(f"Your {role} champion pool has been updated!")

    # *********************************************************************************************************************
    # bot command to choose a random champion from the calling user's champion pool for the given role
    # *********************************************************************************************************************
    @commands.command(name='lolrandomchamp', aliases=['pickchamp', 'randchamp', '🎰'],
                      help=f"🎰 Pick a random champion from your champion pool of the specified role.\n\n"
                           f"[Input Role: type \"<role>\" (ex: mid)]\n"
                           f"[Valid Roles: {', '.join(lol_constants.lol_roles(include_fill=False))}]")
    # only specific roles can use this command
    @commands.has_role(role_specific_command_name)
    async def lol_randomchamp(self, ctx, role: str):
        # Validate role
        valid_roles = lol_constants.lol_roles(include_fill=False)
        if role not in valid_roles:
            await ctx.send(f"Specified role '{role}' not in list of valid roles ({', '.join(valid_roles)})!")

        # Retrieve persisted champ pools from beebot profiles.
        beebot_profiles_data = beebot_profiles.get_beebot_profiles_json()
        user_profile = beebot_profiles_data.get(str(ctx.message.author), {})
        user_champ_pool = user_profile.get(CHAMP_POOL_KEY, {})
        user_role_pool = user_champ_pool.get(role, [])

        # If the user has champions in their pool for that role, pick a random one. Champ names should already be
        # validated when it was inserted.
        if not user_role_pool:
            await ctx.send(f"Your {role} pool is empty! Use \"bb lolchamppooladd\" to add to it.")
        chosen_champ = random.choice(user_role_pool)

        # *********
        # | embed |
        # *********
        formatted_champ_name = lol_api.champion_string_formatting(chosen_champ)
        embed = Embed(title=chosen_champ, colour=discord.Colour.random())
        champions_version = lol_api.get_version()['n']['champion']
        thumb_url = f'http://ddragon.leagueoflegends.com/cdn/{champions_version}/img/champion/{formatted_champ_name}.png'
        embed.set_thumbnail(url=thumb_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(lolprofilemodule(bot))
