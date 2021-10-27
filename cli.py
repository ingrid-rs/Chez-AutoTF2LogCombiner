from settings_logic import *
import os
import combine_logic as cl


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
    raw_logs.reverse()

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
        clog = cl.get_important(cl.getlog(log_id))
        logs.append(clog)
        maps.append(raw_logs[i]["map"])

    sorted(logs, key=timesort)
    for log in logs:
        outlog += log

    red_tag = teamtag(red_players, gamemode)
    blue_tag = teamtag(blue_players, gamemode)

    if options["automaps"]:
        try:
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
