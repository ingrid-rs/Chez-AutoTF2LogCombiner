# -*- coding: utf-8 -*-
import json
import urllib.request as urllib2

from other_logic import usteamid_to_commid


# very basic logic to find the gamemode based on player count in the log; subjective player count limits
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


# given a set of steamid3s and a gamemode (in string form, expected to be 6on6, Highlander, 2on2, 1on1),
# finds the team on etf2l that contains the most given steamids,
# and returns the tag of that team if at least half of the given players belong to the team,
# "team" if that team has no tag, and "mix" otherwise
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
    tag, nr = count_teams[0]
    if nr >= min_count:
        if tag is not None:
            return tag
        return "team"
    return "mix"


# given a dict of players (key is their steamid3, value is a dict that contains an item with the key "team"
# with a value of "Red" or "Blue"), two sets for all the players on "Blue" and "Red" so far,
# and a boolean for if this is the first log chronologically,
# returns two lists, the first with all the players on "Blue", the second with the players on "Red"
def team_sort(all_players, blue_players, red_players, is_first):
    temp_blue = []
    temp_red = []
    player_ids = list(all_players.keys())
    for j in range(len(all_players)):
        player_id = player_ids[j]
        if is_first:
            if all_players[player_id]["team"] == "Red":
                temp_red.append(player_id)
            else:
                temp_blue.append(player_id)
        else:
            if player_id in red_players:
                temp_red.append(player_id)
            elif player_id in blue_players:
                temp_blue.append(player_id)
            else:
                new_team = all_players[player_id]["team"]
                other_players = list(all_players.keys())
                other_players.remove(player_id)
                for other_player in other_players:
                    if all_players[other_player]["team"] == new_team:
                        if other_player in red_players:
                            temp_red.append(player_id)
                            break
                        elif other_player in blue_players:
                            temp_blue.append(player_id)
                            break
                for other_player in other_players:
                    if other_player in red_players:
                        temp_blue.append(player_id)
                        break
                    elif other_player in blue_players:
                        temp_red.append(player_id)
                        break
    return temp_blue, temp_red


# given two teams from two different games,
# returns whether those teams could be the same team (from the same scrim) based on a biased algorithm
def are_same_team(new_team, old_team):
    if not new_team or not old_team:
        return False
    same_count = len(set(new_team).intersection(old_team))
    min_count = (len(new_team) + 1) // 2 if len(new_team) <= len(old_team) else (len(old_team) + 1) // 2
    return same_count >= min_count


def combine_map_names(maps, shortened_maps):
    nmaps = []
    for m in maps:
        name_l = m.split("_")
        if len(name_l) == 2:
            name = name_l[1]
        else:
            name = " ".join(name_l[1:-1])
        if name.lower() in shortened_maps.keys():
            name = shortened_maps[name]
        nmaps.append(name)
    if len(" + ".join(nmaps)) < 25:
        return " + ".join(nmaps)
    else:
        raise RuntimeError("We can't make the mapname small enough")
