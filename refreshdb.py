"""
Purpose: Refreshes the local SQLite database using IMDb datasets,
creating a new database if one does not exist. Will automatically
download the latest version of the datasets if they do not exist
locally, or will ask the user if the latest version must be
downloaded if the files are already present.
"""

import sqlite3
from sqlite3 import Error
import os
import urllib.request
import gzip


def create_connection(db_file):
    """
    Create a SQLite database connection to the specified database file.
    The value ":memory:" should be used if a memory based database is
    desired.
    :param db_file: The file to connect to
    :return: The database connection
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print("Error:", e)
        return None


def exec_stmt(conn, stmt):
    """
    Execute a SQL query without return
    :param conn: Database connection
    :param stmt: The statement to execute
    """
    try:
        c = conn.cursor()
        if isinstance(stmt, tuple):
            c.execute(stmt[0], stmt[1])
        else:
            c.execute(stmt)
    except Error as e:
        print("Error in query", stmt)
        print(e)


def download_or_replace_imdb_dataset(filename):
    """
    Checks if the given filename exists. If it does not exist, downloads
    the filename from the IMDB dataset site. If it does exist, offer to
    redownload the latest version
    :param filename: The filename to download
    """
    download = True

    # Check if requested file already exists
    if os.path.isfile(filename):
        print(filename, "already exists, redownload?")
        response = input("y/n (y): ")

        # Default response is "y". Anything other than "n" will be
        # interpreted as "y"
        if response == "n":
            download = False

    # File doesn't exist
    if download:
        print("Downloading", filename, "(please be patient!)")
        try:
            urllib.request.urlretrieve("https://datasets.imdbws.com/" + filename, "./" + filename)
            print("Successfully downloaded", filename)
        except:
            print("Error downloading", filename)



if __name__ == '__main__':
    # Handle downloading files
    download_or_replace_imdb_dataset("title.basics.tsv.gz")
    download_or_replace_imdb_dataset("name.basics.tsv.gz")
    #download_or_replace_imdb_dataset("title.ratings.tsv.gz")
    download_or_replace_imdb_dataset("title.principals.tsv.gz")

    # Create DB connection (this will create the db if it doesnt exist)
    conn = create_connection("./data.db")

    # Prepare SQL queries
    sql_dropcast = """DROP TABLE IF EXISTS Cast;"""
    sql_droptitles = """DROP TABLE IF EXISTS Titles;"""
    sql_dropnames = """DROP TABLE IF EXISTS Names;"""
    sql_create_titles = """CREATE TABLE IF NOT EXISTS Titles (
                               titleid TEXT PRIMARY KEY,
                               title TEXT NOT NULL,
                               type TEXT NOT NULL,
                               releaseyear TEXT
                           );"""
    sql_create_names = """CREATE TABLE IF NOT EXISTS Names (
                              nameid TEXT PRIMARY KEY,
                              name TEXT,
                              birth TEXT,
                              death TEXT
                          );"""
    sql_create_cast = """CREATE TABLE IF NOT EXISTS Cast (
                              titleid TEXT NOT NULL,
                              nameid TEXT NOT NULL,
                              role TEXT,
                              PRIMARY KEY(titleid, nameid, role),
                              FOREIGN KEY(titleid) REFERENCES Titles(titleid),
                              FOREIGN KEY(nameid) REFERENCES Names(nameid)
                         );"""

    # Set up database structure
    exec_stmt(conn, sql_dropcast)
    exec_stmt(conn, sql_droptitles)
    exec_stmt(conn, sql_dropnames)
    exec_stmt(conn, sql_create_titles)
    exec_stmt(conn, sql_create_names)
    exec_stmt(conn, sql_create_cast)

    # Read data files

    # Titles
    with gzip.open("./title.basics.tsv.gz", "rt", encoding="utf8") as titles:
        # titles line structure:
        # tconst titleType primaryTitle originalTitle isAdult startYear endYear runtimeMinutes genres

        # Discard first line
        line = titles.readline()

        # For each line, extract info
        i = 0
        while True:
            line = titles.readline().lower()
            if line == "":
                break

            # Print some info so user knows we're working
            if i % 100000 == 0:
                print(i, "title records processed")

            # Get components from this record
            parts = line.split("\t")
            id = parts[0]
            ttype = parts[1]
            title = parts[2]
            year = parts[5]

            # SQL query which will be executed
            sql_inserttitle = ("INSERT INTO Titles(titleid, title, type, releaseyear) "
                               "VALUES (?, ?, ?, ?);", (id, title, ttype, year))
            exec_stmt(conn, sql_inserttitle)
            i+=1

        print("Titles imported")

    with gzip.open("./name.basics.tsv.gz", "rt", encoding="utf8") as names:
        # names line structure:
        # nconst name birthYear primaryProfession knownForTitles

        # Discard first line
        line = names.readline()

        # For each line, extract info
        i = 0
        while True:
            line = names.readline().lower()
            if line == "":
                break

            if i % 100000 == 0:
                print(i, "name records processed")

            # Get components from this record
            parts = line.split("\t")
            id = parts[0]
            name = parts[1]
            byear = parts[2]
            dyear = parts[3]
            

            # SQL query which will be executed
            sql_insertname = ("INSERT INTO Names(nameid, name, birth, death) "
                               "VALUES (?, ?, ?, ?);", (id, name, byear, dyear))
            exec_stmt(conn, sql_insertname)
            i += 1

        print("Names imported")

#    # Ratings
#    with gzip.open("./title.ratings.tsv.gz", "rt", encoding="utf8") as ratings:
#        # ratings structure:
#        # tconst	averageRating	numVotes
#
#        # Discard first line
#        line = ratings.readline()
#
#        # For each line, extract info
#        i = 0
#        while True:
#            line = ratings.readline()
#            if line == "":
#                break
#
#            if i % 100000 == 0:
#                print(i, "rating records processed")
#
#            # Get components from this record
#            parts = line.split("\t")
#            id = parts[0]
#            rating = parts[1]
#
#            # SQL query
#            sql_updaterating = ("UPDATE Titles "
#                              "SET avg_rating = ? "
#                              "WHERE titleid = ?", (rating, id))
#            exec_stmt(conn, sql_updaterating)
#            i += 1
#
#        print("Ratings imported")

    # Cast
    with gzip.open("./title.principals.tsv.gz", "rt", encoding="utf8") as principals:
        # principals:
        # tconst    ordering    nconst    category    job    characters

        # Discard first line
        line = principals.readline()

        # For each line, extract info
        i = 0
        while True:
            line = principals.readline().lower()
            if line == "":
                break

            if i % 100000 == 0:
                print(i, "cast records processed")

            # Get components from this record
            parts = line.split("\t")
            titleid = parts[0]
            nameid = parts[2]
            role = parts[3]

            # SQL query
            sql_insertcast = ("INSERT INTO Cast(titleid, nameid, role) "
                               "VALUES (?, ?, ?);", (titleid, nameid, role))
            exec_stmt(conn, sql_insertcast)
            i += 1

        print("Cast imported")

    # Done
    print("Refreshed local IMDb database")


    # Close connection
    conn.commit()
    conn.close()
