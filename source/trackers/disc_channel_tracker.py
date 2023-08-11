import api.utils as utils
import subprocess
import datetime
import json
import time
import re
import os

thread = None


def track_discord(secrets):
    while True:
        thread.sleeping = False
        yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).date()
        if os.path.exists(f"data/discord_tracker/{yesterday}"):
            thread.sleeping = True
            time.sleep(60)
            continue
        os.makedirs("data/discord_tracker", exist_ok=True)
        os.system(f"touch data/discord_tracker/{yesterday}")
        date = f"--after {yesterday}"
        if not os.path.exists("data/discord_tracker/maps.json.gz"):
            date = ""
            mapsets = list()
        else:
            mapsets = utils.load_json_gzip("data/discord_tracker/maps.json.gz")
        res = subprocess.Popen(
            f"dotnet bin/DiscordChatExporter.Cli.dll export -t {secrets['discord_selfbot']} -c 597200076561055795 -f json -o data/discord_tracker/messages.json {date}",
            shell=True,
        )
        res.wait()
        with open("data/discord_tracker/messages.json") as f:
            data = json.load(f)
        for message in data["messages"]:
            if "https://osu.ppy.sh" not in message["content"]:
                continue
            if not message["reactions"]:
                continue
            ranked = False
            emoji = message["reactions"][0]["emoji"]["name"]
            if emoji == "✅":
                ranked = True
            elif emoji == "Loved":
                ranked = False  # does nothing
            else:
                continue
            mapsets.append(
                {
                    "mapset_id": re.findall(r"\d+", message["content"])[0],
                    "ranked": ranked,
                }
            )
        utils.save_json_gzip(mapsets, "data/discord_tracker/maps.json.gz")
