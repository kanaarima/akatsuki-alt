from datetime import timedelta
from discord.ext import tasks
import api.beatmapdb as beatmapdb
import bot.tillerino as tillerino
import api.utils as utils
import discord
import time
import os

client = None
ranked_tag = None
loved_tag = None
channel_id = None


async def create_post(mapset_id, maps, ranked):
    embed = discord.Embed()
    embed.set_image(
        url=f"https://assets.ppy.sh/beatmaps/{mapset_id}/covers/cover@2x.jpg"
    )
    client.get_channel(channel_id)
    title = f"{maps[0]['artist']} - {maps[0]['title']} "
    if len(title) > 84:
        title = title[:84] + "... "
    added = 0
    min_star = 1000
    max_star = 0
    for map in maps:
        min_star = min(min_star, map["stars"])
        max_star = max(max_star, map["stars"])
        if added == 24:
            continue
        name = f"{map['stars']:0.2f}* {map['difficulty']}"
        AR = f"{map['AR']:0.1f}" if "AR" in map else "0"
        OD = f"{map['OD']:0.1f}" if "OD" in map else "0"
        CS = f"{map['CS']:0.1f}" if "CS" in map else "0"
        speed = f"{map['stars_speed']:0.2f}" if "stars_speed" in map else "0"
        aim = f"{map['stars_aim']:0.2f}" if "stars_aim" in map else "0"
        length = timedelta(seconds=map["length"]) if "length" in map else "0"
        value = f"AR: {AR} CS: {CS} OD: {OD}\nLength: {length}\nAim SR: {aim}*\nSpeed SR: {speed}*"
        embed.add_field(name=name, value=value)
        added += 1
    embed.add_field(
        name="Downloads",
        value=f"[Chimu](https://api.chimu.moe/v1/download/{mapset_id}?n=1)\n[Bancho](https://osu.ppy.sh/beatmapsets/{mapset_id})\n[Osu! Direct](https://kanaarima.github.io/osu/osudl-set.html?beatmap={mapset_id})",
    )
    title += f"({min_star:0.2f}-{max_star:0.2f}*)"
    thread, msg = await client.get_channel(channel_id).create_thread(
        name=title,
        embed=embed,
        applied_tags=[ranked_tag if ranked else loved_tag],
    )
    return msg.id


async def check_for_updates():
    if not os.path.exists("data/discord_tracker/maps.json.gz"):
        return
    if not os.path.exists("data/discord_tracker/sent.json.gz"):
        already_sent = dict()
        os.makedirs("data/discord_tracker", exist_ok=True)
    else:
        already_sent = utils.load_json_gzip("data/discord_tracker/sent.json.gz")

    beatmaps = list(tillerino.beatmaps.values())

    def get_beatmap_set(beatmap_set_id):
        maps = beatmapdb.get_from_mapset(beatmap_set_id)
        if not maps:
            return
        beatmapdb.update_beatmaps(beatmaps, maps, overwrite=True)
        beatmapdb.save_beatmaps(beatmaps)
        maps.sort(key=lambda x: x["stars"])
        return maps

    mapsets = utils.load_json_gzip("data/discord_tracker/maps.json.gz")
    for mapset in mapsets:
        maps = get_beatmap_set(mapset["mapset_id"])
        if not maps:
            already_sent[mapset["mapset_id"]] = {"result": "failed"}
            continue
        id = await create_post(mapset["mapset_id"], maps, mapset["ranked"])
        already_sent[mapset["mapset_id"]] = {"result": "success", "msg_id": id}
        time.sleep(3)
    utils.save_json_gzip(already_sent, "data/discord_tracker/sent.json.gz")


@tasks.loop(minutes=30)
async def checker_task():
    global ranked_tag, loved_tag
    if not ranked_tag:
        for tag in client.get_channel(channel_id).available_tags:
            if tag.name.lower() == "ranked":
                ranked_tag = tag
            elif tag.name.lower() == "loved":
                loved_tag = tag

    await check_for_updates()
