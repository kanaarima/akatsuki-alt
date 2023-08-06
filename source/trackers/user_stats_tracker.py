import api.beatmapdb as beatmapdb
import api.akatsuki as akatsuki
import api.utils as utils
import traceback
import datetime
import json
import time
import glob
import os

thread = None


def user_stats_tracker(secrets):
    while True:
        try:
            thread.sleeping = False
            files = glob.glob("data/trackerbot/*.json")
            yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).date()
            dir = f"data/user_stats/{yesterday}"
            if os.path.exists(dir):
                thread.sleeping = True
                time.sleep(60 * 5)
                continue
            os.makedirs(dir)
            beatmaps = beatmapdb.load_beatmaps()
            for file in files:
                with open(file) as f:
                    data = json.load(f)
                filename = f"{dir}/{data['userid']}.json.gz"
                if os.path.exists(
                    filename
                ):  # skip fetching twice if 2 users have the same account linked
                    continue
                fetch = akatsuki.grab_stats(data["userid"])
                fetch["first_places"] = [[0, 0, 0], [0, 0], [0, 0], [0]]
                modes = {
                    "std": ((0, 0), (0, 1), (0, 2)),
                    "taiko": ((1, 0), (1, 1)),
                    "ctb": ((2, 0), (2, 1)),
                    "mania": ((3, 0),),
                }
                akatmaps = list()
                for mode_name in modes.keys():
                    for mode, rx in modes[mode_name]:
                        first_places = akatsuki.grab_all_user_1s(
                            data["userid"], mode, rx
                        )
                        for score in first_places:
                            akatmaps.append(beatmapdb.convert_akatapi(score["beatmap"]))
                            score["beatmap"] = score["beatmap"][
                                "beatmap_id"
                            ]  # dont store all metadata
                        fetch["first_places"][mode][rx] = first_places
                beatmapdb.update_beatmaps(beatmaps, akatmaps)
                utils.save_json_gzip(fetch, filename)
            beatmapdb.save_beatmaps(beatmaps)
        except Exception as e:
            print(e)
            if "error_channel" in secrets:
                utils.send_string_list(
                    f'http://{secrets["flask2discord_host"]}:{secrets["flask2discord_port"]}/send_message',
                    secrets["error_channel"],
                    f"Error in {__name__}",
                    (e.__class__.__name__, str(e), traceback.format_exc()),
                )
            time.sleep(10)
