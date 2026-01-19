# Задача:

  - Создать тг бота, который поможет изучать английский :mortar_board:
  - Добавить основные вопросы английского языка на которые пользователю нужно будет ответить, имея 4 варианта ответа, среди которых только 1 верный
  - Подключить AI агента для практики
  - Добавить основные правила английского языка

# Библиотеки: 

  ```python
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, FSInputFile, KeyboardButton, Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import random
import yaml
import psycopg2
import asyncio
from app.handlers import router # импортируем router для ai агента
```

# Структура тг-бота: 

+ AI помощник на моделе нейросети DeepSeek
+ Тест(вопрос - ответ). С базы данных достаются уникальные вопросы и задаются пользователю, далее ответы на эти вопросы сравниваются с записями в бд
+ Основные правила английского языка. Перечень всех самых важных правил, используемых в английском языке на базовом уровне
