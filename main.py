from threading import Thread
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from commands import *
from mute_control import *

lp = VkBotLongPoll(session, group_id)
VER = "2.4"


def events_handler(event: vk_api.bot_longpoll.VkBotMessageEvent):
    try:

        if 'action' in event.message:
            chat_id = event.chat_id
            user_id = event.message['action']['member_id']

            if event.message['action']['type'] == "chat_invite_user":
                invited_user(chat_id, user_id)

            elif event.message['action']['type'] == "chat_kick_user":
                remove_user(chat_id, user_id)

        elif event.type == VkBotEventType.MESSAGE_NEW:
            message = event.message
            chat_id = event.chat_id
            msg_id = message.conversation_message_id
            user_id = message.from_id
            text = message.text

            argument = get_arg(message)
            to_id = get_to_id(message)

            if "-" in str(to_id): to_id = 0
            try: command = text.split()[0][1:].lower()
            except IndexError: command = ""

            if mute_check(chat_id, user_id, msg_id):
                return
            if get_quiet(chat_id):
                if get_role(chat_id, user_id) == 0:
                    return del_messages(chat_id, [msg_id])

            if command in dev_commands:
                try:
                    if user_id in config.DEV:
                        if command == 'start':
                            get_users(chat_id)  # Получит ошибку, если бот не админ в беседе
                            chat_start(chat_id, msg_id)
                    else:
                        send(chat_id, "Доступно только с правами разработчика!", msg_id)
                except vk_api.exceptions.ApiError:
                    send(chat_id, "Вы должны назначить меня администратором беседы!", msg_id)

            level = get_role(chat_id, user_id)
            access = ((get_role(chat_id, to_id) < level) and (to_id not in config.DEV)) or user_id in config.DEV

            if (text and text[0] not in ['/', '!', '+']) or not text:
                return

            if command in user_commands:

                if command in ['id']:
                    if to_id:
                        send(chat_id, f"Оригинальная ссылка: https://vk.com/id{to_id}", msg_id)
                    else:
                        send(chat_id, f"Некорректно указан пользователь!", msg_id)

                elif command in ['stats']:
                    if to_id:
                        send(chat_id, stats(chat_id, to_id), msg_id)
                    else:
                        send(chat_id, stats(chat_id, user_id), msg_id)

                elif command in ['help']:
                    send(chat_id, get_help(user_id, level), msg_id)

            elif command in moder_commands:
                if level < 1 and user_id not in config.DEV:
                    if chat_id != 17: send(chat_id, "Недостаточно прав!", msg_id)

                elif command in ['mute']:
                    if not access:
                        send(chat_id, "Недостаточно прав!", msg_id)
                    elif to_id and argument:
                        mute(chat_id, to_id, user_id, argument, msg_id)
                    else:
                        send(chat_id, "Некорректно указан пользователь или время!", msg_id)

                elif command in ['unmute']:
                    if not access:
                        send(chat_id, "Недостаточно прав!", msg_id)
                    elif to_id:
                        unmute(chat_id, to_id, user_id, msg_id)
                    else:
                        send(chat_id, "Некорректно указан пользователь!", msg_id)

                elif command in ['snick', 'setnick']:
                    if not access and to_id != user_id:
                        send(chat_id, "Недостаточно прав!", msg_id)
                    elif to_id and argument and "'" not in argument and '"' not in argument:
                        set_nick_name(chat_id, to_id, user_id, argument, msg_id)
                    else:
                        send(chat_id, "Некорректно указан пользователь или никнейм!", msg_id)

                elif command in ['rnick', 'removenick']:
                    if not access and to_id != user_id:
                        send(chat_id, "Недостаточно прав!", msg_id)
                    elif to_id:
                        del_nick_name(chat_id, to_id, user_id, msg_id)
                    else:
                        send(chat_id, "Некорректно указан пользователь!", msg_id)

                elif command in ['nicklist', 'nlist']:
                    nick_list(chat_id, msg_id)

                elif command in ['nonicks']:
                    no_nick_list(chat_id, msg_id)

                elif command in ['find']:
                    request = " ".join(text.split()[1:])
                    find(chat_id, request, msg_id)

                elif command in ['olist']:
                    online_list(chat_id, msg_id)

                elif command in ['staff']:
                    staff_list(chat_id, msg_id)

                elif command in ['gnick', 'getnick']:
                    if to_id:
                        nick = get_nick(chat_id, to_id)
                        if nick:
                            send(chat_id, f"Никнейм @id{to_id} (пользователя) — {nick[0]}", msg_id)
                        else:
                            send(chat_id, "У пользователя не установлен никнейм!", msg_id)
                    else:
                        send(chat_id, "Некорректно указан пользователь!", msg_id)

                elif command in ['getwarn']:
                    if to_id:
                        getwarn(chat_id, to_id, msg_id)
                    else:
                        send(chat_id, "Некорректно указан пользователь!", msg_id)

                elif command in ['clear', 'чистка']:
                    clear(chat_id, message)

                elif command in ['warn']:
                    if not access:
                        send(chat_id, "Недостаточно прав!", msg_id)
                    elif to_id and argument and "'" not in argument and '"' not in argument:
                        warn(chat_id, to_id, msg_id, argument, user_id)
                    else:
                        send(chat_id, "Некорректно указан пользователь или причина!", msg_id)

                elif command in ['unwarn']:
                    if not access:
                        send(chat_id, "Недостаточно прав!", msg_id)
                    elif to_id:
                        unwarn(chat_id, to_id, msg_id, user_id)
                    else:
                        send(chat_id, "Некорректно указан пользователь!", msg_id)

                elif command in ['kick', 'кик']:
                    if not access:
                        send(chat_id, "Недостаточно прав!", msg_id)
                    elif to_id:
                        kick(chat_id, to_id, user_id, msg_id)
                    else:
                        send(chat_id, "Некорректно указан пользователь!", msg_id)

                elif command in ['zov', 'зов', 'вызов']:
                    if (len(command) + 5 <= len(text)) and (len(text) < 1040):
                        make_zov(chat_id, text[(len(command)+2):])
                    else:
                        send(chat_id, "Длина причины должна быть не менее 3 и не более 1024 символов!", msg_id)

                elif command in ['pin']:
                    if "reply_message" in message:
                        pin_message(user_id, chat_id, message.reply_message['conversation_message_id'])
                    else:
                        send(chat_id, "Команда должна быть ответом на сообщение!", msg_id)

                elif command in ['unpin']:
                    remove_pin(user_id, chat_id, msg_id)

                elif command in ['getban']:
                    if to_id:
                        get_user_bans(chat_id, to_id, msg_id)
                    else:
                        send(chat_id, "Некорректно указан пользователь!", msg_id)

            elif command in admin_commands:
                if level < 2 and user_id not in config.DEV:
                    if chat_id != 17: send(chat_id, "Недостаточно прав!", msg_id)

                elif command in ['banlist']:
                    get_ban_list(chat_id, msg_id)

                elif command in ['warnlist']:
                    get_warns_list(chat_id, msg_id)

                elif command in ['history']:
                    if to_id:
                        get_history(chat_id, to_id, msg_id)
                    else:
                        send(chat_id, "Некорректно указан пользователь!", msg_id)

                elif command in ['gsnick']:
                    if not access and to_id != user_id:
                        send(chat_id, "Недостаточно прав!", msg_id)
                    elif to_id and argument and "'" not in argument and '"' not in argument:
                        set_global_name(chat_id, to_id, user_id, argument, msg_id)
                    else:
                        send(chat_id, "Некорректно указан пользователь или никнейм!", msg_id)

                elif command in ['ban', 'бан']:
                    if not access:
                        send(chat_id, "Недостаточно прав!", msg_id)
                    elif to_id and argument and "'" not in argument and '"' not in argument:
                        ban(chat_id, to_id, user_id, argument, msg_id)
                    else:
                        send(chat_id, "Некорректно указан пользователь или причина!", msg_id)

                elif command in ['unban']:
                    if to_id:
                        unban(chat_id, to_id, user_id, msg_id)
                    else:
                        send(chat_id, "Некорректно указан пользователь!", msg_id)

                elif command in ['moder']:
                    if not access:
                        send(chat_id, "Недостаточно прав!", msg_id)
                    elif to_id:
                        set_role(chat_id, to_id, 1, msg_id, user_id, argument)
                    else:
                        send(chat_id, f"Пользователь указан некорректно!", msg_id)

                elif command in ['rrole', 'removerole']:
                    if not access:
                        send(chat_id, "Недостаточно прав!", msg_id)
                    elif to_id:
                        set_role(chat_id, to_id, 0, msg_id, user_id, argument)
                    else:
                        send(chat_id, f"Пользователь указан некорректно!", msg_id)

                elif command in ['ver']:
                    send(chat_id, f"Текущая версия: {VER}", msg_id)

            elif command in sen_admin_commands:
                if level < 3 and user_id not in config.DEV:
                    if chat_id != 17: send(chat_id, "Недостаточно прав!", msg_id)

                elif command in ['quiet', 'тишина']:
                    quiet(chat_id, user_id, msg_id)

                elif command in ['admin']:
                    if not access:
                        send(chat_id, "Недостаточно прав!", msg_id)
                    elif to_id:
                        set_role(chat_id, to_id, 2, msg_id, user_id, argument)
                    else:
                        send(chat_id, f"Пользователь указан некорректно!", msg_id)

                elif command in ['greeting', 'приветствие']:
                    greet = " ".join(text.split()[1:])
                    greeting(chat_id, greet, msg_id)

            elif command in staff_commands:
                if level < 4 and user_id not in config.DEV:
                    if chat_id != 17: send(chat_id, "Недостаточно прав!", msg_id)

                elif command in ['sadmin']:
                    if not access:
                        send(chat_id, "Недостаточно прав!", msg_id)
                    elif to_id:
                        set_role(chat_id, to_id, 3, msg_id, user_id, argument)
                    else:
                        send(chat_id, f"Пользователь указан некорректно!", msg_id)

                elif command in ['skick', 'снят']:
                    if not access:
                        send(chat_id, "Недостаточно прав!", msg_id)
                    elif to_id:
                        global_kick(to_id, user_id, argument)
                    else:
                        send(chat_id, "Некорректно указан пользователь или причина!", msg_id)

                elif command in ['sban']:
                    if not access:
                        send(chat_id, "Недостаточно прав!", msg_id)
                    elif to_id and argument:
                        global_ban(chat_id, to_id, user_id, argument, msg_id, "No")
                    else:
                        send(chat_id, "Некорректно указан пользователь или причина!", msg_id)

                elif command in ['sbanpl']:
                    if not access:
                        send(chat_id, "Недостаточно прав!", msg_id)
                    elif to_id and argument:
                        global_ban(chat_id, to_id, user_id, argument, msg_id, "Pl")
                    else:
                        send(chat_id, "Некорректно указан пользователь или причина!", msg_id)

                elif command in ['sunban']:
                    if to_id:
                        global_unban(chat_id, to_id, user_id, msg_id)
                    else:
                        send(chat_id, "Некорректно указан пользователь!", msg_id)

                elif command in ['typezov']:
                    target, *array = text.split()[1:]
                    type_zov(target, " ".join(array))

            elif command in dev_commands:
                if user_id not in config.DEV:
                    send(chat_id, "Недостаточно прав!", msg_id)

                elif command in ['type']:
                    array = text.split()
                    if len(array) > 1:
                        set_type(chat_id, " ".join(array[1:]), msg_id)
                    else:
                        send(chat_id, "Неверно указан тип беседы!", msg_id)

                elif command in ['chat']:
                    send(chat_id, f"ID чата: {chat_id}\nТип чата: {get_chat_type(chat_id)}", msg_id)

                elif command in ['spec']:
                    if not access:
                        send(chat_id, "Недостаточно прав!", msg_id)
                    elif to_id:
                        set_role(chat_id, to_id, 4, msg_id, user_id, argument)
                    else:
                        send(chat_id, f"Пользователь указан некорректно!", msg_id)

                elif command in ['dev']:
                    set_role(chat_id, user_id, 5, msg_id, user_id, "ALL")

    except:
        pass


def main():
    while True:
        try:

            for event in lp.listen():
                Thread(target=events_handler, args=(event,)).start()

        except:
            pass


if __name__ == "__main__":
    Thread(target=mute_control).start()
    main()
