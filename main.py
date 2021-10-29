# -*- coding: utf-8 -*-
from cli import cl_interface


with open("version") as f:
    version = "v" + f.read()

def_options = {"key": None, "players": {}, "def_steamid": None, "smart_combine": None, "automaps": None,
               "short_maps": {}}

cl_interface(def_options, version)
