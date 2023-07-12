import api.akatsuki as akat
import api.webhook as wh
from datetime import date
import json
import time
import os
import datetime
import unicodedata 

thread = None

def track_clan_leaderboards(secrets):
    while True:
        thread.sleeping = False
        today = date.today()
        yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).date()
        filename = f"data/clan_lb/{today}.json"
        olddata = None
        if os.path.exists(filename):
            thread.sleeping = True
            time.sleep(60*5)
            continue
        if os.path.exists(f"data/clan_lb/{yesterday}.json"):
            with open(f"data/clan_lb/{yesterday}.json") as f:
                olddata = json.load(f)
        os.makedirs("data/clan_lb/", exist_ok=True)
        data = dict()
        data["std_vn_1s"] = akat.grab_clan_ranking(mode=0, relax=0)
        data["std_rx_1s"] = akat.grab_clan_ranking(mode=0, relax=1)
        data["std_ap_1s"] = akat.grab_clan_ranking(mode=0, relax=2)
        data["taiko_vn_1s"] = akat.grab_clan_ranking(mode=1, relax=0)
        data["taiko_rx_1s"] = akat.grab_clan_ranking(mode=1, relax=1)
        data["ctb_vn_1s"] = akat.grab_clan_ranking(mode=2, relax=0)
        data["ctb_rx_1s"] = akat.grab_clan_ranking(mode=2, relax=1)
        data["mania_vn_1s"] = akat.grab_clan_ranking(mode=3, relax=0)
        #data["mania_rx_1s"] = akat.grab_clan_ranking(mode=3, relax=1)
        #data["std_vn_pp"] = akat.grab_clan_ranking(mode=0, relax=0, pp=True)
        #data["std_rx_pp"] = akat.grab_clan_ranking(mode=0, relax=1, pp=True)
        #data["std_ap_pp"] = akat.grab_clan_ranking(mode=0, relax=2, pp=True)
        #data["taiko_vn_pp"] = akat.grab_clan_ranking(mode=1, relax=0, pp=True)
        #data["taiko_rx_pp"] = akat.grab_clan_ranking(mode=1, relax=1, pp=True)
        #data["ctb_vn_pp"] = akat.grab_clan_ranking(mode=2, relax=0, pp=True)
        #data["ctb_rx_pp"] = akat.grab_clan_ranking(mode=2, relax=1, pp=True)
        #data["mania_vn_pp"] = akat.grab_clan_ranking(mode=3, relax=0, pp=True)
        #data["mania_rx_pp"] = akat.grab_clan_ranking(mode=3, relax=1, pp=True)
        data["overall_1s"] = {"clans": list()}
        clans = dict()
        clans_metadata=dict()
        for key in data.keys():
            if not key.endswith("1s"):
                continue
            for clan in data[key]["clans"]:
                if clan["clan"] in clans:
                    clans[clan["clan"]] += clan["count"]
                else:
                    clans[clan["clan"]] = clan["count"]
                    clans_metadata[clan["clan"]] = clan
        sortedclans = dict(sorted(clans.items(), key=lambda x:x[1], reverse=True))
        for k,v in sortedclans.items():
            clan = clans_metadata[k].copy()
            clan["count"] = v
            data["overall_1s"]["clans"].append(clan)
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        for key in data.keys():
            l = list()
            rank = 0
            if not data[key]["clans"]:
                continue
            for clan in data[key]["clans"]:
                rank += 1
                rank_gain = 0
                count_gain = 0
                if olddata and key in olddata:
                    rankold = 0
                    for clanold in olddata[key]["clans"]:
                        rankold += 1
                        if clanold["clan"] == clan["clan"]:
                            count_gain = clan["count"]-clanold["count"]
                            rank_gain = rankold-rank
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
                type_str = "First places" if key.endswith("1s") else "Performance Points"
                if "tag" in clan:
                    clan_tag = unicodedata.normalize("NFC", clan["tag"])
                else:
                    continue
                if "name" in clan:
                    clan_name = unicodedata.normalize("NFC", clan["name"])
                else:
                    continue
                if "count" not in clan:
                    continue
                l.append(f"#{rank} {clan_name} [{clan_tag}] {gain_str} {type_str}: {clan['count']} {gain_str2}")
            wh.send_string_list(secrets[key], f"{today} changes", l)