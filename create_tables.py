import sqlite3, os

def create_connection(db_file):
    connection = None
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except sqlite3.Error as e:
        print(e)

    return connection


def create_tables(connection: sqlite3.Connection):
    create_table(connection, """ 
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY,
            name TEXT
        );""")
    create_table(connection, """ 
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY,
            tier INTEGER,
            team_size INTEGER,
            date TEXT
        );""")
    create_table(connection, """ 
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER NOT NULL,
            team_id INTEGER NOT NULL,
            name TEXT,
            battles INTEGER,
            rating INTEGER,
            win_ratio REAL,
            wn8 INTEGER,
            clan TEXT,
            PRIMARY KEY (id, team_id),
            FOREIGN KEY (team_id) REFERENCES teams (id)
        );""")
    create_table(connection, """
        CREATE TABLE IF NOT EXISTS matches (
            id TEXT PRIMARY KEY,
            tournament_id INTEGER,
            team1_id INTEGER,
            team2_id INTEGER,
            stage TEXT,
            winner_id INTEGER,
            map TEXT,
            FOREIGN KEY (team1_id) REFERENCES teams (id),
            FOREIGN KEY (team2_id) REFERENCES teams (id),
            FOREIGN KEY (tournament_id) REFERENCES tournaments (id)
        );""")


def create_table(connection, create_table_sql):
    try:
        cursor = connection.cursor()
        cursor.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)

def main():
    current_dir = os.getcwd()
    connection = create_connection(f"{current_dir}\\tournament.db")

    # close if coulnd't connect
    if connection is None:
        return

    # create all tables if they don't exist
    create_tables(connection)

    #cursor = connection.cursor()
    #cursor.execute("""ALTER TABLE matches ADD COLUMN clan TEXT""")
    #connection.commit()


if __name__ == '__main__':
    main()