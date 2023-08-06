import api.utils as utils
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
        "artist": "",
        "title": "",
        "difficulty": "",
        "source": "",
    }


def update_beatmaps(data: list, maps: list):
    table = dict()
    for beatmap in data:
        table[beatmap["beatmap_id"]] = beatmap
    for beatmap in maps:
        if beatmap["beatmap_id"] not in table:
            data.append(beatmap)


def convert_osualt_csv_str(values):
    # beatmap_id,approved,submit_date,approved_date,last_update,artist,set_id,bpm,creator,creator_id,stars,diff_aim,diff_speed,cs,od,ar,hp,drain,source,genre,language,title,length,diffname,file_md5,mode,tags,favorites,rating,playcount,passcount,circles,sliders,spinners,maxcombo,storyboard,video,download_unavailable,audio_unavailable
    map = _blank_beatmap()
    map["source"] = "osualt"
    map["beatmap_id"] = int(values[0])
    map["beatmap_set_id"] = int(values[6])
    map["artist"] = values[5]
    map["stars"] = float(values[10])
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
    update_beatmaps(beatmaps, csv_maps)
    save_beatmaps(beatmaps)
