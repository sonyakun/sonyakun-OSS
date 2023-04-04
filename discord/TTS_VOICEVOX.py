import discord
from discord.ext import commands
import json
from typing import Dict
import aiohttp, asyncio
import wave
from voicevox import Client
import datetime
import json
from discord import default_permissions,Option
import os
import uuid
from function.function import get_settings, greetings_re, greetings
from function.db_manager import is_blacklisted
import re

reading_channels = {}

speakers = ["四国めたん","ずんだもん","春日部つむぎ",
"波音リツ","雨晴はう","玄野武宏","白上虎太郎","青山龍星","冥鳴ひまり","九州そら","もち子さん","剣崎雌雄","WhiteCUL","後鬼-人間","後鬼-ぬいぐるみ","No.7-ノーマル","No.7-アナウンス","No.7-読み聞かせ"]

async def auto_complete_speakers(ctx):
    return [rule for rule in speakers if rule.startswith(ctx.value)]

class tts(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.voice_clients: Dict[int, discord.VoiceClient] = {}

    @discord.slash_command(name = "connect", description = "テキスト読み上げを開始します。")
    async def tts_connect(self,ctx):
        global reading_channels
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.respond('先にボイスチャンネルに参加してください')
        else:
            reading_channels[ctx.guild.id] = ctx.channel.id
            vc = await ctx.channel.connect()
            self.voice_clients[ctx.guild.id] = vc
            embed=discord.Embed(title="ボイスチャンネルに接続しました！", description=f"切断は</disconnect:1092593471786864691>を実行してください。", color=discord.Colour.green())
            await ctx.respond(embed=embed)
            src = discord.FFmpegPCMAudio("./tts/voice_template/" + "on_connected" + ".wav")
            vc.play(src)

    @discord.slash_command(name = "disconnect", description = "テキスト読み上げを終了します。")
    async def tts_disconnect(self,ctx):
        global reading_channels
        vc = self.voice_clients.get(ctx.guild.id)
        reading_channels.pop(ctx.guild.id)
        del self.voice_clients[ctx.guild.id]
        await vc.disconnect()
        embed=discord.Embed(title="切断しました", description=f"ボイスチャンネルから切断しました。", color=discord.Colour.green())
        await ctx.respond(embed=embed)

#    @discord.slash_command(name = "speaker", description = "読み上げに利用する音声を変更します。")
#    async def tts_speaker(self,ctx, speaker : Option(str, description = "話者の名前", autocomplete=auto_complete_speakers, required=True)):
#        with open('./tts/config/config.json', 'r') as f:
#            df = json.load(f)
#        with open('./tts/config/config.json', 'w') as f:
#            speak = {
#                "四国めたん" : 2,
#               "ずんだもん" : 3,
#               "春日部つむぎ" : 8,
#               "波音リツ" : 9,
#               "雨晴はう" : 10,
#               "玄野武宏" : 11,
#               "白上虎太郎" : 12,
#               "青山龍星" : 13,
#               "冥鳴ひまり" : 14,
#               "もち子さん" : 20,
#               "剣崎雌雄" : 21,
#               "WhiteCUL" : 23,
#               "後鬼-人間" : 27,
#               "後鬼-ぬいぐるみ" : 28,
#               "No.7-ノーマル" : 29,
#               "No.7-アナウンス" : 30,
#               "No.7-読み聞かせ" : 31
#           }
#            df["voice"][str(ctx.author.id)] = speak[speaker]
#            json.dump(df, f, ensure_ascii=False, indent=4)
#            embed=discord.Embed(title=f"{ctx.author.name}の話者を「{speaker}」に変更しました！", description=f"", color=discord.Colour.green())
#            await ctx.respond(embed=embed)

    @commands.Cog.listener(name = "on_voice_state_update")
    async def tts_join_leave(self, member, before, after):
        file_uuid = str(uuid.uuid4())
        vc: discord.VoiceClient = self.voice_clients.get(member.guild.id)
        if  (before.channel != after.channel):
            if before.channel is None: 
                msg = f'{member.nick}が接続しました。'
                async with Client() as client:
                    audio_query = await client.create_audio_query(msg, speaker=3)
                    with open("./tts/" + file_uuid + ".wav", "wb") as f:
                        f.write(await audio_query.synthesis(speaker=1))
                src = discord.FFmpegPCMAudio("./tts/" + file_uuid + ".wav")
                vc.play(src)
                await asyncio.sleep(3)
                os.remove("./tts/" + file_uuid + ".wav")
            elif after.channel is None: 
                msg = f'{member.nick}が切断しました。'
                async with Client() as client:
                    audio_query = await client.create_audio_query(msg, speaker=3)
                    with open("./tts/" + file_uuid + ".wav", "wb") as f:
                        f.write(await audio_query.synthesis(speaker=1))
                src = discord.FFmpegPCMAudio("./tts/" + file_uuid + ".wav")
                vc.play(src)
                await asyncio.sleep(3)
                os.remove("./tts/" + file_uuid + ".wav")

    async def delete(file_uuid):
        while True:
            try:
                os.remove("./tts/" + file_uuid + ".wav")
                break
            except PermissionError:
                os.remove("./tts/" + file_uuid + ".wav")
        return

    @commands.Cog.listener(name = "on_message")
    async def tts(self, message):
        if message.author.bot:
            return

        if await is_blacklisted(message.author.id):
            return
        pattern = r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
        content = re.sub(pattern, "リンク省略", message.content)
        try:
            file_uuid = str(uuid.uuid4())
            vc: discord.VoiceClient = self.voice_clients.get(message.guild.id)
            if message.channel.id == reading_channels[message.guild.id]:
                t_delta = datetime.timedelta(hours=9)
                JST = datetime.timezone(t_delta, 'JST')
                now = datetime.datetime.now(JST)
                with open('./tts/config/config.json', 'r') as f1:
                    try:
                        print("generating...")
                        df = json.load(f1)
                        async with Client() as client:
                            print(df["voice"][str(message.author.id)])
                            audio_query = await client.create_audio_query(content, speaker=int(df["voice"][str(message.author.id)]))
                            with open("./tts/" + file_uuid + ".wav", "wb") as f:
                                f.write(await audio_query.synthesis(speaker=1))
                            src = discord.FFmpegPCMAudio("./tts/" + file_uuid + ".wav")
                            vc.play(src)
                            print("now playng...")
                            await asyncio.sleep(3)
                            try:
                                os.remove("./tts/" + file_uuid + ".wav")
                            except PermissionError:
                                asyncio.run(self.delete(file_uuid=file_uuid))
                                os.remove("./tts/" + file_uuid + ".wav")
                    except KeyError:
                        async with Client() as client:
                            
                            audio_query = await client.create_audio_query(
                            content, speaker=3
                            )
                            with open("./tts/" + file_uuid + ".wav", "wb") as f:
                                f.write(await audio_query.synthesis(speaker=1))
                            src = discord.FFmpegPCMAudio("./tts/" + file_uuid + ".wav")
                            vc.play(src)
                            await asyncio.sleep(3)
                            os.remove("./tts/" + file_uuid + ".wav")
        except KeyError:
            pass

    @discord.slash_command(name = "debug_speaker", description = "読み上げに利用する音声を**番号を指定して**変更します。")
    async def tts_debug_speaker(self,ctx, speaker : Option(int, description = "話者のID", required=True)):
        with open('./tts/config/config.json', 'r') as f:
            df = json.load(f)
        with open('./tts/config/config.json', 'w') as f:
            df["voice"][str(ctx.author.id)] = speaker
            json.dump(df, f, ensure_ascii=False, indent=4)
            embed=discord.Embed(title=f"{ctx.author.name}の話者を「{speaker}」に変更しました！", description=f"", color=discord.Colour.green())
            await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(tts(bot))
