# games.py

from ast import alias
import os
import discord
import random
import numpy as np
import json

from discord.ext import commands
from discord import Embed
from typing import Optional

# get current directory
current_directory = os.path.dirname(os.path.realpath(__file__))
# role specific names
role_specific_command_name = 'Bot Commander'
owner_specific_command_name = 'Server Owner'

# games class
class games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    # *********************************************************************************************************************
    # bot command to split teams
    # *********************************************************************************************************************
    @commands.command(name='splitteam', aliases=['teamsplit', 'maketeams', 'maketeam', 'pickteams', 'pickteam', 'teams', 'team', '📋'],
                help='📋 Splits members in voice channel into teams. [Auto: 2, Max teams: 101]')
    async def split_team(self, ctx, number_of_teams: Optional[int]):
        max_teams = 101
        team_number = 0
        players_list = []
        teams_list = []

        # check for members in voice call
        if ctx.message.author.voice is None:
            await ctx.send('An error has occurred! :confounded: Try joining a voice channel! :slight_smile:')
        else:
            # set "number_of_teams" to 2 if none
            if number_of_teams == None:
                number_of_teams = 2
            if number_of_teams <= max_teams and number_of_teams > 0:
                # create a "players_list" for members in the voice channel
                channel = ctx.message.author.voice.channel
                for member in channel.members:
                    user = member.display_name
                    players_list.append(user)
                # randomize the elements of the list 1 to "len(channel.members)" times
                for i in range(random.randint(1, len(channel.members))):
                    random.shuffle(players_list)
                # split the teams into the number of teams
                team_splitting = np.array_split(players_list, number_of_teams)
                # create a "team_list" for the split teams
                for i in range(len(team_splitting)):
                    # checking empty
                    # if team_splitting[i]:
                    quote_players = ''
                    for j in range(len(team_splitting[i])):
                        if team_splitting[i][j]:
                            quote_players = quote_players + f'{team_splitting[i][j]}, '
                    teams_list.append(quote_players)

                # create an embed with all the teams
                embed = Embed(title="The Teams:",
                    colour=ctx.author.colour)

                for teams in range(len(teams_list)):
                    team_number += 1
                    # check if element is not empty
                    if teams_list[teams]:
                        # add a new "Team" field to the embed
                        embed.add_field(name=f"Team {team_number}:", value=f"{teams_list[teams][:-2]}", inline=False)

                await ctx.send(embed=embed)
            else:
                await ctx.send('Sorry! Your number is out of bounds! :cry: Try again! [Max teams: 101]')

    # *********************************************************************************************************************
    # bot command to pick a game from an excel sheet of games with number of player specification
    # *********************************************************************************************************************
    @commands.command(name='pickgame', aliases=['🎮'], help='🎮 Picks a game to play. [Auto: Number of people in voice call]')
    async def pick_game(self, ctx, number_of_players: Optional[int]):
        if number_of_players == None:
            if ctx.message.author.voice is not None:
                # if "number_of_players" is none, then get the "number_of_players" in the voice channel of the author
                channel = ctx.message.author.voice.channel
                number_of_players = len(channel.members)
            # else number_of_players was 0
            else:
                await ctx.send('An error occurred! :thinking:\nTry adding a number after "pickgame" '
                        'or joining a voice channel! :slight_smile:')

        # get games.json file
        games_json_path = "/".join(list(current_directory.split('/')[0:-2])) + '/resource_files/json_files/games.json'
        with open(games_json_path) as games_json:
            games = json.load(games_json)
            
            final_games_list = []
            # iterate through games dictionary
            for key in games:
                if games[key]['min'] <= number_of_players and games[key]['max'] >= number_of_players:
                    final_games_list.append(key)  

        # picking a random game from the final_games_list
        random_game = random.choice(final_games_list)


        pg_quotes = [
            f'Have you tried ***{random_game}***? :smile:',
            f'Why not try ***{random_game}***? :open_mouth:',
            f'I recommend ***{random_game}***! :liar:',
            f'I might not have friends, but your friends can play ***{random_game}***! :smiling_face_with_tear:'
        ]
        pg_message = random.choice(pg_quotes)
        await ctx.send(pg_message)

def setup(bot):
    bot.add_cog(games(bot))