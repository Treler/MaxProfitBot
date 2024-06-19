from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from json import load


# описана в ./backend/backend.py
def get_language_phrase(user_id, key):

    with open("./identify/answers.json", "r", encoding="utf-8") as json_file:
        data = load(json_file)

    lang = get_user_language(user_id)

    return data[lang][key]


# описана в ./backend/backend.py
def get_user_language(user_id):

    with open("./identify/users.json", "r", encoding="utf-8") as json_file:
        data = load(json_file)

    return data[str(user_id)]["language"]


# клавиатура выбора языка - с ней пользователь сталкивается после первичной отправки /start
def initial_keyboard():

    all_initial_buttons = InlineKeyboardBuilder()

    # пока что поддерживаем только два языка
    rus_lang_btn = InlineKeyboardButton(text="🇷🇺 Русский", callback_data="language rus")
    eng_lang_btn = InlineKeyboardButton(text="🇺🇲 English", callback_data="language eng")

    all_initial_buttons.add(rus_lang_btn)
    all_initial_buttons.add(eng_lang_btn)

    all_initial_buttons.adjust(1)

    return all_initial_buttons.as_markup()


# клавиатура зарегистрированного пользователя
def user_keyboard(user_id):

    all_user_buttons = InlineKeyboardBuilder()

    # в зависимости от выбранного языка формируем текст на каждой кнопке
    invite_link_btn_text = get_language_phrase(user_id, "invite_link_btn")
    subscription_status_btn_text = get_language_phrase(user_id, "subscription_status_btn")
    subscription_repay_text = get_language_phrase(user_id, "subscription_repay_btn")
    change_language_btn_text = get_language_phrase(user_id, "change_language_btn")

    # закидываем сформированный текст в каждую кнопку и задаем колбек для возможности отследить нажатие
    invite_link_btn = InlineKeyboardButton(text=invite_link_btn_text, callback_data="get invite")
    subscription_status_btn = InlineKeyboardButton(text=subscription_status_btn_text, callback_data="subscription status")
    # url="https://vk.com/feed"
    subscription_repay_btn = InlineKeyboardButton(text=subscription_repay_text, callback_data="subscription repay")
    change_language_btn = InlineKeyboardButton(text=change_language_btn_text, callback_data="xxx")

    all_user_buttons.add(invite_link_btn)
    all_user_buttons.add(subscription_status_btn)
    all_user_buttons.add(subscription_repay_btn)
    all_user_buttons.add(change_language_btn)

    all_user_buttons.adjust(1)

    return all_user_buttons.as_markup()
