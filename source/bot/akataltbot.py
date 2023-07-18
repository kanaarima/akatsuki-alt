from discord import app_commands
from typing import Optional
import api.akatsuki as akatsuki
import datetime
import discord
import json
import os

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
thread = None


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


@client.event
async def on_message(message: discord.Message):
    thread.sleeping = False
    if message.author == client.user:
        return
    args = message.content.split(" ")
    try:
        if message.content.startswith('$link'):
            await link(message, args)
        elif message.content.startswith('$setgamemode'):
            await set_default_gamemode(message, args)
        elif message.content.startswith('$show'):
            await show(message, args)
    except Exception as e:
        print(repr(e))
    thread.sleeping = True


async def set_default_gamemode(message: discord.Message, args):
    if len(args) < 2:
        await message.reply(
            "Specify a gamemode! (std(rx/ap),taiko(rx),ctb(rx),mania)")
        return
    modes = {
        "std": ("std", 0),
        "stdrx": ("std", 1),
        "stdap": ("std", 2),
        "taiko": ("taiko", 0),
        "taikorx": ("taiko", 1),
        "ctb": ("ctb", 0),
        "ctbrx": ("ctb", 1),
        "mania": ("mania", 0)
    }
    if args[1].lower() not in modes:
        await message.reply(
            "Invalid gamemode! Use (std(rx/ap),taiko(rx),ctb(rx),mania)")
        return
    mode = modes[args[1].lower()]
    if os.path.exists(f"data/trackerbot/{message.author.id}.json"):
        with open(f"data/trackerbot/{message.author.id}.json") as f:
            data = json.load(f)
        data["defaultmode"] = mode[0]
        data["defaultrelax"] = mode[1]
        with open(f"data/trackerbot/{message.author.id}.json", "w") as f:
            json.dump(data, f)
        await message.reply("Default gamemode successfully set.")
    else:
        await message.reply(
            "You don't have an account linked! Use $link {UserID} first!")


async def link(message: discord.Message, args):
    if len(args) < 2:
        await message.channel.send("Wrong arguments! Usage: $link {UserID}")
        return
    if not args[1].isnumeric():
        await message.channel.send("Wrong arguments! UserID must be a number.")
        return
    if os.path.exists(f"data/trackerbot/{message.author.id}.json"):
        overwrite = False
        if len(args) > 2:
            if args[2] == "overwrite":
                overwrite = True
        if not overwrite:
            await message.channel.send(
                "You already have an user linked! Append overwrite to command to confirm."
            )
            return
    os.makedirs("data/trackerbot/", exist_ok=True)
    try:
        data = {
            "userid":
            int(args[1]),
            "defaultmode":
            "std",
            "defaultrelax":
            0,
            "fetches": [{
                "time":
                datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                "stats":
                akatsuki.grab_stats(int(args[1]))
            }]
        }
        with open(f"data/trackerbot/{message.author.id}.json", "w") as f:
            json.dump(data, f, indent=4)
        await message.channel.send(
            f'Linked to {data["fetches"][0]["stats"]["username"]}. Use $setgamemode to set default gamemode.'
        )
    except akatsuki.ApiException:
        await message.channel.send('Invalid userID.')


async def show(message: discord.Message, args):
    if os.path.exists(f"data/trackerbot/{message.author.id}.json"):
        data = await update_fetches(f"data/trackerbot/{message.author.id}.json"
                                    )
        debug = f"{data['fetches'][-1]['stats']['stats'][0]['std']['ranked_score']}"
        await message.reply(debug)
    else:
        await message.reply(
            "You don't have an account linked! Use $link {UserID} first!")


async def update_fetches(file):
    with open(file) as f:
        data = json.load(f)
    fetches = list()
    update = False
    for fetch in data["fetches"]:
        time = datetime.datetime.strptime(fetch["time"], '%d/%m/%Y %H:%M:%S')
        if (datetime.datetime.now() - time).days > 0:
            update = True
            continue
        fetches.append(fetch)
    if len(fetches) == 0:
        fetches.append({
            'stats':
            akatsuki.grab_stats(data["userid"]),
            'time':
            datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        })
        update = True
    else:
        if (datetime.datetime.now() - time).seconds > 5 * 60:
            fetches.append({
                'stats':
                akatsuki.grab_stats(data["userid"]),
                'time':
                datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            })
    if update:
        data["fetches"] = fetches
        with open(file, "w") as f:
            json.dump(data, f, indent=4)
    return data


def akataltbot(secrets):
    client.run(secrets["discord_token"])