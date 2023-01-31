import sqlite3
import datetime
import time
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from models import Get, Data
from config import *

vk_session = vk_api.VkApi(token=TOKEN)
lp = VkBotLongPoll(vk_session, 218266206)
vk = vk_session.get_api()


def sender(from_chat_id, text, message_id):
    vk.messages.send(chat_id=from_chat_id, message=text, random_id=0, reply_to=message_id)


def s_sender(from_chat_id, text):
    vk.messages.send(chat_id=from_chat_id, message=text, random_id=0)


def l_sender(for_user_id, text):
    vk.messages.send(user_id=for_user_id, message=text, random_id=0)


def get_name(name_user_id) -> str:
    names = vk_session.method("users.get", {"user_ids": name_user_id, "name_case": "gen"})[0]
    return f"{names['first_name']} {names['last_name']}"


def normal_id(for_user_id):
    if for_user_id == 'Error' or str(for_user_id) == 'None' or '-' in str(for_user_id):
        return 0
    else:
        return 1


def normal_argument(for_argument):
    if for_argument == 'Error' or str(for_argument) == 'None' or for_argument == '':
        return 0
    else:
        return 1


def role(level):
    if level >= 5:
        return "Руководитель Сервера"
    elif level == 4:
        return "Старший Администратор"
    elif level == 3:
        return "Администратор"
    elif level == 2:
        return "Старший Модератор"
    elif level == 1:
        return "Модератор"
    else:
        return "Пользователь"


for event in lp.listen():

    if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat and len(event.object.message['text']) > 0:

        chat_id = event.chat_id
        db = f"data{chat_id}.db"
        message_text = event.object.message['text']
        mid = event.object.message['conversation_message_id']

        if message_text[0] in prefix:

            cmd = (message_text.split()[0])[1:]
            if cmd in users_commands:
                if cmd == 'help':
                    pass

                elif cmd == 'id' or cmd == 'getid':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    db = f"data{chat_id}.db"
                    if to_user_id != 'Error' and to_user_id != 'None' and not ('-' in str(to_user_id)):
                        msg = f"Роль [id{to_user_id}|пользователя] в беседе: {role(Data(db).get_role(to_user_id))}"
                        sender(chat_id, f"Оригинальная ссылка на пользователя: https://vk.com/id{to_user_id}",
                               mid + 95)
                    else:
                        sender(chat_id, "Ссылка указана некорректно.", mid + 95)

                elif cmd == 'stats' or cmd == 'стата':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    db = f"data{chat_id}.db"
                    if to_user_id != 'Error' and to_user_id != 'None' and not ('-' in str(to_user_id)):
                        muted = 'Есть' if Data(db).is_muted(to_user_id)[2] == 1 else 'Нет'
                        msg = f"Общая информация про [id{to_user_id}|{get_name(to_user_id)}]:\n" \
                              f"Роль: {role(Data(db).get_role(to_user_id))}\n" \
                              f"Никнейм: {Data(db).get_nick(to_user_id)[2]}\n" \
                              f"Количество предупреждений: {Data(db).get_warns(to_user_id)[2]}/3"
                        sender(chat_id, msg, mid + 95)
                    else:
                        sender(chat_id, "Ссылка указана некорректно.", mid + 95)

            elif cmd in moder_commands:

                from_user_id = event.object.message['from_id']
                lvl = Data(db).user_role(from_user_id)[2]
                if lvl < 1:
                    sender(chat_id, "Недостаточно прав!", mid + 95)

                elif cmd == 'warn' or cmd == 'варн':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    argument = Get(event.object.message, vk_session).single_argument()
                    if normal_argument(argument) == 1 and normal_id(to_user_id) == 1:
                        moder_nick = Data(db).get_nick(from_user_id)[2]
                        result = Data(db).add_warn(to_user_id, from_user_id, argument)
                        msg = f'[id{from_user_id}|{moder_nick}] выдал предупреждение [id{to_user_id}|пользователю].'
                        msg = msg + f"\nПричина: {argument} | Количество: {result[2]}/3."
                        if result[3] == 1:
                            Data(db).user_kick(to_user_id)
                            vk.messages.removeChatUser(chat_id=chat_id, user_id=to_user_id)
                            sender(chat_id, f'[id{to_user_id}|Пользователь] заблокирован, получено 3/3 предупреждения.')
                        else:
                            sender(chat_id, msg, mid + 95)
                    else:
                        sender(chat_id, "Ссылка или аргумент указаны некорректно.", mid + 95)

                elif cmd == 'unwarn':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    if normal_id(to_user_id) == 1:
                        moder_nick = Data(db).get_nick(from_user_id)[2]
                        warns = Data(db).get_warns(to_user_id)[2]
                        if warns == 0:
                            sender(chat_id, f'У [id{to_user_id}|пользователя] нет активных предупреждений!')
                        else:
                            Data(db).del_warn(to_user_id)
                            warns = Data(db).get_warns(to_user_id)[2]
                            msg = f'[id{from_user_id}|{moder_nick}] снял предупреждение [id{to_user_id}|пользователю].'
                            msg = msg + f"\nТекущее количество предупреждений: {warns}/3."
                            sender(chat_id, msg, mid + 95)
                    else:
                        sender(chat_id, "Ссылка указана некорректно.", mid + 95)

                elif cmd == 'snick' or cmd == 'setnick':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    argument = Get(event.object.message, vk_session).single_argument()
                    if normal_argument(argument) == 1 and normal_id(to_user_id) == 1:
                        Data(db).set_nick(argument, to_user_id)
                        sender(chat_id, f'Новый никнейм [id{to_user_id}|пользователя] — {argument}.', mid + 95)
                    else:
                        sender(chat_id, "Ссылка или аргумент указаны некорректно.", mid + 95)

                elif cmd == 'gnick' or cmd == 'getnick':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    if normal_id(to_user_id) == 1:
                        msg = Data(db).get_nick(to_user_id)[2]
                        if msg == '' or msg == 'Error' or msg == 'Нет' or msg == 'None' or msg == get_name(to_user_id):
                            msg = f"У [id{to_user_id}|пользователя] не установлен никнейм."
                            sender(chat_id, msg, mid + 95)
                        else:
                            sender(chat_id, f'Никнейм [id{to_user_id}|пользователя] — {msg}.', mid + 95)
                    else:
                        sender(chat_id, "Ссылка указана некорректно.", mid + 95)

                elif cmd == 'nlist':
                    sender(chat_id, Data(db).nick_list()[2], mid + 95)

                elif cmd == 'kick' or cmd == 'кик':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    members = vk.messages.getConversationMembers(peer_id=2000000000 + chat_id)['items']
                    all_users = []
                    conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + chat_id))['items']
                    admin_ids = (conservations[0]['chat_settings'])['admin_ids']
                    for member in members:
                        all_users.append(member['member_id'])
                    if normal_id(to_user_id) == 1:
                        if int(to_user_id) in all_users and not (int(to_user_id) in admin_ids):
                            Data(db).user_kick(to_user_id)
                            vk.messages.removeChatUser(chat_id=chat_id, user_id=to_user_id)
                            sender(chat_id, f"[id{to_user_id}|Пользователь] исключён из чата.", mid + 95)
                        else:
                            sender(chat_id, "Не могу исключить данного пользователя.", mid + 95)
                    else:
                        sender(chat_id, "Ссылка указана некорректно.", mid + 95)

                elif cmd == 'staff':
                    sender(chat_id, Data(db).staff()[2], mid)

                elif cmd == 'getacc':
                    argument = Get(event.object.message, vk_session).single_argument()
                    if normal_argument(argument) == 1:
                        pass
                    else:
                        sender(chat_id, "Аргумент указан некорректно.", mid + 95)

                elif cmd == 'rnick' or cmd == 'removenick':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    if normal_id(to_user_id) == 1:
                        moder_nick = Data(db).get_nick(from_user_id)[2]
                        Data(db).rem_nick(to_user_id)
                        sender(chat_id,
                               f"[id{from_user_id}|{moder_nick}] удалил никнейм [id{to_user_id}|пользователю].")
                    else:
                        sender(chat_id, "Ссылка указана некорректно.", mid + 95)

            elif cmd in sen_moder_commands:

                from_user_id = event.object.message['from_id']
                lvl = Data(db).user_role(from_user_id)[2]
                if lvl < 2:
                    sender(chat_id, "Недостаточно прав!", mid + 95)

                elif cmd == 'ban':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    argument = Get(event.object.message, vk_session).single_argument()
                    if normal_argument(argument) == 1 and normal_id(to_user_id) == 1:
                        Data(db).add_ban(to_user_id, argument, from_user_id)
                        members = vk.messages.getConversationMembers(peer_id=2000000000 + chat_id)['items']
                        all_users = []
                        moder_nick = Data(db).get_nick(from_user_id)[2]
                        for member in members:
                            all_users.append(int(member['member_id']))
                        if int(to_user_id) in all_users:
                            Data(db).user_kick(to_user_id)
                            vk.messages.removeChatUser(chat_id=chat_id, user_id=to_user_id)
                        msg = f"[id{from_user_id}|{moder_nick}] заблокировал [id{to_user_id}|пользователя]"
                        msg += f"\nПричина: {argument}."
                        sender(chat_id, msg, mid + 95)
                    else:
                        sender(chat_id, "Ссылка или аргумент указаны некорректно.", mid + 95)

                elif cmd == 'unban':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    if normal_id(to_user_id) == 1:
                        if Data(db).get_ban(to_user_id) == 1:
                            sender(chat_id, f"[id{to_user_id}|Пользователь] был успешно разблокирован.", mid + 95)
                            Data(db).del_ban(str(to_user_id))
                        else:
                            sender(chat_id, f"[id{to_user_id}|Пользователь] не заблокирован в этой беседе.", mid + 95)
                    else:
                        sender(chat_id, "Ссылка указана некорректно.", mid + 95)

                elif cmd == 'getban':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    if normal_id(to_user_id) == 1:
                        dtb = sqlite3.connect('global_base.db')
                        c = dtb.cursor()
                        user_ids_no = c.execute(f"SELECT * FROM ban WHERE ban_type = 'No'").fetchall()
                        user_ids_pl = c.execute(f"SELECT * FROM ban WHERE ban_type = 'Pl'").fetchall()
                        dtb.commit()
                        dtb.close()
                        no_msg = 'Отсутствует'
                        pl_msg = 'Отсутствует'
                        for i in user_ids_no:
                            if int(i[0]) == int(to_user_id):
                                ban_full_date = time.localtime(int(i[2]))
                                ban_date = time.strftime("%d.%m.%Y %H:%M:%S", ban_full_date)
                                no_msg = f"\n[id{i[1]}|Модератор] | {i[3]} | {ban_date}"
                        for i in user_ids_pl:
                            if int(i[0]) == int(to_user_id):
                                ban_full_date = time.localtime(int(i[2]))
                                ban_date = time.strftime("%d.%m.%Y %H:%M:%S", ban_full_date)
                                no_msg = f"\n[id{i[1]}|Модератор] | {i[3]} | {ban_date}"
                        msg = f'Информация о блокировках [id{to_user_id}|пользователя]:\n\n' \
                              f'Глобальная блокировка в беседах игроков: {pl_msg}.\n' \
                              f'Глобальная блокировка во всех беседах: {no_msg}.\n'
                        if Data(db).get_ban(to_user_id)[2] == 1:
                            slovar = Data(db).full_get_ban(to_user_id)[2]
                            ban_full_date = time.localtime(int(slovar['ban_date']))
                            ban_date = time.strftime("%d.%m.%Y %H:%M:%S", ban_full_date)
                            msg += f"\nБлокировка в данной беседе:\n" \
                                   f"[id{slovar['admin_id']}|Модератор] | {slovar['ban_reason']} | {ban_date}."
                        else:
                            msg += f"\nБлокировка в данной беседе: Отсутствует."
                        sender(chat_id, msg, mid + 95)
                    else:
                        sender(chat_id, "Ссылка указана некорректно.", mid + 95)

                elif cmd == 'getwarn' or cmd == 'warnlist':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    if normal_id(to_user_id) == 1:
                        warns = Data(db).get_warns(to_user_id)[2]
                        sender(chat_id, Data(db).warn_history(to_user_id, warns)[2], mid + 95)
                    else:
                        sender(chat_id, "Ссылка указана некорректно.", mid + 95)

                elif cmd == 'moder' or cmd == 'модер':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    if normal_id(to_user_id) == 1:
                        moder_nick = Data(db).get_nick(from_user_id)[2]
                        Data(db).set_role(to_user_id, 1)
                        msg = f'[id{from_user_id}|{moder_nick}] выдал права модератора'
                        msg = msg + f' [id{to_user_id}|пользователю].'
                        sender(chat_id, msg, mid + 95)
                    else:
                        sender(chat_id, "Ссылка указана некорректно.", mid + 95)

                elif cmd == 'rrole' or cmd == 'removerole':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    if normal_id(to_user_id) == 1:
                        Data(db).set_role(to_user_id, 0)
                        moder_nick = Data(db).get_nick(from_user_id)[2]
                        msg = f'[id{from_user_id}|{moder_nick}] снял все права [id{to_user_id}|пользователю].'
                        sender(chat_id, msg, mid + 95)
                    else:
                        sender(chat_id, "Ссылка указана некорректно.", mid + 95)

                elif cmd == 'zov' or cmd == 'зов':
                    argument = Get(event.object.message, vk_session).single_argument()
                    if normal_argument(argument) == 1:
                        members = vk.messages.getConversationMembers(peer_id=2000000000 + chat_id)['items']
                        msg = f'🔔 Вы были вызваны [id{from_user_id}|администратором] беседы!\n\n'
                        for member in members:
                            if not ('-' in str(member['member_id'])):
                                msg = msg + f"[id{member['member_id']}|👤]"
                        msg = msg + f"\n\n❗️ Причина вызова: {argument} ❗️"
                        sender(chat_id, msg, mid + 95)
                    else:
                        sender(chat_id, "Аргумент указан некорректно.", mid + 95)

            elif cmd in admin_commands:

                from_user_id = event.object.message['from_id']
                lvl = Data(db).user_role(from_user_id)[2]
                if lvl < 3:
                    sender(chat_id, "Недостаточно прав!", mid + 95)

                elif cmd == 'smoder' or cmd == 'смодер':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    if normal_id(to_user_id) == 1:
                        moder_nick = Data(db).get_nick(from_user_id)[2]
                        Data(db).set_role(to_user_id, 2)
                        msg = f'[id{from_user_id}|{moder_nick}] выдал права старшего модератора [id{to_user_id}|пользователю].'
                        sender(chat_id, msg, mid + 95)
                    else:
                        sender(chat_id, "Ссылка указана некорректно.", mid + 95)

                elif '/sszov' in message_text:
                    argument = Get(event.object.message, vk_session).single_argument()
                    if normal_argument(argument) == 1:
                        db = sqlite3.connect('global_base.db')
                        c = db.cursor()
                        chat_ids = (c.execute(f"SELECT chat_id FROM chat WHERE chat_type = 'ss'").fetchall())
                        db.commit()
                        db.close()
                        chats = ''
                        for i in range(len(chat_ids)):
                            for_chat_id = (chat_ids[i])[0]
                            members = vk.messages.getConversationMembers(peer_id=2000000000 + for_chat_id)
                            items = members['items']
                            msg = f'🔔 Вы были вызваны [id{from_user_id}|администратором] беседы!\n\n'
                            for b in range(len(items)):
                                if not ('-' in str(items[b]['member_id'])):
                                    msg = msg + f"[id{items[b]['member_id']}|👤]"
                            msg = msg + f"\n\n❗️ Причина вызова: {argument} ❗️"
                            s_sender(for_chat_id, msg)
                            Conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + for_chat_id))[
                                'items']
                            for_chat_name = (Conservations[0]['chat_settings'])['title']
                            chats += f'{for_chat_name} | {for_chat_id}\n'
                        l_sender(from_user_id, f"Сообщение отправлено в чаты:\n\n{chats}\n\nТекст вызова: {argument}")
                    else:
                        sender(chat_id, 'Причина вызова указана некорректно.', mid + 95)

                elif '/mszov' in message_text:
                    argument = Get(event.object.message, vk_session).single_argument()
                    if normal_argument(argument) == 1:
                        db = sqlite3.connect('global_base.db')
                        c = db.cursor()
                        chat_ids = (c.execute(f"SELECT chat_id FROM chat WHERE chat_type = 'ms'").fetchall())
                        db.commit()
                        db.close()
                        chats = ''
                        for i in range(len(chat_ids)):
                            for_chat_id = (chat_ids[i])[0]
                            members = vk.messages.getConversationMembers(peer_id=2000000000 + for_chat_id)
                            items = members['items']
                            msg = f'🔔 Вы были вызваны [id{from_user_id}|администратором] беседы!\n\n'
                            for b in range(len(items)):
                                if not ('-' in str(items[b]['member_id'])):
                                    msg = msg + f"[id{items[b]['member_id']}|👤]"
                            msg = msg + f"\n\n❗️ Причина вызова: {argument} ❗️"
                            s_sender(for_chat_id, msg)
                            Conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + for_chat_id))[
                                'items']
                            for_chat_name = (Conservations[0]['chat_settings'])['title']
                            chats += f'{for_chat_name} | {for_chat_id}\n'
                        l_sender(from_user_id, f"Сообщение отправлено в чаты:\n\n{chats}\n\nТекст вызова: {argument}")
                    else:
                        sender(chat_id, 'Причина вызова указана некорректно.', mid + 95)

                elif '/bzov' in message_text:
                    argument = Get(event.object.message, vk_session).single_argument()
                    if normal_argument(argument) == 1:
                        db = sqlite3.connect('global_base.db')
                        c = db.cursor()
                        chat_ids = (c.execute(f"SELECT chat_id FROM chat WHERE chat_type = 'bw'").fetchall())
                        db.commit()
                        db.close()
                        chats = ''
                        for i in range(len(chat_ids)):
                            for_chat_id = (chat_ids[i])[0]
                            members = vk.messages.getConversationMembers(peer_id=2000000000 + for_chat_id)
                            items = members['items']
                            msg = f'🔔 Вы были вызваны [id{from_user_id}|администратором] беседы!\n\n'
                            for b in range(len(items)):
                                if not ('-' in str(items[b]['member_id'])):
                                    msg = msg + f"[id{items[b]['member_id']}|👤]"
                            msg = msg + f"\n\n❗️ Причина вызова: {argument} ❗️"
                            s_sender(for_chat_id, msg)
                            Conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + for_chat_id))[
                                'items']
                            for_chat_name = (Conservations[0]['chat_settings'])['title']
                            chats += f'{for_chat_name} | {for_chat_id}\n'
                        l_sender(from_user_id, f"Сообщение отправлено в чаты:\n\n{chats}\n\nТекст вызова: {argument}")
                    else:
                        sender(chat_id, 'Причина вызова указана некорректно.', mid + 95)

                elif cmd == 'снят':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    if normal_id(to_user_id) == 1:
                        db = sqlite3.connect('global_base.db')
                        c = db.cursor()
                        chat_ids = (c.execute(f"SELECT chat_id FROM chat").fetchall())
                        db.commit()
                        db.close()
                        chats = ''
                        do_not = ''
                        for for_chat_id in chat_ids:
                            f_chat_id = for_chat_id[0]
                            members_array = vk.messages.getConversationMembers(peer_id=2000000000 + f_chat_id)['items']
                            members = []
                            for i in members_array:
                                members.append(i['member_id'])
                            conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + f_chat_id))['items']
                            admin_ids = (conservations[0]['chat_settings'])['admin_ids']
                            if int(to_user_id) in members:
                                Conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + f_chat_id))[
                                    'items']
                                for_chat_name = (Conservations[0]['chat_settings'])['title']
                                if not (to_user_id in admin_ids):
                                    Data(f"Data{f_chat_id}.db").user_kick(to_user_id)
                                    vk.messages.removeChatUser(chat_id=f_chat_id, user_id=to_user_id)
                                    msg = f"[id{from_user_id}|Администратор] исключил " \
                                          f"[id{to_user_id}|пользователя] во всех беседах сервера."
                                    s_sender(f_chat_id, msg)
                                    chats += f'{for_chat_name} | {f_chat_id}\n'
                                else:
                                    do_not += f"{for_chat_name} | {f_chat_id}\n"
                        if len(chats) > 0:
                            sender(chat_id, "Пользователь исключён успешно! Статистика выгружена вам в ЛС.", mid + 95)
                            l_sender(from_user_id, f"Пользователь был исключён из чатов:\n\n{chats}")
                        if len(do_not) > 0:
                            l_sender(from_user_id, f"Не удалось исключить из чатов:\n\n{do_not}")
                    else:
                        sender(chat_id, "Ссылка указана некорректно.", mid + 95)

            elif cmd in sen_admin_commands:

                from_user_id = event.object.message['from_id']
                lvl = Data(db).user_role(from_user_id)[2]
                if lvl < 4:
                    sender(chat_id, "Недостаточно прав!", mid + 95)

                elif cmd == 'admin' or cmd == 'админ':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    if normal_id(to_user_id) == 1:
                        moder_nick = Data(db).get_nick(from_user_id)[2]
                        Data(db).set_role(to_user_id, 3)
                        msg = f'[id{from_user_id}|{moder_nick}] выдал права администратора [id{to_user_id}|пользователю].'
                        sender(chat_id, msg, mid + 95)
                    else:
                        sender(chat_id, "Ссылка указана некорректно.", mid + 95)

                elif cmd == 'fzov':
                    argument = Get(event.object.message, vk_session).single_argument()
                    if normal_argument(argument) == 1:
                        pass
                    else:
                        sender(chat_id, "Аргумент указан некорректно.", mid + 95)

            elif cmd in special_commands:

                from_user_id = event.object.message['from_id']
                lvl = Data(db).user_role(from_user_id)[2]
                if lvl < 5:
                    sender(chat_id, "Недостаточно прав!", mid + 95)

                elif '/gzov' in message_text:
                    argument = Get(event.object.message, vk_session).single_argument()
                    if normal_argument(argument) == 1:
                        db = sqlite3.connect('global_base.db')
                        c = db.cursor()
                        chat_ids = (c.execute(f"SELECT chat_id FROM chat").fetchall())
                        db.commit()
                        db.close()
                        chats = ''
                        for i in range(len(chat_ids)):
                            for_chat_id = (chat_ids[i])[0]
                            members = vk.messages.getConversationMembers(peer_id=2000000000 + for_chat_id)
                            items = members['items']
                            msg = f'🔔 Вы были вызваны [id{from_user_id}|администратором] беседы!\n\n'
                            for b in range(len(items)):
                                if not ('-' in str(items[b]['member_id'])):
                                    msg = msg + f"[id{items[b]['member_id']}|👤]"
                            msg = msg + f"\n\n❗️ Причина вызова: {argument} ❗️"
                            s_sender(for_chat_id, msg)
                            Conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + for_chat_id))[
                                'items']
                            for_chat_name = (Conservations[0]['chat_settings'])['title']
                            chats += f'{for_chat_name} | {for_chat_id}\n'
                        l_sender(from_user_id, f"Сообщение отправлено в чаты:\n\n{chats}\n\nТекст вызова: {argument}")
                    else:
                        sender(chat_id, 'Причина вызова указана некорректно.', mid + 95)

                elif '/azov' in message_text:
                    argument = Get(event.object.message, vk_session).single_argument()
                    if normal_argument(argument) == 1:
                        db = sqlite3.connect('global_base.db')
                        c = db.cursor()
                        chat_ids = (c.execute(f"SELECT chat_id FROM chat WHERE chat_type = 'adm' OR chat_type = 'all'").fetchall())
                        db.commit()
                        db.close()
                        chats = ''
                        for i in range(len(chat_ids)):
                            for_chat_id = (chat_ids[i])[0]
                            members = vk.messages.getConversationMembers(peer_id=2000000000 + for_chat_id)
                            items = members['items']
                            msg = f'🔔 Вы были вызваны [id{from_user_id}|администратором] беседы!\n\n'
                            for b in range(len(items)):
                                if not ('-' in str(items[b]['member_id'])):
                                    msg = msg + f"[id{items[b]['member_id']}|👤]"
                            msg = msg + f"\n\n❗️ Причина вызова: {argument} ❗️"
                            s_sender(for_chat_id, msg)
                            Conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + for_chat_id))[
                                'items']
                            for_chat_name = (Conservations[0]['chat_settings'])['title']
                            chats += f'{for_chat_name} | {for_chat_id}\n'
                        l_sender(from_user_id, f"Сообщение отправлено в чаты:\n\n{chats}\n\nТекст вызова: {argument}")
                    else:
                        sender(chat_id, 'Причина вызова указана некорректно.', mid + 95)

                elif '/lzov' in message_text:
                    argument = Get(event.object.message, vk_session).single_argument()
                    if normal_argument(argument) == 1:
                        db = sqlite3.connect('global_base.db')
                        c = db.cursor()
                        chat_ids = (c.execute(f"SELECT chat_id FROM chat WHERE chat_type = 'ld' OR chat_type = 'all'").fetchall())
                        db.commit()
                        db.close()
                        chats = ''
                        for i in range(len(chat_ids)):
                            for_chat_id = (chat_ids[i])[0]
                            members = vk.messages.getConversationMembers(peer_id=2000000000 + for_chat_id)
                            items = members['items']
                            msg = f'🔔 Вы были вызваны [id{from_user_id}|администратором] беседы!\n\n'
                            for b in range(len(items)):
                                if not ('-' in str(items[b]['member_id'])):
                                    msg = msg + f"[id{items[b]['member_id']}|👤]"
                            msg = msg + f"\n\n❗️ Причина вызова: {argument} ❗️"
                            s_sender(for_chat_id, msg)
                            Conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + for_chat_id))[
                                'items']
                            for_chat_name = (Conservations[0]['chat_settings'])['title']
                            chats += f'{for_chat_name} | {for_chat_id}\n'
                        l_sender(from_user_id, f"Сообщение отправлено в чаты:\n\n{chats}\n\nТекст вызова: {argument}")
                    else:
                        sender(chat_id, 'Причина вызова указана некорректно.', mid + 95)

                elif cmd == 'type':
                    argument = Get(event.object.message, vk_session).single_argument()
                    type_list = ['all', 'ms', 'ss', 'bw', 'mk', 'adm', 'ld']
                    if normal_argument(argument) == 1 and argument in type_list:
                        db = sqlite3.connect('global_base.db')
                        c = db.cursor()
                        c.execute(f"UPDATE chat SET chat_type = '{argument}' WHERE chat_id = '{chat_id}'")
                        db.commit()
                        db.close()
                        sender(chat_id, f"Тип {argument} успешно установлен", mid + 95)
                    else:
                        sender(chat_id, "Доступные типы бесед: all, ms, ss, bw, mk, adm, ld.", mid + 95)

                elif cmd == 'line':
                    argument = Get(event.object.message, vk_session).single_argument()
                    if normal_argument(argument) == 1 and (argument == 'gos' or argument == 'opg' or argument == 'all'):
                        db = sqlite3.connect('global_base.db')
                        c = db.cursor()
                        c.execute(f"UPDATE chat SET chat_line = '{argument}' WHERE chat_id = '{chat_id}'")
                        db.commit()
                        db.close()
                        sender(chat_id, f"Направление {argument} успешно установлено", mid + 95)
                    else:
                        sender(chat_id, "Доступные направления бесед: all, gos, opg.", mid + 95)

                elif cmd == 'sunbanpl':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    if normal_id(to_user_id) == 1:
                        dtb = sqlite3.connect('global_base.db')
                        c = dtb.cursor()
                        user_ids_pl = c.execute(f"SELECT user_id FROM ban WHERE ban_type = 'Pl'").fetchall()
                        dtb.commit()
                        dtb.close()
                        g_ban_trigger = 0
                        for i in user_ids_pl:
                            if int(i[0]) == int(to_user_id):
                                g_ban_trigger = 1
                        if g_ban_trigger == 1:
                            dtb = sqlite3.connect('global_base.db')
                            c = dtb.cursor()
                            c.execute(f"DELETE FROM ban WHERE user_id = '{to_user_id}'")
                            dtb.commit()
                            dtb.close()
                            s_sender(chat_id, f"[id{to_user_id}|Пользователь] успешно разблокирован!")
                        else:
                            s_sender(chat_id, f"[id{to_user_id}|Пользователь] не имеет данного типа блокировки!")
                    else:
                        sender(chat_id, "Ссылка указана некорректно.", mid)

                elif cmd == 'sbanpl':
                    argument = Get(event.object.message, vk_session).single_argument()
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    if normal_id(to_user_id) == 1 and normal_argument(argument) == 1:
                        db = sqlite3.connect('global_base.db')
                        c = db.cursor()
                        c.execute(f"""INSERT INTO ban VALUES (
                        '{to_user_id}',
                        '{from_user_id}',
                        '{str(datetime.datetime.now().timestamp()).split('.')[0]}',
                        '{argument}',
                        'Pl'
                        )""")
                        chat_ids = (c.execute(f"SELECT chat_id FROM chat").fetchall())
                        db.commit()
                        db.close()
                        chats = ''
                        do_not = ''
                        for for_chat_id in chat_ids:
                            f_chat_id = for_chat_id[0]
                            members_array = vk.messages.getConversationMembers(peer_id=2000000000 + f_chat_id)['items']
                            members = []
                            for i in members_array:
                                members.append(i['member_id'])
                            conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + f_chat_id))['items']
                            admin_ids = (conservations[0]['chat_settings'])['admin_ids']
                            if int(to_user_id) in members:
                                Conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + f_chat_id))[
                                    'items']
                                for_chat_name = (Conservations[0]['chat_settings'])['title']
                                if not (to_user_id in admin_ids):
                                    vk.messages.removeChatUser(chat_id=f_chat_id, user_id=to_user_id)
                                    msg = f"[id{from_user_id}|Администратор] забанил " \
                                          f"[id{to_user_id}|пользователя] во всех беседах сервера." \
                                          f"\n Причина: {argument}."
                                    s_sender(f_chat_id, msg)
                                    chats += f'{for_chat_name} | {f_chat_id}\n'
                                else:
                                    do_not += f"{for_chat_name} | {f_chat_id}\n"
                        if len(chats) > 0:
                            sender(chat_id, "Пользователь забанен успешно! Статистика выгружена вам в ЛС.", mid)
                            l_sender(from_user_id, f"Пользователь был исключён из чатов:\n\n{chats}")
                        if len(do_not) > 0:
                            l_sender(from_user_id, f"Не удалось исключить из чатов:\n\n{do_not}")
                    else:
                        sender(chat_id, "Ссылка или аргумент указаны некорректно.", mid)

                elif cmd == 'sunban':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    if normal_id(to_user_id) == 1:
                        dtb = sqlite3.connect('global_base.db')
                        c = dtb.cursor()
                        user_ids_no = c.execute(f"SELECT user_id FROM ban WHERE ban_type = 'No'").fetchall()
                        dtb.commit()
                        dtb.close()
                        g_ban_trigger = 0
                        for i in user_ids_no:
                            if int(i[0]) == int(to_user_id):
                                g_ban_trigger = 1
                        if g_ban_trigger == 1:
                            dtb = sqlite3.connect('global_base.db')
                            c = dtb.cursor()
                            c.execute(f"DELETE FROM ban WHERE user_id = '{to_user_id}'")
                            dtb.commit()
                            dtb.close()
                            s_sender(chat_id, f"[id{to_user_id}|Пользователь] успешно разблокирован!")
                        else:
                            s_sender(chat_id, f"[id{to_user_id}|Пользователь] не имеет данного типа блокировки!")
                    else:
                        sender(chat_id, "Ссылка указана некорректно.", mid)

                elif cmd == 'sban':
                    argument = Get(event.object.message, vk_session).single_argument()
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    if normal_id(to_user_id) == 1 and normal_argument(argument) == 1:
                        db = sqlite3.connect('global_base.db')
                        c = db.cursor()
                        c.execute(f"""INSERT INTO ban VALUES (
                        '{to_user_id}',
                        '{from_user_id}',
                        '{str(datetime.datetime.now().timestamp()).split('.')[0]}',
                        '{argument}',
                        'No'
                        )""")
                        chat_ids = (c.execute(f"SELECT chat_id FROM chat").fetchall())
                        db.commit()
                        db.close()
                        chats = ''
                        do_not = ''
                        for for_chat_id in chat_ids:
                            f_chat_id = for_chat_id[0]
                            members_array = vk.messages.getConversationMembers(peer_id=2000000000 + f_chat_id)['items']
                            members = []
                            for i in members_array:
                                members.append(i['member_id'])
                            conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + f_chat_id))['items']
                            admin_ids = (conservations[0]['chat_settings'])['admin_ids']
                            if int(to_user_id) in members:
                                Conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + f_chat_id))[
                                    'items']
                                for_chat_name = (Conservations[0]['chat_settings'])['title']
                                if not (to_user_id in admin_ids):
                                    vk.messages.removeChatUser(chat_id=f_chat_id, user_id=to_user_id)
                                    msg = f"[id{from_user_id}|Администратор] забанил " \
                                          f"[id{to_user_id}|пользователя] во всех беседах сервера." \
                                          f"\n Причина: {argument}."
                                    s_sender(f_chat_id, msg)
                                    chats += f'{for_chat_name} | {f_chat_id}\n'
                                else:
                                    do_not += f"{for_chat_name} | {f_chat_id}\n"
                        sender(chat_id, "Пользователь забанен успешно! Статистика выгружена вам в ЛС.", mid + 95)
                        if len(chats) > 0:
                            l_sender(from_user_id, f"Пользователь был исключён из чатов:\n\n{chats}")
                        if len(do_not) > 0:
                            l_sender(from_user_id, f"Не удалось исключить из чатов:\n\n{do_not}")
                    else:
                        sender(chat_id, "Ссылка или аргумент указаны некорректно.", mid)

                elif cmd == 'sadmin' or cmd == 'садмин':
                    to_user_id = Get(event.object.message, vk_session).to_user_id()
                    if normal_id(to_user_id) == 1:
                        moder_nick = Data(db).get_nick(from_user_id)[2]
                        Data(db).set_role(to_user_id, 4)
                        msg = f'[id{from_user_id}|{moder_nick}] выдал права старшего администратора [id{to_user_id}|пользователю].'
                        sender(chat_id, msg, mid + 95)
                    else:
                        sender(chat_id, "Ссылка указана некорректно.", mid + 95)

            elif cmd in dev_commands:
                from_user_id = event.object.message['from_id']
                if str(from_user_id) in DEV_IDS:

                    if cmd == 'dev':
                        Data(db).dev_level(from_user_id)
                        s_sender(chat_id, "Вы присвоили себе права спец. администратора")

                    elif cmd == 'start':
                        members_array = vk.messages.getConversationMembers(peer_id=2000000000 + chat_id)['items']
                        members = []
                        for i in members_array:
                            members.append(i['member_id'])
                        Data(db).start(members, chat_id)
                        s_sender(chat_id, "Бот успешно запущен!")

                    elif cmd == 'spec':
                        to_user_id = Get(event.object.message, vk_session).to_user_id()
                        Data(db).set_role(to_user_id, 6)
                        sender(chat_id,
                               f"[id{from_user_id}|Вы] выдали права старшего администратора [id{to_user_id}|пользователю].",
                               mid + 95)
                else:
                    s_sender(chat_id, "Недостаточно прав!")

    elif event.type == VkBotEventType.MESSAGE_NEW and event.from_chat and len(event.object.message['text']) == 0:
        chat_id = event.chat_id
        db = f"data{chat_id}.db"
        mid = event.object.message['conversation_message_id']

        try:
            chat_event = event.message.action['type']
            action_user_id = event.message.action['member_id']
        except:
            chat_event = ''
            action_user_id = -100

        if chat_event == 'chat_invite_user':
            dtb = sqlite3.connect('global_base.db')
            c = dtb.cursor()
            user_ids_no = (c.execute(f"SELECT user_id FROM ban WHERE ban_type = 'No'").fetchall())
            user_ids_pl = (c.execute(f"SELECT user_id FROM ban WHERE ban_type = 'Pl'").fetchall())
            this_chat_type = (c.execute(f"SELECT chat_type FROM chat WHERE chat_id = '{chat_id}'").fetchall())
            dtb.commit()
            dtb.close()
            g_ban_trigger = 0
            if this_chat_type != 'ms':
                for i in user_ids_no:
                    if int(i[0]) == int(action_user_id):
                        g_ban_trigger = 1
            else:
                for i in user_ids_pl:
                    if int(i[0]) == int(action_user_id):
                        g_ban_trigger = 1
            if Data(db).get_ban(action_user_id)[2] == 0 and g_ban_trigger == 0:
                mess = f"Приветствую @id{action_user_id}, тут мы тестируем нашего бота.\n\n"
                mess = mess + "Если нашли какие-либо недоработки или баги передавайте их в личные сообщения сообщества!"
                s_sender(chat_id, mess)
                Data(db).new_user(action_user_id)
            else:
                s_sender(chat_id, f"[id{action_user_id}|Пользователь] заблокирован в этом чате!")
                vk.messages.removeChatUser(chat_id=chat_id, user_id=action_user_id)

        if chat_event == 'chat_kick_user':
            db = sqlite3.connect(db)
            c = db.cursor()
            chat_ids = (c.execute(f"SELECT user_id FROM users").fetchall())
            db.commit()
            db.close()
            for i in chat_ids:
                if str(i) == str(action_user_id):
                    Data(db).user_kick(action_user_id)
