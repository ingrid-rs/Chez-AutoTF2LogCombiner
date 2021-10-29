# -*- coding: utf-8 -*-
import os
import json
import urllib.request as urllib2
import datetime

from settings_logic import load_settings, write_settings
from log_combine_logic import get_important, getlog
from other_combine_logic import team_sort, are_same_team, determine_gamemode, teamtag, combine_map_names
from other_logic import timesort, upload_logs


def cl_interface(options, version):
    logs = []
    maps = []
    log_ids = []
    outlog = ""
    red_players = set()
    blue_players = set()
    gamemode = "Other"

    if os.path.isfile("settings"):
        load_settings(options)

        if not optmenu("Do you want to change the saved settings? "):

            if not optmenu("Do you want to change your API-key? "):
                set_apikey(options)

            if not optmenu("Do you want to save more players? "):
                add_players(options)

            if not optmenu("Do you want to change the default player? "):
                set_def_player(options)

            set_smart_combine(options)

            set_autocombine(options)

            if not optmenu("Do you want to save more short names for maps? "):
                add_short_maps(options)

            set_outlog(options)

            write_settings(options)

    else:
        print("Running first-time setup.")
        set_apikey(options)

        print("The program will keep a short list of players to easily access their played logs.")
        add_players(options)

        print("The program will also remember one of the added players as the player whose logs to combine.")
        set_def_player(options)

        set_smart_combine(options)

        set_autocombine(options)

        if options["automaps"]:
            print("The program can keep a list of maps to shorten when autocombining map names,"
                  "e.g snakewater -> snake.")
            add_short_maps(options)

        set_outlog(options)

        write_settings(options)

    if options["smart_combine"]:
        nr = 10
    else:
        nr = int(input("How many logs do you want to combine? "))
        while nr < 2:
            nr = int(input("Input a number that is at least 2: "))

    raw_logs = json.loads(urllib2.urlopen(
        "https://logs.tf/api/v1/log?player=" + str(options["def_steamid"]) + "&limit=" + str(nr)).read())["logs"]

    prev_log_date = 0
    old_blue, old_red = [], []
    for i in range(len(raw_logs)):
        log_id = raw_logs[i]["id"]
        if options["smart_combine"]:
            log_date = datetime.datetime.utcfromtimestamp(raw_logs[i]["date"])
            if i > 0 and (log_date - prev_log_date) / datetime.timedelta(seconds=3600) > 1:
                break
            prev_log_date = log_date
        raw_log = json.loads(urllib2.urlopen("https://logs.tf/json/" + str(log_id)).read())
        new_blue, new_red = team_sort(raw_log["players"], blue_players, red_players, i == 0)
        if options["smart_combine"]:
            if i > 0 and not (are_same_team(new_blue, old_blue) and are_same_team(new_red, old_red)):
                break
            old_blue, old_red = new_blue, new_red
        red_players = red_players.union(new_red)
        blue_players = blue_players.union(new_blue)
        if i == 0:
            gamemode = determine_gamemode(len(red_players) + len(blue_players))
        log_ids.append(log_id)
        clog = get_important(getlog(log_id))
        logs.append(clog)
        maps.append(raw_logs[i]["map"])

    sorted(logs, key=timesort)
    for log in logs:
        outlog += log

    red_tag = teamtag(red_players, gamemode)
    blue_tag = teamtag(blue_players, gamemode)

    if options["automaps"]:
        try:
            maps.reverse()
            mape = combine_map_names(maps, options["short_maps"])

        except RuntimeError:
            print("An error happened parsing the maps.")
            print("Please enter the maps (max 24 chars)")
            mape = input()
    else:
        print("Please enter the maps (max 24 chars)")
        mape = input()
    try:
        upload_logs(blue_tag, red_tag, mape, options["key"], version, outlog)
    except RuntimeError as e:
        print(str(e))


def optmenu(question, options=None):
    # default to a simple yes-no menu because i'm lazy
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


def set_smart_combine(options):
    options["smart_combine"] = not bool(optmenu("Do you want the program to just combine the last scrim's logs?"))
