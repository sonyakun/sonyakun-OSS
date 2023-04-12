import discord
from discord.ext import commands
from discord import default_permissions,Option
import json
import httpx
from base64 import b64encode, b64decode
import re
import asyncio

class GlobalChat(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @discord.slash_command(name = "global", description = "グローバルチャットを作成します。すでに作成されている場合は削除します。")
    @default_permissions(manage_channels = True)
    async def gc_join(self, ctx):
        with open("./data/json/global.json", "r") as f:
            load = json.load(f)
        
        try:
            load[str(ctx.guild.id)]
            del load[str(ctx.guild.id)]
            with open("./data/json/global.json", "w") as f1:
                json.dump(load, f1, ensure_ascii=False, indent=4)
                embed = discord.Embed(title = "登録を解除しました。",description="Webhookは手動で削除してください。",colour = discord.Colour.red())
                await ctx.respond(embed = embed)
        except KeyError:
            url = await ctx.channel.create_webhook(name="PubricBot Global")
            load.update({str(ctx.guild.id): {"url": url.url, "channel": ctx.channel.id}})
            with open("./data/json/global.json", "w") as f1:
                json.dump(load, f1, ensure_ascii=False, indent=4)
            embed = discord.Embed(title = "グローバルチャットに接続しました。",colour = discord.Colour.green())
            await ctx.respond(embed = embed)
            await asyncio.sleep(5)
            with open("./data/json/global.json", "r") as f:
                load = json.load(f)
                urls = []
            for key, value in load.items():
                urls.append(value['url'])
            for url in urls:
                async with httpx.AsyncClient() as client:
                    main_content = {
                                        'username': 'PubricBot[SYSTEM]',
                                        'avatar_url': "https://cdn.discordapp.com/embed/avatars/0.png",
                                        'content': f'新しいサーバーが参加しました！\nサーバー名: {ctx.guild.name}'
                                    }
                    headers = {'Content-Type': 'application/json'}
                    await client.post(url, data=json.dumps(main_content), headers=headers)
        

    @commands.Cog.listener(name = "on_message")
    async def gc_msg(self, message):
        if message.author.bot: #BOTの場合は何もせず終了
            return
        dis_tok = re.search(r"[A-Za-z0-9\-_]{23,30}\.[A-Za-z0-9\-_]{6,7}\.[A-Za-z0-9\-_]{27,40}", message.content, re.IGNORECASE) #トークン弾く
        if dis_tok is not None:
            await message.add_reaction('❌')
            return
        invite_link = re.search(r"(https?://)?((ptb|canary)\.)?(discord\.(gg|io)|discord(app)?.com/invite)/[0-9a-zA-Z]+", message.content, re.IGNORECASE) #invite弾く
        if invite_link is not None:
            await message.add_reaction('❌')
            return
        try:
            with open("./data/json/global.json", "r") as f:
                load = json.load(f)
            try:
                if message.channel.id == load[str(message.guild.id)]["channel"]:
                    print(message.channel.id)
                    urls = []
                    
                    for key, value in load.items():
                        if key != str(message.guild.id):
                            urls.append(value['url'])
                    for url in urls:
                        async with httpx.AsyncClient() as client:
                            try:
                                main_content = {
                                    'username': f"{message.author.name}#{message.author.discriminator}|{message.guild.name}[UGC]",
                                    'avatar_url': message.author.display_avatar.url,
                                    'content': message.content,
                                    "embeds": [
                                        {
                                            "title": "添付ファイル",
                                            "image": {
                                                "url": message.attachments[0].url
                                            }
                                        }
                                    ]
                                }
                            except IndexError:
                                    main_content = {
                                        'username': f"{message.author.name}#{message.author.discriminator}|{message.guild.name}[UGC]",
                                        'avatar_url': message.author.display_avatar.url,
                                        'content': message.content,
                                    }
                            headers = {'Content-Type': 'application/json'}
                            await client.post(url, data=json.dumps(main_content), headers=headers)
                            await message.add_reaction("🔄")
                            await message.add_reaction("✅")
                            await message.remove_reaction("✅", message.author)
            except KeyError:
                pass
        except (Exception, BaseException) as e:
            await message.add_reaction('❗')
            await message.add_reaction('⁉️')
            import traceback
            from traceback import TracebackException
            print("---------------------Global Chat Error----------------------")
            print(TracebackException.from_exception(e).format())
            print("------------------------------------------------------------")
        

def setup(bot):
    bot.add_cog(GlobalChat(bot))
