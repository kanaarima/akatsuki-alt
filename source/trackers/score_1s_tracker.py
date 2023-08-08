import api.beatmapdb as beatmapdb
import api.akatsuki as akatsuki
import api.utils as utils
import traceback
import datetime
import time
import glob
import os

thread = None


def score_1s_tracker(secrets):
    while True:
        try:
            thread.sleeping = False
            yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).date()
            if yesterday.weekday() != 0:  # run only on monday
                thread.sleeping = True
                time.sleep(60 * 5)
                continue
            dir = f"data/user_score_stats/{yesterday}"
            if os.path.exists(dir):
                thread.sleeping = True
                time.sleep(60 * 5)
                continue
            os.makedirs(dir)
            time.sleep(60 * 15)  # wait 15 minutes
            leaderboard_pp = akatsuki.grab_user_leaderboards(
                mode=0, relax=1, pages=7, sort="magic"
            )
            beatmaps = beatmapdb.load_beatmaps(as_table=True)
            akatmaps = list()
            scores = list()
            for i in range(1000):
                if i < 100:
                    _scores = akatsuki.grab_user_best(
                        leaderboard_pp["users"][i]["id"], mode=0, relax=1, pages=4
                    )
                elif i < 400:
                    _scores = akatsuki.grab_user_best(
                        leaderboard_pp["users"][i]["id"], mode=0, relax=1, pages=2
                    )
                else:
                    _scores = akatsuki.grab_user_best(
                        leaderboard_pp["users"][i]["id"], mode=0, relax=1, pages=1
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
                    score["user"] = leaderboard_pp["users"][i]["id"]
                    scores.append(score)
            utils.save_json_gzip(scores, f"{dir}/top_plays.json.gz")
            beatmaps = list(beatmaps.values())
            beatmapdb.update_beatmaps(beatmaps, akatmaps)
            beatmapdb.save_beatmaps(beatmaps)
            users = list()
            for user in leaderboard_pp["users"]:
                count = akatsuki.grab_user_1s(user["id"], mode=0, relax=1, length=1)[
                    "total"
                ]
                users.append({"username": user["username"], "count": count})
            users.sort(key=lambda x: x["count"], reverse=True)
            content = list()
            rank = 1
            for user in users[:100]:
                content.append(
                    f"#{rank} {user['username']}: {user['count']} first places"
                )
                rank += 1
            utils.send_string_list(
                f'http://{secrets["flask2discord_host"]}:{secrets["flask2discord_port"]}/send_message',
                secrets["user_std_rx_1s"],
                f"{yesterday} changes",
                content,
            )
            utils.save_json_gzip(
                users,
                f"{dir}/top_1s.json.gz",
            )
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
