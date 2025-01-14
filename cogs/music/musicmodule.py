# *********************************************************************************************************************
# playmusicmodule.py
# codebase: https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34
# *********************************************************************************************************************

import discord
import asyncio
import itertools
import sys
import traceback

from discord.ext import commands
from discord import Embed
from typing import Optional
from async_timeout import timeout
from functools import partial
from youtube_dl import YoutubeDL

# role specific names
role_specific_command_name = 'Bot Commander'
admin_specific_command_name = 'Bot Admin'

ytdlopts = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}

ffmpegopts = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = YoutubeDL(ytdlopts)


class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors."""


class InvalidVoiceChannel(VoiceConnectionError):
    """Exception for cases of invalid Voice Channels."""


# *********************************************************************************************************************
# YTDLSource class
# *********************************************************************************************************************
class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester

        self.title = data.get('title')
        self.web_url = data.get('webpage_url')
        self.thumbnail = data.get('thumbnail')

        # YTDL info dicts (data) have other useful information you might want
        # https://github.com/rg3/youtube-dl/blob/master/README.md

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when you are NOT downloading.
        """
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop, download=False):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        # *********
        # | embed |
        # *********
        embed = Embed(title=f"{data['title']}\n🎶 Added to Queue! 🎶",
                      colour=ctx.author.colour)
        await ctx.send(embed=embed, delete_after=15)

        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title'], 'thumbnail': data['thumbnail']}

        return cls(discord.FFmpegPCMAudio(source), data=data, requester=ctx.author)

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """Used for preparing a stream, instead of downloading.
        Since Youtube Streaming links expire."""
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info,
                         url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester)


# *********************************************************************************************************************
# MusicPlayer class
# *********************************************************************************************************************
class MusicPlayer:
    """A class which is assigned to each guild using the bot for Music.
    This class implements a queue and loop, which allows for different guilds to listen to different playlists
    simultaneously.
    When the bot disconnects from the Voice it's instance will be destroyed.
    """

    __slots__ = ('bot', '_guild', '_channel', '_cog',
                 'queue', 'next', 'current', 'np', 'volume')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None  # Now playing message
        self.volume = .5
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Our main player loop."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(300):  # 5 minutes...
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            if not isinstance(source, YTDLSource):
                # Source was probably a stream (not downloaded)
                # So we should regather to prevent stream expiration
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(f'There was an error processing your song.\n'
                                             f'```css\n[{e}]\n```')
                    continue

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(
                source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))

            # *********
            # | embed |
            # *********
            embed = Embed(title=f"🎵 Now Playing 🎵\n{source.title}",
                          description=f"Requested by: {source.requester}",
                          colour=discord.Colour.random())
            # embed thumbnail
            thumb_url = source.thumbnail
            embed.set_thumbnail(url=thumb_url)
            self.np = await self._channel.send(embed=embed)
            await self.next.wait()

            # Make sure the FFmpeg process is cleaned up.
            source.cleanup()
            self.current = None

            try:
                # We are no longer playing this song...
                await self.np.delete()
            except discord.HTTPException:
                pass

    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))


# *********************************************************************************************************************
# MusicModule class
# *********************************************************************************************************************
class MusicModule(commands.Cog, name="MusicModule", description="BeeBot's Music Bot! Type \"BB help MusicModule\" for options!"):
    """Music related commands."""

    __slots__ = ('bot', 'players')

    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    # *********************************************************************************************************************
    # helper functions
    # *********************************************************************************************************************
    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    async def __local_check(self, ctx):
        """A local check which applies to all commands in this cog."""
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True

    async def __error(self, ctx, error):
        """A local error handler for all errors arising from commands in this cog."""
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send('This command can not be used in Private Messages.')
            except discord.HTTPException:
                pass
        elif isinstance(error, InvalidVoiceChannel):
            await ctx.send('Error connecting to Voice Channel. '
                           'Please make sure you are in a valid channel or provide me with one')

        print('Ignoring exception in command {}:'.format(
            ctx.command), file=sys.stderr)
        traceback.print_exception(
            type(error), error, error.__traceback__, file=sys.stderr)

    def get_player(self, ctx):
        """Retrieve the guild player, or generate one."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player

    # *********************************************************************************************************************
    # bot command to join voice channel
    # *********************************************************************************************************************
    @commands.command(name='join', aliases=['connect', '🔉'],
                      help='🔉 BeeBot joins voice channel!')
    # only specific roles can use this command
    @commands.has_role(role_specific_command_name)
    async def connect_(self, ctx, *, channel: discord.VoiceChannel = None):
        # Connect to voice.
        # Parameters
        # ------------
        # channel: discord.VoiceChannel [Optional]
        #     The channel to connect to. If a channel is not specified, an attempt to join the voice channel you are in
        #     will be made.
        # This command also handles moving the bot to different channels.
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise InvalidVoiceChannel(
                    'Sorry! There\'s no channel to join. :flushed: Please either specify a valid channel or join one! :smile:')
        vc = ctx.voice_client
        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise VoiceConnectionError(
                    f'Moving to channel: <{channel}> timed out.')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise VoiceConnectionError(
                    f'Connecting to channel: <{channel}> timed out.')
        await ctx.send(f'Connected to: **{channel}**', delete_after=15)

    # *********************************************************************************************************************
    # bot command to play music
    # *********************************************************************************************************************
    @commands.command(name='play', aliases=['sing', '▶️'],
                      help='▶️ Plays YouTube audio! [Provide YouTube search or link, Role specific]')
    # only specific roles can use this command
    @commands.has_role(role_specific_command_name)
    async def play_(self, ctx, *, search: Optional[str]):
        # Request a song and add it to the queue.
        # This command attempts to join a valid voice channel if the bot is not already in one.
        # Uses YTDL to automatically search and retrieve a song.
        # Parameters
        # ------------
        # search: str [Required]
        #     The song to search and retrieve using YTDL. This could be a simple search, an ID or URL.
        if search == None:
            await ctx.send('Please provide a YouTube link or YouTube search info! :pleading_face:')
        else:
            if ctx.author.voice is None:
                await ctx.send('Please join a discord channel to use this command! :slight_smile:')
            else:
                await ctx.trigger_typing()
                vc = ctx.voice_client
                if not vc:
                    await ctx.invoke(self.connect_)
                player = self.get_player(ctx)
                # If download is False, source will be a dict which will be used later to regather the stream.
                # If download is True, source will be a discord.FFmpegPCMAudio with a VolumeTransformer.
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=False)
                await player.queue.put(source)

    # *********************************************************************************************************************
    # bot command to pause music
    # *********************************************************************************************************************
    @commands.command(name='pause', aliases=['⏸️'], help='⏸️ Pause current audio playing! [Role specific]')
    # only specific roles can use this command
    @commands.has_role(role_specific_command_name)
    async def pause_(self, ctx):
        # Pause the currently playing song.
        vc = ctx.voice_client
        if not vc or not vc.is_playing():
            return await ctx.send('Sorry! I\'m not currently playing anything! :flushed:')
        elif vc.is_paused():
            return
        vc.pause()
        await ctx.send(f'**{ctx.author.display_name}** paused the song!', delete_after=15)

    # *********************************************************************************************************************
    # bot command to resume audio
    # *********************************************************************************************************************
    @commands.command(name='resume', aliases=['⏯️'], help='⏯️ Resume current audio playing! [Role specific]')
    # only specific roles can use this command
    @commands.has_role(role_specific_command_name)
    async def resume_(self, ctx):
        # Resume the currently paused song.
        vc = ctx.voice_client
        if not vc or not vc.is_connected():
            return await ctx.send('Sorry! I\'m not currently playing anything! :flushed:')
        elif not vc.is_paused():
            return
        vc.resume()
        await ctx.send(f'**{ctx.author.display_name}** resumed the song!', delete_after=15)

    # *********************************************************************************************************************
    # bot command to go to next audio in queue by reaction vote
    # *********************************************************************************************************************
    @commands.command(name='next', aliases=['skip', '⏭️'], help='⏭️ Play the next audio! [Role specific]')
    # only specific roles can use this command
    @commands.has_role(role_specific_command_name)
    async def skip_(self, ctx):
        # Skip the song.
        vc = ctx.voice_client
        if not vc or not vc.is_connected():
            return await ctx.send('Sorry! I\'m not currently playing anything! :flushed:')
        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return
        vc.stop()
        await ctx.send(f'**{ctx.author.display_name}** skipped the song!', delete_after=15)

    # *********************************************************************************************************************
    # bot command to view current queue
    # *********************************************************************************************************************
    @commands.command(name='queue', aliases=['q', 'playlist', '🎶'],
                      help='🎶 View the current queue! [Current and Upcoming 5 songs]')
    async def queue_info(self, ctx):
        # Retrieve a basic queue of upcoming songs.
        vc = ctx.voice_client
        if not vc or not vc.is_connected():
            return await ctx.send('Sorry! I\'m not currently connected to voice! :flushed:')
        player = self.get_player(ctx)
        if not player.current:
            return await ctx.send('There is no audio in the queue! :flushed: Try the "play" command to add a song! :smile:')
        # Grab up to 5 entries from the queue...
        upcoming = list(itertools.islice(player.queue._queue, 0, 5))
        fmt = []
        if upcoming:
            count = 0
            for song in upcoming:
                count += 1
                fmt = fmt + [f"{count}: {song['title']}"]
        # *********
        # | embed |
        # *********
        embed = discord.Embed(title=f'🎶 Current Queue 🎶',
                              colour=ctx.author.colour)
        # embed fields
        embed.add_field(name=f"🎵 Current Song 🎵:",
                        value=vc.source.title, inline=False)
        if fmt:
            embed.add_field(
                name=f"🎶 Upcoming {len(upcoming)} Songs 🎶:", value='\n'.join(fmt), inline=False)
        await ctx.send(embed=embed)

    # *********************************************************************************************************************
    # bot command to view current audio
    # *********************************************************************************************************************

    @commands.command(name='now_playing', aliases=['np', 'current', 'playing', '🎵'],
                      help='🎵 View what\'s playing now!')
    async def now_playing_(self, ctx):
        # Display information about the currently playing song.
        vc = ctx.voice_client
        if not vc or not vc.is_connected():
            return await ctx.send('Sorry! I\'m not currently connected to voice! :flushed:')
        player = self.get_player(ctx)
        if not player.current:
            return await ctx.send('Sorry! I\'m not currently playing anything! :flushed:')
        try:
            # Remove our previous now_playing message.
            await player.np.delete()
        except discord.HTTPException:
            pass
        # *********
        # | embed |
        # *********
        embed = Embed(title=f"🎵 Current song 🎵\n{vc.source.title}",
                      description=f"Requested by: {vc.source.requester}",
                      colour=ctx.author.colour)
        # embed thumbnail
        thumb_url = vc.source.thumbnail
        embed.set_thumbnail(url=thumb_url)
        player.np = await ctx.send(embed=embed)

    # *********************************************************************************************************************
    # bot command to set default volume
    # *********************************************************************************************************************
    @commands.command(name='volume', aliases=['vol', '🔊'],
                      help='🔊 Change the player volume! [Range: 1 to 100]')
    async def change_volume(self, ctx, *, vol: Optional[float]):
        # Change the player volume.
        # Parameters
        # ------------
        # volume: float or int [Required]
        #     The volume to set the player to in percentage. This must be between 1 and 100.
        if vol == None:
            return await ctx.send('Sorry! Please enter a value between 1 and 100. :open_mouth:')
        vc = ctx.voice_client
        if not vc or not vc.is_connected():
            return await ctx.send('Sorry! I\'m not currently connected to voice! :flushed:')
        if not 0 < vol < 101:
            return await ctx.send('Sorry! Please enter a value between 1 and 100. :open_mouth:')
        player = self.get_player(ctx)
        if vc.source:
            vc.source.volume = vol / 100
        player.volume = vol / 100
        await ctx.send(f'**{ctx.author.display_name}** set the volume to **{vol}%**')

    # *********************************************************************************************************************
    # bot command to leave voice channel and deletes queue
    # *********************************************************************************************************************
    @commands.command(name='leave', aliases=['stop', 'deletequeue', 'disconnect', '🔈'],
                      help='🔈 BeeBot leaves voice channel and deletes current queue. [Role specific]')
    # only specific roles can use this command
    @commands.has_role(role_specific_command_name)
    async def stop_(self, ctx):
        # Stop the currently playing song and destroy the player.
        # !Warning!
        #     This will destroy the player assigned to your guild, also deleting any queued songs and settings.
        vc = ctx.voice_client
        if not vc or not vc.is_connected():
            return await ctx.send('Sorry! I\'m not currently playing anything! :thinking:')
        await self.cleanup(ctx.guild)
        vc.disconnect()
        await ctx.send("Okay, I'll leave. :cry:")


def setup(bot):
    bot.add_cog(MusicModule(bot))
