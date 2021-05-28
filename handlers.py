from asyncio.windows_events import NULL
from typing import Set
from aiogram import types
from aiogram.dispatcher.filters import Text
from keyboards import keyboard
from config import *
from contextlib import suppress
from aiogram.utils.exceptions import (MessageToEditNotFound, MessageCantBeEdited, MessageCantBeDeleted,MessageToDeleteNotFound)
import sqlite3, asyncio
from states.createMatch import CreateFight, SetBet, SetWinner
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
    if message.from_user.id != admin_id:
        await message.reply("Хотите поставить на матч?\nНапишите - /allMatches", reply_markup=keyboard.allCommands)
    else:
        await message.reply("Хотите поставить на матч?\nНапишите - /allMatches", reply_markup=keyboard.allCommandsAdmin)


@dp.message_handler(Text(equals=["Баланс"]))
async def send_balance(message: types.Message):
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    man_id = message.from_user.id
    cur.execute(f"SELECT user_balance FROM users WHERE user_id = {man_id}")
    data = cur.fetchone()
    conn.commit()
    await message.reply(f"Ваш счет: {data[0]}", reply_markup=keyboard.allCommands)

async def delete_message(message: types.Message, sleep_time: int = 0):
    await asyncio.sleep(sleep_time)
    with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
        await message.delete()

@dp.message_handler(Text(equals=["Все матчи"]))
async def send_allMatch(message: types.Message):
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    man_id = message.from_user.id
    cur.execute(f'SELECT * FROM matches')
    data = cur.fetchall()
    for i in data:
        keyboard_markup = types.InlineKeyboardMarkup(row_width=2)
        text_and_data = (
            (i[2], f"{i[2]}|{i[0]}"),
            (i[3], f"{i[3]}|{i[0]}"),
        )
        row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
        keyboard_markup.row(*row_btns)
        await message.reply(f"{i[1]}\n{i[2]} vs {i[3]}", reply_markup=keyboard_markup, reply=False)
    man_id = message.from_user.id
    conn.commit()
    cur.execute(f"SELECT * from users WHERE user_id = {man_id}")
    data = cur.fetchone()
    if data[2] > 0:
        msg = await message.reply("Кто выиграет?", reply=False)
    else:
        msg = await message.reply("На вашем счету недостаточно средств\nПроверить баланс /balance", reply_markup=keyboard.allCommands)
    conn.commit()
    asyncio.create_task(delete_message(msg, 30))


@dp.callback_query_handler()
async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    varb = query.data.split("|")
    cur.execute('CREATE TABLE IF NOT EXISTS bets(id INTEGER PRIMARY KEY, user_id INTEGER, user_choice INTEGER, user_bet BIGINT, id_match INTEGER)')
    conn.commit()
    cur.execute(f'SELECT id FROM bets WHERE user_id={query.from_user.id} AND id_match={varb[1]}')
    data = cur.fetchone()
    cur.execute(f'SELECT user_balance FROM users WHERE user_id = {query.from_user.id}')
    balanceuser = cur.fetchone()
    if data==None:
        cur.execute(f'INSERT INTO bets VALUES(NULL,"{query.from_user.id}", "{varb[0]}", {query.from_user.id}, "{varb[1]}")')
        text = 'Отлично сработано! Выберите сумму'
        conn.commit()
        await bot.send_message(query.from_user.id, text , reply_markup=keyboard.betOnmatch)
        await SetBet.B1.set()
    else:
        await bot.send_message(query.from_user.id,text="Вы уже поставили на этот матч", reply_markup=keyboard.allCommands)


@dp.message_handler(state=SetBet.B1)
async def inline_kb_answer_callback_handler(message: types.Message, state: FSMContext):
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    man_id = message.from_user.id
    cur.execute(f'SELECT user_bet FROM bets WHERE user_id={man_id} AND user_bet = {man_id}')
    data = cur.fetchone()
    if data[0] == man_id:
        cur.execute(f'SELECT * FROM users WHERE user_id={man_id}')
        data = cur.fetchone()
        if message.text == '1000' and data[2]>=1000:
            text = 'Спасибо за ставку!'
            cur.execute(f'UPDATE users SET user_balance={data[2]-1000} WHERE user_id={man_id}')
            cur.execute(f"UPDATE bets SET user_bet={1000} WHERE user_id={man_id}")
        elif message.text == '500' and data[2]>=500:
            text = 'Спасибо за ставку!'
            cur.execute(f'UPDATE users SET user_balance={data[2]-500} WHERE user_id={man_id}')
            cur.execute(f'UPDATE bets SET user_bet={500} WHERE user_id={man_id}')
        else:
            if message.text == '250' and data[2]>=250:
                text = 'Ха, клоун! Поставь ты больше'
                cur.execute(f'UPDATE users SET user_balance={data[2]-250} WHERE user_id={man_id}')
                cur.execute(f'UPDATE bets SET user_bet={250} WHERE user_id={man_id}')
            else:
                text = 'На вашем счету нет столько средств! Пополните счет'
                cur.execute(f'DELETE FROM bets WHERE user_bet = {man_id}')
        conn.commit()
    else:
        text = 'Вы уже ставили на этот матч'
    await bot.send_message(message.from_user.id, text, reply_markup=keyboard.allCommands)
    await state.finish()



@dp.message_handler(Text(equals=["Список моих ставок"]))
async def send_listbet(message: types.Message):
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM bets WHERE user_id = {message.from_user.id}')
    data = cur.fetchall()
    conn.commit()
    for i in data:
        await bot.send_message(message.from_user.id, text = f"{i[2]} - {i[3]}")



@dp.message_handler(Text(equals=["Winner"]))
async def setWinner(message: types.Message):
    if message.from_user.id == admin_id:
        await bot.send_message(admin_id, text='Укажи название матча!')
        await SetWinner.first()

@dp.message_handler(state=SetWinner.W1)
async def nameMatch(message: types.Message, state: FSMContext):
    await state.update_data(match=message.text)
    await message.answer("Кто выиграл и проиграл?", parse_mode="HTML")
    await SetWinner.next() 

@dp.message_handler(state=SetWinner.W2)
async def nameMatch(message: types.Message, state: FSMContext):
    await state.update_data(matchWinner=message.text)
    data = await state.get_data()
    wl = data['matchWinner']
    wl = wl.split()
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM bets')
    www = cur.fetchall()
    conn.commit()
    for i in www:
        if wl[0] == i[2]:
            cur.execute(f'SELECT user_balance FROM users WHERE user_id = {i[1]}')
            balance_user = cur.fetchone()
            cur.execute(f'UPDATE users SET user_balance={balance_user[0] + (i[3]*2)} WHERE user_id={i[1]}')
            cur.execute(f'DELETE FROM bets WHERE id = {i[0]}')
            cur.execute(f'DELETE FROM matches WHERE firstTeam LIKE "{i[2]}" OR secondTeam LIKE "{i[2]}"')
        else:
            if wl[1] == i[2]:
                cur.execute(f'DELETE FROM bets WHERE id = {i[0]}')
    conn.commit()
    cur.execute('SELECT user_id FROM users')
    data = cur.fetchall() 
    for i in data:
        await bot.send_message(i[0], text="Матч окончен!\n Проверьте баланс")
    conn.commit()
    await state.finish()


@dp.message_handler(Text(equals=["CreateMatch"]))
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
