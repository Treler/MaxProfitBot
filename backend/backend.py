from requests import post
from json import load, dump
import asyncio
from aiogram import Bot
from aiogram.types import CallbackQuery, Message


# функция ежедневной (можно поменять) проверки подписки
async def subscription_checker(bot: Bot, channel_id: str) -> None:
    while True:

        # получаем всех пользователей
        all_users = get_all_user_from_database()

        with open("./identify/users.json", "r", encoding="utf-8") as json_file:
            data = load(json_file)

        for user_id in all_users:

            # для каждого пользователя делаем запрос в базу
            request = check_subscription_period(data[str(user_id)]["email"])

            # проверяем подписку
            if isinstance(request["has_active_tariff"], str):

                # если ее нет, то баним (кикаем) пользователя из группы
                await bot.ban_chat_member(chat_id=channel_id, user_id=user_id)

        # засыпаем на 24 часа после проверки всей базы
        await asyncio.sleep(86400)


# функция проверки подписки по почте
def check_subscription_period(email: str) -> str or dict:

    api_key = "4819a54c1cbe0d80c61a"

    base_url = f"https://api.maxprofit.cc/s/tg-chat-bot/check-email/?api_key={api_key}"

    headers = {
        "content-type": 'application/json',
        "accept": 'application/json',
    }

    data = {
        "email": email
    }

    # отправляем post-запрос
    response = post(base_url, headers=headers, json=data)

    # если почта не найдена, то возвращаем строку
    if response.status_code == 404:
        result = "Error"

    # если почта найдена, то возвращаем ответ в виде словаря (ответ API)
    else:
        result = response.json()

    return result


# функция записи в базу выбранного пользователем языка
def write_lang_to_database(call: CallbackQuery) -> None:

    lang = call.data[call.data.rfind(" ") + 1::]
    user_id = str(call.from_user.id)

    with open("./identify/users.json", "r", encoding="utf-8") as json_file:
        data = load(json_file)

    # если пользователь не в базе, то создаем атрибут
    if user_id not in data.keys():

        data[user_id] = {}
        data[user_id]["language"] = lang

    # если уже в базе (дальнейший функционал смены языка), то просто меняем язык
    else:

        data[user_id]["language"] = lang

    data[str(user_id)]["invitation_recieved"] = False

    with open(f"./identify/users.json", "w", encoding="utf-8") as outfile:
        dump(data, outfile, indent=4, ensure_ascii=False)


# функция получения фразы исходя из языка пользователя и ключа для фразы. Редачить в ./identify/answers.json
def get_language_phrase(msg: Message, key: str) -> str:

    with open("./identify/answers.json", "r", encoding="utf-8") as json_file:
        data = load(json_file)

    lang = get_user_language(str(msg.from_user.id))

    return data[lang][key]


# функция получения языка для конкретного пользователя
def get_user_language(user_id: str) -> str:

    with open("./identify/users.json", "r", encoding="utf-8") as json_file:
        data = load(json_file)

    return data[str(user_id)]["language"]


# функция получения почты для конкретного пользователя
def get_user_email(user_id: int) -> str:

    with open("./identify/users.json", "r", encoding="utf-8") as json_file:
        data = load(json_file)

    return data[str(user_id)]["email"]


# функция-регистратор прохождения идентификации в боте
def write_user_to_database(msg: Message) -> None:

    with open("./identify/users.json", "r", encoding="utf-8") as json_file:
        data = load(json_file)

    data[str(msg.from_user.id)]["access"] = True

    with open("./identify/users.json", "w", encoding="utf-8") as outfile:
        dump(data, outfile, indent=4, ensure_ascii=False)


# функция получения всех АЙДИ пользователей из базы
def get_all_user_from_database() -> list:

    with open("./identify/users.json", "r", encoding="utf-8") as json_file:
        data = load(json_file)

    return data.keys()


# функция получения всех почт админов. Редачить в ./identify/admins_emails.txt
def get_all_admins_emails() -> list:

    with open("./identify/admins_emails.txt", "r", encoding="utf-8") as data:
        lines = data.readlines()

    result = [i.strip() for i in lines]

    return result


# функция-проверка на указание уже зарегистрированной почты при регистрации нового пользователя
def check_email_already_registered(email: str) -> bool:

    with open("./identify/users.json", "r", encoding="utf-8") as json_file:
        data = load(json_file)

    is_thief = False

    for user_id in data.keys():

        try:
            if data[str(user_id)]["email"] == email:
                is_thief = True
                break

        except KeyError:
            continue

    return is_thief


# функция-проверка на получение пригласительной ссылки
def get_invite_already_recieved(user_id: int) -> bool:

    with open("./identify/users.json", "r", encoding="utf-8") as json_file:
        data = load(json_file)

    return data[str(user_id)]["invitation_recieved"]


# функция получения идентификатора закрытого чата в телеграмме
def get_chat_id() -> str:

    with open("./identify/chat_id.txt", "r", encoding="utf-8") as data:
        result = data.readline()

    return result
