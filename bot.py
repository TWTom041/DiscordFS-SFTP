import discord
from discord.ext import commands
import faker
import dotenv

TOKEN = dotenv.get_key('.env', 'TOKEN')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='_', intents=intents)

fake = faker.Faker(['zh_TW', 'ja_JP', 'ko_KR', 'en_US', 'en_GB'])

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command()
async def gen(ctx, amount: int=None):
    channel = ctx.channel
    urls = []
    if amount is None:
        webhook = await channel.create_webhook(name=fake.name())
        urls.append(webhook.url)
    else:
        for i in range(int(amount)):
            webhook = await channel.create_webhook(name=fake.name())
            urls.append(webhook.url)
    await ctx.send(
        f'Generated {amount} webhook(s) in {channel.mention}\n'
        + '\n'.join(urls)
    )

@bot.command()  
async def rem(ctx):
    channel = ctx.channel
    webhooks = await channel.webhooks()
    for webhook in webhooks:
        await webhook.delete()
    await ctx.send(f'Removed all webhooks in {channel.mention}')

bot.run(TOKEN)