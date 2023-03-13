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


def caluculateMapNorthWin(start, end, connection: sqlite3.Connection):
    cursor = connection.cursor()
    cursor.execute(f"""--sql
        SELECT w.map, AVG(winner), COUNT(d.map), COUNT(w.map)
        FROM (
            SELECT m.id, m.map, CASE WHEN winner_id == team1_id THEN 1 WHEN winner_id == team2_id THEN 0 END AS winner
            FROM matches m
            LEFT JOIN tournaments t
            ON m.tournament_id == t.id
            WHERE t.team_size > 3 AND t.date > '{start}'
        ) AS w LEFT JOIN (
            SELECT m.id, m.map
            FROM matches m
            LEFT JOIN tournaments t
            ON m.tournament_id == t.id
            WHERE t.team_size > 3 AND t.date > '{start}' AND winner_id == 0
        ) AS d ON w.id == d.id
        GROUP BY w.map;
        """)
    
    rows = cursor.fetchall()
    print(rows)
    map_wins = sorted(rows, key=lambda item: -item[1])

    print()
    print("{} | {} | {}".format("Map".rjust(24), "nwin%", "draw%"))
    print("―" * 40)
    for map in map_wins:
        print("{} | {:.1f} | {:.1f}".format(
            map[0].rjust(24), map[1] * 100, map[2] / map[3] * 100))
    print()

    x = np.array([x[0].replace(",", ",\n") for x in map_wins])
    wins = np.array([x[1] for x in map_wins])
    draws = np.array([x[2] / x[3] for x in map_wins])

    plt.figure()
    ax = plt.subplot()
    ax.bar(x, wins, align='center')
    ax.bar(x, draws, align='center')
    plt.xlabel('Worse / Better')
    plt.ylabel('Better team win%')
    ax.set_ylim(0, max(wins))

    plt.show()

def addlabels(x, y, offset):
    for i in range(len(x)):
        plt.text(i + offset, y[i], "{:.1f}%".format(y[i] * 100), ha='center')

def mapWinBySideForTeam(start, team, tier, connection: sqlite3.Connection):
    cursor = connection.cursor()

    cursor.execute(f"""--sql
        SELECT ma.map, SUM(CASE WHEN winner_id == team1_id THEN 1 ELSE 0 END), COUNT(ma.map) FROM matches ma
        LEFT JOIN teams te ON ma.team1_id == te.id
        LEFT JOIN tournaments t ON t.id == ma.tournament_id
        WHERE te.name == '{team}' AND t.date > '{start}' AND t.tier == {tier}
        GROUP BY ma.map;
    """)

    north_rows = cursor.fetchall()
    print(north_rows)

    cursor.execute(f"""--sql
        SELECT ma.map, SUM(CASE WHEN winner_id == team2_id THEN 1 ELSE 0 END), COUNT(ma.map) FROM matches ma
        LEFT JOIN teams te ON ma.team2_id == te.id
        LEFT JOIN tournaments t ON t.id == ma.tournament_id
        WHERE te.name == '{team}' AND t.date > '{start}' AND t.tier == {tier}
        GROUP BY ma.map;
    """)

    south_rows = cursor.fetchall()
    print(south_rows)

    return (north_rows, south_rows)


def caluculateMapNorthWinForTeam(start, end, connection: sqlite3.Connection):
    cursor = connection.cursor()

    cursor.execute(f"""--sql
        SELECT w.map, AVG(winner), COUNT(d.map), COUNT(w.map)
        FROM (
            SELECT m.id, m.map, t.id as tournament_id, m.team1_id, m.team2_id, CASE WHEN winner_id == team1_id THEN 1 WHEN winner_id == team2_id THEN 0 END AS winner
            FROM matches m
            LEFT JOIN tournaments t
            ON m.tournament_id == t.id
            WHERE t.team_size > 3 AND t.date > '{start}'
        ) AS w 
        LEFT JOIN (
            SELECT m.id, m.map
            FROM matches m
            LEFT JOIN tournaments t
            ON m.tournament_id == t.id
            WHERE t.team_size > 3 AND t.date > '{start}' AND winner_id == 0
        ) AS d 
        ON w.id == d.id
        LEFT JOIN teams te 
        ON te.id == w.team1_id OR te.id == w.team2_id
        WHERE te.name == 'Golden Noobs'
        GROUP BY w.map;
        """)
    
    rows = cursor.fetchall()
    print(rows)
    map_wins = sorted(rows, key=lambda item: -item[1])

    print()
    print("{} | {} | {}".format("Map".rjust(24), "nwin%", "draw%"))
    print("―" * 40)
    for map in map_wins:
        print("{} | {:.1f} | {:.1f}".format(
            map[0].rjust(24), map[1] * 100, map[2] / map[3] * 100))
    print()

    x = np.array([x[0].replace(",", ",\n") + "\n" + str(x[2] + x[3]) for x in map_wins])
    wins = np.array([x[1] for x in map_wins])
    draws = np.array([x[2] / x[3] for x in map_wins])

    plt.figure()
    ax = plt.subplot()
    ax.bar(x, wins, align='center')
    ax.bar(x, draws, align='center')

    addlabels(x, wins)
    addlabels(x, draws)

    plt.ylabel('Spawn 1 win%')
    ax.set_ylim(0, max(wins))

    plt.show()

def plt_bar(north_rows, south_rows, axs):
    x = np.array([f"{north_rows[i][0]}\n{north_rows[i][2]} | {south_rows[i][2]}"  for i in range(len(north_rows))])
    north = np.array([x[1] / x[2] for x in north_rows])
    south = np.array([x[1] / x[2] for x in south_rows])

    x_axis = np.arange(len(x))

    addlabels(x, north, -0.2)
    addlabels(x, south, 0.2)

    axs.bar(x_axis - 0.2, north, 0.4)
    axs.bar(x_axis + 0.2, south, 0.4)

    axs.set_xticks(x_axis, x)

    axs.set_xlabel("Map\nspawn 1 | spawn 2")
    axs.set_ylabel("Win%")

    return axs

def main():
    current_dir = os.getcwd()
    connection = create_connection(f"{current_dir}\\tournament.db")

    # close if coulnd't connect
    if connection is None:
        return

    cursor = connection.cursor()
    cursor.execute("""--sql
        SELECT * 
        FROM matches m
        LEFT JOIN teams te
        ON m.team1_id == te.id
        LEFT JOIN tournaments t
        ON m.tournament_id = t.id
        WHERE m.map == 'Cliff' AND te.name == 'Golden Noobs' AND t.date > '2022-01-01'
    ;""")

    rows = cursor.fetchall()
    [print(x) for x in rows]

    print()
    cursor.execute("""--sql
        SELECT * 
        FROM matches m
        LEFT JOIN teams te
        ON m.team2_id == te.id
        LEFT JOIN tournaments t
        ON m.tournament_id = t.id
        WHERE m.map == 'Cliff' AND te.name == 'Golden Noobs' AND t.date > '2022-01-01'
    ;""")

    rows = cursor.fetchall()
    [print(x) for x in rows]

    #caluculateMapNorthWin("2022-01-01", "", connection)
    #caluculateMapNorthWinForTeam("2022-01-01", "", connection)
    north_10, south_10 = mapWinBySideForTeam("2022-01-01", "Golden Noobs", 10, connection)
    north_9, south_9 = mapWinBySideForTeam("2022-01-01", "Golden Noobs", 9, connection)
    
    fig, axs = plt.subplots(2)
    axs[0] = plt_bar(north_10, south_10, axs[0])
    axs[0].set_title("X")
    axs[1] = plt_bar(north_9, south_9, axs[1])
    axs[0].set_title("IX")

    plt.show()

if __name__ == '__main__':
    main()
