import trackers.clan_lb_tracker as clan_lb_tracker
import api.beatmapdb as beatmapdb
import api.akatsuki as akatsuki
import api.utils as utils
import traceback
import datetime
import time
import glob
import os

thread = None


def _user(apiuser):
    user = {}
    user["id"] = apiuser["id"]
    user["username"] = apiuser["username"]
    user["country"] = apiuser["country"]
    user["registered"] = apiuser["registered_on"]
    user["latest_activity"] = apiuser["latest_activity"]
    user["statistics"] = {}
    return user


def _stats(apiuser):
    stats = {}
    stats["ranked_score"] = apiuser["chosen_mode"]["ranked_score"]
    stats["total_score"] = apiuser["chosen_mode"]["total_score"]
    stats["play_count"] = apiuser["chosen_mode"]["playcount"]
    stats["total_hits"] = apiuser["chosen_mode"]["total_hits"]
    stats["performance_points"] = apiuser["chosen_mode"]["pp"]
    stats["accuracy"] = apiuser["chosen_mode"]["accuracy"]
    stats["pp_rank"] = -1
    stats["score_rank"] = -1
    return stats


def user_lb_stats_tracker(secrets):
    while True:
        try:
            thread.sleeping = False
            yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).date()
            dir = f"data/user_lb_stats/"
            file = f"{dir}{yesterday}.json.gz"
            if os.path.exists(file):
                thread.sleeping = True
                time.sleep(60 * 5)
                continue
            time.sleep(60 * 10)  # wait 10 minutes
            os.makedirs(dir, exist_ok=True)
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
            leaderboard_score = [
                [
                    akatsuki.grab_user_leaderboards(
                        mode=0, relax=0, pages=1, sort="score"
                    ),
                    akatsuki.grab_user_leaderboards(
                        mode=0, relax=1, pages=1, sort="score"
                    ),
                    akatsuki.grab_user_leaderboards(
                        mode=0, relax=2, pages=1, sort="score"
                    ),
                ],
                [
                    akatsuki.grab_user_leaderboards(
                        mode=1, relax=0, pages=1, sort="score"
                    ),
                    akatsuki.grab_user_leaderboards(
                        mode=1, relax=1, pages=1, sort="score"
                    ),
                ],
                [
                    akatsuki.grab_user_leaderboards(
                        mode=2, relax=0, pages=1, sort="score"
                    ),
                    akatsuki.grab_user_leaderboards(
                        mode=2, relax=1, pages=1, sort="score"
                    ),
                ],
                [
                    akatsuki.grab_user_leaderboards(
                        mode=3, relax=0, pages=1, sort="score"
                    )
                ],
            ]
            users = dict()
            gamemodes = {
                "std_vn": (0, 0),
                "std_rx": (0, 1),
                "std_ap": (0, 2),
                "taiko_vn": (1, 0),
                "taiko_rx": (1, 1),
                "ctb_vn": (2, 0),
                "ctb_rx": (2, 1),
                "mania_vn": (3, 0),
            }
            for gamemode in gamemodes.keys():
                mode, relax = gamemodes[gamemode]
                rank = 1
                for apiuser in leaderboard_score[mode][relax]["users"]:
                    if apiuser["id"] not in users:
                        user = users[apiuser["id"]] = _user(apiuser)
                    else:
                        user = users[apiuser["id"]]
                    if gamemode not in user["statistics"]:
                        stats = user["statistics"][gamemode] = _stats(apiuser)
                    else:
                        stats = user["statistics"][gamemode]
                    stats["score_rank"] = rank
                    rank += 1
                rank = 1
                for apiuser in leaderboard_pp[mode][relax]["users"]:
                    if apiuser["id"] not in users:
                        user = users[apiuser["id"]] = _user(apiuser)
                    else:
                        user = users[apiuser["id"]]
                    if gamemode not in user["statistics"]:
                        stats = user["statistics"][gamemode] = _stats(apiuser)
                    else:
                        stats = user["statistics"][gamemode]
                    stats["pp_rank"] = rank
                    rank += 1
            for user in users.values():
                stats = {
                    "ranked_score": 0,
                    "total_score": 0,
                    "play_count": 0,
                    "total_hits": 0,
                    "performance_points": 0,
                    "accuracy": 0,
                    "pp_rank": 0,
                    "score_rank": 0,
                }
                for key in user["statistics"]:
                    akatsuki._addition_dict(stats, user["statistics"][key])
                stats["performance_points"] /= 8
                stats["accuracy"] /= 8
                user["statistics"]["overall"] = stats

            gamemodes["overall"] = 0

            def set_rank(statistics_key, rank_key, filter=None):
                for key in gamemodes.keys():
                    cl = list()
                    if filter and filter not in key:
                        continue
                    for user in users.values():
                        if not key in user["statistics"]:
                            continue
                        cl.append((user["id"], user["statistics"][key][statistics_key]))
                        cl.sort(key=lambda x: x[1], reverse=True)
                        rank = 1
                        for x in cl:
                            users[x[0]]["statistics"][key][rank_key] = rank
                            rank += 1

            set_rank("ranked_score", "score_rank", "overall")
            set_rank("performance_points", "pp_rank", "overall")
            utils.save_json_gzip(
                sorted(list(users.values()), key=lambda x: x["id"]),
                file,
            )
            pp = list()
            score = list()
            rank = 1
            for user in clan_lb_tracker.get_leaderboard(
                users.values(), "overall", "pp_rank"
            ):
                pp.append(
                    f"#{rank} {user['username']}: {user['statistics']['overall']['performance_points']} pp"
                )
                rank += 1
            rank = 1
            for user in clan_lb_tracker.get_leaderboard(
                users.values(), "overall", "score_rank"
            ):
                score.append(
                    f"#{rank} {user['username']}: {user['statistics']['overall']['ranked_score']} ranked score"
                )
                rank += 1
            utils.send_string_list(
                f'http://{secrets["flask2discord_host"]}:{secrets["flask2discord_port"]}/send_message',
                secrets["user_overall_score"],
                f"{yesterday} changes",
                score,
            )
            utils.send_string_list(
                f'http://{secrets["flask2discord_host"]}:{secrets["flask2discord_port"]}/send_message',
                secrets["user_overall_pp"],
                f"{yesterday} changes",
                pp,
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
