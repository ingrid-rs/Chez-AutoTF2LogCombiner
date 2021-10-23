# -*- coding: utf-8 -*-
from io import BytesIO, StringIO
import zipfile
import urllib.request as urllib2
# import urllib.parse as ulparse
import codecs
import requests
import time
import datetime
import webbrowser
import json
import os.path
from collections import OrderedDict


# from distutils.version import LooseVersion


def get_important(log):
    startline = 0
    endline = 0
    lc = 0
    tournament = False
    knownnames = []
    out = ""

    tournamentexists = True

    if "Tournament mode started" not in "".join(log):
        tournamentexists = False

    for line in log:
        if lc == 0:
            out = line + "\n"
        t = line.split(": ")
        if len(t) > 1:
            tcl = t[1]
            if tcl.startswith("Tournament mode started"):
                tournament = True
            if tcl.startswith('World triggered "Round_Start"') and (not tournament) and tournamentexists:
                startline = lc
                tournamentexists = False
            elif tcl.startswith("Log file closed."):
                endline = lc
        lc += 1
    if endline == 0:
        endline = lc - 1

    # minimize the log a tiny bit
    lc = len(log) - 1
    for line in reversed(log):
        t = line.split(": ")
        if len(t) > 1:
            tcl = t[1]
            if tcl[0] == '"':
                eventname = tcl[1:].split("><")[0]
                for n in knownnames:
                    if lc + 1000 < endline:
                        log[lc] = log[lc].replace(n, n[:1] + "<" + "".join(n.split("<")[-1:]))
                if len(eventname) > 0:
                    if eventname + ">" not in knownnames:
                        knownnames.append(eventname + ">")
        lc -= 1
    for line in log[startline:endline]:
        if not ('triggered "shot_hit"' in line or 'triggered "shot_fired"' in line):
            out += line
    return out


def getlog(logid):
    myzipfile = zipfile.ZipFile(BytesIO(urllib2.urlopen(
        "https://logs.tf/logs/log_" + str(logid) + ".log.zip").read()), "r")
    out = []
    for name in myzipfile.namelist():
        with myzipfile.open(name, "r") as readfile:
            for line in codecs.iterdecode(readfile, 'utf8', errors='ignore'):
                out.append(line)
    return out


def getmap(url):
    return urllib2.urlopen(url).read().decode('utf-8').split('<h3 id="log-map">')[1].split("</h3>")[0]


def loadsettings():
    i = 0
    with open("settings") as file:
        ro = file.read().split("\n")
    for t in op:
        options[t] = ro[i]
        i += 1


def optmenu(question, option):
    maxv = len(option)
    while True:
        print(question)
        for i in range(len(option)):
            print("   " + str(i + 1) + ".  " + option[i])
        a = input()
        if a.isdigit():
            a = int(a)
            if 0 < a <= maxv:
                return a - 1
            else:
                print("Your choice is outside the range")
        else:
            print("Please input a number")


def timesort(log):
    times = log[2:23]
    return time.mktime(datetime.datetime.strptime(times, "%m/%d/%Y - %H:%M:%S").timetuple())


def usteamid_to_commid(usteamid):
    steamid64ident = 76561197960265728
    for ch in ['[', ']']:
        if ch in usteamid:
            usteamid = usteamid.replace(ch, '')
    usteamid_split = usteamid.split(':')
    commid = int(usteamid_split[2]) + steamid64ident
    return commid


def teamtag(usteamids, gamemode):
    min_count = (len(usteamids) + 1) // 2
    count_teams = {}

    for usteamid in usteamids:
        steamid = usteamid_to_commid(usteamid)
        hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
               'Accept-Encoding': 'none',
               'Accept-Language': 'en-US,en;q=0.8',
               'Connection': 'keep-alive'}
        teams = json.loads(urllib2.urlopen(urllib2.Request(
            "https://api.etf2l.org/player/" + str(steamid) + ".json", headers=hdr)).read())["player"]["teams"]
        if teams is not None:
            for team in teams:
                teamtype = team["type"]
                if gamemode == teamtype \
                        or gamemode == "6on6" and (teamtype == "National 6v6 Team" or teamtype == "LAN Team") \
                        or gamemode == "Highlander" and teamtype == "National Highlander Team":
                    if team["tag"] in count_teams.keys():
                        count_teams[team["tag"]] += 1
                    else:
                        count_teams[team["tag"]] = 1

    count_teams = sorted(count_teams.items(), key=lambda x: x[1], reverse=True)
    most = count_teams[0]
    if most[1] >= min_count:
        return most[0]
    return "mix"


def determine_gamemode(playercount):
    if playercount < 3:
        return "1on1"
    if 4 <= playercount < 7:
        return "2on2"
    if 11 <= playercount < 17:
        return "6on6"
    if 17 <= playercount:
        return "Highlander"
    return "Other"


def team_sort(all_players, red_players, blue_players, isFirst):
    player_ids = list(all_players.keys())
    for j in range(len(all_players)):
        player_id = player_ids[j]
        if isFirst:
            if all_players[player_id]["team"] == "Red":
                red_players.append(player_id)
            else:
                blue_players.append(player_id)
        else:
            if player_id not in red_players and player_id not in blue_players:
                new_team = all_players[player_id]["team"]
                other_players = list(all_players.keys())
                other_players.remove(player_id)
                for other_player in other_players:
                    if all_players[other_player]["team"] == new_team:
                        if other_player in red_players:
                            red_players.append(player_id)
                            break
                        elif other_player in blue_players:
                            blue_players.append(player_id)
                            break
                for other_player in other_players:
                    if other_player in red_players:
                        blue_players.append(player_id)
                        break
                    elif other_player in blue_players:
                        red_players.append(player_id)
                        break


def interface():
    logs = []
    maps = []
    log_ids = []
    outlog = ""
    red_players = []
    blue_players = []
    gamemode = "Other"

    nr = int(input("How many logs do you want to combine? "))
    while nr < 2:
        nr = input("Input a number that is at least 2: ")
    raw_logs = json.loads(urllib2.urlopen(
        "https://logs.tf/api/v1/log?player=" + str(def_steamid) + "&limit=" + str(nr)).read())["logs"]
    raw_logs.reverse()

    for i in range(len(raw_logs)):
        log_id = raw_logs[i]["id"]
        raw_log = json.loads(urllib2.urlopen("https://logs.tf/json/" + str(log_id)).read())
        team_sort(raw_log["players"], red_players, blue_players, i == 0)
        if i == 0:
            gamemode = determine_gamemode(len(red_players) + len(blue_players))
        log_ids.append(log_id)
        clog = get_important(getlog(log_id))
        logs.append(clog)
        maps.append(raw_logs[i]["map"])

    sorted(logs, key=timesort)
    for log in logs:
        outlog += log

    key = options["k"]
    # print("Please enter a title for your log (max 40 characters)")
    # title = input()
    red_tag = teamtag(red_players, gamemode)
    blue_tag = teamtag(blue_players, gamemode)
    title = blue_tag + " vs " + red_tag

    if options["o"] == "t":
        outlog += outlog.split("\n")[-2][
                  :24] + ' "Auto Log Combiner<0><Console><Console>" say "The following logs were combined: ' + \
                  " & ".join(log_ids) + '"\n'

    mape = "Error"
    try:
        nmaps = []
        for m in maps:
            name_l = m.split("_")
            if len(name_l) == 2:
                name = name_l[1]
            else:
                name = " ".join(name_l[1:-1])
            if name in mapnames_map.keys():
                name = mapnames_map[name]
            nmaps.append(name)
        if len(" + ".join(nmaps)) < 25:
            mape = " + ".join(nmaps)
        else:
            raise RuntimeError("We can't make the mapname small enough")

    except RuntimeError:
        print("An error happened parsing the maps.")
        print("Please enter the maps (max 24 chars)")
        mape = input()
    payload = {
        "title": title[0:40],
        "map": mape[0:24],
        "key": str(key),
        "uploader": "Auto Log Combiner " + version
    }

    files = {
        "logfile": StringIO(outlog)
    }
    r = requests.post("https://logs.tf/upload", data=payload, files=files)
    x = json.loads(r.text)
    if x["success"]:
        webbrowser.open_new_tab("https://www.logs.tf" + x["url"])
    else:
        print(r.text)


with open("version") as f:
    version = "v" + f.read()

op = ["u", "m", "o", "k"]
options = {}
if os.path.isfile("settings"):
    loadsettings()

def_steamid = 76561198150315584
mapnames_map = {
    "badlands": "blands", "badlands_pro": "blands", "prolands": "blands",
    "granary": "gran", "granary_pro": "gran",
    "viaduct_pro": "product", "snakewater": "snake", "gullywash": "gully", "metalworks": "metal"
}
interface()
