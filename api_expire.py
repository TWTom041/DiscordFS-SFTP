import requests
from typing import Union, Iterable
import ssl
import asyncio
import time

import aiohttp

from dsurl import BaseExpirePolicy, DSUrl


def iter_over_async(ait, loop):
    ait = ait.__aiter__()
    async def get_next():
        try:
            obj = await ait.__anext__()
            return False, obj
        except StopAsyncIteration:
            return True, None
    while True:
        done, obj = loop.run_until_complete(get_next())
        if done:
            break
        yield obj


class ApiExpirePolicy(BaseExpirePolicy):
    api_url_template = "https://discord.com/api/v9/channels/{channel_id}/messages?{message_id}&limit=3"

    def __init__(self):
        self.loop = asyncio.new_event_loop()
    
    async def fetch_msg(self, session: aiohttp.ClientSession, url:DSUrl, force_get=False):
        if not self.is_expired(url) and not force_get:
            return url
        async with session.get(self.api_url_template.format(channel_id=url.channel_id, message_id=url.message_id), ssl=ssl.SSLContext()) as response:
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
            return resp[0]["attachments"][0]["url"], resp[0]["id"]

    async def fetch_msg_all(self, urls: Iterable[DSUrl], loop: asyncio.AbstractEventLoop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        async with aiohttp.ClientSession(loop=loop, headers={"Authorization": f"Bot {self.token}"}) as session:
            tasks = []
            for url in urls:
                task = asyncio.ensure_future(self.fetch_msg(session, url))
                tasks.append(task)
                await asyncio.sleep(1/45)
            
            for task in tasks:
                yield await task
            # return await asyncio.gather(*tasks, return_exceptions=True)
        
    def setup(self, token):
        self.token = token

    def renew_url(self, dsurls: Iterable[DSUrl]) -> Iterable[DSUrl]:
        # urls = [self.api_url_template.format(channel_id=dsurl.channel_id, message_id=dsurl.message_id) for dsurl in dsurls]
        results = self.fetch_msg_all(dsurls)
        results = iter_over_async(results, self.loop)
        
        for result in results:
            if isinstance(result, Exception):
                raise result
            yield result

    def __del__(self):
        self.loop.close()


def test():
    from datetime import datetime
    policy = ApiExpirePolicy()
    policy.setup(input("Token: "))
    dsurl = DSUrl.from_url("https://cdn.discordapp.com/attachments/1183629078323019841/1191694542261452871/59bcfcc8fda508c307155d49952a9f1d-8bd0d1a2?ex=65a65f07&is=6593ea07&hm=628fb61c14b8b7d27f0684ad2a5b013bacebf960d9b91e76e717890269122774&", "1191694541993033761")
    print(dsurl)
    renewed = list(policy.renew_url([dsurl]))
    print(datetime.fromtimestamp(renewed[0].issue))

if __name__ == "__main__":
    test()

