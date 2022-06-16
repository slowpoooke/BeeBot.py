# reactions.py
import os
import discord
import random
import requests
import json

from discord.ext import commands
from typing import Optional
from dotenv import load_dotenv

# get tenor_key from .env file
load_dotenv()
TENOR_KEY = os.getenv('TENOR_KEY')

# get current directory
current_directory = os.path.dirname(os.path.realpath(__file__))
# role specific names
role_specific_command_name = 'Bot Commander'
owner_specific_command_name = 'Server Owner'

# reactions class
class reactions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # *********************************************************************************************************************
    # bot command to show bee facts
    # *********************************************************************************************************************
    @commands.command(name='facts', aliases=['fact'], help='~ Bee facts!')
    async def facts(self, ctx):
        # get resources directory
        resources_directory = "/".join(list(current_directory.split('/')[0:-2])) + '/resource_files'
        # get image directory
        img_directory = resources_directory + '/image_files/bee_facts_images'
        fact_images = random.choice([
            x for x in os.listdir(img_directory)
            if os.path.isfile(os.path.join(img_directory, x))
        ])
        # credits:
        # idea from https://github.com/SamKeathley/BeeBot
        # additional facts from https://www.sciencelearn.org.nz/resources/2002-bees-fun-facts
        with open(resources_directory + '/text_files/bee_facts.txt', 'r') as file:
            fact_quotes = file.readlines()
            fact_message = random.choice(fact_quotes)

        await ctx.send('{}'.format(fact_message),
                    file=discord.File('resource_files/image_files/bee_facts_images/{}'.format(fact_images)))

    # *********************************************************************************************************************
    # bot command to pick random colour
    # *********************************************************************************************************************
    @commands.command(name='pickcolour', aliases=['pickcolor', 'colour', 'color'],
                help='~ Picks a colour. (Typically chroma colours)')
    async def colour(self, ctx):
        colours_quotes = [
            'Red', 'Orange', 'Yellow', 'Green', 'Light Blue', 'Indigo', 'Purple', 'White', 'Black', 'Pink', 'Rainbow']
        colours_message = random.choice(colours_quotes)
        await ctx.send(colours_message)

    # *********************************************************************************************************************
    # bot command to wish someone a Happy Birthday
    # *********************************************************************************************************************
    @commands.command(name='happybirthday', aliases=['hbd', 'birthday'],
                help='~ Wishes someone a Happy Birthday! (Try a mention!)')
    async def hbd(self, ctx, *, member_name: Optional[str]):
        if member_name == None:
            member_name = ''
        else:
            member_name = ' ' + member_name
        hbd_quotes = [
            'HAPPY BIRTHDAY{}!!!!!  :partying_face: :birthday: :tada:'.format(member_name),
            'Wishing you a Happy Birthday{}! :relieved: :birthday: :tada:'.format(member_name),
            'May all your birthday wishes come true{} — except for the illegal ones! :birthday: :tada: :neutral_face:'.format(member_name)
        ]
        hbd_message = random.choice(hbd_quotes)
        await ctx.send(hbd_message)

    # *********************************************************************************************************************
    # bot command to flip coin
    # *********************************************************************************************************************
    @commands.command(name='coinflip', aliases=['coin', 'coins', 'flip', 'flips'], help='~ Simulates coin flip.')
    async def coin_flip(self, ctx, number_of_coins: Optional[int]):
        try:
            # empty message
            cf_message = ''
            # default 1 coin
            if number_of_coins == None:
                number_of_coins = 1
            if number_of_coins > 300 or number_of_coins < 1:
                await ctx.send('Sorry! The coin is broken. :cry: Try again!')
            else:
                coin_flip_ht = [
                    'Heads, ',
                    'Tails, '
                ]
                cf_quotes = [
                    'You coin flip(s) were:\n',
                    'Clink, spin, spin, clink:\n',
                    'Heads or Tails? :open_mouth:\n',
                    'I wish you good RNG :relieved:\n',
                    ':coin:\n'
                ]
                # add coin flips to string
                for i in range(number_of_coins):
                    cf_message = cf_message + random.choice(coin_flip_ht)
                await ctx.send('{}{}'.format(random.choice(cf_quotes), cf_message[:-2]))
        except:
            # if out of bounds of bot's capability
            await ctx.send('Sorry! The coin is broken. :cry: Try again!')

    # *********************************************************************************************************************
    # bot command to roll dice (no specification is an auto 1D6)
    # *********************************************************************************************************************
    @commands.command(name='rolldice', aliases=['diceroll', 'roll', 'dice'],
                help='~ Simulates rolling dice. (Auto: 1D6)')
    async def roll(self, ctx, number_of_dice: Optional[int], number_of_sides: Optional[int]):
        try:
            # default 1D6 dice
            if number_of_dice == None:
                number_of_dice = 1
            if number_of_sides == None:
                number_of_sides = 6
            if number_of_dice > 500 or number_of_dice < 1 or number_of_sides < 1:
                await ctx.send('Sorry! The dice is broken. :cry: Try again! ')
            else:
                dice = [
                    str(random.choice(range(1, number_of_sides + 1)))
                    for _ in range(number_of_dice)
                ]
                rd_quotes = [
                    'Your dice roll(s) were:\n',
                    'Clack, rattle, clatter:\n',
                    'Highroller?!? :open_mouth:\n',
                    'I wish you good RNG :relieved:\n',
                    ':game_die:\n',
                    ':skull: + :ice_cube:\n'
                ]
                rd_message = random.choice(rd_quotes)
                await ctx.send('{}'.format(rd_message) + ', '.join(dice))
        except:
            # if out of bounds of bot's capability
            await ctx.send('Sorry! The dice is broken. :cry: Try again! ')

    # *********************************************************************************************************************
    # bot command to send gif/tenor
    # *********************************************************************************************************************
    @commands.command(name='gif', aliases=['giphy', 'tenor'], help='~ Random gif from Tenor.')
    # only specific roles can use this command
    @commands.has_role(role_specific_command_name)
    async def gif(self, ctx, *, search: Optional[str]):
        # search 'bees' if no given search
        if search == None:
            search = 'bees'
        # set discord.Embed colour to blue
        embed = discord.Embed(colour=discord.Colour.blue(), title='GIF from Tenor for \"{}\"'.format(search))
        # make the search, url friendly by changing all spaces into "+"
        search.replace(' ', '+')
        # api.tenor website for given search
        # settings: ContentFilter = medium (PG)
        url = 'https://api.tenor.com/v1/search?q={}&key={}&ContentFilter=medium'.format(search, TENOR_KEY)
        # get url info
        get_url_info = requests.get(url)
        # 200 status_code means tenor is working
        if get_url_info.status_code == 200:
            # checking for results
            json_search = get_url_info.json()
            json_check = json_search['next']
            if json_check == "0":
                await ctx.send("Sorry! Couldn't find any gifs for {}! :cry:".format(search))
            else:
                # load json to get url data
                data = json.loads(get_url_info.text)
                # random choice between 0 and min of "9 or len(data['results'])"
                gif_choice = random.randint(0, min(9, len(data['results'])))
                # get gif result
                result_gif = data['results'][gif_choice]['media'][0]['gif']['url']
                # embed gif and send
                embed.set_image(url=result_gif)
                await ctx.send(embed=embed)
        # 404 status_code means tenor is not working/down
        elif get_url_info.status_code == 404:
            await ctx.send("Sorry! Tenor is not working at the moment! :cry:")

def setup(bot):
    bot.add_cog(reactions(bot))