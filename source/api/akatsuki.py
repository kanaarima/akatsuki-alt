import requests
import time


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
            req["clans"].extend(
                grab_clan_ranking(mode, relax, p, 1, pp)["clans"])
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
        "pp": 0
    }
    for req in reqs:
        stats["ranked_score"] += req["clan"]["chosen_mode"]["ranked_score"]
        stats["total_score"] += req["clan"]["chosen_mode"]["total_score"]
        stats["replay_watched"] += req["clan"]["chosen_mode"][
            "replays_watched"]
        stats["total_hits"] += req["clan"]["chosen_mode"]["total_hits"]
        stats["pp"] += req["clan"]["chosen_mode"]["pp"]
    stats["pp"] /= 8
    return stats


def handle_api_throttling():
    time.sleep(1)


class ApiException(Exception):
    pass