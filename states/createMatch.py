from aiogram.dispatcher.filters.state import StatesGroup, State


class CreateFight(StatesGroup):
    E1 = State()
    E2 = State()
    E3 = State()




class SetBet(StatesGroup):
    B1 = State()


class SetWinner(StatesGroup):
    W1 = State()
    W2 = State()
    W3 = State()
    