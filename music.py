from http.client import HTTPException
import discord as dc
import asyncio
from discord.ext import commands
import youtube_dl
from youtube_search import YoutubeSearch
from logs import log


class SoundQueue:
    def __init__(self):
        self.q = []

    def enqueue(self, elem):
        self.q.append(elem)

    def dequeue(self, elem=0):
        try:
            return self.q.pop(elem)
        except IndexError:
            return None

    def size(self):
        return len(self.q)

    def empty(self):
        self.q.clear()

    def isEmpty(self):
        return len(self.q) == 0

    def getQueueState(self):
        queueString = ""
        for index, elem in enumerate(self.q):
            duration = int(elem['duration'])
            queueString += "{}. {} ({}:{})\n".format(index+1, elem['title'], int(duration/60), duration%60)
        return queueString.strip()  

class Music(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = SoundQueue()

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("Gdzie jest głośnik?!")
        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()
            self.queue.empty()
        elif ctx.voice_client.is_playing():
            await ctx.send("Z A M K N I J  R Y J")
        else:
            await ctx.voice_client.move_to(voice_channel)

    @commands.command()
    async def stop(self, ctx):
        if ctx.author.voice.channel is not ctx.voice_client.channel or not ctx.voice_client.is_playing():
            await ctx.send("Tam nikogo nie ma")
        else:
            self.queue.empty()
            ctx.voice_client.stop()

    @commands.command()
    async def pause(self, ctx):
        if ctx.author.voice.channel is not ctx.voice_client.channel or not ctx.voice_client.is_playing():
            await ctx.send("Tam nikogo nie ma")
        else:
            ctx.voice_client.pause()            

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client is not None and ctx.author.voice.channel == ctx.voice_client.channel and not ctx.voice_client.is_playing():
            ctx.voice_client.resume()       

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client is not None and ctx.author.voice.channel == ctx.voice_client.channel:
            ctx.voice_client.stop()
               
    @commands.command()
    async def dc(self, ctx):
        if ctx.voice_client is not None and ctx.author.voice.channel == ctx.voice_client.channel:
            self.queue.empty()
            await ctx.voice_client.disconnect()
        else:
            await ctx.send("Z A M K N I J  R Y J")

    async def run(self, ctx, src):
        ctx.voice_client.play(src, after=(lambda x=None: asyncio.run_coroutine_threadsafe(self.check_for_next(ctx), self.client.loop).result()))     

    async def check_for_next(self, ctx):
        if self.queue.size() > 0:
            await self.start(ctx, self.queue.dequeue())

    def prepare(self, ctx, query):
        try:
            YDL_OPTIONS = {'format': "bestaudio", 'noplaylist':'True'}
            with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
                try:
                    return ydl.extract_info(query, download=False) 
                except youtube_dl.utils.DownloadError:
                    new_url = "https://www.youtube.com{}".format(YoutubeSearch(query, max_results=1).to_dict()[0]["url_suffix"])
                    return ydl.extract_info(new_url, download=False)
        except Exception as e:
            log("music.prepare", query, e)

    async def start(self, ctx, info):
        try:
            FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 3',
                            'options': '-vn'}
            url2 = info['formats'][0]['url']
            source = await dc.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
            await self.join(ctx)
            await self.run(ctx, source)
            await ctx.send("Teraz leci: \n{}".format(info["title"]))   
        except Exception as e:
            log("music.prepare", str(info), e)                      

    @commands.command()
    async def play(self, ctx, url, *args):
        query = url
        if len(args) > 0:
            query += ' '.join(args)
        result = self.prepare(ctx, query)
        await self.start(ctx, result)

    @commands.command()
    async def add(self, ctx, url, *args):
        query = url
        if len(args) > 0:
            query += ' ' + ' '.join(args)
        if ctx.voice_client is None or not ctx.voice_client.is_playing():
            await self.play(ctx, query)
        else:
            self.queue.enqueue(self.prepare(ctx, query))

    @commands.command()
    async def this(self, ctx):
        if ctx.voice_client is None or not ctx.voice_client.is_playing():
            for activity in ctx.author.activities:
                if str(activity) == "Spotify":
                    spotify_song = activity.title
                    for artist in activity.artists:
                        spotify_song += " {}".format(artist)
                    await self.play(ctx, spotify_song)
                    break              

    @commands.has_role('gajs')                
    @commands.command()
    async def sporting(self, ctx):
        if ctx.voice_client is None or not ctx.voice_client.is_playing():
            await self.play(ctx, "sporting anthem")
    
    @commands.has_role('gajs')
    @commands.command()
    async def lm(self, ctx):
        if ctx.voice_client is None or not ctx.voice_client.is_playing():
            await self.play(ctx, "champions league anthem")

    @commands.has_role('gajs')
    @commands.command()
    async def le(self, ctx):
        if ctx.voice_client is None or not ctx.voice_client.is_playing():
            await self.play(ctx, "europa league anthem")  

    @commands.command()
    async def queue(self, ctx):
        try:
            await ctx.send(self.queue.getQueueState())
        except HTTPException:
            await ctx.send("Ludzie, tu nikogo nie ma")    

    @commands.command()
    async def dequeue(self, ctx, arg=''):
        try:
            index = int(arg)
        except:
            await ctx.send("Chłopie, zdecyduj się!")
        if index > self.queue.size() or index < 1:
            await ctx.send("Chłopie, zdecyduj się!")
        else:
            self.queue.dequeue(index-1)


    @commands.command()
    async def essa(self, ctx):
        import random
        songs = [
            "https://www.youtube.com/watch?v=Sug433bP-mw", # impreza
            "https://www.youtube.com/watch?v=xm_ujA1CXCc", # testarossa
            "https://www.youtube.com/watch?v=iewMEY-66yw", # kokaina
            "https://youtu.be/3dHpEfmegOA", # harnaś ice tea
            "https://youtu.be/i92EzcnOMJY" # bandyta
        ]
        comms = [
            "Ale mam esse :cowboy: :call_me: ",
            "Ktoś zajebał misclicka",
            "Ogarniemy stary :sunglasses: ",
        ]
        await ctx.send(random.choice(comms))
        await self.play(ctx, random.choice(songs))


def setup(client):
    asyncio.run(client.add_cog(Music(client)))
