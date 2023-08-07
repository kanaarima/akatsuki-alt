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


def user_lb_stats_tracker(secrets):
    while True:
        try:
            thread.sleeping = False
            files = glob.glob("data/trackerbot/*.json")
            yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).date()
            if yesterday.weekday != 6:  # run only on sunday
                thread.sleeping = True
                time.sleep(60 * 5)
                continue
            dir = f"data/user_lb_stats/{yesterday}"
            if os.path.exists(dir):
                thread.sleeping = True
                time.sleep(60 * 5)
                continue
            os.makedirs(dir)
            leaderboard_pp = [
                [
                    akatsuki.grab_user_leaderboards(
                        mode=0, relax=0, pages=8, sort="magic"
                    ),
                    akatsuki.grab_user_leaderboards(
                        mode=0, relax=1, pages=8, sort="magic"
                    ),
                    akatsuki.grab_user_leaderboards(
                        mode=0, relax=2, pages=8, sort="magic"
                    ),
                ],
                [
                    akatsuki.grab_user_leaderboards(
                        mode=1, relax=0, pages=1, sort="magic"
                    ),
                    akatsuki.grab_user_leaderboards(
                        mode=1, relax=1, pages=1, sort="magic"
                    ),
                ],
                [
                    akatsuki.grab_user_leaderboards(
                        mode=2, relax=0, pages=1, sort="magic"
                    ),
                    akatsuki.grab_user_leaderboards(
                        mode=2, relax=1, pages=1, sort="magic"
                    ),
                ],
                [
                    akatsuki.grab_user_leaderboards(
                        mode=3, relax=0, pages=1, sort="magic"
                    )
                ],
            ]
            beatmaps = beatmapdb.load_beatmaps(as_table=True)
            akatmaps = list()
            scores = list()
            # Grab all top 1000 top 100 scores of std rx
            for i in range(1000):
                if i < 100:
                    _scores = akatsuki.grab_user_best(
                        leaderboard_pp[0][1]["users"][i]["id"], mode=0, relax=1, pages=4
                    )
                elif i < 400:
                    _scores = akatsuki.grab_user_best(
                        leaderboard_pp[0][1]["users"][i]["id"], mode=0, relax=1, pages=2
                    )
                else:
                    _scores = akatsuki.grab_user_best(
                        leaderboard_pp[0][1]["users"][i]["id"], mode=0, relax=1, pages=1
                    )
                for score in _scores["scores"]:
                    if score["beatmap"]["beatmap_id"] not in beatmaps:
                        akatmaps.append(
                            beatmapdb.convert_akatapi(
                                score["beatmap"], source="akatsuki_top100"
                            )
                        )
                    score["beatmap"] = score["beatmap"][
                        "beatmap_id"
                    ]  # strip map metadata
                    score["user"] = leaderboard_pp[0][1]["users"][i]["id"]
                    scores.append(score)
            utils.save_json_gzip(scores, f"{dir}/top_plays.json.gz")
            beatmaps = list(beatmaps.values())
            beatmapdb.update_beatmaps(beatmaps, akatmaps)
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
