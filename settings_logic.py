# -*- coding: utf-8 -*-
from other_logic import str_to_bool
from cli import optmenu


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
