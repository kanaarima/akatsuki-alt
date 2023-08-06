import api.akatsuki as akat
import api.utils as utils
import traceback
import datetime
import time
import os

thread = None

lb_keys = [
    "std_vn",
    "std_rx",
    "std_ap",
    "taiko_vn",
    "taiko_rx",
    "ctb_vn",
    "ctb_rx",
    "mania_vn",
    "overall",
]
rank_keys = {
    "score_rank": ("Ranked score", "ranked_score"),
    "pp_rank": ("Performance points", "performance_points"),
    "1s_rank": ("First places", "first_places"),
}


def format_string(clan, type, gamemode, rank_gain, count_gain):
    if rank_gain < 0:
        gain_str = f"({rank_gain})"
    elif rank_gain > 0:
        gain_str = f"(+{rank_gain})"
    else:
        gain_str = ""
    if count_gain < 0:
        gain_str2 = f"({format_number(count_gain)})"
    elif count_gain > 0:
        gain_str2 = f"(+{format_number(count_gain)})"
    else:
        gain_str2 = ""
    tag = f" [{clan['tag']}]" if clan["tag"] else ""
    keys = rank_keys[type]
    return f"#{clan['statistics'][gamemode][type]} {clan['name']}{tag} {gain_str} {keys[0]}: {format_number(clan['statistics'][gamemode][keys[1]])} {gain_str2}"


def format_number(actual_number):
    number = actual_number
    if actual_number < 0:
        number *= -1
    if number < 1000:
        return str(actual_number)
    if number < 1000000:
        return f"{actual_number:,}"
    if number < 1000000000:
        return f"{actual_number/1000000:.1f}m"
    else:
        return f"{actual_number/1000000000:.1f}b"


def get_leaderboard(data, gamemode_key, rank_key, limit=100):
    res = list()
    for clan in data:
        if gamemode_key in clan["statistics"]:
            if clan["statistics"][gamemode_key][rank_key]:
                res.append(clan)
    res.sort(key=lambda clan: clan["statistics"][gamemode_key][rank_key])
    return res[:limit]


def track_clan_leaderboards(secrets):
    URL = f'http://{secrets["flask2discord_host"]}:{secrets["flask2discord_port"]}/send_message'
    while True:
        try:
            thread.sleeping = False
            today = (datetime.datetime.today() - datetime.timedelta(days=1)).date()
            yesterday = (datetime.datetime.today() - datetime.timedelta(days=2)).date()
            filename = f"data/clan_lb/{today}.json.gz"
            filename_old = f"data/clan_lb/{yesterday}.json.gz"
            table = {}
            if os.path.exists(filename):
                thread.sleeping = True
                time.sleep(60 * 5)
                continue
            if os.path.exists(filename_old):
                for clan in utils.load_json_gzip(filename_old):
                    table[clan["id"]] = clan
            os.makedirs("data/clan_lb/", exist_ok=True)
            data = akat.fetch_clan_data()
            utils.save_json_gzip(data, filename)
            os.system(f"cp {filename} data/clan_lb/latest.json.gz")
            for lb_key in lb_keys:
                for rank_key in rank_keys.keys():
                    clans = list()
                    for clan in get_leaderboard(data, lb_key, rank_key, 100):
                        rank_gain = 0
                        count_gain = 0
                        if (
                            clan["id"] in table
                            and lb_key in table[clan["id"]]["statistics"]
                        ):
                            rank_gain = (
                                clan["statistics"][lb_key][rank_key]
                                - table[clan["id"]]["statistics"][lb_key][rank_key]
                            )
                            count_gain = (
                                clan["statistics"][lb_key][rank_keys[rank_key][1]]
                                - table[clan["id"]]["statistics"][lb_key][
                                    rank_keys[rank_key][1]
                                ]
                            )
                        clans.append(
                            format_string(clan, rank_key, lb_key, rank_gain, count_gain)
                        )
                    key = f"{lb_key}_{rank_key.split('_')[0]}"
                    if key in secrets:
                        utils.send_string_list(
                            URL, secrets[key], f"{today} changes", clans
                        )

        except Exception as e:
            print(e)
            if "error_channel" in secrets:
                utils.send_string_list(
                    URL,
                    secrets["error_channel"],
                    f"Error in {__name__}",
                    (e.__class__.__name__, str(e), traceback.format_exc()),
                )
            time.sleep(10)
