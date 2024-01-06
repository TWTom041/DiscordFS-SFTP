# this is the script for webhook management, the difference between webhook_man_bot.py is that it does not use a bot, but use discord API instead.

from typing import Iterable, Union, Optional
from itertools import cycle, chain

import requests


class WebhookApiMan:
    def __init__(self, token=None):
        self.token = token


    @property
    def headers(self):
        headers = {}
        if self.token is not None:
            headers |= {"Authorization": f"Bot {self.token}"}
        return headers
            

    def gen_webhooks(self, channel_id: Union[int, str], amount:int =1):
        url = f"https://discord.com/api/channels/{channel_id}/webhooks"
        body = {"name": "DSFS Hook"}
        for _ in range(amount):
            resp = requests.post(url, json=body, headers=self.headers)
            if resp.status_code != 200:
                raise Exception(f"Status code {resp.status_code}. Note: If you are using a bot token, make sure it has the 'MANAGE_WEBHOOKS' permission, or it'll return 401 error.")
            context = resp.json()
            yield context["id"], context["token"]
    
    def delete_webhooks(self, webhook_ids: Iterable[Union[int, str]], tokens: Optional[Iterable[Union[str, None]]] = None):
        if tokens is not None:
            if len(webhook_ids) != len(tokens):
                tokens = chain(tokens, cycle([None]))
        for webhook_id, webhook_token in zip(webhook_ids, tokens or cycle([None])):
            url = f"https://discord.com/api/webhooks/{webhook_id}"
            if webhook_token is not None:
                url += f"/{webhook_token}"
            
            resp = requests.delete(url, headers=self.headers)
            if resp.status_code != 204:
                raise Exception(f"Status code {resp.status_code}. Note: If you are using a bot token, make sure it has the 'MANAGE_WEBHOOKS' permission, or it'll return 401 error. Another choice is to provide webhook token.")
    
    def list_webhooks_in_channel(self, channel_id: Union[int, str]):
        url = f"https://discord.com/api/channels/{channel_id}/webhooks"
        resp = requests.get(url, headers=self.headers)
        if resp.status_code != 200:
            raise Exception(f"Status code {resp.status_code}. Note: If you are using a bot token, make sure it has the 'MANAGE_WEBHOOKS' permission, or it'll return 401 error.")
        return resp.json()
    
    def delete_webhooks_in_channel(self, channel_id: Union[int, str]):
        webhooks = self.list_webhooks_in_channel(channel_id)
        self.delete_webhooks(webhook["id"] for webhook in webhooks)


def test():
    api = WebhookApiMan(input("Token: "))
    webhooks = list(api.gen_webhooks(12345678, 3))
    print(webhooks)
    input()
    api.delete_webhooks(*zip(*webhooks))


def app():
    token = input("Token: ")
    api = WebhookApiMan(token)
    channel_id = input("Channel ID: ")
    webhooks = list(api.gen_webhooks(channel_id, 3))
    while True:
        print("1. List webhooks")
        print("1-1. List webhooks to urls")
        print("2. Create webhooks")
        print("3. Delete all webhooks in channel")
        print("4. Delete one webhook")
        print("5. Exit")
        choice = input("Choice: ")
        if choice == "1":
            webhooks = api.list_webhooks_in_channel(channel_id)
            print(webhooks)
        elif choice == "1-1":
            webhooks = api.list_webhooks_in_channel(channel_id)
            for webhook in webhooks:
                print(f"https://discord.com/api/webhooks/{webhook['id']}/{webhook['token']}")
        elif choice == "2":
            amount = int(input("Number of webhooks to create: "))
            webhooks = list(api.gen_webhooks(channel_id, amount))
            print(webhooks)
        elif choice == "3":
            api.delete_webhooks_in_channel(channel_id)
        elif choice == "4":
            webhook_id = input("Webhook ID: ")
            api.delete_webhooks([webhook_id])
        elif choice == "5":
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    app()
