import threading
import sqlite3
import time


class Connect:

    def __init__(self, chat):
        self.chat = chat

    def __enter__(self):
        self.lock = threading.Lock()
        self.lock.acquire()

        self.db = sqlite3.connect(f"databases/data_{self.chat}.db")
        self.c = self.db.cursor()
        return self.c

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.commit()
        self.db.close()
        self.lock.release()


def start(chat_id: int):
    with Connect(chat_id) as c:

        c.execute("CREATE TABLE admins (user_id INTEGER, level INTEGER)")
        c.execute("CREATE TABLE nicks (user_id INTEGER, nick_name TEXT)")
        c.execute("CREATE TABLE mutes (user_id INTEGER, end INTEGER)")
        c.execute("CREATE TABLE bans (user_id INTEGER, admin_id INTEGER, date INTEGER, reason TEXT)")
        c.execute("CREATE TABLE warns (user_id INTEGER, count INTEGER)")
        c.execute("CREATE TABLE logs (user_id INTEGER, admin_id INTEGER, date INTEGER, reason TEXT, type TEXT)")


def add_admin(chat_id: int, user_id: int, level: int):
    with Connect(chat_id) as c:
        c.execute(f"DELETE FROM admins WHERE user_id = '{user_id}'")
        c.execute(f"INSERT INTO admins VALUES ('{user_id}', '{level}')")


def del_admin(chat_id: int, user_id: int):
    with Connect(chat_id) as c:
        c.execute(f"DELETE FROM admins WHERE user_id = '{user_id}'")


def get_level(chat_id, user_id):
    with Connect(chat_id) as c:
        return c.execute(f"SELECT level FROM admins WHERE user_id = '{user_id}'").fetchone()


def get_admins(chat_id: int):
    with Connect(chat_id) as c:
        data = {
            'Ст. администраторы:': c.execute(f"SELECT user_id FROM admins WHERE level = '3'").fetchall(),
            'Администраторы:': c.execute(f"SELECT user_id FROM admins WHERE level = '2'").fetchall(),
            'Модераторы:': c.execute(f"SELECT user_id FROM admins WHERE level = '1'").fetchall()
        }
    return data


def set_nick(chat_id: int, user_id: int, nick: str):
    with Connect(chat_id) as c:
        c.execute(f"DELETE FROM nicks WHERE user_id = '{user_id}'")
        c.execute(f"INSERT INTO nicks VALUES ('{user_id}', '{nick}')")


def all_nicks(chat_id):
    with Connect(chat_id) as c:
        return c.execute(f"SELECT * FROM nicks").fetchall()


def del_nick(chat_id: int, user_id: int):
    with Connect(chat_id) as c:
        c.execute(f"DELETE FROM nicks WHERE user_id = '{user_id}'")


def get_nick(chat_id: int, user_id: int):
    with Connect(chat_id) as c:
        result = c.execute(f"SELECT nick_name FROM nicks WHERE user_id = '{user_id}'").fetchone()
    return result


def find_nick(chat_id: int, request: str):
    with Connect(chat_id) as c:
        result = c.execute(f"SELECT * FROM nicks WHERE nick_name LIKE '%{request}%'").fetchall()
    return result


def get_mute(chat_id, user_id):
    with Connect(chat_id) as c:
        result = c.execute(f"SELECT end FROM mutes WHERE user_id = '{user_id}'").fetchall()
    if len(result) > 1:
        return int(result[-1][0])
    elif len(result) == 1:
        return int(result[0][0])
    return 0


def all_mutes(chat_id):
    with Connect(chat_id) as c:
        return c.execute(f"SELECT end FROM mutes").fetchall()


def del_mute_by_end(chat_id, end_time):
    with Connect(chat_id) as c:
        c.execute(f"DELETE FROM mutes WHERE end = '{end_time}'")


def add_mute(chat_id, user_id, minutes):
    end_time = int(time.time()) + (int(minutes) * 60)
    with Connect(chat_id) as c:
        c.execute(f"INSERT INTO mutes VALUES ('{user_id}', '{end_time}')")
    return end_time


def del_mute(chat_id, user_id):
    with Connect(chat_id) as c:
        c.execute(f"DELETE FROM mutes WHERE user_id = '{user_id}'")


def add_warn(chat_id, user_id, reason, admin_id):
    with Connect(chat_id) as c:
        result = c.execute(f"SELECT count FROM warns WHERE user_id = '{user_id}'").fetchone()
        if result:
            c.execute(f"UPDATE warns SET 'count' = '{int(result[0])+1}' WHERE user_id = '{user_id}'")
        else:
            c.execute(f"INSERT INTO warns VALUES ('{user_id}', '1')")
        c.execute(f"INSERT INTO logs VALUES ('{user_id}', '{admin_id}', '{int(time.time())}', '{reason}', 'Плюс варн')")


def del_warn(chat_id, user_id, admin_id):
    with Connect(chat_id) as c:
        result = int(c.execute(f"SELECT count FROM warns WHERE user_id = '{user_id}'").fetchone()[0])
        if result == 1:
            c.execute(f"DELETE FROM warns WHERE user_id = '{user_id}'")
        else:
            c.execute(f"UPDATE warns SET count = '{result-1}' WHERE user_id = '{user_id}'")
        c.execute(f"INSERT INTO logs VALUES ('{user_id}', '{admin_id}', '{int(time.time())}', 'None', 'Минус варн')")


def warns_count(chat_id, user_id):
    with Connect(chat_id) as c:
        result = c.execute(f"SELECT count FROM warns WHERE user_id = '{user_id}'").fetchone()
    return int(result[0]) if result else 0


def warns_list(chat_id):
    with Connect(chat_id) as c:
        result = c.execute("SELECT * FROM warns").fetchall()
    return result


def history(chat_id, user_id):
    with Connect(chat_id) as c:
        result = c.execute(f"SELECT * FROM logs WHERE user_id = '{user_id}'").fetchall()
    return result


def add_ban(chat_id, user_id, admin_id, reason):
    with Connect(chat_id) as c:
        c.execute(f"INSERT INTO logs VALUES ('{user_id}', '{admin_id}', '{int(time.time())}', '{reason}', 'Плюс бан')")
        c.execute(f"INSERT INTO bans VALUES ('{user_id}', '{admin_id}', '{int(time.time())}', '{reason}')")


def del_ban(chat_id, user_id, admin_id):
    with Connect(chat_id) as c:
        c.execute(f"DELETE FROM bans WHERE user_id = '{user_id}'")
        c.execute(f"INSERT INTO logs VALUES ('{user_id}', '{admin_id}', '{int(time.time())}', 'None', 'Минус бан')")


def get_ban(chat_id, user_id):
    with Connect(chat_id) as c:
        result = c.execute(f"SELECT * FROM bans WHERE user_id = '{user_id}'").fetchall()
    return result


def bans_list(chat_id):
    with Connect(chat_id) as c:
        result = c.execute(f"SELECT user_id FROM bans").fetchall()
    return result


def insert_chat(chat_id):
    with Connect('main') as c:
        c.execute(f"INSERT INTO chats VALUES ('{chat_id}', 'None', '0', 'NONE')")


def get_chats_list():
    with Connect('main') as c:
        result = c.execute("SELECT chat_id FROM chats").fetchall()
    return set(map(lambda el: int(el[0]), result))


def add_global_ban(user_id, admin_id, date, reason, btype):
    with Connect('main') as c:
        c.execute(f"INSERT INTO bans VALUES ('{user_id}', '{admin_id}', '{date}', '{reason}', '{btype}')")


def del_global_ban(user_id):
    with Connect('main') as c:
        c.execute(f"DELETE FROM bans WHERE user_id = '{user_id}'")


def global_getban(user_id):
    with Connect('main') as c:
        return c.execute(f"SELECT * FROM bans WHERE user_id = '{user_id}'").fetchall()


def get_quiet(chat_id):
    with Connect('main') as c:
        result = c.execute(f"SELECT quiet FROM chats WHERE chat_id = '{chat_id}'").fetchone()
    return int(result[0]) if result else 0


def set_quiet(chat_id, quiet: bool):
    with Connect('main') as c:
        c.execute(f"UPDATE chats SET quiet = '{1 if quiet else 0}' WHERE chat_id = '{chat_id}'").fetchone()


def get_greeting(chat_id):
    with Connect('main') as c:
        result = c.execute(f"SELECT greeting FROM chats WHERE chat_id = '{chat_id}'").fetchone()
    return result[0] if result else 0


def set_greeting(chat_id, text):
    with Connect('main') as c:
        c.execute(f"UPDATE chats SET greeting = '{text}' WHERE chat_id = '{chat_id}'")


def get_chat_type(chat_id):
    with Connect('main') as c:
        result = c.execute(f"SELECT type FROM chats WHERE chat_id = '{chat_id}'").fetchall()
    return result[0][0] if result else []


def set_chat_type(chat_id, text):
    with Connect('main') as c:
        c.execute(f"UPDATE chats SET type = '{text}' WHERE chat_id = '{chat_id}'")


def get_chats_by_type(text):
    with Connect('main') as c:
        if text.upper() != "ALL":
            result = c.execute(f"SELECT chat_id FROM chats WHERE type LIKE '%{text.replace(' ', '% %')}%'").fetchall()
        else:
            result = c.execute(f"SELECT chat_id FROM chats").fetchall()
    return list(map(lambda el: el[0], result)) if result else []
