from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, FSInputFile, KeyboardButton, Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import random
import yaml
import psycopg2
import asyncio
from app.handlers import router # импортируем router для ai агента

with open('text.yaml', 'r') as file: # открываем yaml файл с данными
    config = yaml.safe_load(file)

db_config = config['database']
bot_token = config['bot']['token']
user_link = config['user_id']['user_idlink']

bot = Bot(token=bot_token)
dp = Dispatcher()

# Глобальные словари для хранения данных
user_correct_answers = {} # словарь с правильными ответами
user_last_question = {} # словарь с последним вопросом
user_current_question = {}
ai_mode_activate = {}
users_info = set()

def get_start_keyboard(): # создаем reply клавиатуру
    keyboard_builder = ReplyKeyboardBuilder()
    keyboard_builder.add(KeyboardButton(text='AI обучение'))
    keyboard_builder.add(KeyboardButton(text='Тест (вопрос - выбор ответа на английском)'))
    keyboard_builder.add(KeyboardButton(text='Основные правила на английском'))
    return keyboard_builder.as_markup(resize_keyboard=True)

@dp.message(Command('start'))
async def start_command(message: Message):
    await message.answer('Привет! Я бот который поможет тебе в изучении английского.\n Вы можете отправить боту сообщение "/start" и обновить бота, а также вы можете вернуться в меню, если напишишете "/menu".\n Теперь выберите режим работы с ботом:', reply_markup=get_start_keyboard())

@dp.message(Command('id'))
async def id_command(message: Message):
    user = message.from_user.username
    if user not in users_info:
        users_info.add(str(user))
        await bot.send_message(chat_id=user_link, text=f'Пользователь {user} добавлен.' )
        await message.answer(f'Привет, {user}!')

@dp.message(Command('menu'))
async def function_menu(message: types.Message):
    await message.answer('Вы перешли в главное меню.', reply_markup=get_start_keyboard())

@dp.message(F.text == "Назад в главное меню") 
async def back_to_main(message: types.Message):
    await message.answer("Вы перешли в главное меню.", reply_markup=get_start_keyboard())

async def get_random_question(user_id): # извлекаем рандомный вопрос
    try:
        connection = psycopg2.connect( # обращаемся к базе данных
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['db_name']
        )

        with connection.cursor() as cursor: # извлекаем данные из базы данных
            cursor.execute("SELECT question FROM questions")
            all_questions = [q[0] for q in cursor.fetchall()]

            last_question = user_last_question.get(user_id) # получаем последний вопрос
            available_questions = [q for q in all_questions if q != last_question] # создаем список неповторяющихся вопросов

            if not available_questions:
                available_questions = all_questions

            random_question = random.choice(available_questions) 

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT answer1, answer2, answer3, answer4, correct_answer FROM questions WHERE question=%s", # извлекаем все данные где вопрос равен рандомному вопросу
                (random_question,)
            )
            answer1, answer2, answer3, answer4, correct_answer = cursor.fetchone()

        connection.close()

        user_last_question[user_id] = random_question

        return random_question, answer1, answer2, answer3, answer4, correct_answer

    except Exception as ex:
        print('Мы получили ошибку: ', ex)
        return None

async def send_question(chat_id, message_id=None):
    question_data = await get_random_question(chat_id)
    if question_data is None or question_data[0] is None: # Если функция вернула нам значение None или вопрос is None
        await bot.send_message(chat_id, "Все все вопросы закончились, можешь перезапустить бот кнопкой /start, если хочешь еще поотвечать на вопросы!")
        return

    question, answer1, answer2, answer3, answer4, correct_answer = question_data

    keyboard = InlineKeyboardMarkup(inline_keyboard=[ # клавиатура с ответами на вопросы
        [InlineKeyboardButton(text=answer1, callback_data=f"answer_{answer1}")],
        [InlineKeyboardButton(text=answer2, callback_data=f"answer_{answer2}")],
        [InlineKeyboardButton(text=answer3, callback_data=f"answer_{answer3}")],
        [InlineKeyboardButton(text=answer4, callback_data=f"answer_{answer4}")],
    ])

    user_correct_answers[chat_id] = correct_answer
    user_current_question[chat_id] = question

    try:
        if message_id:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f'Твой вопрос: {question}', # выводим вопрос для пользователя
                reply_markup=keyboard # присоединяем kb с ответами на вопросы
            )
        else:
            await bot.send_message(chat_id, f'Твой вопрос: {question}', reply_markup=keyboard)
    except Exception as e:
        await bot.send_message(chat_id, f'Твой вопрос: {question}', reply_markup=keyboard) # обработка ошибки если пользователь изменил или удалил сообщение

@dp.message(lambda message: message.text == 'AI обучение')
async def ai_learning_handler(message: types.Message):
        await message.answer(f'Бот запущен! Введите ваш запрос, а наш виртуальный помощник попробует вам помочь.')
        
@dp.message(lambda message: message.text == 'Тест (вопрос - выбор ответа на английском)')
async def test_handler(message: types.Message):
    await send_question(message.chat.id)

@dp.message(lambda message: message.text == 'Основные правила на английском')
async def english_rules_handler(message: types.Message):
    rules_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text='Времена Английский')],
            [types.KeyboardButton(text='Артикли')],
            [types.KeyboardButton(text='Модальные глаголы')],
            [types.KeyboardButton(text='Правила построения предложений')],
            [types.KeyboardButton(text='Местоимения')],
            [types.KeyboardButton(text='Назад в главное меню')] 
        ],
        resize_keyboard=True
    )
    await message.answer('Выбирете раздел граматики:', reply_markup=rules_keyboard)

@dp.message(lambda message: message.text == 'Времена Английский')
async def times(message: types.Message):

    await message.answer('Всего в английском 12 времен: \n\nПервое время - это <b>Present Simple</b>. Оно используется для описания действий, который происходят <b>на регулярной основе</b> (<b>Пример:</b> Он готовит - He <b>cooks</b>), а также для <b>описания фактов</b> и <b>общей информации</b>(Собака друг человека - Dog <b>is</b> a friend for person \n\n <b>Слова маркеры:</b> often - часто, always - всегда, never - никогда, regularly - регулярно, sometimes - иногда и другие \n\n <b>Вспомогательный глагол Present Simple:</b> do/does, в отрицательных формах мы добавляем к вспомогательному глаголу not. Рассмотрим таблицу: ', parse_mode='html')
    photo_path1 = "pictures/Вспомогательный глагол do in Present Simple.jpg"
    photo1 = FSInputFile(photo_path1)
    await bot.send_photo(chat_id = message.chat.id, photo=photo1)

    await message.answer('Второе время - это <b>Past Simple</b>. Оно используется для того чтобы рассказать о действиях, которые произошли <b>в прошлом</b>.(<b>Пример:</b> I played this game - Я играл в эту игру, I <b>came</b> home yesterday - Я пришел домой вчера). \n\n<b>Слова маркеры:</b> yesterday, last year, ten years ago и другие.\n\nВспомогательный глагол в past simple - <b>did</b>, также как и с do формирует отрицательную форму при помощи not. Рассмотрим виды предложений в Past Simple:', parse_mode='html')
    photo_path2 = "pictures/Past Simple.jpg"
    photo2 = FSInputFile(photo_path2)
    await bot.send_photo(chat_id = message.chat.id, photo=photo2)

    await message.answer('Третье время - это <b>Future Simple</b>. Оно используется для того чтобы рассказать о действия которое будет <b>произойдено в будущем</b>.(<b>Пример:</b> I <b>will do</b> it - Я сделаю это).\n\n<b>Временные маркеры:</b> tomorrow, next summer, in ten years, in the future.\n\n Предложения в Present Future используют вспомогательный глагол <b>will, также как и с will формирует отрицательную форму при помощи not</b>. Рассмотрим таблицу с формообразованием: ', parse_mode='html')
    photo_path3 = "pictures/Future Simple.jpg"
    photo3 = FSInputFile(photo_path3)
    await bot.send_photo(chat_id=message.chat.id, photo=photo3)

    await message.answer('Четвертое время - это <b>Present Continuous</b>. Оно используется для действия, <b>совершающееся сейчас, в данный момент</b>(<b>Пример:</b> I <b>am eating</b> right now).\n\nДействие,которое охватывает отрезок времени <b>в настоящем</b>.(She <b>is doing</b> youga today from 7 am till 9 am - Она занимается йогой сегодня с 7 до 9), а также действие, которое запланировано, и при этом нам известны время и место.(I <b>am meeting</b> her tonight after favourite Italian restaurant(Я встречаюсь с ней  сегодня вечером в ее любимом итальянском ресторане).\n\n<b>Временные марки Present Continuous:</b> now, at the moment, right now. <b>Вспомогательный глагол Present Continuous:</b> 3 формы TO BE(am, are, is) + глагол с ing окончанием.\n\nРассмотрим виды предложений с Present Continuous:', parse_mode='html')
    photo_path4 = "pictures/Present Continuous.jpg"
    photo4 = FSInputFile(photo_path4)
    await bot.send_photo(chat_id=message.chat.id, photo=photo4)

    await message.answer('Пятое время - это <b>Past Continuous</b>. Оно используется для <b>продолжительного действия, которое происходило в прошлом</b> в какой-то определенный период.(<b>Пример:</b> I was watching TV).\n\nПроцесс в <b>прошлом</b>, <b>во время которого</b> произошло другое действие .(I <b>was watching</b> a movie, when someone knocked at the door - Я смотрела кино, когда кто-то постучал в дверь).\n\n<b>Временные марки Present Continuous:</b> all day long, all the time, the whole day, from 7 till 10. <b>Вспомогательный глаголы Past Continuous:</b> 2 формы TO BE(was - был(а), were - были) + глагол с ing окончанием, глаголы was и were могут использоваться с частицей not.\n\nРассмотрим виды предложений с Past Continuous:', parse_mode='html')
    photo_path5 = 'pictures/Past Continious.jpg'
    photo5 = FSInputFile(photo_path5)
    await bot.send_photo(chat_id=message.chat.id, photo=photo5)

    await message.answer('Шестое время - <b>Future Continuous</b>. Используется, когда говорим о <b>продолжительном действии, которое будет происходить в будущем</b>(<b>Пример:</b> This time tomorrow I <b>will be runing</b> at the park.\n\n<b>Временные марки Future Continuous:</b> at 5 pm tomorrow - завтра в 5 часов вечера, at this time next week - в это время на следующей неделе, in an hour - через час.<b>Вспомогательный глагол Future Continuous:</b> will be ,так же для образования отрицательной формы используем not.Таблица с формами глаголов в Future Continuous: ', parse_mode="html")
    photo_path6 = 'pictures/Future Continuous.jpg'
    photo6 = FSInputFile(photo_path6)
    await bot.send_photo(chat_id=message.chat.id, photo=photo6)

    await message.answer('Седьмое время - <b>Present Perfect</b>. Используется для обозначения действия, которое <b>завершено в прошлом но связано с настоящим</b> посредством результата(<b>Пример:</b> I <b>have finished</b> my home task, so now we can go for a run(Я закончил с домашним задание, так что мы можем пойти на пробежку сейчас). Также, это время используется для характеристики действия, которое началось в прошлом, но продолжается и в настоящий момент(<b>Пример:</b> I <b>have lived</b> in this area for 2 years - Я живу в этом районе 2 года).\n\n<b>Временные маркеры:</b> just - просто, already - уже, yet - еще, ever когда-либо. <b>Вспомогательные глаголы</b> have, has мы также используем частицу not для образования отрицания.\n Формула образования - Подлежащее + have/has + not(если нужно) + третья форма глагола\n\nТаблица с формами:', parse_mode="html")
    photo_path7 = 'pictures/Present Perfect.jpg'
    photo7 = FSInputFile(photo_path7)
    await bot.send_photo(chat_id=message.chat.id, photo=photo7)

    await message.answer('Восьмое время - Past Perfect. Это действия, которые завершены <b>до какого-то момента в прошлом.</b>(<b>Пример:</b> The rain <b>had stopped</b> before she woke bp - дождь завершился до того, как она проснулась). <b>Временные маркеры:</b> by that time, by Monday. <b>Вспомогательный глагол</b> - had ,также с помощью not можем образовывать отрицание.\n\nФормула образования: Подлежащие + вспом глагол + глагол + not(если нужно) + глагол в третьей форме.\n\nТаблица с формами:', parse_mode='html')
    photo_path8 = 'pictures/Past Perfect.jpg'
    photo8 = FSInputFile(photo_path8)
    await bot.send_photo(chat_id=message.chat.id, photo=photo8)

    await message.answer('Девятое время - <b>Future Perfect</b>. Действие, которое <b>должно закончиться к определенному времени в будущем или когда мы думаем, что действие, скорее всего, должно было завершиться к определенному моменту в будущем</b>(<b>Пример:</b> I <b>will have finished</b> my essay by 4 pm tonight - Я закончу свое эссе к 4 часам вечера).\n\n<b>Временные маркеры Future Perfect:</b> <b>by that time</b> - к тому времени, <b>by Sunday</b> - к воскресенью, <b>by 2030</b> - к 2030. <b>Вспомогательный глагол</b> - <b>will have</b>. Формула: Подлежащее + вспомогательный + not(если нужно) + глагол в форме 3 лица.Таблица с формами:', parse_mode="html")
    photo_path9 = 'pictures/Future Perfect.jpg'
    photo9 = FSInputFile(photo_path9)
    await bot.send_photo(chat_id=message.chat.id, photo=photo9)

    await message.answer('Десятое время - <b>Present Perfect Continuous</b>. Описывает <b>действие, начавшееся в прошлом и продолжающееся на момента речи или завершившееся длительное действие, результат которого влияет на настоящее</b>.(<b>Пример:</b> I <b>have been working</b> for 6 hours already - Я уже работаю 6 часов. <b>Временные марки:</b> <b>for a week</b>, <b>since morning</b>, <b>lately</b>, <b>all my life</b>.\n\n<b>Вспомогательный глагол:</b> <b>have/has been</b>. <b>Формула</b>: Подлежащее + вспомогательный глагол + not(если нужно) + глагол в третьей форме. Таблица с формами:', parse_mode="html")
    photo_path10 = 'pictures/Present Perfect Continuous.jpg'
    photo10 = FSInputFile(photo_path10)
    await bot.send_photo(chat_id=message.chat.id, photo=photo10)

    await message.answer('Одинадцатое время - <b>Past Perfect Continuous</b>. Описывает процесс <b>до определенного момента в прошлом</b>(<b>Пример</b>: I <b>had been working</b> on my assignment for 2 hours when my flatmate came). \n\n<b>Временные маркеры:</b> <b>for six months</b> - в течение 6 месяцев, <b>for a long time</b> - в течение долгого времени, <b>since 7 hours</b> - с 7 часов', parse_mode="html")
    photo_path11 = 'pictures/Past Perfect Continuous.jpg'
    photo11 = FSInputFile(photo_path11)
    await bot.send_photo(chat_id=message.chat.id, photo=photo11)

    await message.answer('Двенадцатое время - <b>Fture Perfect Continuous</b>.Употребляется, когда мы описываем <b>продолжительное действие</b>, которое начнется <b>в будущем</b> и будет происходить <b>до определенного момента</b>(<b>Пример</b>: He <b>will have been</b> skiing in Switzerland for a week when she joins him - Он будет кататься на лыжах в Швейцарию целую неделю, когда она присоединиться к нему). \n\n<b>Временные маркеры:</b> <b>by the end of the hour/day/month</b> - к концу часа, дня, месяца, <b>till/until</b> - пока не, <b>for 2 hours/months/years</b> - уже 2 часа, месяца, года. <b>Вспомогательный глагол</b> - wil have. <b>Формула:</b> Подлежащее + вспомогательный + not(если нужно) + глагол с ing окончанием. Таблица с формами:', parse_mode="html")
    photo_path12 = 'pictures/Future Perfect Continuous.jpg'
    photo12 = FSInputFile(photo_path12)
    await bot.send_photo(chat_id=message.chat.id, photo=photo12)

@dp.message(lambda message: message.text == 'Артикли')
async def articles(message: types.Message):

    await message.answer('Основные артикли: <b>an</b>, <b>the</b>, <b>а</b>.\nУпотребляется, если говорим о чем-то определенном.\n\nЕсть слово после артикля имеет <b>гласный звук</b> - мы используем <b>an</b>, если <b>согласный</b> - <b>a</b>.(<b>Пример:</b> I am <b>a</b> stranger - Я не знакомец, It is <b>an</b> advice - Это совет).\n\nТаблица артиклей:', parse_mode="html")
    photo_articles = 'pictures/Articles.jpg'
    photoarticles = FSInputFile(photo_articles)
    await bot.send_photo(chat_id=message.chat.id, photo=photoarticles)

    await message.answer('Особенные случаи употребления <b>определененого артикля</b>: ', parse_mode="html")
    photo_esspecial_articles = 'pictures/esspecial_for_articles.jpg'
    photo_articles_sp = FSInputFile(photo_esspecial_articles)
    await bot.send_photo(chat_id=message.chat.id, photo=photo_articles_sp)

@dp.message(lambda message: message.text == 'Модальные глаголы')
async def modal_verbs(message: types.Message):

    await message.answer('К модальным глаголам относятся: <b>can</b>, <b>could</b>, <b>may</b>, <b>might</b>, <b>will</b>, <b>shall</b>, <b>would</b>, <b>should</b>, <b>must</b>. Разберем модальный глагол <b>can</b>: ', parse_mode="html")
    photo_can = 'pictures/modal_verb_can.jpg'
    photo_can_sp = FSInputFile(photo_can)
    await bot.send_photo(chat_id=message.chat.id, photo=photo_can_sp)

    await message.answer('Разберем глаголы <b>may</b>, <b>might</b>: 1.<b>May</b> - используется для просьб, разрешений также как и can(только это слово чаще всего используется в <b>формальной обстановке</b>)', parse_mode="html")

    await message.answer('Разберем модальные глаголы <b>will</b>(<b>would</b> - форма глагола <b>will</b>), <b>should</b> и <b>ought to</b>.Разберем глагол <b>will</b>: ', parse_mode="html")
    photo_will_shall = 'pictures/modal_verbs_will.jpg'
    photo_will = FSInputFile(photo_will_shall)
    await bot.send_photo(chat_id=message.chat.id, photo=photo_will)

    await message.answer('Разбрем глаголы <b>should</b> и <b>ought to</b>: ', parse_mode="html")
    photo_ought_should = 'pictures/Modal_verbs_should_oughtto.jpg'
    photo_ought_should_sd = FSInputFile(photo_ought_should)
    await bot.send_photo(chat_id=message.chat.id, photo=photo_ought_should_sd)

    await message.answer('Разберем модальный глагол <b>must</b>. <b>Must</b> - выражает <b>обязательство</b> и <b>необходимость</b>(<b>Пример</b>: We must finish this project by October - Мы должны закончить этот проект к октябрю).', parse_mode="html")

    await message.answer('Разберем глагол <b>have to</b>:', parse_mode="html")
    photo_have_to = 'pictures/modal_verb_haveto.jpg'
    photo_have_to_sd = FSInputFile(photo_have_to)
    await bot.send_photo(chat_id=message.chat.id, photo=photo_have_to_sd)

@dp.message(lambda message: message.text == 'Правила построения предложений')
async def rules_create(message: types.Message):
    await message.answer(f'Всего есть <b>несколько</b> порядков построения предложений.\n\n<b>Первый - прямой порядок</b>.\nФормула1: определение(или перед подлежащим(необязательно)) + подлежащее + определение(или после(необязательно)) + сказуемое + дополнение + обстоятельство(по ситуации). <b>Примеры:</b> My mother is a great woman, Linda never touches me. \n\n<b>Непрямой порядок слов</b> - используется в вопросах, повелительных высказываниях и высказываниях. <b>Примеры:</b> When you come home?(Когда ты пришел домой) - вопрос, Vlad, come here!(Влад иди сюда) - повеление, The view is nice!(хороший вид) - восклицание\n\n<b>Конструкция:</b> There is, there are. Примеры: There is a spoon on the table(Ложка на столе)', parse_mode="html")

@dp.message(lambda message: message.text == 'Местоимения')
async def pronoun(message: types.Message):
    await message.answer(f'Есть всего несколько видов местоимений: 1) <b>личные</b>, 2) <b>притяжательные</b>, 3) <b>возвратные</b>. Примеры с личными местоимениями: <b>I</b> am student, <b>She</b> has gone to the USA, Tell <b>me</b> about it, Can <b>you</b> support me?', parse_mode="html")
    photo_pronouns_personal = 'pictures/personal_pronouns.jpg'
    photo_pronouns_p = FSInputFile(photo_pronouns_personal)
    await bot.send_photo(chat_id=message.chat.id, photo=photo_pronouns_p)

    await message.answer(f'Примеры с притяжательными местоимениями: This is <b>my</b> car, It is <b>his</b> dog', parse_mode="html")
    photo_pronouns = 'pictures/притяжательные местоимения.jpg'
    photo_p = FSInputFile(photo_pronouns)
    await bot.send_photo(chat_id=message.chat.id, photo=photo_p)

    await message.answer(f'Примеры с возвратными местоимениями: I do it <b>myself</b>, He needs to do it <b>himself</b>', parse_mode="html")
    photo_reflexive = 'pictures/reflexive pronouns.jpg'
    photo_r = FSInputFile(photo_reflexive)
    await bot.send_photo(chat_id=message.chat.id, photo=photo_r)

@dp.message(lambda message: message.text=='Неправильные глаголы')
async def wrong_verbs(message: types.Message):
    await message.answer(f'Основная таблица с неправильными глаголами: ')
    photo_wrong_verbs_part1 = 'pictures/wrong_verbs_part1.jpg'
    photo_part1 = FSInputFile(photo_wrong_verbs_part1)
    await bot.send_photo(chat_id=message.chat.id, photo=photo_part1)

    photo_wrong_verbs_part2 = 'pictures/wrong_verbs_part2.jpg'
    photo_part2 = FSInputFile(photo_wrong_verbs_part2)
    await bot.send_photo(chat_id=message.chat.id, photo=photo_part2)

    photo_wrong_verbs_part3 = 'pictures/wrong_verbs_part3.jpg'
    photo_part3 = FSInputFile(photo_wrong_verbs_part3)
    await bot.send_photo(chat_id=message.chat.id, photo=photo_part3)

    photo_wrong_verbs_part4 = 'pictures/wrong_verbs_part4.jpg'
    photo_part4 = FSInputFile(photo_wrong_verbs_part4)
    await bot.send_photo(chat_id=message.chat.id, photo=photo_part4)

    photo_wrong_verbs_part5 = 'pictures/wrong_verbs_part5.jpg'
    photo_part5 = FSInputFile(photo_wrong_verbs_part5)
    await bot.send_photo(chat_id=message.chat.id, photo=photo_part5)
    
@dp.callback_query(F.data.startswith('answer_')) # декоратор срабатывающий на кнопки с ответами 
async def handle_answer(callback: CallbackQuery):
    user_id = callback.from_user.id
    selected_answer = callback.data.replace('answer_', '') # убираем answer_ и получаем "чистый" ответ

    if user_id in user_correct_answers: # проверка правильности 
        correct_answer = user_correct_answers[user_id]
    if selected_answer == correct_answer: # если выбранный ответ правильный
        try:
            connection = psycopg2.connect(
                host=db_config['host'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['db_name']
            )

            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM questions WHERE question = %s", # удаляем информацию по тем вопросам, которые были уже заданы
                    (user_current_question[user_id],)
                )
                connection.commit()

                connection.close()

        except Exception as ex:
            print(f'Mistake - {ex}')

        if user_id in user_correct_answers: # очищаем данные 
            del user_correct_answers[user_id]
        if user_id in user_current_question: # очищаем данные
            del user_current_question[user_id]

        await send_question(user_id, callback.message.message_id) # отправляем новый вопрос 
        await callback.answer("Правильно!")
    else:
        await callback.answer("Неправильно!")

@dp.message(lambda message: message.text == 'Назад в главное меню')
async def back_to_main(message: types.Message):
    await message.answer('Главное меню:', reply_markup=get_start_keyboard()) # возвращаемся в исходное положение для пользователя 

async def main(): 
    dp.include_router(router) # подключает к диспетчеру наш роутер
    await dp.start_polling(bot)
    
if __name__ == '__main__':
    asyncio.run(main())
