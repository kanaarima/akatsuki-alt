import api.akatsuki as akat
import api.webhook as wh
from datetime import date
import unicodedata
import traceback
import datetime
import copy
import json
import time
import os

thread = None


def get_data_pp():
    data = dict()
    data["std_vn_pp"] = akat.grab_clan_ranking(mode=0,
                                               relax=0,
                                               pages=4,
                                               pp=True)
    data["std_rx_pp"] = akat.grab_clan_ranking(mode=0,
                                               relax=1,
                                               pages=4,
                                               pp=True)
    data["std_ap_pp"] = akat.grab_clan_ranking(mode=0,
                                               relax=2,
                                               pages=4,
                                               pp=True)
    data["taiko_vn_pp"] = akat.grab_clan_ranking(mode=1,
                                                 relax=0,
                                                 pages=4,
                                                 pp=True)
    data["taiko_rx_pp"] = akat.grab_clan_ranking(mode=1,
                                                 relax=1,
                                                 pages=4,
                                                 pp=True)
    data["ctb_vn_pp"] = akat.grab_clan_ranking(mode=2,
                                               relax=0,
                                               pages=4,
                                               pp=True)
    data["ctb_rx_pp"] = akat.grab_clan_ranking(mode=2,
                                               relax=1,
                                               pages=4,
                                               pp=True)
    data["mania_vn_pp"] = akat.grab_clan_ranking(mode=3,
                                                 relax=0,
                                                 pages=4,
                                                 pp=True)
    data["overall_pp"] = {"clans": get_overall_pp(data)}
    return data


def get_data_1s():
    data = dict()
    data["std_vn_1s"] = akat.grab_clan_ranking(mode=0, relax=0)
    data["std_rx_1s"] = akat.grab_clan_ranking(mode=0, relax=1)
    data["std_ap_1s"] = akat.grab_clan_ranking(mode=0, relax=2)
    data["taiko_vn_1s"] = akat.grab_clan_ranking(mode=1, relax=0)
    data["taiko_rx_1s"] = akat.grab_clan_ranking(mode=1, relax=1)
    data["ctb_vn_1s"] = akat.grab_clan_ranking(mode=2, relax=0)
    data["ctb_rx_1s"] = akat.grab_clan_ranking(mode=2, relax=1)
    data["mania_vn_1s"] = akat.grab_clan_ranking(mode=3, relax=0)
    data["overall_1s"] = {"clans": get_overall_1s(data)}
    return data


def get_overall_1s(data):
    res = list()
    clans = dict()
    clans_metadata = dict()
    for key in data.keys():
        for clan in data[key]["clans"]:
            if clan["clan"] in clans:
                clans[clan["clan"]] += clan["count"]
            else:
                clans[clan["clan"]] = clan["count"]
                clans_metadata[clan["clan"]] = clan
    sortedclans = dict(sorted(clans.items(), key=lambda x: x[1], reverse=True))
    for k, v in sortedclans.items():
        clan = copy.deepcopy(clans_metadata[k])
        clan["count"] = v
        res.append(clan)
    return res[:100]


def get_overall_ranked_score(data_pp):
    res = list()
    clans = dict()
    clans_metadata = dict()
    for clan in data_pp["clans"]:
        if clan["id"] in clans:
            clans[clan["id"]] += clan["chosen_mode"]["ranked_score"]
        else:
            clans[clan["id"]] = clan["chosen_mode"]["ranked_score"]
            clans_metadata[clan["id"]] = clan
    sortedclans = dict(sorted(clans.items(), key=lambda x: x[1], reverse=True))
    for k, v in sortedclans.items():
        clan = copy.deepcopy(clans_metadata[k])
        clan["chosen_mode"]["ranked_score"] = v
        res.append(clan)
    return res[:100]


def get_overall_pp(data):
    res = list()
    clans = dict()
    clans_metadata = dict()
    for key in data.keys():
        for clan in data[key]["clans"]:
            if clan["id"] in clans:
                clans[clan["id"]] += clan["chosen_mode"]["pp"]
            else:
                clans[clan["id"]] = clan["chosen_mode"]["pp"]
                clans_metadata[clan["id"]] = clan
    sortedclans = dict(sorted(clans.items(), key=lambda x: x[1], reverse=True))
    for k, v in sortedclans.items():
        clan = copy.deepcopy(clans_metadata[k])
        clan["chosen_mode"]["pp"] = v / 8
        res.append(clan)
    return res[:100]


def format_1s_string(clan, rank, rank_gain, count_gain):
    if rank_gain < 0:
        gain_str = f"({rank_gain})"
    elif rank_gain > 0:
        gain_str = f"(+{rank_gain})"
    else:
        gain_str = ""
    if count_gain < 0:
        gain_str2 = f"({count_gain})"
    elif count_gain > 0:
        gain_str2 = f"(+{count_gain})"
    else:
        gain_str2 = ""
    type_str = "First places"
    clan_tag = unicodedata.normalize("NFC", clan["tag"])
    clan_name = unicodedata.normalize("NFC", clan["name"])
    return f"#{rank} {clan_name} [{clan_tag}] {gain_str} {type_str}: {clan['count']} {gain_str2}"


def format_pp_string(clan, rank, rank_gain, count_gain):
    if rank_gain < 0:
        gain_str = f"({rank_gain})"
    elif rank_gain > 0:
        gain_str = f"(+{rank_gain})"
    else:
        gain_str = ""
    if count_gain < 0:
        gain_str2 = f"({count_gain})"
    elif count_gain > 0:
        gain_str2 = f"(+{count_gain})"
    else:
        gain_str2 = ""
    type_str = "Performance Points"
    clan_name = unicodedata.normalize("NFC", clan["name"])
    return f"#{rank} {clan_name} {gain_str} {type_str}: {clan['chosen_mode']['pp']}pp {gain_str2}"


def format_score_string(clan, rank, rank_gain, count_gain):
    if rank_gain < 0:
        gain_str = f"({rank_gain})"
    elif rank_gain > 0:
        gain_str = f"(+{rank_gain})"
    else:
        gain_str = ""
    if count_gain < 0:
        gain_str2 = f"({count_gain})"
    elif count_gain > 0:
        gain_str2 = f"(+{count_gain})"
    else:
        gain_str2 = ""
    type_str = "Ranked score"
    clan_name = unicodedata.normalize("NFC", clan["name"])
    return f"#{rank} {clan_name} {gain_str} {type_str}: {int(clan['chosen_mode']['ranked_score']/1000000)}mil {gain_str2}"


def track_clan_leaderboards(secrets):
    while True:
        try:
            thread.sleeping = False
            today = date.today()
            yesterday = (datetime.datetime.today() -
                         datetime.timedelta(days=1)).date()
            filename = f"data/clan_lb/{today}.json"
            olddata = None
            if os.path.exists(filename):
                thread.sleeping = True
                time.sleep(60 * 5)
                continue
            if os.path.exists(f"data/clan_lb/{yesterday}.json"):
                with open(f"data/clan_lb/{yesterday}.json") as f:
                    olddata = json.load(f)
            os.makedirs("data/clan_lb/", exist_ok=True)
            data_1s = get_data_1s()
            data_pp = get_data_pp()
            ranked_score = get_overall_ranked_score(data_pp["overall_pp"])
            with open(filename, "w") as f:
                json.dump(data_1s | data_pp
                          | {"overall_ranked_score": {
                              "clans": ranked_score
                          }},
                          f,
                          indent=4)
            for key in data_1s.keys():
                clan_list = list()
                rank = 0
                if not data_1s[key]["clans"]:
                    continue
                for clan in data_1s[key]["clans"]:
                    rank += 1
                    rank_gain = 0
                    count_gain = 0
                    if olddata and key in olddata:
                        rankold = 0
                        for clanold in olddata[key]["clans"]:
                            rankold += 1
                            if clanold["clan"] == clan["clan"]:
                                count_gain = clan["count"] - clanold["count"]
                                rank_gain = rankold - rank
                    clan_list.append(
                        format_1s_string(clan, rank, rank_gain, count_gain))
                if key in secrets:
                    wh.send_string_list(secrets["flask2discord"], secrets[key],
                                        f"{today} changes", clan_list)
            for key in data_pp.keys():
                clan_list = list()
                rank = 0
                if not data_pp[key]["clans"]:
                    continue
                for clan in data_pp[key]["clans"][:100]:
                    rank += 1
                    rank_gain = 0
                    count_gain = 0
                    if olddata and key in olddata:
                        rankold = 0
                        for clanold in olddata[key]["clans"]:
                            rankold += 1
                            if clanold["id"] == clan["id"]:
                                count_gain = clan["chosen_mode"]["pp"] - clan[
                                    "chosen_mode"]["pp"]
                                rank_gain = rankold - rank
                    clan_list.append(
                        format_pp_string(clan, rank, rank_gain, count_gain))
                if key in secrets:
                    wh.send_string_list(secrets["flask2discord"], secrets[key],
                                        f"{today} changes", clan_list)
            clan_list = list()
            rank = 0
            for clan in ranked_score:
                rank += 1
                rank_gain = 0
                count_gain = 0
                if olddata and "overall_ranked_score" in olddata:
                    rankold = 0
                    for clanold in olddata["overall_ranked_score"]["clans"]:
                        rankold += 1
                        if clanold["id"] == clan["id"]:
                            count_gain = clan["chosen_mode"][
                                "ranked_score"] - clan["chosen_mode"][
                                    "ranked_score"]
                            rank_gain = rankold - rank
                clan_list.append(
                    format_score_string(clan, rank, rank_gain, count_gain))
            if "overall_ranked_score" in secrets:
                wh.send_string_list(secrets["flask2discord"],
                                    secrets["overall_ranked_score"],
                                    f"{today} changes", clan_list)
        except Exception as e:
            print(e)
            if "error_channel" in secrets:
                wh.send_string_list(
                    secrets["flask2discord"], secrets["error_channel"],
                    f"Error in {__name__}",
                    (e.__class__.__name__, str(e), traceback.format_exc()))
            time.sleep(10)
