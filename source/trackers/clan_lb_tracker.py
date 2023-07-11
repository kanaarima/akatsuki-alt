import api.akatsuki as akat
from datetime import date
import json
import time
import os

def track():
    while True:
        today = date.today()
        filename = f"data/clan_lb/{today}.json"
        if os.path.exists(filename):
            time.sleep(60*60)
            continue
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
        data["mania_rx_1s"] = akat.grab_clan_ranking(mode=3, relax=1)
        data["std_vn_pp"] = akat.grab_clan_ranking(mode=0, relax=0, pp=True)
        data["std_rx_pp"] = akat.grab_clan_ranking(mode=0, relax=1, pp=True)
        data["std_ap_pp"] = akat.grab_clan_ranking(mode=0, relax=2, pp=True)
        data["taiko_vn_pp"] = akat.grab_clan_ranking(mode=1, relax=0, pp=True)
        data["taiko_rx_pp"] = akat.grab_clan_ranking(mode=1, relax=1, pp=True)
        data["ctb_vn_pp"] = akat.grab_clan_ranking(mode=2, relax=0, pp=True)
        data["ctb_rx_pp"] = akat.grab_clan_ranking(mode=2, relax=1, pp=True)
        data["mania_vn_pp"] = akat.grab_clan_ranking(mode=3, relax=0, pp=True)
        data["mania_rx_pp"] = akat.grab_clan_ranking(mode=3, relax=1, pp=True)
        with open(filename, "w") as f:
            json.dump(data, f)
        # Do stuff