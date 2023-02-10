import sqlite3
import requests
import os
import matplotlib.pyplot as plt
import numpy as np


def create_connection(db_file):
    connection = None
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except sqlite3.Error as e:
        print(e)

    return connection


def calculateRatingWinChances(connection: sqlite3.Connection, rounding: int) -> dict:
    cursor = connection.cursor()
    cursor.execute("""
        SELECT m.winner_id, tr1.team_id, tr2.team_id, tr1.rating, tr2.rating
        FROM (matches m 
            LEFT JOIN (
                SELECT AVG(rating) as rating, team_id 
                FROM players 
                GROUP BY team_id
            ) tr1 
            ON m.team1_id = tr1.team_id) 
            LEFT JOIN (
                SELECT AVG(rating) as rating, team_id 
                FROM players 
                GROUP BY team_id
            ) tr2 
            ON m.team2_id = tr2.team_id
            LEFT JOIN teams t1 ON m.team1_id = t1.id
            LEFT JOIN teams t2 ON m.team2_id = t2.id
        WHERE tr1.team_id IS NOT NULL AND tr2.team_id IS NOT NULL
        """)
    rows = cursor.fetchall()

    # size of rating difference buckets as decimals
    rounding = 1

    win_chances = {}
    for row in rows:
        winner, team1, team2, rating1, rating2 = row

        ratio = round(min(rating1, rating2) / max(rating1, rating2), rounding)
        if ratio not in win_chances:
            win_chances[ratio] = {"betterWins": 0, "betterLoses": 0}

        if (winner == team1 and rating1 > rating2) or (winner == team2 and rating2 > rating1):
            win_chances[ratio]["betterWins"] += 1
        else:
            win_chances[ratio]["betterLoses"] += 1

    win_chances_percent = {}
    for item in win_chances.items():
        win_chances_percent[item[0]] = (
            item[1]["betterWins"]) / sum(item[1].values())

    win_chances_percent = dict(sorted(win_chances_percent.items()))

    return win_chances_percent


def caluculateMapWin(connection: sqlite3.Connection):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT map, CASE WHEN winner_id == team1_id THEN 'north' else 'south' END
        FROM matches m
        LEFT JOIN tournaments t
        ON m.tournament_id == t.id
        WHERE t.team_size > 3 AND t.date > '2022-01-01'
        """)
    rows = cursor.fetchall()

    map_wins = {}
    for row in rows:
        if row[0] not in map_wins:
            map_wins[row[0]] = {"north": 0, "south": 0}
        map_wins[row[0]][row[1]] += 1

    map_wins_percent = {k: v["north"] /
                        sum(v.values()) for k, v in map_wins.items()}
    map_wins = dict(sorted(map_wins_percent.items(),
                    key=lambda item: -item[1]))

    print()
    print("{} | {}".format("Map".ljust(12), "win%"))
    print("―" * 19)
    for map in map_wins.items():
        print("{} | {:.2f}".format(
            map[0].ljust(12), map[1]))
    print()


def main():
    current_dir = os.getcwd()
    connection = create_connection(f"{current_dir}\\tournament.db")

    # close if coulnd't connect
    if connection is None:
        return

    cursor = connection.cursor()
    cursor.execute("""
        SELECT COUNT(m.map), m.map FROM matches m WHERE m.winner_id == 0 GROUP BY m.map
        """)
    rows = cursor.fetchall()
    print(rows)

    caluculateMapWin(connection)

    rounding = 1
    win_chances_percent = calculateRatingWinChances(connection, rounding)

    x = np.array(list(win_chances_percent.keys()))
    y = np.array(list(win_chances_percent.values()))

    a, b = np.polyfit(x, y, 1)

    plt.figure()
    ax = plt.subplot()
    ax.bar(x, y, width=10 ** -rounding, align='center')
    plt.xlabel('Worse / Better')
    plt.ylabel('Better team win%')
    ax.set_ylim(0, 1)
    ax.set_xlim(0, 1 + 10 ** -rounding / 2)

    plt.plot(x, a * x + b, color='orange')

    print(a, b)

    plt.show()


if __name__ == '__main__':
    main()
