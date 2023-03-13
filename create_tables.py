import sqlite3, os

def create_connection(db_file):
    connection = None
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except sqlite3.Error as e:
        print(e)

    return connection

def main():
    current_dir = os.getcwd()
    connection = create_connection(f"{current_dir}\\tournament.db")

    # close if coulnd't connect
    if connection is None:
        return

    # create all tables if they don't exist
    table_sql = open(os.getcwd() + "\\create_tables.sql", "r").read()
    cursor = connection.cursor()
    cursor.executescript(table_sql)



if __name__ == '__main__':
    main()