from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


betOnmatch = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="1000"),
            KeyboardButton(text="500"),
            KeyboardButton(text="250")
        ]
    ],
    resize_keyboard=True
)


allCommands = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Все матчи"),
            KeyboardButton(text="Список моих ставок"),
            KeyboardButton(text="Баланс")
        ],

        [
            KeyboardButton(text="Магазин")
        ]
    ],
    resize_keyboard=True
)


allCommandsAdmin = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Все матчи"),
            KeyboardButton(text="Список моих ставок"),
            KeyboardButton(text="Баланс")
        ],

        [
            KeyboardButton(text="CreateMatch"),
            KeyboardButton(text="Winner"),
            KeyboardButton(text="count"),
            KeyboardButton(text="Магазин")

        ]
    ],
    resize_keyboard=True
)
