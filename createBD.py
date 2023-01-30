import sqlite3

db = sqlite3.connect('global_base.db')
c = db.cursor()
c.execute("""CREATE TABLE ban (
    user_id integer,
    admin_id integer,
    ban_date text,
    ban_days integer,
    ban_reason text
    )""")
c.execute("""CREATE TABLE chat (
    chat_id integer,
    chat_type text,
    chat_line text
    )""")
db.commit()
db.close()
# fkjfghfkjhfgjhfgjhfgjhf