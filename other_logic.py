# -*- coding: utf-8 -*-
from io import StringIO
import requests
import webbrowser
import datetime
import json
import time


def timesort(log):
    times = log[2:23]
    return time.mktime(datetime.datetime.strptime(times, "%m/%d/%Y - %H:%M:%S").timetuple())


# given a steamid3 (starts with U:), returns the corresponding steamid64 a.k.a community steamid
# blatantly stolen from github user bcahue
def usteamid_to_commid(usteamid):
    steamid64ident = 76561197960265728
    for ch in ['[', ']']:
        if ch in usteamid:
            usteamid = usteamid.replace(ch, '')
    usteamid_split = usteamid.split(':')
    commid = int(usteamid_split[2]) + steamid64ident
    return commid


def str_to_bool(string):
    if str(string).lower() in ("true", "t", "1"):
        return True
    if str(string).lower() in ("false", "f", "0"):
        return False
    raise ValueError("Given str cannot be parsed to bool.")


def upload_logs(first_tag, second_tag, map_name, api_key, version, combined_logs):
    payload = {
        "title": (first_tag + " vs " + second_tag)[0:40],
        "map": map_name[0:24],
        "key": str(api_key),
        "uploader": "Auto Log Combiner " + version
    }
    files = {
        "logfile": StringIO(combined_logs)
    }
    r = requests.post("https://logs.tf/upload", data=payload, files=files)
    x = json.loads(r.text)
    if x["success"]:
        webbrowser.open_new_tab("https://www.logs.tf" + x["url"])
    else:
        raise RuntimeError(r.text)
