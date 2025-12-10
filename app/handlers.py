# Мой переделанный код
#Основная часть кода была взята с ютуб канала https://www.youtube.com/watch?v=lUy3ZqhnpKQ&t=1566s
from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode 

from app.generate import ai_generate
router = Router()

class Gen(StatesGroup):
    wait = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):  
    await message.answer('Привет! Напиши свой запрос')
    await state.set_state(None)  

@router.message(Gen.wait)
async def stop_flood(message: Message, state: FSMContext):
    await message.answer('Подождите, ваш запрос генерируется.....')
    await state.clear()  

@router.message()
async def generating(message: Message, state: FSMContext):
    await state.set_state(Gen.wait)

    await stop_flood(message, state) 

    try:  # Проверка на длину текста (она должна быть меньше 4096 символов)
        response = await ai_generate(message.text)
        if len(response) > 4096:
            parts = [response[i:i + 4096] for i in range(0, len(response), 4096)]

            for part in parts:
                await message.answer(part)  
        else:
 
            await message.answer(response)
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")

    finally:
       await state.clear() # очищаем состояние
