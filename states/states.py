from aiogram.fsm.state import State, StatesGroup


# машина состояний для регистрации пользователя в боте
class GetInitialAccess(StatesGroup):
    GET_USER_EMAIL = State()
