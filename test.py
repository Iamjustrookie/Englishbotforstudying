from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import asyncio
from config import API_BOT

bot = Bot(token=API_BOT)
dp = Dispatcher()

def get_start_button():
    get_start_button = ReplyKeyboardBuilder()
    get_start_button.add(KeyboardButton(text='Получить сообщение номер 1'))
    get_start_button.add(KeyboardButton(text='Получить сообщение номер 2'))
    get_start_button.add(KeyboardButton(text='Назад в главное меню'))
    return get_start_button.as_markup(resize_keyboard=True)

@dp.message(Command('start'))
async def start_command(message: Message): 
    await message.answer('Привет выбери кнопку', reply_markup=get_start_button())

@dp.message(lambda message: message.text == 'Получить сообщение номер 1')
async def get_first_message(message: Message): 
    await message.answer('Твое первое сообщение')

@dp.message(lambda message: message.text == 'Получить сообщение номер 2')
async def get_first_message(message: Message): 
    await message.answer('Твое второе сообщение')

@dp.message(lambda message: message.text == 'Назад в главное меню')
async def back_to_main(message: types.Message):
    await message.answer('Главное меню:', reply_markup=get_start_button())

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())