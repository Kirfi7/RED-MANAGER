import sqlite3

db = sqlite3.connect('database.db')
c = db.cursor()
c.execute("""CREATE TABLE warn (
    user_id integer,
    admin_id integer,
    warn_reason text,
    operation text
    )""")
db.commit()
db.close()
