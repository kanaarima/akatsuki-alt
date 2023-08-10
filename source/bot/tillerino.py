import requests
import api.beatmapdb as beatmapdb
import api.akatsuki as akat
import api.utils as utils
import numpy

beatmaps = None
scores = list()


def load_scores():
    global scores, beatmaps
    beatmaps = beatmapdb.load_beatmaps(as_table=True)
    scores = utils.load_json_gzip("top_plays.json.gz")


def _map():
    return {
        "beatmap_id": 0,
        "total_frequency": 0,
        "farm_index": 0,
        "pp": 0,
        "mods": list(),
    }


def process_maps():
    global scores, beatmaps
    farm_index = {}
    for score in scores:
        if score["beatmap"] in farm_index:
            farm_index[score["beatmap"]] += 1
        else:
            farm_index[score["beatmap"]] = 1
    modded = dict()
    modded_final = list()
    for score in scores:
        mods = utils.get_mods(score["mods"])
        mods.remove("RX")
        if "NC" in mods:
            mods.remove("NC")
        if "SO" in mods:
            mods.remove("SO")
        mods = "".join(mods)
        if not score["beatmap"] in modded:
            modded[score["beatmap"]] = {}
        if not mods in modded[score["beatmap"]]:
            modded[score["beatmap"]][mods] = list()
        modded[score["beatmap"]][mods].append(score)
    for beatmap_id in modded.keys():
        for mods_key in modded[beatmap_id].keys():
            modded_scores = modded[beatmap_id][mods_key]
            modded_scores.sort(key=lambda x: x["pp"], reverse=True)
            avg_pp = 0
            selected = 0
            for modded_score in modded_scores:
                # Filter scores with a delta of 65+
                if (modded_scores[0]["pp"] - modded_score["pp"]) > 65:
                    continue
                selected += 1
                avg_pp += modded_score["pp"]

            avg_pp /= selected
            map = _map()
            map["pp"] = avg_pp
            map["beatmap_id"] = beatmap_id
            map["mods"] = [mods_key[i : i + 2] for i in range(0, len(mods_key), 2)]
            map["total_frequency"] = farm_index[beatmap_id]
            map["farm_index"] = selected
            modded_final.append(map)
    return modded_final


def recommend(
    total_pp,
    top100=None,
    mods=None,
    mods_exclude=None,
    pp_min=None,
    pp_max=None,
    quantity=1,
):
    key = "total_frequency"
    maps = process_maps()
    maps.sort(key=lambda x: x[key], reverse=True)
    min_pp = (total_pp / 20) - 40
    max_pp = (total_pp / 20) + 80
    if pp_min:
        min_pp = pp_min
    if pp_max:
        max_pp = pp_max
    possible_maps = list()
    for map in maps:
        if map["pp"] < min_pp or map["pp"] > max_pp:
            continue
        skip = False
        if mods:
            for mod in mods:
                if mod == "NM":
                    if map["mods"]:
                        skip = True
                    else:
                        map["mods"].append("NM")
                elif mod not in map["mods"]:
                    skip = True
        if mods_exclude:
            for mod in mods_exclude:
                if mod == "NM":
                    if map["mods"]:
                        skip = True
                    else:
                        map["mods"].append("NM")
                elif mod in map["mods"]:
                    skip = True
        if not skip:
            possible_maps.append(map)
    if top100:
        topmaps = dict()
        for score in top100["scores"]:
            topmaps[score["beatmap"]["beatmap_id"]] = score
        for possible_map in possible_maps:
            if possible_map["beatmap_id"] in topmaps:
                possible_maps.remove(possible_map)
    weights = list()
    for map in possible_maps:
        weights.append(get_weight(map))
    return random_choices(possible_maps, weights=weights, samples=quantity)


def get_weight(map):
    frequency = map["total_frequency"]
    mod_frequency = map["farm_index"]
    return float(max(frequency / 2, 300) * (mod_frequency))


def random_choices(data, weights, samples):
    normalised = numpy.asarray(weights)
    normalised /= normalised.sum()
    choices = numpy.random.choice(data, p=normalised, size=samples * 2)
    result = list()
    [result.append(x) for x in choices if x not in result]
    return result[:samples]


simple_cache = {}


def get_data(id):
    if id in simple_cache:
        return simple_cache[id]
    pp = requests.get(f"https://akatsuki.gg/api/v1/users/full?id={id}&relax=-1").json()[
        "stats"
    ][1]["std"]["pp"]
    top100 = akat.grab_user_best(id, mode=0, relax=1)
    simple_cache[id] = {"top_100": top100, "pp": pp}
    return simple_cache[id]


load_scores()
