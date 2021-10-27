# -*- coding: utf-8 -*-
from other_logic import *


def load_settings(options):
    with open("settings") as file:
        lines = file.read().split("\n")
    current_key = ""
    appending = False
    for line in lines:
        if line in options.keys():
            current_key = line
            if isinstance(options[current_key], dict):
                appending = True
            else:
                appending = False
        elif appending:
            split_line = line.split(",")
            options[current_key][split_line[0]] = split_line[1]
        else:
            try:
                options[current_key] = str_to_bool(line)
            except ValueError:
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


def set_smart_combine(options):
    options["smart_combine"] = not bool(optmenu("Do you want the program to just combine the last scrim's logs?"))


def write_settings(options):
    out = ""
    for option in options.keys():
        out += option + "\n"
        if isinstance(options[option], dict):
            for first, second in options[option].items():
                out += first + "," + second + "\n"
        else:
            out += str(options[option]) + "\n"
    with open("settings", "w") as fl:
        fl.write(out.rstrip())
