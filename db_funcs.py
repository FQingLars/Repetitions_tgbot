import sqlite3 as s3
from datas import *


def db_init(primadmin: int):
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS reps (
    id INTEGER PRIMARY KEY,
    groupname TEXT NOT NULL,
    datetime TEXT NOT NULL,
    UNIQUE(groupname, datetime)
)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY
)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY,
    groupname TEXT NOT NULL,
    date_time TEXT NOT NULL,
    action TEXT NOT NULL,
    UNIQUE (groupname, date_time, action)
    )""")

    insert_admin(primadmin)

    db.commit()
    db.close()


def insert_admin(user_id: int):
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("INSERT OR IGNORE INTO admins (id) VALUES (?)", (user_id,))

    db.commit()
    db.close()


def delete_admin(user_id: int):
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("DELETE FROM admins WHERE id = ?", (user_id,))

    db.commit()
    db.close()


def check_primary_admin(user_id: int):
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("SELECT id FROM admins WHERE id = ?", (user_id,))
    try:
        id = cur.fetchone()[0]
    except TypeError as e:
        return False

    return id == 1


def insert_rep(group: str, date_time: datetime):
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("INSERT OR IGNORE INTO reps (groupname, datetime) VALUES (?, ?)", (group, date_time))

    db.commit()
    db.close()


def delete_rep(group: str, date_time: datetime):
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("DELETE FROM reps WHERE groupname = ? AND datetime = ?", (group, date_time))

    db.commit()
    db.close()


def check_admin(user_id: int) -> bool:
    with s3.connect("repdatabase.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM admins WHERE id = ?", (user_id,))
        is_admin = cursor.fetchone() is not None

    return is_admin


def select_admins():
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("SELECT id FROM admins")
    admins = cur.fetchall()
    admins = [admin[0] for admin in admins]

    db.close()

    return admins


def automatic_clean():
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("DELETE FROM reps WHERE datetime < datetime('now', 'localtime')")

    db.commit()
    db.close()


def select_rasp():
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("SELECT id, groupname, datetime FROM reps ORDER BY datetime")
    data = cur.fetchall()
    data = [{'id': data[i][0], 'group_name': data[i][1], 'date_time': normalize_date(data[i][2])} for i, _ in enumerate(data)]

    db.close()

    return data


def insert_req(group: str, date_time: datetime, action: str):
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("INSERT OR IGNORE INTO requests (groupname, date_time, action) VALUES (?, ?, ?)",
                (group, date_time, action))

    db.commit()
    db.close()


def delete_req(group: str, date_time: datetime, action: str):
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("DELETE FROM requests WHERE groupname = ? AND date_time = ? AND action = ?",
                (group, date_time, action))

    db.commit()
    db.close()


def select_req():
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("SELECT id, groupname, date_time, action FROM requests ORDER BY date_time")
    data = cur.fetchall()
    data = [{'id': data[i][0], 'group_name': data[i][1], 'date_time': normalize_date(data[i][2]), 'action': data[i][3]} for i, _ in enumerate(data)]

    db.close()

    return data

def process_req(req_id: int, appr: bool):
    db = s3.connect("repdatabase.db")
    cur = db.cursor()

    cur.execute("SELECT groupname, date_time, action FROM requests WHERE id = ?", (req_id,))
    data = cur.fetchone()
    cur.execute("DELETE FROM requests WHERE id = ?", (req_id,))

    db.commit()
    db.close()

    if appr:
        if data[2] == "add":
            insert_rep(data[0], to_datetime(normalize_date(data[1])))
        else:
            delete_rep(data[0], to_datetime(normalize_date(data[1])))

if __name__ == "__main__":
    db_init(940454804)
