import api.utils as utils
import api.bancho as bancho
import time
import csv
import os


def load_beatmaps(as_table=False):
    if not os.path.exists("data/beatmaps.json.gz"):
        save_beatmaps(list())
        return list()
    data = utils.load_json_gzip("data/beatmaps.json.gz")
    if as_table:
        table = dict()
        for map in data:
            table[map["beatmap_id"]] = map
        return table
    return data


def save_beatmaps(data: list):
    utils.save_json_gzip(data, "data/beatmaps.json.gz")


def _blank_beatmap():
    return {
        "beatmap_id": 0,
        "beatmap_set_id": 0,
        "stars": 0,
        "stars_aim": 0,
        "stars_speed": 0,
        "artist": "",
        "title": "",
        "difficulty": "",
        "source": "",
        "CS": 0,
        "OD": 0,
        "AR": 0,
        "HP": 0,
        "length": 0,
        "length_drain": 0,
    }


def update_beatmaps(data: list, maps: list, overwrite=False):
    table = dict()
    for beatmap in data:
        table[beatmap["beatmap_id"]] = beatmap
    for beatmap in maps:
        if beatmap["beatmap_id"] not in table:
            data.append(beatmap)
        elif overwrite:
            data.remove(table[beatmap["beatmap_id"]])
            data.append(beatmap)


def convert_osualt_csv_str(values):
    # beatmap_id,approved,submit_date,approved_date,last_update,artist,set_id,bpm,creator,creator_id,stars,diff_aim,diff_speed,cs,od,ar,hp,drain,source,genre,language,title,length,diffname,file_md5,mode,tags,favorites,rating,playcount,passcount,circles,sliders,spinners,maxcombo,storyboard,video,download_unavailable,audio_unavailable
    map = _blank_beatmap()
    map["source"] = "osualt"
    map["beatmap_id"] = int(values[0])
    map["beatmap_set_id"] = int(values[6])
    map["artist"] = values[5]
    map["stars"] = float(values[10])
    map["stars_aim"] = float(values[11])
    map["stars_speed"] = float(values[12])
    map["CS"] = float(values[13])
    map["OD"] = float(values[14])
    map["AR"] = float(values[15])
    map["HP"] = float(values[16])
    map["length"] = float(values[22])
    map["length_drain"] = float(values[17])
    map["title"] = values[21]
    map["difficulty"] = values[23]
    return map


def convert_akatapi(data, source="akatsuki_1s"):
    songname, difficulty = data["song_name"].rsplit("[", 1)
    map = _blank_beatmap()
    map["source"] = source
    map["beatmap_id"] = data["beatmap_id"]
    map["beatmap_set_id"] = data["beatmapset_id"]
    map["artist"] = songname.split("-", 1)[0]
    map["title"] = songname.split("-", 1)[1]
    map["difficulty"] = difficulty[: len(difficulty) - 1]
    map["stars"] = data["difficulty"]
    return map


def load_osualt_csv():
    beatmaps = load_beatmaps()
    with open("osualt.csv") as f:
        csv_file = csv.reader(f, delimiter=",")
        csv_maps = list()
        for values in csv_file:
            if values[0] == "beatmap_id":  # description string
                continue
            csv_maps.append(convert_osualt_csv_str(values))
    update_beatmaps(beatmaps, csv_maps, overwrite=True)
    save_beatmaps(beatmaps)


def repair_maps(data):
    for map in data:
        repair = False
        if map["stars"] == 0:
            repair = True
        if "OD" not in map:
            repair = True
        if not repair:
            continue
        empty = _blank_beatmap()
        for key in empty.keys():
            if key not in map:
                map[key] = empty[key]
        try:
            apimap = bancho.client.beatmap(beatmap_id=map["beatmap_id"])
            attr = bancho.client.beatmap_attributes(
                beatmap_id=map["beatmap_id"]
            ).attributes
            time.sleep(2)
        except Exception as e:
            print(e)
            time.sleep(1)
            continue
        map["artist"] = apimap._beatmapset.artist
        map["title"] = apimap._beatmapset.title
        map["difficulty"] = apimap.version
        map["stars"] = attr.star_rating
        map["stars_speed"] = attr.aim_difficulty
        map["stars_aim"] = attr.speed_difficulty
        map["CS"] = apimap.cs
        map["OD"] = attr.overall_difficulty
        map["AR"] = attr.approach_rate
        map["length"] = apimap.total_length
        map["length_drain"] = apimap.drain
