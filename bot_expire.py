"""
Not implemented yet
"""

import os
from io import BytesIO
import threading
import asyncio
import time
import getpass
from typing import Iterable, Union

import requests
import fs.path
import discord
from discord.ext import commands

from key_mgr import AESCipher
from dsurl import BaseExpirePolicy, DSUrl


class UrlEvent(threading.Event):
    def __init__(self):
        threading.Event.__init__(self)
        self.url = None
    
    def set_url(self, url):
        self.url = url
        self.set()
    
    def get_url(self):
        self.wait()
        return self.url


class RenewCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_get_url(self, channel_id, message_id, event: UrlEvent):
        message = await self.bot.get_channel(channel_id).fetch_message(message_id)
        event.set_url(message.attachments[0].url)
    
    @commands.command(name="status", pass_context=True)
    async def status(self, ctx: commands.context.Context):
        await ctx.channel.send("Listening")

    @commands.command(name="showurl", pass_context=False)
    async def showurl(self, chanid, msgid):
        message = await self.bot.get_channel(chanid).fetch_message(msgid)
        print(message.attachments[0].url)

    
class BotExpirePolicy(BaseExpirePolicy):
    def __init__(self):
        self.bot = None
        self.bot_thread = None
        self.bot_loop = asyncio.new_event_loop()
    
    def _run_bot(self, token):
        asyncio.set_event_loop(self.bot_loop)
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix="!", intents=intents)
        asyncio.run(self.bot.add_cog(RenewCog(self.bot)))
        self.bot.run(token)
       
    
    def run_bot_background(self, token, block=True):
        self.bot_thread = threading.Thread(target=self._run_bot, args=(token,))
        self.bot_thread.start()
        while block == True and (self.bot is None) or (not self.bot.is_ready()):
            pass
    
    def setup(self):
        self.run_bot_background()
    
    def renew_url(self, dsurls: Iterable[DSUrl]):
        events = []
        for dsurl in dsurls:
            channel_id = dsurl.channel_id
            message_id = dsurl.message_id
            event = UrlEvent()
            events.append(event)
            # self.bot.dispatch("get_url", self.channel_id, message_id, event)  <- this is slow
            asyncio.run_coroutine_threadsafe(self.bot.get_cog("RenewCog").on_get_url(channel_id, message_id, event), self.bot.loop)

        return [event.get_url() for event in events]
    
    def stop(self):
        try:
            # self.bot.loop.call_soon_threadsafe(self.bot.loop.stop)
            self.bot.close()
        except RuntimeError:
            pass
        self.bot_thread.join()
    
    def __del__(self):
        self.stop()

def main():
    chanid = 1183629078323019841  # 1111111111111111111
    msgid = 1190682612184915980  # 1111111111111111111

    bottool = BotExpirePolicy(chanid)
    bottool.run_bot_background(token=getpass.getpass("token: "))
    print("start")
    stime = time.time()
    url = bottool.renew_url([msgid])
    print("time:", time.time() - stime)
    print("start")
    stime = time.time()
    url = bottool.renew_url([msgid] * 5)
    print("time:", time.time() - stime)
    print(url)
    bottool.stop()
    time.sleep(3)
    print("done")

if __name__ == "__main__":
    main()
