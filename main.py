# -*- coding: utf-8 -*-
from io import BytesIO, StringIO
import zipfile
import urllib.request as urllib2
import urllib.parse as ulparse
import codecs
import requests
import time
import datetime
import webbrowser
import json
import os.path
from collections import OrderedDict
from distutils.version import LooseVersion


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


def interface():
    logs = []
    maps = []
    ids = []
    outlog = ""

    nr = input("How many logs do you want to combine? ")
    raw_logs = json.loads(urllib2.urlopen(
        "https://logs.tf/api/v1/log?player=" + str(steamid) + "&limit=" + str(nr)).read())["logs"]

    for raw_log in raw_logs:
        logid = raw_log["id"]
        clog = get_important(getlog(logid))
        logs.append(clog)
    sorted(logs, key=timesort)
    for log in logs:
        outlog += log

    key = options["k"]
    print("Please enter a title for your log (max 40 characters)")
    title = input()

    if options["o"] == "t":
        outlog += outlog.split("\n")[-2][
                  :24] + ' "Auto Log Combiner<0><Console><Console>" say "The following logs were combined: ' + \
                  " & ".join(ids) + '"\n'

    mape = "Error"
    if options["m"] == "t":
        try:
            maps = list(OrderedDict.fromkeys(maps))
            if len(" + ".join(maps)) < 25:
                mape = " + ".join(maps)
            elif len(",".join(maps)) < 25:
                mape = ",".join(maps)
            else:
                nmaps = list()
                for m in maps:
                    p = m.split("_")
                    if len(p) == 2:
                        nmaps.append(p[1])
                    else:
                        nmaps.append("_".join(p[1:-1]))
                if len(" + ".join(nmaps)) < 25:
                    mape = " + ".join(nmaps)
                elif len(",".join(nmaps)) < 25:
                    mape = ",".join(nmaps)
                else:
                    raise RuntimeError("We can't make the mapname small enough")

        except RuntimeError:
            print("An error happened parsing the maps, please enter the map now yourself.")
            print("Please enter the maps (max 24 chars)")
            mape = input()
    else:
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

steamid = 76561198150315584
interface()
