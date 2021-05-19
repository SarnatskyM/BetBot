import logging
from sqlite3.dbapi2 import Cursor
from aiogram import Bot, Dispatcher, executor, types
import config
import asyncio
from contextlib import suppress
from aiogram.utils.exceptions import (MessageToEditNotFound, MessageCantBeEdited, MessageCantBeDeleted,MessageToDeleteNotFound)
import sqlite3

balance = config.Balance
arrayBet ={
    "edik": 0,
    "max": 0,
    "alan": 0
}
bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands='start')
async def send_welcome(message: types.Message):
    try:
        startMoney = 1000
        conn = sqlite3.connect('data.db')
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS users(user_id INTEGER, username TXT, user_balance BIGINT, user_choice TEXT)')
        conn.commit()
        man_id = message.from_user.id
        cur.execute(f"SELECT user_id FROM users WHERE user_id = {man_id}")
        data = cur.fetchone()
        print(data)
        if data is None:
            cur.execute(f'INSERT INTO users VALUES("{message.from_user.id}", "@{message.from_user.username}", "{startMoney}","")')
            conn.commit()
    except Exception as e:
        conn = sqlite3.connect('data.db')
        cur = conn.cursor()
        cur.execute(f'INSERT INTO users VALUES("{message.from_user.id}")')
        conn.commit()
    await message.reply("To bet on today's match, write /go")


@dp.message_handler(commands='balance')
async def send_welcome(message: types.Message):
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    man_id = message.from_user.id
    cur.execute(f"SELECT user_balance FROM users WHERE user_id = {man_id}")
    data = cur.fetchone()
    conn.commit()
    await message.reply(f"your balance: {data[0]}")

async def delete_message(message: types.Message, sleep_time: int = 0):
    await asyncio.sleep(sleep_time)
    with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
        await message.delete()

@dp.message_handler(commands='go')
async def send_welcome(message: types.Message):
    keyboard_markup = types.InlineKeyboardMarkup(row_width=3)

    text_and_data = (
        ('Edik', 'edik'),
        ('Max', 'max'),
        ('Alan', 'alan'),
    )
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
    
    keyboard_markup.row(*row_btns)
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    man_id = message.from_user.id
    cur.execute(f"SELECT * from users WHERE user_id = {man_id}")
    data = cur.fetchone()
    if data[2] > 0:
        msg = await message.reply("Сhoose who will win today?", reply_markup=keyboard_markup)
    else:
        msg = await message.reply("Wait for the end of the match!")
    conn.commit()
    asyncio.create_task(delete_message(msg, 4))



@dp.callback_query_handler(text='max')  # if cb.data == 'max' 
@dp.callback_query_handler(text='edik')  # if cb.data == 'edik'
@dp.callback_query_handler(text='alan')  # if cb.data == 'alan'
async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
    global arrayBet
    keyboard_markup = types.InlineKeyboardMarkup(row_width=2)
    text_and_data = (
        ('1000', '1000'),
        ('500', '500'),
        ('250', '250'),
    )
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
    keyboard_markup.row(*row_btns)
    answer_data = query.data
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    man_id = query.from_user.id
    cur.execute(f"UPDATE users SET user_choice='{answer_data}' WHERE user_id={man_id}")
    text = 'Great job!! Good luck'
    conn.commit()
    await bot.send_message(query.from_user.id, text , reply_markup=keyboard_markup)


@dp.callback_query_handler(text='1000')  # if cb.data == '1000 money' 
@dp.callback_query_handler(text='500')  # if cb.data == '500 money'
@dp.callback_query_handler(text='250')  # if cb.data == '250 money'
async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
    answer_data = query.data
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    man_id = query.from_user.id
    cur.execute(f"SELECT * FROM users WHERE user_id={man_id}")
    data = cur.fetchone()
    global arrayBet
    if answer_data == '1000':
        text = 'Are you sure? /listBet'
        arrayBet[data[3]] += 1000
        cur.execute(f"UPDATE users SET user_balance={data[2]-1000} WHERE user_id={man_id}")
    elif answer_data == '500':
        text = 'Serious bet /listBet'
        arrayBet[data[3]] += 500
        cur.execute(f"UPDATE users SET user_balance={data[2]-500} WHERE user_id={man_id}")
    else:
        if answer_data == "250":
            text = 'Ha, pennies /listBet'
            arrayBet[data[3]] += 250
            cur.execute(f"UPDATE users SET user_balance={data[2]-250} WHERE user_id={man_id}")
    conn.commit()

    await bot.send_message(query.from_user.id, text)



@dp.message_handler(commands='listBet')
async def send_welcome(message: types.Message):
    global arrayBet
    text = ""
    for item in arrayBet.items():
        text +="- " + item[0]+" "+str(item[1]) + "\n"
    
    text += "\n if you want check your balance /balance"
    await message.reply(text)



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)