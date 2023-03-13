import sqlite3
import os
import json


def roman_numeral_to_int(numeral: str):
    numbers = {
        "I": 1,
        "II": 2,
        "III": 3,
        "IV": 4,
        "V": 5,
        "VI": 6,
        "VII": 7,
        "VIII": 8,
        "IX": 9,
        "X": 10,
    }

    return numbers[numeral.split("-")[-1]]


def create_connection(db_file):
    connection = None
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except sqlite3.Error as e:
        print(e)

    return connection


def move_tournaments(tournament_id: str, tournament_info_json: str, connection: sqlite3.Connection):
    tournament_info = json.loads(tournament_info_json)

    title = tournament_info["tournament_title"]
    tier = roman_numeral_to_int(tournament_info["tier"])
    team_size = int(tournament_info["team_size"])
    date = tournament_info["tournament_start"]
    is_reward_allowed = None
    bracket_type = tournament_info["bracket"]["Tournament bracket"]

    cursor = connection.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO tournaments 
        VALUES(?, ?, ?, ?, DATE(?, 'unixepoch'), ?, ?);
    """, (tournament_id, title, tier, team_size, date, is_reward_allowed, bracket_type))

    connection.commit()


def move_teams(tournament_id: str, teams_json: str, connection: sqlite3.Connection):
    teams = json.loads(teams_json)

    for team in teams:
        team_id = team["id"]
        title = team["title"]
        has_password = team["extra_data"]["password"]

        cursor = connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO teams 
            VALUES(?, ?, ?, ?);
        """, (team_id, title, has_password, tournament_id))

        for player in team["players"]:
            player_id = player["uuid"]
            name = player["nickname"]
            cursor.execute("""
            INSERT OR REPLACE INTO players 
            VALUES(?, ?, ?, ?, ?, ?, ?, ?);
        """, (player_id, name, None, None, None, None, None, team_id))

    connection.commit()


def move_stages(tournament_id: str, tournament_json: str, tournament_info_json: str, connection: sqlite3.Connection):
    tournament = json.loads(tournament_json)
    tournament_info = json.loads(tournament_info_json)

    stage_type = tournament_info["bracket"]["Tournament bracket"].split("+")
    for (i, stage_id) in enumerate(tournament["tournament_participation"][tournament_id]["stages"]):
        cursor = connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO stages 
            VALUES(?, ?, ?);
        """, (stage_id, stage_type[min(i, len(stage_type) - 1)], tournament_id))

    connection.commit()


def move_groups(tournament_id: str, groups_json: str, connection: sqlite3.Connection):
    groups = json.loads(groups_json)

    for stage_id in groups:
        for group in groups[stage_id]:
            id = group["id"]
            winner_rounds_count = group["summary"]["winner_rounds_count"]
            loser_rounds_count = group["summary"]["looser_rounds_count"]
            teams_count = group["teams_count"]
            order = group["order"]

            cursor = connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO stage_groups 
                VALUES(?, ?, ?, ?, ?, ?);
            """, (id, winner_rounds_count, loser_rounds_count, teams_count, order, tournament_id))

    connection.commit()


def move_matches(tournament_id: str, matches_json: str, connection: sqlite3.Connection):
    mathces = json.loads(matches_json)

    for stage_id in mathces:
        for group_id in mathces[stage_id]:
            for match in mathces[stage_id][group_id]:
                id = match["uuid"]
                map_name = match["settings"]["map"]
                team1_id = match["team_1"]["id"]
                team2_id = match["team_2"]["id"]
                winner_id = match["winner_team_id"]

                cursor = connection.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO matches 
                    VALUES(?, ?, ?, ?, ?, ?, ?);
                """, (id, map_name, tournament_id, group_id, team1_id, team2_id, winner_id))

    connection.commit()


def main():
    current_dir = os.getcwd()
    connection = create_connection(f"{current_dir}\\tournament.db")

    # close if coulnd't connect
    if connection is None:
        return

    for subdir, dirs, files in os.walk(current_dir + "\\tournaments\\"):
        if len(files) < 5:
            continue

        id = subdir.split("\\")[-1]
        print(id)
        with open(os.path.join(subdir, "tournament_info.json"), "r") as info_json:
            move_tournaments(id, info_json.read(), connection)

        with open(os.path.join(subdir, "tournament.json"), "r") as tournament_json:
            with open(os.path.join(subdir, "tournament_info.json"), "r") as info_json:
                move_stages(id, tournament_json.read(), info_json.read(), connection)

        with open(os.path.join(subdir, "groups.json"), "r") as groups_json:
            move_groups(id, groups_json.read(), connection)
        
        with open(os.path.join(subdir, "teams.json"), "r") as teams_json:
            move_teams(id, teams_json.read(), connection)

        with open(os.path.join(subdir, "matches.json"), "r") as matches_json:
            move_matches(id, matches_json.read(), connection)

        # print(dirs)


if __name__ == '__main__':
    main()
