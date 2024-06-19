from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from asyncio import get_event_loop
from aiogram.methods import DeleteWebhook
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
import json
import aiogram

from keyboards.keyboard import initial_keyboard, user_keyboard
from backend.backend import (write_lang_to_database, get_language_phrase, check_subscription_period,
                             write_user_to_database, get_all_user_from_database, subscription_checker, get_user_email,
                             get_all_admins_emails, check_email_already_registered, get_invite_already_recieved,
                             get_chat_id)
from states.states import GetInitialAccess

# здесь прописывается токен бота
bot = Bot(token="7426360149:AAGLPPCz4cCEf8mROMly58f6q4LpcjNkn80", default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# идентификатор чата, с которым будет работать. Редачить в ./identify/chat_id.txt
chat_id = str(get_chat_id())


# главная функция-обработчик всех событий в боте
async def start() -> None:

    # функция откликается на первичное взаимодействие с ботом и через команду /start
    @dp.message(F.text == "/start")
    async def start_command(msg: Message) -> None:

        all_users = get_all_user_from_database()

        # если пользователь не в базе, то выводим на процесс регистрации
        if str(msg.from_user.id) not in all_users:
            await msg.answer(text="🌍", reply_markup=initial_keyboard())

        # если в базе, то выдаем сообщение, что уже зареган и выдаем клавиатуру
        else:
            await bot.send_sticker(msg.chat.id,
                                   "CAACAgIAAxkBAAEGPktmccBh1AaVp3ghxW9uuTqrLeyNkgACAgEAAladvQpO4myBy0Dk_zUE")
            text = get_language_phrase(msg, "already_registered")
            await msg.answer(text=text, reply_markup=user_keyboard(str(msg.from_user.id)))

    # запускается после выбора языка и предлагает ввести почту пользователю
    @dp.callback_query(F.data.startswith('language'))
    async def enter_user_email_call(call: CallbackQuery, state: FSMContext) -> None:
        write_lang_to_database(call)
        text = get_language_phrase(call, 'enter_email')
        await bot.send_message(call.from_user.id, text=text)
        await state.set_state(GetInitialAccess.GET_USER_EMAIL)

    # запускается после ввода почты и делает много различных проверок
    @dp.message(GetInitialAccess.GET_USER_EMAIL)
    async def enter_user_email(msg: Message, state: FSMContext) -> None:
        user_email = msg.text

        # если результат - строка, то говорим, что почта неверная и предлагаем ввести еще раз
        if isinstance(check_subscription_period(user_email), str):
            text = get_language_phrase(msg, "wrong_email")
            await bot.send_sticker(msg.chat.id,
                                   "CAACAgIAAxkBAAEGPehmcbGDX9Ua3ml-Zs0RDTeGo7a-GAAC-QADVp29CpVlbqsqKxs2NQQ")
            await msg.answer(text=text)

        # если результат - словарь
        else:

            # проверяем, принадлежит ли почта админам (вдруг найдутся умники)
            if user_email not in get_all_admins_emails():
                # проверяем, не была ли эта почта зарегистрирована ранее (все те же умники)
                if not check_email_already_registered(user_email):

                    # делаем статус "enable" - пользователь зарегистрирован
                    write_user_to_database(msg)
                    text = get_language_phrase(msg, "get_access")
                    await bot.send_message(msg.from_user.id, text=text, reply_markup=user_keyboard(msg.from_user.id))
                    await register_user_email_call(msg, state)

                # если почта уже зарегана, говорим об этом и предлагаем ввести еще раз
                else:
                    text = get_language_phrase(msg, "email_already_registered")
                    await bot.send_sticker(msg.from_user.id,
                                           "CAACAgIAAxkBAAEGQcJmcpGQnL4wvTYEaJj_bt42BEJdlAAC-wADVp29ClYO2zPbysnmNQQ")
                    await msg.answer(text=text)

            # если почта админская, говорим об этом и предлагаем ввести еще раз
            else:
                text = get_language_phrase(msg, "this_is_admin_email")
                await bot.send_sticker(msg.from_user.id,
                                       "CAACAgIAAxkBAAEGQcJmcpGQnL4wvTYEaJj_bt42BEJdlAAC-wADVp29ClYO2zPbysnmNQQ")
                await msg.answer(text=text)

    # записывает почту пользователя в базу и чистит машину состояний
    async def register_user_email_call(msg: Message, state: FSMContext) -> None:
        user_email = msg.text

        with open("identify/users.json", "r", encoding="utf-8") as json_file:
            data = json.load(json_file)

        data[str(msg.from_user.id)]["email"] = user_email

        with open(f"identify/users.json", "w", encoding="utf-8") as outfile:
            json.dump(data, outfile, indent=4, ensure_ascii=False)

        await state.clear()


    # отвечает за получение пригласительной ссылки в закрутую группу
    @dp.callback_query(F.data.startswith("get invite"))
    async def get_invite_call(call: CallbackQuery) -> None:

        # получаем словарь значений
        check_subscription = check_subscription_period(get_user_email(call.from_user.id))

        # проверяем активна ли подписка
        if check_subscription["has_active_tariff"]:

            # проверяем получал ли пользователь ссылку ранее (защищает от бесконечной генерации ссылок одним пользователем)
            if not get_invite_already_recieved(call.from_user.id):

                # производим разбан пользователя, если ранее он был кикнут ботом
                # await bot.unban_chat_member(chat_id, call.from_user.id)

                # генерируем ссылку и отправляем пользователю
                link = await bot.create_chat_invite_link(chat_id, member_limit=1)
                text = get_language_phrase(call, "invitation_link_recieved")
                await bot.send_message(call.from_user.id, f"{text} {link.invite_link}")

                # записываем в базу получение ссылки конкретным пользователем (бесконечная генерация)
                with open("identify/users.json", "r", encoding="utf-8") as json_file:
                    data = json.load(json_file)

                data[str(call.from_user.id)]["invitation_recieved"] = True

                with open(f"identify/users.json", "w", encoding="utf-8") as outfile:
                    json.dump(data, outfile, indent=4, ensure_ascii=False)

            # если получал ссылку ранее, то не выдаем ее и сообщаем об этом
            else:
                await bot.send_sticker(call.from_user.id,
                                       "CAACAgIAAxkBAAEGPktmccBh1AaVp3ghxW9uuTqrLeyNkgACAgEAAladvQpO4myBy0Dk_zUE")
                text = get_language_phrase(call, "invitation_already_recieved")
                await bot.send_message(call.from_user.id, text=text, reply_markup=user_keyboard(str(call.from_user.id)))

        # если подписка неактивна, то сообщаем об этом и не выдаем ссылку
        else:
            text = get_language_phrase(call, "subscription_expired")
            await bot.send_sticker(call.from_user.id,
                                   "CAACAgIAAxkBAAEGPehmcbGDX9Ua3ml-Zs0RDTeGo7a-GAAC-QADVp29CpVlbqsqKxs2NQQ")
            await bot.send_message(call.from_user.id, text=text, reply_markup=user_keyboard(call.from_user.id))



# ------------------------------------ БУДУЩИЕ РАЗРАБОТКИ ------------------------------------ #

    @dp.callback_query(F.data.startswith("subscription status"))
    async def subscription_status_call(call: CallbackQuery) -> None:
        await bot.send_message(call.from_user.id, text="⚙️ Coming soon")
        # await bot.send_message(call.from_user.id, text="Статус: ✅ Активна / ❌ Неактивна\nСрок действия: 49 дней / истек\n")

    @dp.callback_query(F.data.startswith("subscription repay"))
    async def subscription_repay_call(call: CallbackQuery) -> None:
        await bot.send_message(call.from_user.id, text="⚙️ Coming soon")
        # link = await bot.create_chat_invite_link(chat_id, member_limit=1)
        #
        # await bot.send_message(call.from_user.id, link.invite_link)

    @dp.callback_query(F.data.startswith("xxx"))
    async def subscription_repay_call(call: CallbackQuery) -> None:
        await bot.send_message(call.from_user.id, text="⚙️ Coming soon")
        # link = await bot.create_chat_invite_link(chat_id, member_limit=1)
        #
        # await bot.send_message(call.from_user.id, link.invite_link)


# ------------------------------------ БУДУЩИЕ РАЗРАБОТКИ ------------------------------------ #



    try:

        # выключаем все вызовы вне работы бота (когда он включится не будет выполнять все команды, которые были
        # отданы в момент его отключенного состояния
        await bot(DeleteWebhook(drop_pending_updates=True))
        await dp.start_polling(bot)

    except aiogram.exceptions.TelegramNetworkError:
        pass

    finally:
        await bot.session.close()


if __name__ == '__main__':
    loop = get_event_loop()

    # создаем вечный цикл нашей основной функции
    loop.create_task(start())

    # создаем вечный цикл функции проверки подписки
    # loop.create_task(subscription_checker(bot, chat_id))

    # запускаем все вечные циклы, заданные выше
    loop.run_forever()
