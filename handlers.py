from asyncio.windows_events import NULL
from sqlite3.dbapi2 import Cursor
from aiogram import types
from aiogram.types import callback_query
from aiogram.types import message
from aiogram.types.message import Message
from config import *
from contextlib import suppress
from aiogram.utils.exceptions import (MessageToEditNotFound, MessageCantBeEdited, MessageCantBeDeleted,MessageToDeleteNotFound)
import sqlite3, asyncio
from states.createMatch import CreateFight
from aiogram.dispatcher import FSMContext
from loader import dp, bot


balance = Balance


@dp.message_handler(commands='start')
async def send_welcome(message: types.Message):
    try:
        startMoney = 1000
        conn = sqlite3.connect('data.db')
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS users(user_id INTEGER, username TXT, user_balance BIGINT)')
        conn.commit()
        man_id = message.from_user.id
        cur.execute(f"SELECT user_id FROM users WHERE user_id = {man_id}")
        data = cur.fetchone()
        if data is None:
            cur.execute(f'INSERT INTO users VALUES("{message.from_user.id}", "@{message.from_user.username}", "{startMoney}")')
            conn.commit()
    except Exception as e:
        conn = sqlite3.connect('data.db')
        cur = conn.cursor()
        cur.execute(f'INSERT INTO users VALUES("{message.from_user.id}")')
        conn.commit()
    await message.reply("Хотите поставить на матч?\nНапишите - /allMatches")


@dp.message_handler(commands='balance')
async def send_balance(message: types.Message):
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    man_id = message.from_user.id
    cur.execute(f"SELECT user_balance FROM users WHERE user_id = {man_id}")
    data = cur.fetchone()
    conn.commit()
    await message.reply(f"Ваш счет: {data[0]}")

async def delete_message(message: types.Message, sleep_time: int = 0):
    await asyncio.sleep(sleep_time)
    with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
        await message.delete()

@dp.message_handler(commands='allMatches')
async def send_allMatch(message: types.Message):
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    man_id = message.from_user.id
    cur.execute(f'SELECT * FROM matches')
    data = cur.fetchall()
    for i in data:
        keyboard_markup = types.InlineKeyboardMarkup(row_width=2)
        text_and_data = (
            (i[2], 'firstTeam'),
            (i[3], 'secondTeam'),
        )
        row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
        keyboard_markup.row(*row_btns)
        await message.reply(f"{i[1]}\n{i[2]} vs {i[3]}", reply_markup=keyboard_markup)
    man_id = message.from_user.id
    conn.commit()
    cur.execute(f"SELECT * from users WHERE user_id = {man_id}")
    data = cur.fetchone()
    if data[2] > 0:
        msg = await message.reply("Кто выиграет?", reply=False)
    else:
        msg = await message.reply("На вашем счету недостаточно средств\nПроверить баланс /balance")
    conn.commit()
    asyncio.create_task(delete_message(msg, 30))



@dp.callback_query_handler(text = 'firstTeam') 
@dp.callback_query_handler(text = 'secondTeam') 
async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
    print(query.keyboard_markup)
    keyboard_markup = types.InlineKeyboardMarkup(row_width=2)
    text_and_data = (
        ('1000', 1000),
        ('500', 500),
        ('250', 250),
    )
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
    keyboard_markup.row(*row_btns)
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS bets(id INTEGER PRIMARY KEY, user_id INTEGER, user_choice INTEGER, user_bet BIGINT)')
    conn.commit()
    cur.execute(f'INSERT INTO bets VALUES(NULL,"{query.from_user.id}", "{query.data}", NULL)')
    text = 'Отлично сработано! Выберите сумму'
    conn.commit()
    await bot.send_message(query.from_user.id, text , reply_markup=keyboard_markup)


@dp.callback_query_handler(text='1000')  # if cb.data == '1000 money' 
@dp.callback_query_handler(text='500')  # if cb.data == '500 money'
@dp.callback_query_handler(text='250')  # if cb.data == '250 money'
async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    man_id = query.from_user.id
    cur.execute(f'SELECT * FROM bets WHERE user_id={man_id}')
    data = cur.fetchone()
    print(data)
    if data[3] == None: 
        cur.execute(f'SELECT * FROM users WHERE user_id={man_id}')
        data = cur.fetchone()
        if query.data == '1000' and data[2]>=1000:
            text = 'Серьезная ставочка /listBet'
            cur.execute(f'UPDATE users SET user_balance={data[2]-1000} WHERE user_id={man_id}')
            cur.execute(f"UPDATE bets SET user_bet={1000} WHERE user_id={man_id}")
        elif query.data == '500' and data[2]>=500:
            text = 'А вы уверены? /listBet'
            cur.execute(f'UPDATE users SET user_balance={data[2]-500} WHERE user_id={man_id}')
            cur.execute(f'UPDATE bets SET user_bet={500} WHERE user_id={man_id}')
        else:
            if query.data == '250' and data[2]>=250:
                text = 'Ха, клоун! Поставь ты больше /listBet'
                cur.execute(f'UPDATE users SET user_balance={data[2]-250} WHERE user_id={man_id}')
                cur.execute(f'UPDATE bets SET user_bet={250} WHERE user_id={man_id}')
            else:
                text = 'На вашем счету нет столько средств! Пополните счет'
        conn.commit()
    else:
        text = 'Вы уже ставили на этот матч'
    await bot.send_message(query.from_user.id, text)



@dp.message_handler(commands='listBet')
async def send_listbet(message: types.Message):
    a = 1


@dp.message_handler(commands='listMatch')
async def send_listMatch(message: types.Message):
    global mathList
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM matches')
    data = cur.fetchall()
    conn.commit()
    for i in data:
        mathList += i[0] + " :" + i[1] + " vs " + i[2]+"\n"
    await message.reply(mathList)


@dp.message_handler(commands='createMatch')
async def CreateMatch(message: types.Message):
    if message.from_user.id == admin_id:
        await bot.send_message(admin_id, text='Название мероприятия')
        await CreateFight.first()

@dp.message_handler(state=CreateFight.E1)
async def nameMatch(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Название первой команды", parse_mode="HTML")
    await CreateFight.next() 

@dp.message_handler(state=CreateFight.E2)
async def nameMatch(message: types.Message, state: FSMContext):
    await state.update_data(teamFirst=message.text)
    await message.answer("Название второй команды", parse_mode="HTML")
    await CreateFight.next() 

@dp.message_handler(state=CreateFight.E3)
async def nameMatch(message: types.Message, state: FSMContext):
    global mathList
    await state.update_data(teamSecond=message.text)
    data = await state.get_data()
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS matches(id INTEGER PRIMARY KEY,name_match TEXT, firstTeam TEXT, secondTeam TEXT)')
    cur.execute(f'INSERT INTO matches VALUES(NULL,"{data["name"]}", "{data["teamFirst"]}","{data["teamSecond"]}")')
    conn.commit()
    cur.execute('SELECT user_id FROM users')
    data = cur.fetchall() 
    for i in data:
        await bot.send_message(i[0], text="Доступная новая ставка!")
    conn.commit()
    await state.finish()
