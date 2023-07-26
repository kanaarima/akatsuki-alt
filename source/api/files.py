import json
import gzip


def load_json_gzip(filepath):
    with gzip.open(filepath, "r") as fin:
        return json.loads(fin.read().decode("utf-8"))


def save_json_gzip(data, filepath):
    with gzip.open(filepath, "w") as fout:
        fout.write(json.dumps(data).encode("utf-8"))
