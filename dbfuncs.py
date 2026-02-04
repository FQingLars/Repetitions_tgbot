import sqlite3 as s3
from functools import wraps
from datetime import datetime


def db_init(primadmin: int):
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS Reps (
    id INTEGER PRIMARY KEY,
    groupname TEXT NOT NULL,
    datetime TEXT NOT NULL,
    UNIQUE(groupname, datetime)
)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS BotAdmins (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER NOT NULL UNIQUE
)""")

    insert_admin(primadmin)

    db.commit()
    db.close()

def insert_admin(tgid: int):
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("INSERT OR IGNORE INTO BotAdmins (telegram_id) VALUES (?)", (tgid,))

    db.commit()
    db.close()

def delete_admin(tgid: int):
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("DELETE FROM BotAdmins WHERE telegram_id = ?", (tgid,))

    db.commit()
    db.close()

def check_primary_admin(tgid: int):
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("SELECT id FROM BotAdmins WHERE telegram_id = ?", (tgid,))
    try:
        id = cur.fetchone()[0]
    except TypeError as e:
        return False

    return id == 1

def insert_rep(group: str, date_time: datetime):

    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("INSERT OR IGNORE INTO Reps (groupname, datetime) VALUES (?, ?)", (group, date_time))

    db.commit()
    db.close()

def delete_rep(group: str, date_time: datetime):
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("DELETE FROM Reps WHERE groupname = ? AND datetime = ?", (group, date_time))

    db.commit()
    db.close()

def check_admin(tgid: int) -> bool:
    with s3.connect("repdatabase.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM BotAdmins WHERE telegram_id = ?", (tgid,))
        is_admin = cursor.fetchone() is not None

    return is_admin

def select_admins():
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("SELECT telegram_id FROM BotAdmins")
    admins = cur.fetchall()
    admins = [admin[0] for admin in admins]

    db.close()

    return admins

def automatic_clean():
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("DELETE FROM Reps WHERE datetime < datetime('now', 'localtime')")

    db.commit()
    db.close()

def select_rasp():
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("SELECT groupname, datetime FROM Reps")
    data = cur.fetchall()

    db.close()

    return data

if __name__ == "__main__":
    db_init(940454804)

    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("INSERT INTO BotAdmins (telegram_id) VALUES (940454804)")
    db.commit()

    db.close()