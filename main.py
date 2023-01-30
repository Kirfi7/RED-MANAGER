import sqlite3

import vk_api

from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from venv.AppData.config import TOKEN, DEV_IDS
from models import Get, Data

vk_session = vk_api.VkApi(token=TOKEN)
lp = VkBotLongPoll(vk_session, 218266206)
vk = vk_session.get_api()


def get_name(for_user_id):
    names = vk_session.method("users.get", {"user_ids": for_user_id})[0]
    return f"{names['first_name']} {names['last_name']}"


def get_all(user_id):
    return vk_session.method("users.get", {
        "user_ids": user_id,
        "fields": "last_seen, online, timezone, status"
    })


def delete(from_chat_id, cm):
    vk_session.method('messages.delete', {
        'peer_id': from_chat_id + 2000000000,
        'delete_for_all': 1,
        'cmids': cm,
        'random_id': 0
    })


def kick(from_chat_id, uid):
    vk_session.method("messages.removeChatUser", {
        'chat_id': from_chat_id,
        'user_id': uid
    })


def sender(from_chat_id, text):
    vk_session.method('messages.send', {
        'chat_id': from_chat_id,
        'message': text,
        'random_id': 0
    })


def l_sender(for_user_id, text):
    vk_session.method('messages.send', {
        'user_id': for_user_id,
        'message': text,
        'random_id': 0
    })


def role_inter(level):
    if level >= 5:
        return "Специальный Администратор"
    elif level == 4:
        return "Старший Администратор"
    elif level == 3:
        return "Администратор"
    elif level == 2:
        return "Старший Модератор"
    elif level == 1:
        return "Модератор"
    elif level == 0:
        return "Пользователь"
    else:
        return "Сообщество"


for event in lp.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        if event.from_chat:
            print(event)
            sm = event.object.message
            from_user_id = sm['from_id']
            chat_id = event.chat_id
            message_text = sm['text']
            cmds = event.object.message['conversation_message_id']
            db = f"data{chat_id}.db"
            gdb = "global_base.db"
            conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + chat_id))['items']
            chat_name = (conservations[0]['chat_settings'])['title']
            online_ids = (conservations[0]['chat_settings'])['active_ids']
            admin_ids = (conservations[0]['chat_settings'])['admin_ids']
            owner_id = (conservations[0]['chat_settings'])['owner_id']

            try:
                datab = sqlite3.connect('global_base.db')
                c = datab.cursor()
                from_chat_type = c.execute(f"SELECT chat_type WHERE chat_id = '{chat_id}'").fetchone()[0]
                datab.commit()
                datab.close()
            except:
                pass

            if '/start' in message_text:
                if str(from_user_id) in DEV_IDS:
                    members = vk.messages.getConversationMembers(peer_id=2000000000 + chat_id)
                    items = members['items']
                    all_user_ids = []
                    for b in range(len(items)):
                        all_user_ids.append(items[b]['member_id'])
                    if Data(db).start(all_user_ids, chat_id)[2] == 1:
                        sender(chat_id, 'Бот успешно запущен!')
                    else:
                        sender(chat_id, 'Произошла непредвиденная ошибка!')
                else:
                    sender(chat_id, 'Недостаточно прав!')

            elif not ('start' in message_text) and Data(db).is_muted(from_user_id)[2] == 1:
                delete(chat_id, cmds)

            elif '/type' in message_text:
                if str(from_user_id) in DEV_IDS:
                    argument = str(Get(sm, vk_session).single_argument())[1:]
                    db = sqlite3.connect('global_base.db')
                    c = db.cursor()
                    types_list = ['all', 'ms', 'ss', 'bw', 'mk', 'adm', 'ld']
                    if not (argument in types_list):
                        msg = 'Чтобы указать тип беседы введите:'
                        msg = msg + '\n/type ms — для беседы младшего состава.'
                        msg = msg + '\n/type ss — для беседы старшего состава.'
                        msg = msg + '\n/type bw — для любой беседы BW состава.'
                        msg = msg + '\n/type ld — для беседы лидерского состава.'
                        msg = msg + '\n/type mk — для беседы младших кураторов.'
                        msg = msg + '\n/type red — для беседы состава редакторов.'
                        msg = msg + '\n/type adm — для беседы состава администраторов.'
                        msg = msg + '\n/type all — для любой дополнительной беседы сервера.'
                    else:
                        c.execute(f"UPDATE chat SET chat_type = '{argument}' WHERE chat_id = '{chat_id}'")
                        db.commit()
                        db.close()
                        msg = f'Тип беседы успешно установлен!'
                    sender(chat_id, msg)
                else:
                    sender(chat_id, 'Недостаточно прав!')

            elif '/line' in message_text:
                if str(from_user_id) in DEV_IDS:
                    argument = str(Get(sm, vk_session).single_argument())[1:]
                    print(argument)
                    db = sqlite3.connect('global_base.db')
                    c = db.cursor()
                    lines_list = ['gos', 'opg', 'all']
                    if not (argument in lines_list):
                        msg = 'Чтобы указать напрвавление беседы введите:'
                        msg = msg + '\n/line gos — для беседы направления ГОСС.'
                        msg = msg + '\n/line opg — для беседы направления ОПГ.'
                        msg = msg + '\n/line all — беседа без привязки к направлению.'
                        db.commit()
                        db.close()
                    else:
                        c.execute(f"UPDATE chat SET chat_line = '{argument}' WHERE chat_id = '{chat_id}'")
                        db.commit()
                        db.close()
                        msg = f'Направление беседы успешно установлено!'
                    sender(chat_id, msg)
                else:
                    sender(chat_id, 'Недостаточно прав!')

            elif '/chat_info' in message_text:
                if Data(db).roles_access(from_user_id, from_user_id, 1, 5) == 1:
                    db = sqlite3.connect('global_base.db')
                    c = db.cursor()
                    result = c.execute(f"SELECT chat_line, chat_type FROM chat WHERE chat_id = '{chat_id}'")
                    result_2 = (result.fetchall())[0]
                    chat_line = result_2[0]
                    chat_type = result_2[1]
                    db.commit()
                    db.close()
                    sender(chat_id,
                           f'ID данной беседы: {chat_id}\nНаправление беседы: {chat_line}\nТип беседы: {chat_type}')
                else:
                    sender(chat_id, 'Недостаточно прав!')

            elif '/setnick' in message_text or '/snick' in message_text:
                argument = Get(sm, vk_session).single_argument()
                to_user_id = Get(sm, vk_session).to_user_id()
                if to_user_id == 'Error' or to_user_id == 'None' or '-' in str(to_user_id):
                    sender(chat_id, 'Ссылка на пользователя указана некорректно.')
                else:
                    if Data(db).roles_access(from_user_id, to_user_id, 1, 2) == 1:
                        Data(db).set_nick(argument, to_user_id)
                        sender(chat_id, f'Новый никнейм [id{to_user_id}|пользователя] — {argument}.')
                    else:
                        sender(chat_id, 'Недостаточно прав!')

            elif '/getnick' in message_text or '/gnick' in message_text:
                to_user_id = Get(sm, vk_session).to_user_id()
                if to_user_id == 'Error' or to_user_id == 'None' or '-' in str(to_user_id):
                    sender(chat_id, 'Ссылка на пользователя указана некорректно.')
                else:
                    if Data(db).roles_access(from_user_id, to_user_id, 1, 2) == 1:
                        msg = Data(db).get_nick(to_user_id)[2]
                        if msg == '' or msg == 'Error' or msg == 'Нет' or msg == 'None' or msg == get_name(to_user_id):
                            msg = f"У [id{to_user_id}|пользователя] не установлен никнейм."
                            sender(chat_id, msg)
                        else:
                            sender(chat_id, f'Никнейм [id{to_user_id}|пользователя] — {msg}.')
                    else:
                        sender(chat_id, 'Недостаточно прав!')

            elif '/removenick' in message_text or '/rnick' in message_text:
                to_user_id = Get(sm, vk_session).to_user_id()
                if to_user_id == 'Error' or to_user_id == 'None' or '-' in str(to_user_id):
                    sender(chat_id, 'Ссылка на пользователя указана некорректно.')
                else:
                    if Data(db).roles_access(from_user_id, to_user_id, 1, 2) == 1:
                        moder_nick = Data(db).get_nick(from_user_id)[2]
                        Data(db).rem_nick(to_user_id)
                        msg = f'[id{from_user_id}|{moder_nick}] удалил никнейм '
                        msg = msg + f'[id{to_user_id}|пользователю].'
                        sender(chat_id, msg)
                    else:
                        sender(chat_id, 'Недостаточно прав!')

            elif '/id' in message_text or '/getid' in message_text:
                to_user_id = Get(sm, vk_session).to_user_id()
                if to_user_id == 'Error' or to_user_id == 'None' or '-' in str(to_user_id):
                    sender(chat_id, 'Ссылка на пользователя указана некорректно.')
                else:
                    sender(chat_id, f'Оригинальная ссылка пользователя: https://vk.com/id{to_user_id}')

            elif '/kick' in message_text or '/кик' in message_text:
                to_user_id = Get(sm, vk_session).to_user_id()
                if to_user_id == 'Error' or to_user_id == 'None' or '-' in str(to_user_id):
                    sender(chat_id, 'Ссылка на пользователя указана некорректно.')
                else:
                    if Data(db).roles_access(from_user_id, to_user_id, 1, 0) == 1:
                        Data(db).user_kick(to_user_id)
                        vk_session.method("messages.removeChatUser", {
                            'chat_id': chat_id,
                            'user_id': to_user_id
                        })
                        sender(chat_id, f'[id{to_user_id}|Пользователь] исключён из чата.')
                    else:
                        sender(chat_id, 'Недостаточно прав!')

            elif '/removerole' in message_text or '/минусроль' in message_text:
                to_user_id = Get(sm, vk_session).to_user_id()
                if to_user_id == 'Error' or to_user_id == 'None' or '-' in str(to_user_id):
                    sender(chat_id, 'Ссылка на пользователя указана некорректно.')
                else:
                    if Data(db).roles_access(from_user_id, to_user_id, 1, 0) == 1:
                        moder_nick = Data(db).get_nick(from_user_id)[2]
                        if to_user_id == '':
                            sender(chat_id, 'Ссылка на пользователя указана некорректно.')
                        else:
                            Data(db).set_role(to_user_id, 0)
                            msg = f'[id{from_user_id}|{moder_nick}] снял все права'
                            msg = msg + f' [id{to_user_id}|пользователю].'
                            sender(chat_id, msg)
                    else:
                        sender(chat_id, 'Недостаточно прав!')

            elif '/addmoder' in message_text or '/модер' in message_text:
                to_user_id = Get(sm, vk_session).to_user_id()
                if to_user_id == 'Error' or to_user_id == 'None' or '-' in str(to_user_id):
                    sender(chat_id, 'Ссылка на пользователя указана некорректно.')
                else:
                    if Data(db).roles_access(from_user_id, to_user_id, 2, 0) == 1:
                        moder_nick = Data(db).get_nick(from_user_id)[2]
                        Data(db).set_role(to_user_id, 1)
                        msg = f'[id{from_user_id}|{moder_nick}] выдал права модератора'
                        msg = msg + f' [id{to_user_id}|пользователю].'
                        sender(chat_id, msg)
                    else:
                        sender(chat_id, 'Недостаточно прав!')

            elif '/addsmoder' in message_text or '/смодер' in message_text:
                to_user_id = Get(sm, vk_session).to_user_id()
                if to_user_id == 'Error' or to_user_id == 'None' or '-' in str(to_user_id):
                    sender(chat_id, 'Ссылка на пользователя указана некорректно.')
                else:
                    if Data(db).roles_access(from_user_id, to_user_id, 3, 0) == 1:
                        moder_nick = Data(db).get_nick(from_user_id)[2]
                        Data(db).set_role(to_user_id, 2)
                        msg = f'[id{from_user_id}|{moder_nick}] выдал права старшего модератора'
                        msg = msg + f' [id{to_user_id}|пользователю].'
                        sender(chat_id, msg)
                    else:
                        sender(chat_id, 'Недостаточно прав!')

            elif '/addadmin' in message_text or '/админ' in message_text:
                to_user_id = Get(sm, vk_session).to_user_id()
                if to_user_id == 'Error' or to_user_id == 'None' or '-' in str(to_user_id):
                    sender(chat_id, 'Ссылка на пользователя указана некорректно.')
                else:
                    if Data(db).roles_access(from_user_id, to_user_id, 4, 0) == 1:
                        moder_nick = Data(db).get_nick(from_user_id)[2]
                        Data(db).set_role(to_user_id, 3)
                        msg = f'[id{from_user_id}|{moder_nick}] выдал права администратора'
                        msg = msg + f' [id{to_user_id}|пользователю].'
                        sender(chat_id, msg)
                    else:
                        sender(chat_id, 'Недостаточно прав!')

            elif '/addsadmin' in message_text or '/садмин' in message_text:
                to_user_id = Get(sm, vk_session).to_user_id()
                if to_user_id == 'Error' or to_user_id == 'None' or '-' in str(to_user_id):
                    sender(chat_id, 'Ссылка на пользователя указана некорректно.')
                else:
                    if Data(db).roles_access(from_user_id, to_user_id, 5, 0) == 1:
                        moder_nick = Data(db).get_nick(from_user_id)[2]
                        Data(db).set_role(to_user_id, 4)
                        msg = f'[id{from_user_id}|{moder_nick}] выдал права старшего администратора'
                        msg = msg + f' [id{to_user_id}|пользователю].'
                        sender(chat_id, msg)
                    else:
                        sender(chat_id, 'Недостаточно прав!')

            elif '/addspec' in message_text:
                to_user_id = Get(sm, vk_session).to_user_id()
                if to_user_id == 'Error' or to_user_id == 'None' or '-' in str(to_user_id):
                    sender(chat_id, 'Ссылка на пользователя указана некорректно.')
                else:
                    if str(from_user_id) in DEV_IDS:
                        moder_nick = Data(db).get_nick(from_user_id)[2]
                        Data(db).set_role(to_user_id, 5)
                        msg = f'[id{from_user_id}|{moder_nick}] выдал права специального администратора'
                        msg = msg + f' [id{to_user_id}|пользователю].'
                        sender(chat_id, msg)
                    else:
                        sender(chat_id, 'Недостаточно прав!')

            elif '/warnhistory' in message_text or '/getwarn' in message_text:
                to_user_id = Get(sm, vk_session).to_user_id()
                if to_user_id == 'Error' or to_user_id == 'None' or '-' in str(to_user_id):
                    sender(chat_id, 'Ссылка на пользователя указана некорректно.')
                else:
                    if Data(db).roles_access(from_user_id, to_user_id, 1, 1) == 1:
                        warns = Data(db).get_warns(to_user_id)[2]
                        sender(chat_id, Data(db).warn_history(to_user_id, warns)[2])
                    else:
                        sender(chat_id, 'Недостаточно прав!')

            elif '/warn' in message_text or '/варн' in message_text:
                to_user_id = Get(sm, vk_session).to_user_id()
                argument = Get(sm, vk_session).single_argument()
                if to_user_id == 'Error' or to_user_id == 'None' or '-' in str(to_user_id):
                    sender(chat_id, 'Ссылка на пользователя указана некорректно.')
                else:
                    if Data(db).roles_access(from_user_id, to_user_id, 1, 0) == 1:
                        moder_nick = Data(db).get_nick(from_user_id)[2]
                        result = Data(db).add_warn(to_user_id, from_user_id, argument)
                        msg = f'[id{from_user_id}|{moder_nick}] выдал предупреждение [id{to_user_id}|пользователю].'
                        msg = msg + f"\nТекущее количество варнов пользователя: {result[2]}."
                        if result[3] == 1:
                            Data(db).user_kick(to_user_id)
                            vk_session.method("messages.removeChatUser", {
                                'chat_id': chat_id,
                                'user_id': to_user_id
                            })
                            sender(chat_id, f'[id{to_user_id}|Пользователь] заблокирован (получено 3 предупреждения).')
                        else:
                            sender(chat_id, msg)
                    else:
                        sender(chat_id, 'Недостаточно прав!')

            elif '/unwarn' in message_text:
                to_user_id = Get(sm, vk_session).to_user_id()
                if to_user_id == 'Error' or to_user_id == 'None' or '-' in str(to_user_id):
                    sender(chat_id, 'Ссылка на пользователя указана некорректно.')
                else:
                    if Data(db).roles_access(from_user_id, to_user_id, 1, 0) == 1:
                        moder_nick = Data(db).get_nick(from_user_id)[2]
                        warns = Data(db).get_warns(to_user_id)[2]
                        if warns == 0:
                            sender(chat_id, f'У [id{to_user_id}|пользователя] нет активных предупреждений!')
                        else:
                            Data(db).del_warn(to_user_id)
                            warns = Data(db).get_warns(to_user_id)[2]
                            msg = f'[id{from_user_id}|{moder_nick}] снял предупреждение [id{to_user_id}|пользователю].'
                            msg = msg + f"\nТекущее количество предупреждений пользователя: {warns}."
                            sender(chat_id, msg)
                    else:
                        sender(chat_id, 'Недостаточно прав!')

            elif '/role' in message_text or '/роль' in message_text:
                to_user_id = Get(sm, vk_session).to_user_id()
                if to_user_id == 'Error' or to_user_id == 'None' or '-' in str(to_user_id):
                    sender(chat_id, 'Ссылка на пользователя указана некорректно.')
                else:
                    if to_user_id == from_user_id:
                        msg = f"Ваша роль в беседе: {role_inter(Data(db).get_role(to_user_id))}"
                    else:
                        msg = f"Роль [id{to_user_id}|пользователя] в беседе: {role_inter(Data(db).get_role(to_user_id))}"
                    sender(chat_id, msg)

            elif '/staff' in message_text or '/стафф' in message_text:
                if Data(db).get_role(from_user_id) >= 1:
                    sender(chat_id, Data(db).staff()[2])
                else:
                    sender(chat_id, 'Недостаточно прав!')

            elif '/zov' in message_text or '/зов' in message_text:
                if Data(db).get_role(from_user_id) >= 2:
                    argument = Get(sm, vk_session).single_argument()
                    if argument == 'Error' or argument == 'None' or argument == '':
                        sender(chat_id, 'Причина вызова указана некорректно.')
                    else:
                        members = vk.messages.getConversationMembers(peer_id=2000000000 + chat_id)
                        items = members['items']
                        msg = f'🔔 Вы были вызваны [id{from_user_id}|администратором] беседы!\n\n'
                        for b in range(len(items)):
                            if not ('-' in str(items[b]['member_id'])):
                                msg = msg + f"[id{items[b]['member_id']}|👤]"
                        msg = msg + f"\n\n❗️ Причина вызова: {argument} ❗️"
                        sender(chat_id, msg)
                else:
                    sender(chat_id, 'Недостаточно прав!')

            elif '/gzov' in message_text:
                if Data(db).get_role(from_user_id) >= 5:
                    argument = Get(sm, vk_session).single_argument()
                    if argument == 'Error' or argument == 'None' or argument == '':
                        sender(chat_id, 'Причина вызова указана некорректно.')
                    else:
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
                            sender(for_chat_id, msg)
                            Conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + for_chat_id))[
                                'items']
                            for_chat_name = (Conservations[0]['chat_settings'])['title']
                            chats += f'{for_chat_name} | {for_chat_id}\n'
                        l_sender(from_user_id, f"Сообщение отправлено в чаты:\n\n{chats}\n\nТекст вызова: {argument}")
                else:
                    sender(chat_id, 'Недостаточно прав!')

            elif '/sszov' in message_text:
                if Data(db).get_role(from_user_id) >= 5:
                    argument = Get(sm, vk_session).single_argument()
                    if argument == 'Error' or argument == 'None' or argument == '':
                        sender(chat_id, 'Причина вызова указана некорректно.')
                    else:
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
                            sender(for_chat_id, msg)
                            Conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + for_chat_id))[
                                'items']
                            for_chat_name = (Conservations[0]['chat_settings'])['title']
                            chats += f'{for_chat_name} | {for_chat_id}\n'
                        l_sender(from_user_id, f"Сообщение отправлено в чаты:\n\n{chats}\n\nТекст вызова: {argument}")
                else:
                    sender(chat_id, 'Недостаточно прав!')

            elif '/mszov' in message_text:
                if Data(db).get_role(from_user_id) >= 5:
                    argument = Get(sm, vk_session).single_argument()
                    if argument == 'Error' or argument == 'None' or argument == '':
                        sender(chat_id, 'Причина вызова указана некорректно.')
                    else:
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
                            sender(for_chat_id, msg)
                            Conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + for_chat_id))[
                                'items']
                            for_chat_name = (Conservations[0]['chat_settings'])['title']
                            chats += f'{for_chat_name} | {for_chat_id}\n'
                        l_sender(from_user_id, f"Сообщение отправлено в чаты:\n\n{chats}\n\nТекст вызова: {argument}")
                else:
                    sender(chat_id, 'Недостаточно прав!')

            elif '/lzov' in message_text:
                if Data(db).get_role(from_user_id) >= 5:
                    argument = Get(sm, vk_session).single_argument()
                    if argument == 'Error' or argument == 'None' or argument == '':
                        sender(chat_id, 'Причина вызова указана некорректно.')
                    else:
                        db = sqlite3.connect('global_base.db')
                        c = db.cursor()
                        chat_ids = (c.execute(f"SELECT chat_id FROM chat WHERE chat_type = 'ld'").fetchall())
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
                            sender(for_chat_id, msg)
                            Conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + for_chat_id))[
                                'items']
                            for_chat_name = (Conservations[0]['chat_settings'])['title']
                            chats += f'{for_chat_name} | {for_chat_id}\n'
                        l_sender(from_user_id, f"Сообщение отправлено в чаты:\n\n{chats}\n\nТекст вызова: {argument}")
                else:
                    sender(chat_id, 'Недостаточно прав!')

            elif '/bzov' in message_text:
                if Data(db).get_role(from_user_id) >= 5:
                    argument = Get(sm, vk_session).single_argument()
                    if argument == 'Error' or argument == 'None' or argument == '':
                        sender(chat_id, 'Причина вызова указана некорректно.')
                    else:
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
                            sender(for_chat_id, msg)
                            Conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + for_chat_id))[
                                'items']
                            for_chat_name = (Conservations[0]['chat_settings'])['title']
                            chats += f'{for_chat_name} | {for_chat_id}\n'
                        l_sender(from_user_id, f"Сообщение отправлено в чаты:\n\n{chats}\n\nТекст вызова: {argument}")
                else:
                    sender(chat_id, 'Недостаточно прав!')

            elif '/fzov' in message_text:
                if Data(db).get_role(from_user_id) >= 5:
                    argument = Get(sm, vk_session).single_argument()
                    if argument == 'Error' or argument == 'None' or argument == '':
                        sender(chat_id, 'Причина вызова указана некорректно.')
                    else:
                        db = sqlite3.connect('global_base.db')
                        c = db.cursor()
                        chat_ids = (c.execute(
                            f"SELECT chat_id FROM chat WHERE chat_line = 'gos' OR chat_line = 'opg'").fetchall())
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
                            sender(for_chat_id, msg)
                            Conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + for_chat_id))[
                                'items']
                            for_chat_name = (Conservations[0]['chat_settings'])['title']
                            chats += f'{for_chat_name} | {for_chat_id}\n'
                        l_sender(from_user_id, f"Сообщение отправлено в чаты:\n\n{chats}\n\nТекст вызова: {argument}")
                else:
                    sender(chat_id, 'Недостаточно прав!')

            elif '/azov' in message_text:
                if Data(db).get_role(from_user_id) >= 5:
                    argument = Get(sm, vk_session).single_argument()
                    if argument == 'Error' or argument == 'None' or argument == '':
                        sender(chat_id, 'Причина вызова указана некорректно.')
                    else:
                        db = sqlite3.connect('global_base.db')
                        c = db.cursor()
                        chat_ids = (c.execute(f"SELECT chat_id FROM chat WHERE chat_type = 'adm'").fetchall())
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
                            sender(for_chat_id, msg)
                            Conservations = (vk.messages.getConversationsById(peer_ids=2000000000 + for_chat_id))[
                                'items']
                            for_chat_name = (Conservations[0]['chat_settings'])['title']
                            chats += f'{for_chat_name} | {for_chat_id}\n'
                        l_sender(from_user_id, f"Сообщение отправлено в чаты:\n\n{chats}\n\nТекст вызова: {argument}")
                else:
                    sender(chat_id, 'Недостаточно прав!')

            elif '/stats' in message_text:
                to_user_id = Get(sm, vk_session).to_user_id()
                if to_user_id == 'Error' or to_user_id == 'None' or '-' in str(to_user_id):
                    sender(chat_id, 'Ссылка на пользователя указана некорректно.')
                else:
                    if Data(db).roles_access(from_user_id, to_user_id, 0, 2) == 1:
                        closed = 'Открытый' if str(get_all(to_user_id)[0]['is_closed']) == 'False' else 'Закрытый'
                        is_admin = 'Да' if int(to_user_id) in admin_ids else 'Нет'
                        is_owner = 'Да' if int(to_user_id) == owner_id else 'Нет'
                        msg = f"Информация о [id{to_user_id}|пользователе]\n\nОбщая информация:\n"
                        status = get_all(to_user_id)[0]['status']
                        nick = Data(db).get_nick(to_user_id)[2]
                        invited_name = invited_by = ''
                        m_count = 0
                        muted = 'Есть' if Data(db).is_muted(to_user_id)[2] == 1 else 'Нет'
                        if nick == '' or nick == 'Error' or nick == 'Нет' or nick == 'None' or nick == get_name(to_user_id):
                            nick = f"Отсутствует"
                        for i in range(vk.messages.getConversationMembers(peer_id=2000000000 + chat_id)['count']):
                            if (vk.messages.getConversationMembers(peer_id=2000000000 + chat_id)['items'])[i]['member_id'] == to_user_id:
                                invited_name = get_name((vk.messages.getConversationMembers(peer_id=2000000000 + chat_id)['items'])[i]['invited_by'])
                                invited_by = (vk.messages.getConversationMembers(peer_id=2000000000 + chat_id)['items'])[i]['invited_by']
                                m_count = (vk.messages.getConversationMembers(peer_id=2000000000 + chat_id)['items'])[i]['invited_by']
                        msg = msg + f"Имя пользователя: {get_name(to_user_id)}\n" \
                                    f"Никнейм: {nick}\n" \
                                    f"Статус профиля: {closed}\n" \
                                    f"Статус пользователя: «{status}»\n" \
                                    f"\nПользователь в беседе:\n" \
                                    f"Админка в беседе: {is_admin}\n" \
                                    f"Владелец беседы: {is_owner}\n" \
                                    f"Роль: {role_inter(Data(db).get_role(to_user_id))}\n" \
                                    f"Кем приглашён: [id{invited_by}|{invited_name}]\n" \
                                    f"\nНаказания в беседе:\n" \
                                    f"Имеется ли блокировка чата: {muted}\n" \
                                    f"Количество предупреждений: {Data(db).get_warns(to_user_id)[2]}/3"
                        sender(chat_id, msg)
                    else:
                        sender(chat_id, 'Недостаточно прав!')

            elif '/getacc' in message_text:
                msg = Get(sm, vk_session).single_argument()
                user_id = Data(db).get_acc(msg)[2]
                if user_id == 'Error' or user_id == 'None':
                    sender(chat_id, 'Нет такого пользователя.')
                else:
                    if Data(db).roles_access(from_user_id, from_user_id, 1, 2) == 1:
                        sender(chat_id, f'Ссылка на ВКонтакте пользователя: https://vk.com/id{user_id}.')
                    else:
                        sender(chat_id, 'Недостаточно прав!')

            elif '/nlist' in message_text or '/nicklist' in message_text:
                if Data(db).roles_access(from_user_id, from_user_id, 1, 2) == 1:
                    msg = Data(db).nick_list()[2]
                    sender(chat_id, msg)
                else:
                    sender(chat_id, 'Недостаточно прав!')

            try:
                chat_event = event.message.action['type']
                action_user_id = event.message.action['member_id']
            except:
                chat_event = ''
                action_user_id = -100

            if chat_event == 'chat_invite_user':
                # if Data(db).get_ban == 0 and Data(db).get_global_ban == 0:
                mess = f"Приветствую @id{action_user_id}, тут мы тестируем нашего бота.\n\n"
                mess = mess + "Если нашли какие-либо недоработки или баги передавайте их в личные сообщения сообщества!"
                sender(chat_id, mess)
                Data(db).new_user(action_user_id)
                # else:
                #    kick(chat_id, action_user_id)
                #    sender(chat_id, f"[id{action_user_id}|пользователь] заблокирован в этой беседе.")

            if chat_event == 'chat_kick_user':
                db = sqlite3.connect(db)
                c = db.cursor()
                chat_ids = (c.execute(f"SELECT user_id FROM users").fetchall())
                db.commit()
                db.close()
                for i in range(len(chat_ids)):
                    for_chat_id = (chat_ids[i])[0]
                    if str(for_chat_id) == str(action_user_id):
                        Data(db).user_kick(action_user_id)
