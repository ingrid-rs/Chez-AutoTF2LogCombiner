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
import datetime
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


def optmenu(question, options=None):
    if options is None:
        options = ["Yes", "No"]
    maxv = len(options)
    while True:
        print(question)
        for i in range(len(options)):
            print("   " + str(i + 1) + ".  " + options[i])
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


def interface(options):
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
        "https://logs.tf/api/v1/log?player=" + str(options["def_steamid"]) + "&limit=" + str(nr)).read())["logs"]
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

    key = options["key"]
    red_tag = teamtag(red_players, gamemode)
    blue_tag = teamtag(blue_players, gamemode)
    title = blue_tag + " vs " + red_tag

    if options["outlog"] == "t":
        outlog += outlog.split("\n")[-2][
                  :24] + ' "Auto Log Combiner<0><Console><Console>" say "The following logs were combined: ' + \
                  " & ".join(log_ids) + '"\n'

    try:
        nmaps = []
        for m in maps:
            name_l = m.split("_")
            if len(name_l) == 2:
                name = name_l[1]
            else:
                name = " ".join(name_l[1:-1])
            if name in options["short_maps"].keys():
                name = options["short_maps"][name]
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


def load_settings(options):
    with open("settings") as file:
        lines = file.read().split("\n")
    current_key = ""
    appending = False
    for line in lines:
        if line in options.keys():
            current_key = line
            if options[current_key] is not None:
                appending = True
            else:
                appending = False
        elif appending:
            split_line = line.split(",")
            options[current_key][split_line[0]] = split_line[1]
        else:
            options[current_key] = line


def set_apikey(options):
    print("Enter logs.tf API-key:")
    options["key"] = input()


def add_players(options):
    adding_players = True
    while adding_players:
        print("Enter the SteamID64 of the player to be added:")
        playerid = input()
        print("Enter that player's nickname:")
        playername = input()
        options["players"][playername] = playerid
        if optmenu("Do you want to add more players? "):
            adding_players = False


def set_def_player(options):
    print("Which of the players do you want to use by default?")
    msg = "Players: "
    player_names = options["players"].keys()
    for name in player_names:
        msg += name + ", "
    print(msg[0:-2])
    while True:
        answer = input()
        if answer in player_names:
            options["def_steamid"] = options["players"][answer]
            break
        print("Player name misspelt or hasn't been added yet.")


def set_autocombine(options):
    options["automaps"] = not bool(optmenu("Do you want the program to autocombine map names?"))


def add_short_maps(options):
    while True:
        print("Enter the full mapname (without the prefix and suffix), or \"stop\" to quit:")
        full = input()
        if full == "stop":
            break
        print("Enter the short version of that mapname, or \"stop\" to quit:")
        short = input()
        if short == "stop":
            break
        options["short_maps"][full] = short


def set_outlog(options):
    options["outlog"] = not bool(optmenu("Do you want the program to print out a message with the combined logs?"))


def write_settings(options):
    out = ""
    for option in options.keys():
        out += option + "\n"
        if isinstance(options[option], dict):
            pairs = options[option].items()
            for pair in pairs:
                out += pair[0] + "," + pair[1] + "\n"
        else:
            out += str(options[option]) + "\n"
    with open("settings", "w") as fl:
        fl.write(out.rstrip())


with open("version") as f:
    version = "v" + f.read()

def_options = {"key": None, "players": {}, "def_steamid": None, "automaps": None, "short_maps": {}, "outlog": None}

if os.path.isfile("settings"):
    load_settings(def_options)

    if not optmenu("Do you want to change the saved settings? "):

        if not optmenu("Do you want to change your API-key? "):
            set_apikey(def_options)

        if not optmenu("Do you want to save more players? "):
            add_players(def_options)

        if not optmenu("Do you want to change the default player? "):
            set_def_player(def_options)

        set_autocombine(def_options)

        if not optmenu("Do you want to save more short names for maps? "):
            add_short_maps(def_options)

        set_outlog(def_options)

        write_settings(def_options)

else:
    print("Running first-time setup.")
    set_apikey(def_options)

    print("The program will keep a short list of players to easily access their played logs.")
    add_players(def_options)

    print("The program will also remember one of the added players as the player whose logs to combine.")
    set_def_player(def_options)

    set_autocombine(def_options)

    if def_options["automaps"]:
        print("The program can keep a list of maps to shorten when autocombining map names,"
              "e.g snakewater -> snake.")
        add_short_maps(def_options)

    set_outlog(def_options)

    write_settings(def_options)

interface(def_options)
