# -*- coding: utf-8 -*-
from io import BytesIO
import zipfile
import urllib.request as urllib2
import codecs


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
