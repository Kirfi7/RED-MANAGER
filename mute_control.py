import time

from data_functions import all_mutes, del_mute_by_end, get_chats_list, get_mute, add_mute, del_mute
from vk_functions import send, del_messages
from functions import tag


def mute(chat_id, user_id, admin_id, argument, msg_id):
    if get_mute(chat_id, user_id):
        return send(chat_id, f"У [id{user_id}|пользователя] уже есть блокировка чата!", msg_id)
    try:
        minutes = int(argument.split()[0])

        if minutes >= 1440:
            return send(chat_id, "Нельзя выдать мут более, чем на 1440 минут!", msg_id)

        end = add_mute(chat_id, user_id, minutes)
        send(chat_id, f"{tag(chat_id, admin_id)} выдал мут {tag(chat_id, user_id, 'dat')}\nВремя окончания мута: "
                      f"{time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(end))}", msg_id)
    except ValueError:
        send(chat_id, "Неверно указано время мута!", msg_id)


def unmute(chat_id, user_id, admin_id, msg_id):
    if not get_mute(chat_id, user_id):
        return send(chat_id, f"У [id{user_id}|пользователя] нет блокировки чата!", msg_id)
    send(chat_id, f"{tag(chat_id, admin_id)} снял мут {tag(chat_id, user_id, 'dat')}", msg_id)
    del_mute(chat_id, user_id)


def mute_check(chat_id, user_id, msg_id):
    try:
        is_muted = get_mute(chat_id, user_id)
        if is_muted > int(time.time()):
            del_messages(chat_id, [msg_id])
            return 1
        return 0
    except:
        return 0


def mutes_checker():
    chats = get_chats_list()

    for chat in chats:
        mutes = all_mutes(chat)

        for end in mutes:
            secs = int(time.time())

            if int(end[0]) <= secs:
                del_mute_by_end(chat, end[0])


def mute_control():
    while True:

        try:
            mutes_checker()
            time.sleep(15)

        except:
            pass
