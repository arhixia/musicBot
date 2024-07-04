import asyncio

import discord
from discord.ext import commands
import yt_dlp as youtube_dl
from collections import deque
from config import token 

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
queue = deque()  # Очередь для хранения треков
is_playing = False  # Переменная для отслеживания состояния воспроизведения


@bot.event
async def on_ready():
    print(f'Bot {bot.user} has connected to Discord!')


@bot.command(name='join', help='Bot joins the voice channel')
async def join(ctx):
    if not ctx.author.voice:
        await ctx.send(f'{ctx.author.name} is not connected to a voice channel')
        return

    channel = ctx.author.voice.channel
    await channel.connect()


@bot.command(name='leave', help='Bot leaves the voice channel')
async def leave(ctx):
    voice_client = ctx.voice_client
    if voice_client:
        await voice_client.disconnect()
        await ctx.send("Bot left the voice channel")
    else:
        await ctx.send("Bot is not in a voice channel")


@bot.command(name='play', help='Play a song from YouTube and add to queue')
async def play(ctx, *, search: str):
    global is_playing

    if not ctx.voice_client:
        await ctx.send("Bot is not in a voice channel. Use !join to make the bot join a voice channel first.")
        return

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist': True,
        'quiet': False,  # Включение вывода подробной информации для отладки
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{search}", download=False)
            if 'entries' in info:
                info = info['entries'][0]
            URL = info['url']

        queue.append((URL, info))

        if not is_playing:
            await play_song(ctx, info)
            is_playing = True

        await ctx.send(f'Added to queue: {info["title"]}')

    except Exception as e:
        await ctx.send(f'An error occurred: {str(e)}')


@bot.command(name='skip', help='Skip the current song')
async def skip(ctx):
    global is_playing

    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await ctx.send("Bot is not currently playing any song.")
        return

    ctx.voice_client.stop()
    await ctx.send("Skipped the current song.")

    if len(queue) > 0:
        next_song = queue.popleft()
        await play_song(ctx, next_song[1])
    else:
        is_playing = False


async def play_song(ctx, info):
    global is_playing

    URL, title = info['url'], info['title']

    ctx.voice_client.play(discord.FFmpegPCMAudio(URL))
    ctx.voice_client.source = discord.PCMVolumeTransformer(ctx.voice_client.source)
    ctx.voice_client.source.volume = 0.5

    embed = discord.Embed(title="Now playing", description=f"Now playing: {title}", color=discord.Color.green())
    embed.add_field(name="Uploader", value=info['uploader'])
    embed.add_field(name="Duration", value=info['duration'])

    await ctx.send(embed=embed)

    while ctx.voice_client.is_playing():
        await asyncio.sleep(1)

    if len(queue) > 0:
        next_song = queue.popleft()
        await play_song(ctx, next_song[1])
    else:
        is_playing = False


bot.run(token)
