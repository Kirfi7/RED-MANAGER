import sqlite3
import datetime
import vk_api
from config import TOKEN

vk_session = vk_api.VkApi(token=TOKEN)


def get_name(user_id):
    names = vk_session.method("users.get", {"user_ids": user_id})[0]
    return f"{names['first_name']} {names['last_name']}"


class Get:
    def __init__(self, message, session):
        self.message = message
        self.forward = session.method('messages.getByConversationMessageId', {
            'conversation_message_ids': message['conversation_message_id'],
            'peer_id': message['peer_id']
        })
        self.vk = session.get_api()

    def to_user_id(self):
        message_text = self.message['text']
        fwd = self.forward['items'][0]
        if 'reply_message' in fwd:
            f = fwd['reply_message']
            return f['from_id']
        elif len(fwd['fwd_messages']) > 0:
            f = fwd['fwd_messages'][0]
            return f['from_id']
        elif '@' in message_text or 'vk' in message_text:
            if '@' in message_text:
                if 'id' in message_text and not('|' in message_text):
                    return ((message_text.split())[1])[3:]
                else:
                    u = ((message_text.split())[1])[3:]
                    return (u.split('|'))[0]
            link_text = (message_text.split())[1]
            if link_text != '':
                link_text = (link_text.split('/'))[-1]
                if 'object_id' in self.vk.utils.resolveScreenName(screen_name=link_text):
                    to_user_id = self.vk.utils.resolveScreenName(screen_name=link_text)['object_id']
                    return to_user_id
                else:
                    return 'Error'
            else:
                return 'Error'
        else:
            return 'Error'

    def single_argument(self):
        message_text = self.message['text']
        fwd = self.forward['items'][0]
        if 'reply_message' in fwd:
            lcmd = len((message_text.split())[0])
            return message_text[lcmd:]
        elif len(fwd['fwd_messages']) > 0:
            lcmd = len((message_text.split())[0])
            return message_text[lcmd:]
        elif '@' in message_text or 'vk' in message_text:
            lcmd = (message_text.split())[0] + (message_text.split())[1]
            lcmd = len(lcmd) + 2
            return message_text[lcmd:]
        else:
            if len(message_text.split()) > 1:
                x = len(message_text.split()[0])
                return message_text[x+1:]
            else:
                return 'Error'


class Data:
    def __init__(self, data_name):
        self.conn = sqlite3.connect(data_name)
        self.c = self.conn.cursor()

    def set_nick(self, nick_name, to_user_id):
        self.c.execute(f"UPDATE users SET nick_name = '{nick_name}' WHERE user_id = '{to_user_id}'")
        return self.conn.commit(), self.conn.close()

    def get_nick(self, to_user_id):
        result = self.c.execute(f"SELECT nick_name FROM users WHERE user_id = '{to_user_id}'")
        try:
            nick_name = result.fetchone()[0]
            if nick_name == 'Нет' or nick_name == 'None' or nick_name == 'Error' or nick_name == '':
                nick_name = get_name(to_user_id)
            return self.conn.commit(), self.conn.close(), nick_name
        except:
            return self.conn.commit(), self.conn.close(), "Error"

    def user_kick(self, to_user_id):
        self.c.execute(f"DELETE FROM users WHERE user_id = '{to_user_id}'")
        return self.conn.commit(), self.conn.close()

    def rem_nick(self, to_user_id):
        self.c.execute(f"UPDATE users SET nick_name = '' WHERE user_id = '{to_user_id}'")
        return self.conn.commit(), self.conn.close()

    def roles_access(self, from_user_id, to_user_id, access, self_level):
        result1 = self.c.execute(f"SELECT admin_roles FROM users WHERE user_id = '{from_user_id}'")
        from_level = str(result1.fetchone())[1]
        result2 = self.c.execute(f"SELECT admin_roles FROM users WHERE user_id = '{to_user_id}'")
        to_level = str(result2.fetchone())[1]
        self.conn.commit(), self.conn.close()
        if to_level == 'None' or to_level == '' or to_level == 'o':
            to_level = '0'
        if from_level == 'None' or from_level == '' or from_level == 'o':
            from_level = '0'
        to_level = int(to_level)
        from_level = int(from_level)
        if self_level >= 1 and from_user_id == to_user_id and (not('-' in str(from_user_id))):
            if from_level >= access:
                return 1
            else:
                return 0
        elif self_level == 2:
            if from_level >= access and from_level >= to_level:
                return 1
            else:
                return 0
        elif from_level > to_level:
            return 1
        else:
            return 0

    def get_role(self, to_user_id):
        result = self.c.execute(f"SELECT admin_roles FROM users WHERE user_id = '{to_user_id}'").fetchone()
        if result is None:
            from_level = 0
        else:
            from_level = result[0]
        return self.conn.commit(), self.conn.close(), int(from_level)

    def new_user(self, to_user_id):
        self.c.execute(f"""INSERT INTO users VALUES (
        '{to_user_id}',
        'Нет',
        '{0}',
        '{0}',
        '{0}'
        )""")
        return self.conn.commit(), self.conn.close()

    def start(self, user_ids, chat_id):
        try:
            self.c.execute("""CREATE TABLE ban (
                user_id integer,
                admin_id integer,
                ban_date text,
                ban_reason text
                )""")
            self.c.execute("""CREATE TABLE warn (
                user_id integer,
                admin_id integer,
                warn_reason text
                )""")
            self.c.execute("""CREATE TABLE mute (
                user_id integer,
                minutes integer
                )""")
            self.c.execute("""CREATE TABLE users (
                user_id text,
                nick_name text,
                is_mute integer,
                warn_count integer,
                admin_roles integer
                )""")
        except:
            return self.conn.commit(), self.conn.close(), 0
        db = sqlite3.connect('global_base.db')
        c = db.cursor()
        c.execute(f"""INSERT INTO chat VALUES (
                '{chat_id}',
                'all',
                'all'
                )""")
        db.commit()
        db.close()
        for i in user_ids:
            self.c.execute(f"""INSERT INTO users VALUES (
                '{i}',
                'Нет',
                '{0}',
                '{0}',
                '{0}'
                )""")
        return self.conn.commit(), self.conn.close(), 1

    def add_warn(self, to_user_id, admin_id, reason):
        self.c.execute(f"""INSERT INTO warn VALUES (
            '{to_user_id}',
            '{admin_id}',
            '{reason}'
            )""")
        row = self.c.execute(f"SELECT rowid FROM warn WHERE user_id = '{to_user_id}'").fetchall()
        if len(row) > 5:
            first_row = row[-5]
            for i in row:
                if i[0] < first_row[0]:
                    self.c.execute(f"DELETE FROM warn WHERE rowid = '{i[0]}'")
        result = self.c.execute(f"SELECT warn_count FROM users WHERE user_id = '{to_user_id}'")
        count = int(str(result.fetchone())[1]) + 1
        if count == 3:
            self.c.execute(f"UPDATE users SET warn_count = {0} WHERE user_id = '{to_user_id}'")
            return self.conn.commit(), self.conn.close(), 0, 1
        else:
            self.c.execute(f"UPDATE users SET warn_count = {count} WHERE user_id = '{to_user_id}'")
            return self.conn.commit(), self.conn.close(), count, 0

    def del_warn(self, to_user_id):
        result = self.c.execute(f"SELECT warn_count FROM users WHERE user_id = '{to_user_id}'")
        count = int(str(result.fetchone())[1]) - 1
        self.c.execute(f"UPDATE users SET warn_count = {count} WHERE user_id = '{to_user_id}'")
        return self.conn.commit(), self.conn.close()

    def get_warns(self, to_user_id):
        try:
            result = self.c.execute(f"SELECT warn_count FROM users WHERE user_id = '{to_user_id}'")
            count = int(str(result.fetchone())[1])
            return self.conn.commit(), self.conn.close(), count
        except:
            return self.conn.commit(), self.conn.close(), 0

    def warn_history(self, to_user_id, count):
        result = self.c.execute(f"SELECT * FROM warn WHERE user_id = '{to_user_id}'").fetchall()
        x = len(result)
        msg = f"Последние 5 выданных предупреждений [id{to_user_id}|пользователя]:\n\n"
        for i in range(x):
            reason = (result[i][2])
            if reason == '' or reason == 'None':
                reason = '—'
            first_plus = x-count
            if i < first_plus:
                smile = '❌'
            else:
                smile = '✅'
            msg = msg + f"[id{result[i][1]}|Администратор] | {reason} | {smile}\n"
        msg = msg + f"\nАктивных предупреждений: {count}."
        return self.conn.commit(), self.conn.close(), msg

    def staff(self):
        msg_5 = 'Главный Администратор:\n— [id468509613|Kirfi_Marciano]' \
              '\n\nЗам. Главного Администратора:\n— [id327113505|Ricardo_Vendetta]\n— [id16715256|Prokhor_Adzinets]' \
                '\n\nКураторы Администрации:\n— [id534422651|Mikhail_Pearson]\n— [id137480835|Serega_Forestry]\n'
        r = self.c.execute(f"SELECT user_id FROM users WHERE admin_roles = '4'").fetchall()
        msg_4 = msg_5 + '\nСтаршие Администраторы:\n'
        for i in range(len(r)):
            for_id = r[i][0]
            fet = self.c.execute(f"SELECT nick_name FROM users WHERE user_id = {for_id}")
            for_nick = fet.fetchone()[0]
            if for_nick == 'Нет' or for_nick == 'None' or for_nick == 'Error' or for_nick == '':
                for_nick = get_name(for_id)
            msg_4 = msg_4 + f'— [id{for_id}|{for_nick}]\n'
        r = self.c.execute(f"SELECT user_id FROM users WHERE admin_roles = '3'").fetchall()
        msg_3 = msg_4 + '\nАдминистраторы:\n'
        for i in range(len(r)):
            for_id = r[i][0]
            fet = self.c.execute(f"SELECT nick_name FROM users WHERE user_id = {for_id}")
            for_nick = fet.fetchone()[0]
            if for_nick == 'Нет' or for_nick == 'None' or for_nick == 'Error' or for_nick == '':
                for_nick = get_name(for_id)
            msg_3 = msg_3 + f'— [id{for_id}|{for_nick}]\n'
        r = self.c.execute(f"SELECT user_id FROM users WHERE admin_roles = '2'").fetchall()
        msg_2 = msg_3 + '\nСтаршие Модераторы:\n'
        for i in range(len(r)):
            for_id = r[i][0]
            fet = self.c.execute(f"SELECT nick_name FROM users WHERE user_id = {for_id}")
            for_nick = fet.fetchone()[0]
            if for_nick == 'Нет' or for_nick == 'None' or for_nick == 'Error' or for_nick == '':
                for_nick = get_name(for_id)
            msg_2 = msg_2 + f'— [id{for_id}|{for_nick}]\n'
        r = self.c.execute(f"SELECT user_id FROM users WHERE admin_roles = '1'").fetchall()
        msg = msg_2 + '\nМодераторы:\n'
        for i in range(len(r)):
            for_id = r[i][0]
            fet = self.c.execute(f"SELECT nick_name FROM users WHERE user_id = {for_id}")
            for_nick = fet.fetchone()[0]
            if for_nick == 'Нет' or for_nick == 'None' or for_nick == 'Error' or for_nick == '':
                for_nick = get_name(for_id)
            msg = msg + f'— [id{for_id}|{for_nick}]\n'
        return self.conn.commit(), self.conn.close(), msg

    def get_acc(self, nick_name):
        try:
            result = self.c.execute(f"SELECT user_id FROM users WHERE nick_name = '{nick_name}'")
            user_id = result.fetchone()[0]
            if user_id == 'Нет' or str(user_id) == 'None' or user_id == 'Error' or user_id == '':
                user_id = 'Error'
            return self.conn.commit(), self.conn.close(), user_id
        except:
            return self.conn.commit(), self.conn.close(), 'Error'

    def nick_list(self):
        r = self.c.execute(f"SELECT nick_name, user_id FROM users WHERE nick_name <> 'None' AND nick_name <> 'Нет' AND nick_name <> ''").fetchall()
        msg = f"Список пользователей с никами:"
        for i in range(len(r)):
            msg += f"\n{i+1}) [id{r[i][1]}|{get_name(r[i][1])}] — {r[i][0]}"
        return self.conn.commit(), self.conn.close(), msg

    def add_ban(self, to_user_id, reason, admin):
        self.c.execute(f"""INSERT INTO ban VALUES (
        '{to_user_id}',
        '{admin}',
        '{str(datetime.datetime.now().timestamp()).split('.')[0]}',
        '{reason}'
        )""")
        return self.conn.commit(), self.conn.close()

    def del_ban(self, to_user_id):
        self.c.execute(f"DELETE FROM ban WHERE user_id = '{to_user_id}'")
        return self.conn.commit(), self.conn.close()

    def get_ban(self, to_user_id):
        r = self.c.execute(f"SELECT user_id FROM ban").fetchall()
        for user in r:
            if int(user[0]) == int(to_user_id):
                return self.conn.commit(), self.conn.close(), 1
        return self.conn.commit(), self.conn.close(), 0

    def set_level(self, to_user_id, level):
        self.c.execute(f"UPDATE users SET admin_roles = '{level}' WHERE user_id = '{to_user_id}'")
        return self.conn.commit(), self.conn.close()

    def full_get_ban(self, to_user_id):
        result = self.c.execute(f"SELECT * FROM ban WHERE user_id = '{to_user_id}'").fetchall()[0]
        slovar = {'admin_id': f'{result[1]}', 'ban_reason': f'{result[3]}', 'ban_date': f'{result[2]}'}
        return self.conn.commit(), self.conn.close(), slovar
