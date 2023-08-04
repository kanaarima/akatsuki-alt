import requests
import datetime
import time
import api.utils as utils
from bs4 import BeautifulSoup

scorelb = dict()
last_fetch = None
scorelb_lock = utils.SimpleLock()
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
    global last_fetch, scorelb
    scorelb_lock.wait()
    scorelb_lock.block()
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

    scorelb_lock.unblock()


def handle_api_throttling():
    time.sleep(0.7)


def grab_clan_ranking_all(pages, pp):
    data = dict()
    data["std_vn"] = grab_clan_ranking(mode=0, relax=0, pages=pages, pp=pp)
    data["std_rx"] = grab_clan_ranking(mode=0, relax=1, pages=pages, pp=pp)
    data["std_ap"] = grab_clan_ranking(mode=0, relax=2, pages=pages, pp=pp)
    data["taiko_vn"] = grab_clan_ranking(mode=1, relax=0, pages=pages, pp=pp)
    data["taiko_rx"] = grab_clan_ranking(mode=1, relax=1, pages=pages, pp=pp)
    data["ctb_vn"] = grab_clan_ranking(mode=2, relax=0, pages=pages, pp=pp)
    data["ctb_rx"] = grab_clan_ranking(mode=2, relax=1, pages=pages, pp=pp)
    data["mania_vn"] = grab_clan_ranking(mode=3, relax=0, pages=pages, pp=pp)
    return data


def fetch_clan_members(clan_id):
    r = requests.get(f"https://akatsuki.gg/c/{clan_id}?mode=0&rx=1")
    if r.status_code != 200:
        return None
    if "Clan not found" in r.text:
        return None
    soup = BeautifulSoup(r.content, "lxml")
    members = list()
    for playerhref in soup.find_all("a", {"class": "player"}):
        members.append(int(playerhref["href"].split("/")[2]))
    return members


def _blank_clan():
    return {"name": "", "tag": "", "id": 0, "statistics": {}}


def _blank_stats():
    return {
        "performance_points": 0,
        "accuracy": 0,
        "ranked_score": 0,
        "total_score": 0,
        "play_count": 0,
        "first_places": 0,
        "pp_rank": 0,
        "score_rank": 0,
        "1s_rank": 0,
    }


def _addition_dict(target: dict, source: dict):
    for key in source.keys():
        if key in target:
            target[key] += source[key]


def fetch_clan_data():
    table = {}
    pp = grab_clan_ranking_all(pages=8, pp=True)
    firstplaces = grab_clan_ranking_all(pages=2, pp=False)
    for key in pp.keys():
        for api_clan in pp[key]["clans"]:
            if api_clan["id"] not in table:
                clan = table[api_clan["id"]] = _blank_clan()
                clan["name"] = api_clan["name"]
                clan["id"] = api_clan["id"]
            else:
                clan = table[api_clan["id"]]
            stats = _blank_stats()
            stats["ranked_score"] = api_clan["chosen_mode"]["ranked_score"]
            stats["total_score"] = api_clan["chosen_mode"]["total_score"]
            stats["play_count"] = api_clan["chosen_mode"]["playcount"]
            stats["accuracy"] = api_clan["chosen_mode"]["accuracy"]
            stats["performance_points"] = api_clan["chosen_mode"]["pp"]
            stats["pp_rank"] = api_clan["chosen_mode"]["global_leaderboard_rank"]
            clan["statistics"][key] = stats
    for key in firstplaces.keys():
        rank = 1
        for api_clan in firstplaces[key]["clans"]:
            if api_clan["clan"] not in table:  # clan == id for some reason
                clan = table[api_clan["clan"]] = _blank_clan()
                clan["name"] = api_clan["name"]
                clan["id"] = api_clan["clan"]
            else:
                clan = table[api_clan["clan"]]
            # For some reason there isn't tag info on pp clan leaderboards
            clan["tag"] = api_clan["tag"]
            if key in clan["statistics"]:
                stats = clan["statistics"][key]
            else:
                stats = clan["statistics"][key] = _blank_stats()
            stats["first_places"] = api_clan["count"]
            stats["1s_rank"] = rank
            rank += 1
    for clan in table.values():
        stats = _blank_stats()
        for key in clan["statistics"]:
            _addition_dict(stats, clan["statistics"][key])
        stats["performance_points"] /= 8
        stats["accuracy"] /= 8
        clan["statistics"]["overall"] = stats
    keys = [
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

    def set_rank(statistics_key, rank_key, filter=None):
        for key in keys:
            cl = list()
            if filter and filter not in key:
                continue
            for clan in table.values():
                if not key in clan["statistics"]:
                    continue
                cl.append((clan["id"], clan["statistics"][key][statistics_key]))
                cl.sort(key=lambda x: x[1], reverse=True)
                rank = 1
                for x in cl:
                    table[x[0]]["statistics"][key][rank_key] = rank
                    rank += 1

    set_rank("ranked_score", "score_rank")
    set_rank("performance_points", "pp_rank", "overall")
    set_rank("first_places", "1s_rank", "overall")

    # Probably theres a better way to do this but this works
    return sorted(list(table.values()), key=lambda x: x["id"])


class ApiException(Exception):
    pass
