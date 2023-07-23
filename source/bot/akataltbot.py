from discord import app_commands
from typing import Optional
import api.akatsuki as akatsuki
import traceback
import datetime
import discord
import json
import time
import os

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
thread = None
bot_prefix = None


@client.event
async def on_ready():
    akatsuki.update_scorelb()
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    thread.sleeping = False
    args = message.content.split(" ")
    try:
        if message.content.startswith("$link"):
            await link(message, args)
        elif message.content.startswith(f"{bot_prefix}setgamemode"):
            await set_default_gamemode(message, args)
        elif message.content.startswith(f"{bot_prefix}showclan"):
            await show_clan(message, args)
        elif message.content.startswith(f"{bot_prefix}show"):
            await show(message, args)
        elif message.content.startswith(f"{bot_prefix}reset"):
            await reset(message, args)
    except Exception as e:
        print(repr(e))
        print(traceback.format_exc())
    thread.sleeping = True


async def set_default_gamemode(message: discord.Message, args):
    if len(args) < 2:
        await message.reply("Specify a gamemode! (std(rx/ap),taiko(rx),ctb(rx),mania)")
        return
    mode = await verify_mode_string(message, args[1])
    if not mode:
        return
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
            "You don't have an account linked! Use $link {UserID} first!"
        )


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
            "userid": int(args[1]),
            "defaultmode": "std",
            "defaultrelax": 0,
            "fetches": [
                {
                    "time": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "stats": akatsuki.grab_stats(int(args[1])),
                }
            ],
        }
        with open(f"data/trackerbot/{message.author.id}.json", "w") as f:
            json.dump(data, f, indent=4)
        await message.channel.send(
            f'Linked to {data["fetches"][0]["stats"]["username"]}. Use $setgamemode to set default gamemode.'
        )
    except akatsuki.ApiException:
        await message.channel.send("Invalid userID.")


async def show(message: discord.Message, args):
    userid = None
    if len(args) > 1:
        for arg in args:
            subargs = arg.split("=")
            if len(subargs) == 2:
                if subargs[0].lower() == "user" and subargs[1].isnumeric():
                    userid = int(subargs[1])
    if os.path.exists(f"data/trackerbot/{message.author.id}.json") or userid:
        if userid:
            data = akatsuki.grab_stats(userid)
            username = data["username"]
            rx = 0
            mode = "std"
        else:
            data = await update_fetches(f"data/trackerbot/{message.author.id}.json")
            username = data["fetches"][0]["stats"]["username"]
            rx = data["defaultrelax"]
            mode = data["defaultmode"]
        e = discord.Embed(
            colour=discord.Color.og_blurple(),
            title=f"Stats for {username}",
        )
        if len(args) > 1:
            if not len(args[1].split("=")) == 2:
                mode, rx = await verify_mode_string(message, args[1])
                if not mode:
                    return
        if userid:
            oldest = data["stats"][rx][mode]
            latest = data["stats"][rx][mode]
        else:
            oldest = data["fetches"][0]["stats"]["stats"][rx][mode]
            latest = data["fetches"][-1]["stats"]["stats"][rx][mode]
        ranked_score = f"{latest['ranked_score']:,} {get_gain_string(oldest['ranked_score'], latest['ranked_score'])}"
        total_score = f"{latest['total_score']:,} {get_gain_string(oldest['total_score'], latest['total_score'])}"
        total_hits = f"{latest['total_hits']:,} {get_gain_string(oldest['total_hits'], latest['total_hits'])}"
        playcount = f"{latest['playcount']:,} {get_gain_string(oldest['playcount'], latest['playcount'])}"
        playtime = f"{latest['playtime']/60/60:.0f}h {get_gain_string(oldest['playtime']/60/60, latest['playtime']/60/60,float=True)}"
        replays_watched = f"{latest['replays_watched']} {get_gain_string(oldest['replays_watched'], latest['replays_watched'])}"
        level = f"{latest['level']:.2f} {get_gain_string(oldest['level'], latest['level'], float=True)}"
        accuracy = f"{latest['accuracy']:.2f}% {get_gain_string(oldest['accuracy'], latest['accuracy'], float=True)}"
        max_combo = f"{latest['max_combo']:,} {get_gain_string(oldest['max_combo'], latest['max_combo'])}"
        global_leaderboard_rank = f"#{latest['global_leaderboard_rank']} {get_gain_string(oldest['global_leaderboard_rank'], latest['global_leaderboard_rank'],swap=True)}"
        country_leaderboard_rank = f"#{latest['country_leaderboard_rank']} {get_gain_string(oldest['country_leaderboard_rank'], latest['country_leaderboard_rank'],swap=True)}"
        global_score_rank = f"#{latest['global_rank_score']} {get_gain_string(oldest['global_rank_score'], latest['global_rank_score'],swap=True)}"
        country_score_rank = f"#{latest['country_rank_score']} {get_gain_string(oldest['country_rank_score'], latest['country_rank_score'],swap=True)}"
        count_1s = f"{latest['count_1s']} {get_gain_string(oldest['count_1s'], latest['count_1s'])}"

        pp = f"{latest['pp']:,}pp {get_gain_string(oldest['pp'], latest['pp'])}"

        e.add_field(name=f"Ranked score", value=ranked_score)
        e.add_field(name=f"Total score", value=total_score)
        e.add_field(name=f"Total hits", value=total_hits)
        e.add_field(name=f"Play count", value=playcount)
        e.add_field(name=f"Play Time", value=playtime)
        e.add_field(name=f"Replays watched", value=replays_watched)
        e.add_field(name=f"Level", value=level)
        e.add_field(name=f"Accuracy", value=accuracy)
        e.add_field(name=f"Max combo", value=max_combo)
        e.add_field(name=f"Global rank", value=global_leaderboard_rank)
        e.add_field(name=f"Country rank", value=country_leaderboard_rank)
        e.add_field(name=f"Performance points", value=pp)
        e.add_field(name=f"Global score rank", value=global_score_rank)
        e.add_field(name=f"Country score rank", value=country_score_rank)
        e.add_field(name=f"#1 Count", value=count_1s)
        if userid:
            e.set_thumbnail(url=f"https://a.akatsuki.gg/{userid}")
        else:
            e.set_thumbnail(url=f"https://a.akatsuki.gg/{data['userid']}")
        if not userid:
            timeold = datetime.datetime.strptime(
                data["fetches"][0]["time"], "%d/%m/%Y %H:%M:%S"
            )
            timenew = datetime.datetime.strptime(
                data["fetches"][-1]["time"], "%d/%m/%Y %H:%M:%S"
            )
            e.set_footer(
                text=f"Comparing to {timeold} (UTC+2). Last fetch: {timenew}. Use $reset to clear."
            )
        await message.reply(embed=e)
    else:
        await message.reply(
            "You don't have an account linked! Use $link {UserID} first!"
        )


async def show_clan(message: discord.Message, args):
    clan_id = None
    clan_name = None
    if len(args) > 1:
        for arg in args:
            subargs = arg.split("=")
            if len(subargs) == 2:
                if subargs[0].lower() == "clan" and subargs[1].isnumeric():
                    clan_id = int(subargs[1])
                    clan_name = clan_id
    if not os.path.exists(f"data/trackerbot/{message.author.id}.json") and not clan_id:
        await message.reply(
            "You don't have an account linked! Use $link {UserID} first or use clan=clanid!"
        )
        return
    if not clan_id:
        data = await update_fetches(f"data/trackerbot/{message.author.id}.json")
        if not data["fetches"][-1]["stats"]["clan"]["id"]:
            await message.reply(
                "You haven't join any clan! Join one or use clan=clanid!"
            )
            return
        clan_id = data["fetches"][-1]["stats"]["clan"]["id"]
        clan_name = data["fetches"][-1]["stats"]["clan"]["name"]
    today = datetime.date.today()
    filename = f"data/clan_lb/{today}.json"
    if not os.path.exists(filename):
        await message.reply(
            "Leaderboard data is still being generated. Please wait a few minutes."
        )
        return
    with open(filename) as f:
        lbdata = json.load(f)
    if clan_id == clan_name:
        for x in lbdata["std_rx_1s"]["clans"]:
            if x["clan"] == clan_id:
                clan_name = x["name"]
                break

    def find_lb_pos(clan_id, data, type=""):
        i = 1
        for x in data:
            if type == "pp":
                if x["id"] == clan_id:
                    return f'#{i} ({x["chosen_mode"]["pp"]}pp)'
            elif type == "score":
                if x["id"] == clan_id:
                    return f'#{i} ({int(x["chosen_mode"]["ranked_score"]/1000000)} mil)'
            else:
                if x["clan"] == clan_id:
                    return f'#{i} ({x["count"]} #1)'
            i += 1
        return "-"

    std_vn_1s = find_lb_pos(clan_id, lbdata["std_vn_1s"]["clans"])
    std_rx_1s = find_lb_pos(clan_id, lbdata["std_rx_1s"]["clans"])
    std_ap_1s = find_lb_pos(clan_id, lbdata["std_ap_1s"]["clans"])
    std_vn_pp = find_lb_pos(clan_id, lbdata["std_vn_pp"]["clans"], type="pp")
    std_rx_pp = find_lb_pos(clan_id, lbdata["std_rx_pp"]["clans"], type="pp")
    std_ap_pp = find_lb_pos(clan_id, lbdata["std_ap_pp"]["clans"], type="pp")
    std_vn_score = find_lb_pos(clan_id, lbdata["std_vn_score"]["clans"], type="score")
    std_rx_score = find_lb_pos(clan_id, lbdata["std_rx_score"]["clans"], type="score")
    std_ap_score = find_lb_pos(clan_id, lbdata["std_ap_score"]["clans"], type="score")
    taiko_vn_1s = find_lb_pos(clan_id, lbdata["taiko_vn_1s"]["clans"])
    taiko_rx_1s = find_lb_pos(clan_id, lbdata["taiko_rx_1s"]["clans"])
    taiko_vn_pp = find_lb_pos(clan_id, lbdata["taiko_vn_pp"]["clans"], type="pp")
    taiko_rx_pp = find_lb_pos(clan_id, lbdata["taiko_rx_pp"]["clans"], type="pp")
    taiko_vn_score = find_lb_pos(
        clan_id, lbdata["taiko_vn_score"]["clans"], type="score"
    )
    taiko_rx_score = find_lb_pos(
        clan_id, lbdata["taiko_rx_score"]["clans"], type="score"
    )
    ctb_vn_1s = find_lb_pos(clan_id, lbdata["ctb_vn_1s"]["clans"])
    ctb_rx_1s = find_lb_pos(clan_id, lbdata["ctb_rx_1s"]["clans"])
    ctb_vn_pp = find_lb_pos(clan_id, lbdata["ctb_vn_pp"]["clans"], type="pp")
    ctb_rx_pp = find_lb_pos(clan_id, lbdata["ctb_rx_pp"]["clans"], type="pp")
    ctb_vn_score = find_lb_pos(clan_id, lbdata["ctb_vn_score"]["clans"], type="score")
    ctb_rx_score = find_lb_pos(clan_id, lbdata["ctb_rx_score"]["clans"], type="score")
    mania_vn_1s = find_lb_pos(clan_id, lbdata["mania_vn_1s"]["clans"])
    mania_vn_pp = find_lb_pos(clan_id, lbdata["mania_vn_pp"]["clans"], type="pp")
    mania_vn_score = find_lb_pos(
        clan_id, lbdata["mania_vn_score"]["clans"], type="score"
    )
    overall_1s = find_lb_pos(clan_id, lbdata["overall_1s"]["clans"])
    overall_pp = find_lb_pos(clan_id, lbdata["overall_pp"]["clans"], type="pp")
    overall_score = find_lb_pos(
        clan_id, lbdata["overall_ranked_score"]["clans"], type="score"
    )
    e = discord.Embed(
        colour=discord.Color.og_blurple(),
        title=f"Stats for {clan_name}",
    )
    e.add_field(name="Standard VN #1", value=std_vn_1s)
    e.add_field(name="Standard VN Score", value=std_vn_score)
    e.add_field(name="Standard VN PP", value=std_vn_pp)
    e.add_field(name="Standard RX #1", value=std_rx_1s)
    e.add_field(name="Standard RX Score", value=std_rx_score)
    e.add_field(name="Standard RX PP", value=std_rx_pp)
    e.add_field(name="Standard AP #1", value=std_ap_1s)
    e.add_field(name="Standard AP Score", value=std_ap_score)
    e.add_field(name="Standard AP PP", value=std_ap_pp)
    e.add_field(name="Taiko VN #1", value=taiko_vn_1s)
    e.add_field(name="Taiko VN Score", value=taiko_vn_score)
    e.add_field(name="Taiko VN PP", value=taiko_vn_pp)
    e.add_field(name="Taiko RX #1", value=taiko_rx_1s)
    e.add_field(name="Taiko RX Score", value=taiko_rx_score)
    e.add_field(name="Taiko RX PP", value=taiko_rx_pp)
    e.add_field(name="Ctb VN #1", value=ctb_vn_1s)
    e.add_field(name="Ctb VN Score", value=ctb_vn_score)
    e.add_field(name="Ctb VN PP", value=ctb_vn_pp)
    e.add_field(name="Ctb RX #1", value=ctb_rx_1s)
    e.add_field(name="Ctb RX Score", value=ctb_rx_score)
    e.add_field(name="Ctb RX PP", value=ctb_rx_pp)
    e.add_field(name="Mania VN #1", value=mania_vn_1s)
    e.add_field(name="Mania VN Score", value=mania_vn_score)
    e.add_field(name="Mania VN PP", value=mania_vn_pp)
    e.set_footer(
        text=f"Overall #1: {overall_1s} | Overall Score: {overall_score} | Overall PP: {overall_pp}"
    )
    await message.reply(embed=e)


async def reset(message: discord.Message, args):
    if os.path.exists(f"data/trackerbot/{message.author.id}.json"):
        with open(f"data/trackerbot/{message.author.id}.json") as f:
            data = json.load(f)
        if len(data["fetches"]) == 0:
            await message.reply("You have no data.")
            return
        data["fetches"] = []
        with open(f"data/trackerbot/{message.author.id}.json", "w") as f:
            json.dump(data, f)
        await message.reply("Data resetted.")
    else:
        await message.reply(
            "You don't have an account linked! Use $link {UserID} first!"
        )


def get_gain_string(old, new, float=False, swap=False):
    if not old and old != 0:
        return ""
    if swap:
        oold = old
        old = new
        new = oold
    if old == new:
        return ""
    if old > new:
        return f"({new-old:,.2f})" if float else f"({new-old:,})"
    else:
        return f"(+{new-old:,.2f})" if float else f"(+{new-old:,})"


async def verify_mode_string(message, arg):
    modes = {
        "std": ("std", 0),
        "stdrx": ("std", 1),
        "stdap": ("std", 2),
        "taiko": ("taiko", 0),
        "taikorx": ("taiko", 1),
        "ctb": ("ctb", 0),
        "ctbrx": ("ctb", 1),
        "mania": ("mania", 0),
    }
    if arg.lower() not in modes:
        await message.reply(
            "Invalid gamemode! Use (std(rx/ap),taiko(rx),ctb(rx),mania)"
        )
        return None, None
    return modes[arg.lower()]


async def update_fetches(file):
    with open(file) as f:
        data = json.load(f)
    fetches = list()
    update = False
    for fetch in data["fetches"]:
        time = datetime.datetime.strptime(fetch["time"], "%d/%m/%Y %H:%M:%S")
        if (datetime.datetime.now() - time).days > 0:
            update = True
            continue
        fetches.append(fetch)
    if len(fetches) == 0:
        fetches.append(
            {
                "stats": akatsuki.grab_stats(data["userid"]),
                "time": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            }
        )
        update = True
    else:
        update = True
        if (datetime.datetime.now() - time) > datetime.timedelta(minutes=5):
            fetches.append(
                {
                    "stats": akatsuki.grab_stats(data["userid"]),
                    "time": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                }
            )
    if update:
        data["fetches"] = fetches
        with open(file, "w") as f:
            json.dump(data, f, indent=4)
    return data


def akataltbot(secrets):
    global bot_prefix
    bot_prefix = secrets["discord_command_prefix"]
    client.run(secrets["discord_token"])
