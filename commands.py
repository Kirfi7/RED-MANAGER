import config
from functions import *
from config import *


def chat_start(chat_id, chat_owner, msg_id):
    if chat_id in get_chats_list():
        send(chat_id, "Беседа уже зарегистрирована!", msg_id)
    else:
        start(chat_id, chat_owner)
        insert_chat(chat_id)
        send(chat_id, "Беседа успешно зарегистрирована!", msg_id)


def set_role(chat_id_, user_id, level, msg_id, admin_id, argument):
    if argument:
        chats = get_chats_by_type(argument)
        msg = {}
    else:
        chats = [chat_id_]
        msg = {"reply": msg_id}

    if level == 0:
        send(chat_id_, f"{tag(chat_id_, admin_id)} снял(-а) все права {tag(chat_id_, user_id, 'dat')}", **msg)

    for chat_id in chats:
        if level == 0:
            del_admin(chat_id, user_id)
            continue

        elif level == 1: text = "модератора"
        elif level == 2: text = "администратора"
        elif level == 3: text = "старшего администратора"
        else: text = "руководителя сервера"

        add_admin(chat_id, user_id, level)
        send(chat_id, f"{tag(chat_id, admin_id)} выдал(-а) права {text} {tag(chat_id, user_id, 'dat')}", **msg)


def stats(chat_id, user_id):
    name = session.method("users.get", {"user_ids": user_id})[0]
    nick = get_nick(chat_id, user_id)
    return f"Информация о [id{user_id}|пользователе]\n" \
           f"Имя: {name['first_name']} {name['last_name']}\n" \
           f"Никнейм: {'Отсутствует' if not nick else nick[0]}\n" \
           f"Роль в беседе: {roles[get_role(chat_id, user_id)]}\n" \
           f"Активные предупреждения: {warns_count(chat_id, user_id)}\n" \
           f"Блокировка чата: {'Нет' if not get_mute(chat_id, user_id) else 'Есть'}\n" \
           f"Постоянная ссылка: https://vk.com/id{user_id}"


def get_help(user_id, level):
    with open("texts/help_text.txt", encoding='utf-8') as file:
        array = file.read().splitlines()

    if user_id in config.DEV: level = 5
    text = ""

    for line in array:
        if line not in ['0', '1', '2', '3', '4']:
            text += f"{line}\n"
        if line == str(level):
            break
    return text


def warn(chat_id, user_id, msg_id, reason, admin_id):
    warns = warns_count(chat_id, user_id)

    if len(reason) > 32:
        return send(chat_id, "Длина причины не может быть больше 32 символов!", msg_id)

    if warns == 2:
        del_warn(chat_id, user_id, admin_id)
        del_warn(chat_id, user_id, admin_id)
        add_ban(chat_id, user_id, admin_id, "3/3 предупреждения")
        remove_user(chat_id, user_id)
        send(chat_id, f"@id{user_id} (Пользователь) заблокирован за 3/3 предупреждения", msg_id)
    else:
        add_warn(chat_id, user_id, reason, admin_id)
        send(chat_id, f"{tag(chat_id, admin_id)} выдал(-а) предупреждение {tag(chat_id, user_id, 'dat')}"
                      f"\nКоличество активных предупреждений: {warns + 1}", msg_id)


def getwarn(chat_id, user_id, msg_id):
    warns = warns_count(chat_id, user_id)
    send(chat_id, f"Количество активных предупреждений: {warns}", msg_id)


def unwarn(chat_id, user_id, msg_id, admin_id):
    warns = warns_count(chat_id, user_id)
    if warns > 0:
        del_warn(chat_id, user_id, admin_id)
        send(chat_id, f"{tag(chat_id, admin_id)} снял(-а) предупреждение {tag(chat_id, user_id, 'dat')}"
                      f"\nКоличество активных предупреждений: {warns - 1}", msg_id)
    else:
        send(chat_id, "У пользователя нет активных предупреждений!", msg_id)


def set_nick_name(chat_id, user_id, admin_id, argument, msg_id):
    if len(argument) <= 32:
        send(chat_id, f"{tag(chat_id, admin_id)} изменил(-а) никнейм {tag(chat_id, user_id, 'dat')}\n"
                      f"Новый никнейм: {argument}", msg_id)
        set_nick(chat_id, user_id, argument)
    else:
        send(chat_id, "Длина никнейма не может быть больше 32 символов!", msg_id)


def set_global_name(chat_id, user_id, admin_id, argument, msg_id):
    array = argument.split()
    if len(array) != 2:
        send(chat_id, "Некорректно указан ник или тип бесед!", msg_id)

    nick_name, chat_type = array
    chats = get_chats_by_type(" ".join(chat_type.split('_')))

    if len(nick_name) <= 32:
        for chat in chats:
            send(chat, f"{tag(chat, admin_id)} изменил(-а) никнейм {tag(chat, user_id, 'dat')}\n"
                       f"Новый никнейм: {nick_name}")
            set_nick(chat, user_id, nick_name)
    else:
        send(chat_id, "Длина никнейма не может быть больше 32 символов!", msg_id)


def del_nick_name(chat_id, user_id, admin_id, msg_id):
    old_nick = get_nick(chat_id, user_id)
    if old_nick:
        del_nick(chat_id, user_id)
        send(chat_id, f"{tag(chat_id, admin_id)} удалил(-а) никнейм {tag(chat_id, user_id, 'dat')}\n"
                      f"Старый никнейм: {old_nick[0]}", msg_id)
    else:
        send(chat_id, f"У [id{user_id}|пользователя] не установлен никнейм!", msg_id)


def nick_list(chat_id, msg_id):
    array = sorted(all_nicks(chat_id), key=lambda el: el[1], reverse=True)

    if not array:
        return send(chat_id, "Нет участников с установленными никнеймами!", msg_id)

    pages, data, c = 1, {}, 0
    data[pages] = ""

    for user, nick in array:
        c += 1
        data[pages] += f"\n{c}) @id{user} ({nick})"

        if len(data[pages]) > 3600:
            pages += 1
            data[pages], c = "", 0

    send(chat_id, f"Список пользователей с никами:{data[1]}", msg_id)
    if pages > 1:
        for page in range(2, pages + 1):
            if not data[pages]:
                break
            send(chat_id, data[page])


def no_nick_list(chat_id, msg_id):
    nicks = set(map(lambda a: a[0] if a else set(), all_nicks(chat_id)))
    users = set(map(lambda a: a['member_id'], get_users(chat_id)))

    pages, data, c = 1, {}, 0
    data[pages] = ""

    for user in users:
        if user in nicks or "-" in str(user):
            continue

        c += 1
        data[pages] += f"\n{c}) {tag(chat_id, user)}"

        if len(data[pages]) > 3600:
            pages += 1
            data[pages], c = "", 0

    send(chat_id, f"Список пользователей без ников:{data[1]}", msg_id)
    if pages > 1:
        for page in range(2, pages + 1):
            if not data[pages]:
                break
            send(chat_id, data[page])


def online_list(chat_id, msg_id):
    array = get_online(chat_id)
    message = "Список пользователей в сети:\n"
    for user in array:
        message += f"— {tag(chat_id, user)}\n"
    send(chat_id, message, msg_id)


def staff_list(chat_id, msg_id):
    admins = get_admins(chat_id)

    text = ("Главный администратор:\n[id468509613|Kirfi_Marciano]\n\n"
            "Зам. главного администратора:\n[id16715256|Prokhor_Adzinets]\n[id534422651|Mikhail_Pearson]\n\n"
            "Кураторы администрации:\n[id345814069|Kostya_Vagner]\n[id799543560|Shark_Nightmare]\n")
    for key in admins:
        text += f"\n{key}\n"

        for admin in admins[key]:
            if not admin:
                continue
            text += f"{tag(chat_id, admin[0])}\n"

    send(chat_id, text, msg_id)


def get_user_bans(chat_id, user_id, msg_id):
    global_array = global_getban(user_id)
    local_array = get_ban(chat_id, user_id)

    msg = f"Информация о блокировках [id{user_id}|пользователя]\n"
    if not global_array:
        g_text = "—"
    else:
        user, admin, date, reason, btype = global_array[0]
        g_text = f"\n{reason} | {btype} | [id{admin}|Админ] | {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(date))}"

    if not local_array:
        l_text = "—"
    else:
        user, admin, date, reason = local_array[0]
        l_text = f"\n{reason} | [id{admin}|Модератор] | {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(date))}"

    send(chat_id, f"{msg}\nИнформация о глобальной блокировке: {g_text}\n\n"
                  f"Информация о локальной блокировке: {l_text}", msg_id)


def clear(chat_id, message):
    if "reply_message" in message:
        try:
            del_messages(chat_id, [message.reply_message['conversation_message_id']])
        except vk_api.exceptions.ApiError:
            send(chat_id, "Не могу удалить сообщение данного пользователя!", message.conversation_message_id)

    elif message.fwd_messages:
        for item in message.fwd_messages:
            try:
                del_messages(chat_id, [item['conversation_message_id']])
            except:
                pass
    else:
        send(chat_id, "Команда должна быть ответом на сообщение, либо она должна быть отправлена с"
                      " пересланными сообщениями, которые необходимо удалить!", message.conversation_message_id)


def ban(chat_id, user_id, admin_id, reason, msg_id):
    if get_ban(chat_id, user_id):
        send(chat_id, f"[id{user_id}|Пользователь] уже заблокирован в этом чате!", msg_id)
    elif len(reason) <= 32:
        add_ban(chat_id, user_id, admin_id, reason)
        remove_user(chat_id, user_id)
        send(chat_id, f"{tag(chat_id, admin_id)} заблокировал(-а) {tag(chat_id, user_id, 'acc')} в этом чате", msg_id)
    else:
        send(chat_id, "Длина причины не может быть больше 32 символов!", msg_id)


def unban(chat_id, user_id, admin_id, msg_id):
    if get_ban(chat_id, user_id):
        del_ban(chat_id, user_id, admin_id)
        send(chat_id, f"{tag(chat_id, admin_id)} разблокировал(-а) [id{user_id}|пользователя]", msg_id)
    else:
        send(chat_id, f"[id{user_id}|Пользователь] не заблокирован в этом чате!", msg_id)


def kick(chat_id, user_id, admin_id, msg_id):
    if remove_user(chat_id, user_id):
        send(chat_id, f"{tag(chat_id, admin_id)} исключил(-а) {tag(chat_id, user_id, 'acc')}", msg_id)
    else:
        send(chat_id, "Не могу исключить данного пользователя!", msg_id)


def get_ban_list(chat_id, msg_id):
    bans = list(map(lambda it: it[0], bans_list(chat_id)))

    if not bans:
        return send(chat_id, "В беседе нет заблокированных пользователей!", msg_id)

    data, pages, chars = {}, 1, 0
    data[pages] = ""

    for user in bans:
        data[pages] += f"@id{user} ({get_name(chat_id, user)})\n"

        if len(data[pages]) > 3600:
            pages += 1
            data[pages] = ""

    send(chat_id, f"Список заблокированных пользователей:\n{data[1]}")
    if pages > 1:
        for page in range(2, pages + 1):
            send(chat_id, f"Страница {page}:\n{data[page]}")


def get_warns_list(chat_id, msg_id):
    warns = warns_list(chat_id)

    if not warns:
        return send(chat_id, "Нет участников с активными предупреждениями!", msg_id)

    pages, data = 1, {}
    data[pages] = ""
    for user, count in warns:
        data[pages] += f"@id{user} ({get_name(chat_id, user)}): {count}\n"

        if len(data[pages]) > 3600:
            pages += 1
            data[pages] = ""

    send(chat_id, f"Список активных предупреждений:\n{data[1]}", msg_id)
    if pages > 1:
        for page in range(2, pages + 1):
            send(chat_id, f"Страница {page}:\n{data[page]}", msg_id)


def get_history(chat_id, user_id, msg_id):
    array = history(chat_id, user_id)

    if not array:
        send(chat_id, "История наказаний пользователя отсутствует!", msg_id)

    pages, data = 1, {}
    data[pages] = ""

    for user, admin, date, reason, act in array:
        date_time = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(date))
        data[pages] += f"{date_time} | [id{admin}|Админ] | {act} | {reason}\n"

        if len(data[pages]) > 3600:
            pages += 1
            data[pages] = ""

    send(chat_id, f"История наказаний [id{user_id}|пользователя]:\n\n{data[1]}", msg_id)
    if pages > 1:
        for page in range(2, pages + 1):
            send(chat_id, f"Страница {page}:\n{data[page]}", msg_id)


def find(chat_id, request, msg_id):
    array = find_nick(chat_id, request)
    if not array:
        return send(chat_id, "Не найдено никнеймов по запросу!", msg_id)
    if len(array) > 20:
        return send(chat_id, f"Слишком много никнеймов по запросу!", msg_id)
    answer = "Найденные пользователи:\n"
    for user, nick in array:
        answer += f"@id{user} ({nick})\n"
    send(chat_id, answer, msg_id)


def pin_message(user_id, chat_id, message):
    pin(chat_id, message)
    send(chat_id, f"{tag(chat_id, user_id)} закрепил(-а) сообщение", message)


def remove_pin(user_id, chat_id, msg_id):
    unpin(chat_id)
    send(chat_id, f"{tag(chat_id, user_id)} открепил(-а) сообщение", msg_id)


def make_zov(chat_id, reason):
    users = list(map(lambda it: it['member_id'], get_users(chat_id)))

    data, pages = {}, 1
    data[pages] = ""

    for user in users:
        if "-" in str(user):
            continue

        data[pages] += f"[id{user}|👤]"

        if len(data[pages]) > 3600:
            pages += 1
            data[pages] = ""

    if pages > 1:
        send(chat_id, f"🔔 Вы были вызваны администратором беседы\n\n{data[1]}")
        for page in range(2, pages + 1):
            send(chat_id, data[page])
        send(chat_id, f"❗Причина вызова: {reason}")

    elif pages == 1 and len(reason) + len(data[1]) < 3900:
        send(chat_id, f"🔔 Вы были вызваны администратором беседы\n\n{data[1]}\n\n❗Причина вызова: {reason}")
    else:
        send(chat_id, f"🔔 Вы были вызваны администратором беседы\n\n{data[1]}")
        send(chat_id, f"❗Причина вызова: {reason}")


def greeting(chat_id, text, msg_id):
    msg = f"Новое приветствие: {text}"
    if not text:
        text, msg = "None", "Приветствие в беседе убрано!"
    send(chat_id, msg, msg_id)
    set_greeting(chat_id, text)


def quiet(chat_id, admin, msg_id):
    if get_quiet(chat_id):
        set_quiet(chat_id, False)
        send(chat_id, f"{tag(chat_id, admin)} выключил режим тишины!", msg_id)
    else:
        set_quiet(chat_id, True)
        send(chat_id, f"{tag(chat_id, admin)} включил режим тишины!", msg_id)


def global_kick(user_id, admin, reason):
    chats = list(get_chats_list())

    for chat in chats:
        if not remove_user(chat, user_id):
            continue
        send(chat, f"{tag(chat, admin)} исключил(-а) {tag(chat, user_id, 'acc')} во всех беседах\nПричина: {reason}")


def global_ban(chat_id, user_id, admin, reason, msg_id, btype):
    if len(reason) > 32:
        return send(chat_id, "Длина причины не может быть более 32 символов!", msg_id)

    is_banned = global_getban(user_id)
    if is_banned:
        return send(chat_id, "Пользователь уже имеет глобальную блокировку!", msg_id)
    add_global_ban(user_id, admin, int(time.time()), reason, btype)

    chats = list(get_chats_list())
    for chat in chats:
        if btype != "Players" and "МС" in get_chat_type(chat): continue
        if not remove_user(chat, user_id): continue
        send(chat,
             f"{tag(chat, admin)} заблокировал(-а) {tag(chat, user_id, 'acc')} во всех беседах\nПричина: {reason}")


def global_unban(chat_id, user_id, admin_id, msg_id):
    if global_getban(user_id):
        send(chat_id, f"{tag(chat_id, admin_id)} снял(-а) глобальную блокировку [id{user_id}|пользователю]", msg_id)
        return del_global_ban(user_id)
    send(chat_id, f"[id{user_id}|Пользователь] не имеет глобальной блокировки!", msg_id)


def type_zov(target, text):
    chats = get_chats_by_type(target.replace('-', ' '))

    for chat_id in chats:
        make_zov(chat_id, text)


def set_type(chat_id, text, msg_id):
    set_chat_type(chat_id, text)
    send(chat_id, f"В беседе установлен тип: {text}", msg_id)
