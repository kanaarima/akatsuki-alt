import requests
import datetime
import time

scorelb = dict()
last_fetch = None
lock = False
modes = {"std": 0, "taiko": 1, "ctb": 2, "mania": 3}


def grab_stats(userid):
    update_scorelb()
    req = requests.get(f"https://akatsuki.gg/api/v1/users/full?id={userid}&relax=-1")
    if req.status_code != 200 and req.status_code < 500:  # ignore code 500
        raise ApiException(f"Error code {req.status_code}")
    data = req.json()
    rx = 0
    for dikt in scorelb:
        for key in dikt.keys():
            global_score, country_score = get_score_rank(
                userid, key, rx, data["country"]
            )
            count_1s = grab_user_1s(userid=userid, mode=modes[key], relax=rx, length=1)[
                "total"
            ]
            data["stats"][rx][key]["count_1s"] = count_1s
            data["stats"][rx][key]["global_rank_score"] = global_score
            data["stats"][rx][key]["country_rank_score"] = country_score
        rx += 1
    return data


def grab_clan_ranking(mode=0, relax=0, page=1, pages=1, pp=False):
    """_summary_
    Args:
        mode (int, optional): Game mode. (0: std, 1: taiko, 2: catch, 3: mania) Defaults to 0.
        relax (int, optional): Rx leaderboards. (0: vanilla, 1: relax, 2: autopilot) Defaults to 0.
        page (int, optional): Page. Defaults to 1.
        pages (int, optional): Pages to fetch. page is ignored if pages is over 1. Defaults to 50.
        pp (bool, optional): Use PP leaderboards. Defaults to False (#1 lb).
    """
    if pages > 1:
        req = grab_clan_ranking(mode, relax, 1, 1, pp)
        for p in range(2, pages + 1):
            req["clans"].extend(grab_clan_ranking(mode, relax, p, 1, pp)["clans"])
        return req
    handle_api_throttling()
    if pp:
        req = requests.get(
            f"https://akatsuki.gg/api/v1/clans/stats/all?m={mode}&p={page}&l=50&rx={relax}"
        )
    else:
        req = requests.get(
            f"https://akatsuki.gg/api/v1/clans/stats/first?m={mode}&p={page}&l=50&rx={relax}"
        )
    if req.status_code != 200:
        raise ApiException(f"Error code {req.status_code}")
    return req.json()


def grab_clan_stats(clan_id, mode=0, relax=0):
    handle_api_throttling()
    req = requests.get(
        f"https://akatsuki.gg/api/v1/clans/stats?id={clan_id}&m={mode}&rx={relax}"
    )
    if req.status_code != 200 and req.status_code < 500:  # ignore code 500
        raise ApiException(f"Error code {req.status_code}")
    return req.json()


def grab_all_clan_stats(clan_id):
    reqs = list()
    reqs.append(grab_clan_stats(clan_id, mode=0, relax=0))
    reqs.append(grab_clan_stats(clan_id, mode=0, relax=1))
    reqs.append(grab_clan_stats(clan_id, mode=0, relax=2))
    reqs.append(grab_clan_stats(clan_id, mode=1, relax=0))
    reqs.append(grab_clan_stats(clan_id, mode=1, relax=1))
    reqs.append(grab_clan_stats(clan_id, mode=2, relax=0))
    reqs.append(grab_clan_stats(clan_id, mode=2, relax=1))
    reqs.append(grab_clan_stats(clan_id, mode=3, relax=0))
    return reqs


def grab_all_clan_stats_avg(clan_id):
    reqs = grab_all_clan_stats(clan_id)
    stats = {
        "ranked_score": 0,
        "total_score": 0,
        "replay_watched": 0,
        "total_hits": 0,
        "pp": 0,
    }
    for req in reqs:
        stats["ranked_score"] += req["clan"]["chosen_mode"]["ranked_score"]
        stats["total_score"] += req["clan"]["chosen_mode"]["total_score"]
        stats["replay_watched"] += req["clan"]["chosen_mode"]["replays_watched"]
        stats["total_hits"] += req["clan"]["chosen_mode"]["total_hits"]
        stats["pp"] += req["clan"]["chosen_mode"]["pp"]
    stats["pp"] /= 8
    return stats


def grab_score_leaderboards(mode=0, relax=0, page=1, length=500):
    time.sleep(0.4)
    req = requests.get(
        f"https://akatsuki.gg/api/v1/leaderboard?mode={mode}&p={page}&l={length}&country=&rx={relax}&sort=score"
    )
    if req.status_code != 200 and req.status_code < 500:  # ignore code 500
        raise ApiException(f"Error code {req.status_code}")
    return req.json()


def grab_user_1s(userid, mode=0, relax=0, page=1, length=10):
    time.sleep(0.2)
    req = requests.get(
        f"https://akatsuki.gg/api/v1/users/scores/first?mode={mode}&p={page}&l={length}&rx={relax}&id={userid}&uid={userid}"
    )
    if req.status_code != 200 and req.status_code < 500:  # ignore code 500
        raise ApiException(f"Error code {req.status_code}")
    return req.json()


def get_score_rank(userid, mode, relax, country):
    update_scorelb()
    global_rank = 1
    country_rank = 1
    for user in scorelb[relax][mode]:
        if user["id"] == userid:
            return global_rank, country_rank
        global_rank += 1
        if user["country"] == country:
            country_rank += 1
    return 0, 0


def update_scorelb():
    global lock, last_fetch, scorelb
    while lock:
        time.sleep(1)
    lock = True
    if not last_fetch or (datetime.datetime.now() - last_fetch) > datetime.timedelta(
        minutes=30
    ):
        last_fetch = datetime.datetime.now()
        scorelb = [
            {"std": list(), "taiko": list(), "ctb": list(), "mania": list()},
            {"std": list(), "taiko": list(), "ctb": list()},
            {"std": list()},
        ]
        scorelb[0]["std"] = grab_score_leaderboards(mode=0, relax=0)["users"]
        scorelb[1]["std"] = grab_score_leaderboards(mode=0, relax=1)["users"]
        scorelb[2]["std"] = grab_score_leaderboards(mode=0, relax=2)["users"]
        scorelb[0]["taiko"] = grab_score_leaderboards(mode=1, relax=0)["users"]
        scorelb[1]["taiko"] = grab_score_leaderboards(mode=1, relax=1)["users"]
        scorelb[0]["ctb"] = grab_score_leaderboards(mode=2, relax=0)["users"]
        scorelb[1]["ctb"] = grab_score_leaderboards(mode=2, relax=1)["users"]
        scorelb[0]["mania"] = grab_score_leaderboards(mode=3, relax=0)["users"]
        for i in range(2, 4 + 1):
            scorelb[0]["std"].extend(
                grab_score_leaderboards(mode=0, relax=0, page=i)["users"]
            )
            scorelb[1]["std"].extend(
                grab_score_leaderboards(mode=0, relax=1, page=i)["users"]
            )

    lock = False


def handle_api_throttling():
    time.sleep(1)


class ApiException(Exception):
    pass
