import sqlite3
import requests
import json
import os
import sys
from datetime import date
from pathlib import Path


def create_connection(db_file):
    connection = None
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except sqlite3.Error as e:
        print(e)

    return connection


def getTeams(url, tournament_id: int):
    teams = []

    # loop through team pages
    i = 1
    while True:
        params = {
            "filter[language]": "en",
            "filter[tournament_id]": tournament_id,
            "page[size]": 100,
            "page[number]": i,
            "filter[status]": "confirmed"
        }

        response = requests.get(url, params=params)
        responseBody = json.loads(response.text)
        if responseBody["status"] == "error":
            break

        teams += responseBody["data"]["results"]
        i += 1

    return teams


def getPlayers(player_ids: list[int]) -> dict:
    url = """https://api.worldoftanks.eu/wot/account/info/
                ?application_id=68dcea4e997b1914c362b0679261e9e0
                &account_id={}
                &language=en
                &extra=statistics.random
                &fields=account_id, global_rating, clan_id, statistics.random.wins, statistics.random.battles, nickname""".format(
        ', '.join(str(x) for x in player_ids))
    response = requests.get(url)
    responseBody = json.loads(response.text)

    players = []
    for player_stats in responseBody["data"].items():
        if player_stats[1] == None:
            players.append({
                "uuid": int(player_stats[0]),
                "nickname": "",
                "battles": 0,
                "rating": None,
                "wins_ratio": None,
                "clan_id": "",
            })
            continue

        player_stats = player_stats[1]
        players.append({
            "uuid": player_stats["account_id"],
            "nickname": player_stats["nickname"],
            "battles": player_stats["statistics"]["random"]["battles"],
            "rating": player_stats["global_rating"],
            "wins_ratio": None if player_stats["statistics"]["random"]["battles"] == 0 else round(player_stats["statistics"]["random"]["wins"] / player_stats["statistics"]["random"]["battles"], 4),
            "clan_id": player_stats["clan_id"]
        })

    return players


def getPlayer(playerJSON) -> dict:
    url = "https://worldoftanks.eu/wotup/profile/summary/?spa_id={}&battle_type=random".format(
        playerJSON["uuid"])
    response = requests.get(url)
    responseBody = json.loads(response.text)

    player = {
        "uuid": "",
        "nickname": "",
        "battles": 0,
        "rating": 0,
        "wins_ratio": 0
    }
    player["uuid"] = playerJSON["uuid"]
    player["nickname"] = playerJSON["nickname"]

    if len(responseBody["data"]) == 0:
        return player

    player["battles"] = responseBody["data"]["battles_count"]
    player["rating"] = responseBody["data"]["global_rating"]
    player["wins_ratio"] = responseBody["data"]["wins_ratio"]

    return player


def getMatches(url, tournament_id: str, stage_id: int, group_id: int):
    params = {
        "filter[language]": "en",
        "filter[tournament_id]": tournament_id,
        "filter[stage_id]": stage_id,
        "filter[group_id]": group_id,
    }

    response = requests.get(url, params=params)
    responseBody = json.loads(response.text)

    return responseBody


def getStageIds(url: str, tournament_id: int) -> list[str]:
    params = {
        "filter[language]": "en",
        "filter[tournament_id]": tournament_id
    }

    response = requests.get(url, params=params)
    responseBody = json.loads(response.text)

    # match stage type to stage id
    ids = {}
    for result in responseBody["data"]["results"]:
        if result["bracket_type"] == "RR":
            ids["group"] = result["id"]
        elif result["bracket_type"] == "SE":
            ids["playoff"] = result["id"]

    return ids


def getGroupIds(url: str, tournament_id: int, stage_ids: dict):
    group_ids = {}
    params = {
        "filter[language]": "en",
        "filter[tournament_id]": tournament_id,
        "filter[stage_id]": stage_ids["group"],
        "sort": "order",
        "page[number]": 1,
        "page[size]": 100
    }

    # fetch group stage group id
    response = requests.get(url, params=params)
    responseBody = json.loads(response.text)

    ### FIX THIS if there is more than 100 groups ###
    group_ids["group"] = [x["id"] for x in responseBody["data"]["results"]]

    # fetch playoff stage group id
    params["filter[stage_id]"] = stage_ids["playoff"]

    response = requests.get(url, params=params)
    responseBody = json.loads(response.text)

    group_ids["playoff"] = responseBody["data"]["results"][0]["id"]

    return group_ids


def getTournamentStats(url, id):
    i = 1
    while True:
        params = {
            "filter[language]": "en",
            "filter[status]": "upcoming,registration_started,registration_finished,running,finished,complete",
            "filter[min_players]": "",
            "filter[tag_id]": "",
            "page[number]": i,
            "page[size]": 100
        }

        # fetch group stage group id
        response = requests.get(url, params=params)
        responseBody = json.loads(response.text)

        if responseBody["status"] != "ok" or len(responseBody["data"]["results"]) == 0:
            break

        stats = {}

        for result in responseBody["data"]["results"]:
            if result["registrations"][0]["id"] == id:
                stats["tier"] = result["extra_data"]["allowed_vehicles_tier_up_to"]
                stats["players"] = result["limitations"]["team"]["max_size"]
                stats["time"] = result["schedule"][0]["start"]
                break

        i += 1

    return stats


def printJSON(j):
    print(json.dumps(j, indent=4))


def pushTeams(teams: dict, connection: sqlite3.Connection):
    cursor = connection.cursor()
    for team in teams:
        cursor.execute("""
            INSERT OR REPLACE INTO teams(id, name) 
            VALUES(?, ?);
        """, (team["id"], team["title"]))

        players = getPlayers([x["uuid"] for x in team["players"]])

        for player in players:
            cursor.execute("""
                INSERT OR REPLACE INTO players(id, team_id, name, battles, rating, win_ratio, wn8, clan) 
                VALUES(?, ?, ?, ?, ?, ?, ?, ?);
            """, (player["uuid"], team["id"], player["nickname"], player["battles"], player["rating"], player["wins_ratio"], None, player["clan_id"]))

    connection.commit()


def pushResults(tournament_id: int, results: dict, stage: str, connection: sqlite3.Connection):
    cursor = connection.cursor()
    for result in results:
        if "summary" in result:
            continue
        cursor.execute("""
            INSERT OR REPLACE INTO matches(id, tournament_id, team1_id, team2_id, stage, winner_id, map) 
            VALUES(?, ?, ?, ?, ?, ?, ?);
        """, (result["uuid"], tournament_id, result["team_1"]["id"], result["team_2"]["id"], stage, result["winner_team_id"], result["settings"]["map"]))

    connection.commit()


def pushStats(tournament_id: int, tier: int, team_size: int, date: int, connection: sqlite3.Connection):
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO tournaments(id, tier, team_size, date) 
        VALUES(?, ?, ?, DATE(?, 'unixepoch'));
    """, (tournament_id, tier, team_size, date))

    connection.commit()


def fetchTournamentData(tournament_id: int, connection: sqlite3.Connection, is_user_info: bool):
    # fetch stage and group ids
    stage_ids = []
    if is_user_info:
        params = {
            "filter[language]": "en",
            "filter[tournament_id]": tournament_id,
        }
        cookies = {
        }
        url = API_URL + \
            f"tournament/user_info/?filter[tournament_id]={tournament_id}"
        # fetch group stage group id
        response = requests.get(url, params=params, cookies=cookies)
        print(response.status_code)
        responseBody = json.loads(response.text)
        printJSON(responseBody)
        if len(responseBody["results"]["tournament_participation"]) == 0:
            return
        else:
            stage_ids["group"] = responseBody["results"]["tournament_participation"][str(
                tournament_id)]["stages"].keys()[-1]
            stage_ids["playoff"] = stage_ids["group"] - 1

        printJSON(stage_ids)
        return
    else:
        print("Fetching stage ids.")
        stage_ids = getStageIds(API_URL + STAGE_IDS_EXT, tournament_id)

    print("Fetching group ids.")
    group_ids = getGroupIds(API_URL + GROUP_ID_EXT, tournament_id, stage_ids)

    # fetch teams
    print("Fetching teams.")
    teams = getTeams(API_URL + TEAMS_EXT, tournament_id)
    pushTeams(teams, connection)

    # fetch tier and team size for tournament
    print("Fetching stats.")
    stats = getTournamentStats(API_URL + TOURNAME_STAT_EXT, tournament_id)

    pushStats(tournament_id, stats["tier"],
              stats["players"], stats["time"], connection)

    # fetch playoff matches
    print("Fetching playoff matches.")
    playoff = getMatches(API_URL + MATCHES_EXT, tournament_id,
                         stage_ids["playoff"], group_ids["playoff"])

    pushResults(tournament_id, playoff["data"]
                ["results"], "playoff", connection)

    print("Fetching groups matches.")
    for group_id in group_ids["group"]:
        # fetch group stage result
        group = getMatches(API_URL + MATCHES_EXT, tournament_id,
                           stage_ids["group"], group_id)
        pushResults(tournament_id, group["data"]
                    ["results"], "groups", connection)


API_URL = "https://worldoftanks.eu/tmsis/api/v1/"
STAGE_IDS_EXT = "stages/"
GROUP_ID_EXT = "stages/groups/"
TEAMS_EXT = "tournament/teams/"
MATCHES_EXT = "stages/groups/matches/"
TOURNAME_STAT_EXT = "lobby/"


def main():
    current_dir = os.getcwd()
    connection = create_connection(f"{current_dir}\\tournament.db")

    # close if coulnd't connect
    if connection is None:
        return

    # parse tournament id from link
    args = sys.argv[1:]
    # args = ["https://worldoftanks.eu/en/tournaments/5000008408/"]

    #ids = [5000008616, 5000008065]
    #for id in ids:
    #    fetchTournamentData(id, connection, False)
    #    break

    fetchTournamentData(int(args[0].split('/')[-2]), connection, False)

    # for id in range(5000008532, 5000008530, -1):
        # fetchTournamentData(id, connection, False)


if __name__ == '__main__':
    main()
