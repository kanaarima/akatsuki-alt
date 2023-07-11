import requests
import time

def grab_clan_ranking(mode=0, relax=0, page=1, length=50, pp=False):
    """_summary_
    Args:
        mode (int, optional): Game mode. (0: std, 1: taiko, 2: catch, 3: mania) Defaults to 0.
        relax (int, optional): Rx leaderboards. (0: vanilla, 1: relax, 2: autopilot) Defaults to 0.
        page (int, optional): Page. Defaults to 1.
        length (int, optional): Length. Defaults to 50.
        pp (bool, optional): Use PP leaderboards. Defaults to False (#1 lb).
    """
    time.sleep(1)
    if pp:
        req = requests.get(f"https://akatsuki.gg/api/v1/clans/stats/all?m={mode}&p={page}&l={length}&rx={relax}")
    else:
        req = requests.get(f"https://akatsuki.gg/api/v1/clans/stats/first?m={mode}&p={page}&l={length}&rx={relax}")
    if req.status_code != 200:
        raise ApiException(f"Error code {req.status_code}")
    return req.json()

class ApiException(Exception):
    pass