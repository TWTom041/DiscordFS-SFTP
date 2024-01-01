import requests
from typing import Union, Iterable
import ssl
import asyncio
import time

import aiohttp

from dsurl import BaseExpirePolicy, DSUrl


class ApiExpirePolicy(BaseExpirePolicy):
    api_url_template = "https://discord.com/api/v9/channels/{channel_id}/messages?{message_id}"

    def __init__(self):
        self.loop = asyncio.new_event_loop()
    
    async def fetch_msg(self, session: aiohttp.ClientSession, url):
        async with session.get(url, ssl=ssl.SSLContext()) as response:
            status = response.status
            if status != 200:
                if status == 429:
                    # get retry_after
                    retry_after = response.headers["Retry-After"] + 0.08
                    await asyncio.sleep(retry_after)
                    return await self.fetch_msg(session, url)
                else:
                    raise Exception(f"Status code {status}")
            resp = await response.json()
            return resp[0]["attachments"][0]["url"]

    async def fetch_msg_all(self, urls: Iterable, loop: asyncio.AbstractEventLoop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        async with aiohttp.ClientSession(loop=loop, headers={"Authorization": f"Bot {self.token}"}) as session:
            tasks = []
            for url in urls:
                task = asyncio.ensure_future(self.fetch_msg(session, url))
                tasks.append(task)
                await asyncio.sleep(1/45)
            return await asyncio.gather(*tasks, return_exceptions=True)
        
    def setup(self, token):
        self.token = token

    def renew_url(self, dsurls: Iterable[DSUrl]) -> Iterable[DSUrl]:
        urls = [self.api_url_template.format(channel_id=dsurl.channel_id, message_id=dsurl.message_id) for dsurl in dsurls]
        results = self.loop.run_until_complete(self.fetch_msg_all(urls))
        out = []
        for result in results:
            if isinstance(result, Exception):
                raise result
            out.append(DSUrl.from_url(result))
        return out


def test():
    from datetime import datetime
    policy = ApiExpirePolicy()
    policy.setup("MTE5MDY3MzE1MjkzNDY5NDk4Mg.Gwye8U.YkhRTTScyZYqT8nMKyuVHQK5Mx5GenEH33f3vE")
    dsurl = DSUrl.from_url("https://cdn.discordapp.com/attachments/1183629078323019841/1185892155919708212/37b51d194a7513e45b56f6524f2d51f2-76ff8caa?ex=65914322&is=657ece22&hm=fe46401dd2ca842e43a5dbd70a9d35d893236632a6047fa13e15080ba7b1a3de&")
    print(dsurl)
    renewed = policy.renew_url([dsurl])
    print(datetime.fromtimestamp(renewed[0].expire))

if __name__ == "__main__":
    test()

