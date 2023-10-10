import json
import vk_api

from config import token, group_id

session = vk_api.VkApi(token=token)
vk = session.get_api()


def send(chat_id, message, reply=None):
    data = {
        "random_id": 0,
        "chat_id": chat_id,
        "message": message
    }
    if reply:
        query_json = json.dumps({
            "peer_id": 2000000000 + chat_id,
            "conversation_message_ids": [reply],
            "is_reply": True
        })
        data['forward'] = [query_json]
    session.method("messages.send", data)


def kick_member(chat_id, user_id):
    session.method("messages.removeChatUser", {
        "chat_id": chat_id,
        "user_id": user_id
    })


def pin(chat_id, message_id):
    session.method("messages.pin", {
        "peer_id": 2000000000 + chat_id,
        "conversation_message_id": message_id
    })


def unpin(chat_id):
    session.method("messages.unpin", {
        "peer_id": 2000000000 + chat_id
    })


def del_messages(chat_id, msg_ids):
    session.method("messages.delete", {
        "peer_id": 2000000000 + chat_id,
        "delete_for_all": 1,
        "cmids": msg_ids
    })


def get_users(chat_id):
    return session.method("messages.getConversationMembers", {
        "peer_id": 2000000000 + chat_id
    })["items"]


def get_online(chat_id):
    return session.method("messages.getConversationsById", {
        "peer_ids": 2_000_000_000 + chat_id
    })['items'][0]['chat_settings']['active_ids']


def get_vk_name(user_id):
    data = session.method("users.get", {"user_ids": user_id})[0]
    return data["first_name"] + " " + data["last_name"]
