# *********************************************************************************************************************
# lolskinsmodule.py
# - pick_skin command
# *********************************************************************************************************************

import os
import discord
import random
import requests
import cogs.helper.api.league_of_legends_api as lolapi

from discord.ext import commands
from discord import Embed
from typing import Optional


# role specific names
role_specific_command_name = 'Bot Commander'
admin_specific_command_name = 'Bot Admin'

# lolskinsmodule class


class lolskinsmodule(commands.Cog, name="LoLSkinsModule", description="pickskin"):
    def __init__(self, bot):
        self.bot = bot

    # *********************************************************************************************************************
    # bot command pick a random skin for champion
    # *********************************************************************************************************************
    @commands.command(name='pickskin', aliases=['skinlol', 'lolskin', 'skinpick', 'champskin', 'skinchamp', '👗'],
                      help='👗 Pick a random skin for a champion! [Auto: random champ]')
    # only specific roles can use this command
    @commands.has_role(role_specific_command_name)
    async def pick_skin(self, ctx, *, lol_champion: Optional[str]):
        # get current lol version for region
        champions_version = lolapi.get_version()['n']['champion']
        champ_list = lolapi.get_champion_list(champions_version)['data']
        if lol_champion == None:
            lol_champion = random.choice(list(champ_list))
        else:
            # format string
            lol_champion = lol_champion.replace(
                "'", '').lower().title().replace(' ', '').strip('"')
        if lol_champion not in champ_list:
            await ctx.send("Sorry! An error has occurred! :cry: Check your spelling and try again! :slight_smile:")
        else:
            # API champion info
            response = requests.get(
                f'http://ddragon.leagueoflegends.com/cdn/{champions_version}/data/en_US/champion/{lol_champion}.json')
            champion_info = response.json()['data'][lol_champion]
            # get skin number dict
            num_dict = {}
            for skin in champion_info['skins']:
                num_dict[skin['num']] = skin['name']
            skin_key = random.choice(list(num_dict))

            # *********
            # | embed |
            # *********
            embed = Embed(title=num_dict.get(skin_key),
                          description=champion_info['title'],
                          colour=discord.Colour.random())
            # embed image
            img_url = f'http://ddragon.leagueoflegends.com/cdn/img/champion/splash/{lol_champion}_{skin_key}.jpg'
            embed.set_image(url=img_url)
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(lolskinsmodule(bot))
