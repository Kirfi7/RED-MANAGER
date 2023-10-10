import re

import config
from vk_functions import *
from data_functions import *


def get_to_id(message):
    if message.fwd_messages:
        return int(message.fwd_messages[0]['from_id'])
    if "reply_message" in message:
        return int(message.reply_message['from_id'])

    try:
        text = message['text'].split()[1]
    except IndexError:
        return 0

    if "vk.com" in text:
        mention = text.split('/')[-1]
        if not re.match(r'id\d*', mention):
            screen = session.method("utils.resolveScreenName", {"screen_name": mention})
            return screen['object_id'] if screen else 0
        return int(mention[2:])

    to_id = re.search(r'id\d*', text)
    if to_id:
        return int(to_id.group()[2:])
    return 0


def get_arg(message):
    if "reply_message" in message or message.fwd_messages:
        x = 1
    else:
        x = 2
    array = message.text.split()
    if len(array) < x:
        return None
    return " ".join(array[x:])


def get_role(chat_id, user_id):
    if user_id in config.DEV: return 5
    response = get_level(chat_id, user_id)
    if response: return int(response[0])
    return 0


def get_name(chat_id, user_id, to=None):
    response = get_nick(chat_id, user_id)
    if response:
        return response[0]
    request = {"user_ids": user_id}
    if to:
        request["name_case"] = to
    data = session.method("users.get", request)[0]
    return data["first_name"] + " " + data["last_name"]


def tag(chat_id, user_id, to=None):
    name = get_name(chat_id, user_id, to)
    return f"@id{user_id} ({name})"


def remove_user(chat_id, user_id):
    try:
        kick_member(chat_id, user_id)
        del_nick(chat_id, user_id)
        del_admin(chat_id, user_id)
        return 1
    except:
        return 0


def invited_user(chat_id, user_id):
    is_banned = get_ban(chat_id, user_id)
    is_gbanned = global_getban(user_id)
    chat_type = get_chat_type(chat_id)

    if is_banned:
        kick_member(chat_id, user_id)
        return send(chat_id, f"@id{user_id} (Пользователь) заблокирован в этом чате.")

    if is_gbanned:
        if not ("МС" in chat_type and is_gbanned[-1] != "Pl"):
            kick_member(chat_id, user_id)
            return send(chat_id, f"@id{user_id} (Пользователь) заблокирован в этом чате.")

    greeting = get_greeting(chat_id)
    if greeting != "None":
        greet_text = f"Здравствуйте, {tag(chat_id, user_id)}!\n\n{greeting}"
        send(chat_id, greet_text)
