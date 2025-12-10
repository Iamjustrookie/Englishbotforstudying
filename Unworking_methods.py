#Уже использовал или не могу использовать: 

""" Первый код: 
@dp.message(Text(equals="Назад в главное меню", ignore_case=True)) # Используем Text, не использовал т.к в новой версии aiogram такого метода нету
async def back_to_main(message: types.Message):
    await message.answer("Главное меню:", reply_markup=get_start_keyboard()) """ 

""" Второй код: 
@dp.message(F.text == "Назад в главное меню") # Используем F # Ошибку не выводит, но почему-то после нажатия кнопка обрабатывается роутером и deep seek начинает отвечать на вопрос "вернуться в главное меню"
async def back_to_main(message: types.Message):
    await message.answer("Главное меню:", reply_markup=get_start_keyboard()) """ 

""" Третий код: 
@dp.callback_query_handler(text="Назад в главное меню") # Не работает на новой версии aiogram
async def send_random_value(call: types.CallbackQuery):
    await call.answer(text="Спасибо, что воспользовались ботом!", show_alert=True)
    # или просто await call.answer() """

""" Почти такой же код как и  второй: 
@dp.message(lambda message: message.text == 'Назад в главное меню') # Ошибку не выводит, но почему-то после нажатия кнопка обрабатывается роутером и deep seek начинает отвечать на вопрос "вернуться в главное меню"
async def back_to_main(message: types.Message):
    await message.answer('Главное меню:', reply_markup=get_start_keyboard())
 """