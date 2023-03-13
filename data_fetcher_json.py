import sqlite3
import requests
import json
import os
import sys
from datetime import date
from pathlib import Path
from bs4 import BeautifulSoup
import codecs


API_URL = "https://worldoftanks.eu/tmsis/api/v1/"
STAGE_IDS_EXT = "stages/"
GROUP_ID_EXT = "stages/groups/"
TEAMS_EXT = "tournament/teams/"
MATCHES_EXT = "stages/groups/matches/"
TOURNAME_STAT_EXT = "lobby/"

API_FOR_USER_URL = "https://worldoftanks.eu/tmsis/api/v1/tournament/user_info/"

CWD = os.getcwd()


def createDir(path: str):
    if not os.path.exists(path):
        os.mkdir(path)


def fetchTournamentIds(tournament_id: str, session_id: str):
    params = {
        "filter[tournament_id]": tournament_id
    }

    # fetch group stage group id
    response = requests.get(API_FOR_USER_URL,
                            params=params, headers={"cookie": f"sessionid={session_id};"})

    tournament_ids = json.loads(response.text)
    return tournament_ids["data"]["results"]


def fetchTeams(tournament_id: str):
    i = 1
    teams = []
    while True:
        params = {
            "filter[language]": "en",
            "filter[tournament_id]": tournament_id,
            "page[size]": 100,
            "page[number]": i,
            "filter[status]": "confirmed"
        }

        response = requests.get(API_URL + TEAMS_EXT, params=params)
        responseBody = json.loads(response.text)
        if responseBody["status"] == "error":
            break

        teams += responseBody["data"]["results"]
        i += 1

    return teams


def fetchGroupIds(tournament_id: str, stage_id: str):
    groups = []

    i = 1
    while True:
        params = {
            "filter[language]": "en",
            "filter[tournament_id]": tournament_id,
            "filter[stage_id]": stage_id,
            "sort": "order",
            "page[number]": i,
            "page[size]": 100
        }

        # fetch group stage group id
        response = requests.get(API_URL + GROUP_ID_EXT, params=params)
        responseBody = json.loads(response.text)

        if responseBody["status"] == "error":
            break

        groups += responseBody["data"]["results"]
        i += 1

    return groups


def fetchMatches(tournament_id: str, stage_id: int, group_id: int) -> dict:
    params = {
        "filter[language]": "en",
        "filter[tournament_id]": tournament_id,
        "filter[stage_id]": stage_id,
        "filter[group_id]": group_id,
    }

    response = requests.get(API_URL + MATCHES_EXT, params=params)
    responseBody = json.loads(response.text)

    return responseBody["data"]["results"]


def fetchTournamentInfo(tournamet_id: str) -> dict:
    # fetch group stage group id
    response = requests.get(
        f"https://worldoftanks.eu/en/tournaments/{tournamet_id}/")
    responseBody = BeautifulSoup(response.text, features="html.parser")

    small_info = {}
    for li in responseBody.body.find("ul", attrs={"class": "tournament-info-list"}).findChildren("li", recursive=False):
        small_info[li.find("span", attrs={"class": "tournament-info-list_name"}).text.strip()] = li.find(
            "span", attrs={"class": "tournament-info-list_description"}).text.replace(" ", "").replace("\n", "")

    rewards = []
    for h2 in responseBody.body.findAll("h2", attrs={"class": "tournament-heading"}):
        if h2.text == "Reward":
            for tr in h2.parent.find("table", attrs={"class": "tournament-table"}).findAll("tr", attrs={"class": "tournament-table_tr"}):
                if tr.find("span", attrs={"class": "tournament-table_title"}) == None:
                    continue
                title = tr.find("span", attrs={
                                "class": "tournament-table_title"}).text.strip().replace(":", "")
                value = ""
                try:
                    value = tr.find(
                        "span", attrs={"class": "tournament-table_prize"}).text.strip()
                except:
                    print("No reward")
                rewards.append({"placement": title, "reward": value})

    team_size = responseBody.body.find(
        "span", attrs={"class": "js-min-players"}).get("data-min-players")
    vehicle_tier = responseBody.body.find("ul", attrs={
        "class": "detail-lists_list detail-lists_list__half detail-lists_list__border-type-2"}).findChild("span", attrs={"class": "detail-lists_description"}).text.replace(" ", "").replace("\n", "")

    # team_size = responseBody.body.find(
    # "span", attrs={"class": "data-min-players"}).get("data-min-players")
    # vehicle_tier = responseBody.body.find("span", attrs={
    # "class": "detail-lists_list detail-lists_list__half detail-lists_list__border-type-2"}).findChild("span", attrs={"class": "detail-lists_description"}).text
    # except:
    # print("No details")

    info = {
        "tournament_title": responseBody.body.find("span", attrs={"class": "header-inner_name"}).text.strip(),
        "tournament_start": responseBody.body.find("span", attrs={"class": "header-inner_status js-tournament-schedule"}).get("data-start-date"),
        "tournament_end": responseBody.body.find("span", attrs={"class": "header-inner_status js-tournament-schedule"}).get("data-end-date"),
        "bracket": small_info,
        "rewards": rewards,
        "team_size": team_size,
        "tier": vehicle_tier
    }

    return info


def writeJsonToFile(path: str, value: dict):
    with open(path, "w+", encoding="utf-8") as outfile:
        outfile.write(json.dumps(value, indent=4))


def main():
    jsonDirPath = CWD + "\\tournaments"
    createDir(jsonDirPath)

    for line in open(CWD + "\ids.txt", "r"):
        id = line[:-1]
        print(id)

        if id > "5000002157":
            continue

        tournamentPath = f"{jsonDirPath}\\{id}"
        createDir(tournamentPath)
        # Fetch tournament ids json
        tournament_json = fetchTournamentIds(
            id, "0ia3b7lmspp7rhorl8bycqauwb8dzeme")
        print(tournament_json)
        #writeJsonToFile(f"{tournamentPath}\\tournament.json", tournament_json)

        if not tournament_json["tournament_participation"]:
            continue
            
        """

        # Fetch teams
        teams = fetchTeams(id)
        with open(f"{tournamentPath}\\teams.json", "w+") as outfile:
            outfile.write(json.dumps(teams, indent=4))

        # Fetch groups
        groups = {}
        for stage_id in tournament_json["tournament_participation"][id]["stages"]:
            groups[stage_id] = fetchGroupIds(id, stage_id)

        writeJsonToFile(f"{tournamentPath}\\groups.json", groups)

        # Fetch matches
        matches = {}
        for stage_id in groups:
            matches[stage_id] = {}
            for group_id in groups[stage_id]:
                group_id = group_id["id"]
                matches[stage_id][group_id] = fetchMatches(
                    id, stage_id, group_id)

        writeJsonToFile(f"{tournamentPath}\\matches.json", matches)"""

        # Fetching tournament info
        tournament_info = fetchTournamentInfo(id)
        writeJsonToFile(
            f"{tournamentPath}\\tournament_info.json", tournament_info)


if __name__ == '__main__':
    main()
