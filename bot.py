import requests
import discord
from discord.ext import commands
import asyncio
import locale
from config import TOKEN, API_KEY

intents = discord.Intents.all()

client = commands.Bot(command_prefix='!', intents=intents, case_insensitive=True)

stop_flag = False
symbol_map = {}  # Symbol map to store symbol-id pairs
last_price = None  # Variable to store the last retrieved price

# Global conversion rates dictionary
conversion_rates = {
    'USD': 1.0,
    'AUD': 1.50,
    'NZD': 1.59,
    'INR': 82.91,
    'GBP': 0.80,
    'CNY': 7.01,
    'JPY': 137.96,
}

# Set the locale to the user's default setting
locale.setlocale(locale.LC_ALL, '')

@client.event
async def on_ready():
    print('Bot is ready')
    print('--------------------')
    await load_symbol_map()  # Load the symbol map at the start of the bot

async def load_symbol_map():
    response = requests.get('https://api.coincap.io/v2/assets')
    if response.status_code == 200:
        data = response.json()
        for asset in data['data']:
            symbol = asset['symbol'].lower()
            asset_id = asset['id']
            symbol_map[symbol] = asset_id
    else:
        print(response.status_code)
        print(response.content)

@client.command(name='stop')
async def stop_bot(ctx):
    global stop_flag
    stop_flag = True
    await ctx.send('Bot has stopped sending messages. Waiting for 5 seconds before responding to commands.')
    await asyncio.sleep(5)
    stop_flag = False

@client.command(name='check')
async def check(ctx, *args):
    if stop_flag:
        await asyncio.sleep(5)

    if len(args) == 0:
        await ctx.send('Please provide a coin/token to check.')
        return

    amount = None
    query = args[0].lower()
    currency = None

    if len(args) > 1:
        if args[0].isdigit():
            amount = float(args[0])
            query = args[1].lower()
        else:
            query = args[0].lower()
            currency = args[1].upper()

    if len(args) > 2:
        currency = args[2].upper()

    asset_id = symbol_map.get(query)

    if not asset_id:
        asset_id = query

    headers = {
        'Authorization': API_KEY
    }
    response = requests.get(f'https://api.coincap.io/v2/assets/{asset_id}', headers=headers)
    if response.status_code == 200:
        data = response.json()
        symbol = data['data']['symbol']
        price = round(float(data['data']['priceUsd']), 2)

        if currency is not None:
            converted_price = convert_price(price, currency)
            if amount is not None and converted_price is not None:
                converted_price_amount = f'{locale.currency(float(converted_price.split()[0]) * amount, grouping=True)} {converted_price.split()[1]}'
                await ctx.send(f'The price of {amount} {symbol} is {converted_price_amount}')
            else:
                if converted_price is not None:
                    await ctx.send(f'The price of {symbol} is {locale.currency(float(converted_price.split()[0]), grouping=True)}')
                else:
                    supported_currencies = ', '.join(conversion_rates.keys())
                    await ctx.send(f'Please use a supported currency. Supported currencies are: {supported_currencies}')
        else:
            if amount is not None:
                price *= amount
                await ctx.send(f'The price of {amount} {symbol} is {locale.currency(price, grouping=True)}')
            else:
                await ctx.send(f'The price of {symbol} is {locale.currency(price, grouping=True)}')

        global last_price
        last_price = price

def convert_price(price, currency):
    if currency in conversion_rates:
        converted_price = round(price * conversion_rates[currency] / conversion_rates['USD'], 2)
        return f'{converted_price:.2f} {currency}'
    else:
        return None


client.run(TOKEN)
