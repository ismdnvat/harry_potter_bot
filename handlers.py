import random
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from config import VALID_SUBJECTS, FACULTIES, PLAYER_ROLE
from db import get_connection
from states import ProfileStates, QuizStates

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

conn = get_connection()
cursor = conn.cursor()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Настроить профиль', 'Редактировать профиль', 'Удалить профиль', 'Просмотреть информацию о себе')
    await message.answer(
        "Добро пожаловать в Гарри Поттер Опросник! Вы можете настроить свой профиль.",
        reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == 'Настроить профиль')
async def setup_profile(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Имя", callback_data='name'),
                 InlineKeyboardButton("Факультет", callback_data='faculty'),
                 InlineKeyboardButton("Курс", callback_data='year'),
                 InlineKeyboardButton("Роль в Квиддиче", callback_data='quidditch_role'),
                 InlineKeyboardButton("Оценки", callback_data='grades'))
    await message.answer('Выберите, что вы хотите настроить:', reply_markup=keyboard)
    await ProfileStates.SETTING_PROFILE.set()


@dp.callback_query_handler(state=ProfileStates.SETTING_PROFILE)
async def process_profile_setup(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == 'name':
        await callback_query.message.answer('Введите ваше имя:')
        await ProfileStates.SETTING_NAME.set()
    elif callback_query.data == 'faculty':
        await callback_query.message.answer('Хммм... куда же тебя распределить? 🤔')
        await distribute_faculty(callback_query.message, state)
    elif callback_query.data == 'year':
        keyboard = InlineKeyboardMarkup(row_width=2)
        for year in range(1, 8):
            keyboard.add(InlineKeyboardButton(str(year), callback_data=str(year)))
        await callback_query.message.answer('Выберите ваш курс:', reply_markup=keyboard)
        await ProfileStates.SETTING_YEAR.set()
    elif callback_query.data == 'quidditch_role':
        keyboard = InlineKeyboardMarkup(row_width=2)
        roles = ["Охотник", "Ловец", "Загонщик", "Вратарь", "Зритель"]
        for role in roles:
            keyboard.add(InlineKeyboardButton(role, callback_data=role.lower()))
        await callback_query.message.answer('Выберите вашу роль в Квиддиче:', reply_markup=keyboard)
        await ProfileStates.SETTING_QUIDDITCH_ROLE.set()
    elif callback_query.data == 'grades':
        keyboard = InlineKeyboardMarkup()
        subjects = ['Астрономия', 'Заклинания', 'Защита от Тёмных искусств', 'Зельеварение', 'История магии', 'Травология', 'Трансфигурация', 'Полёты на мётлах']
        for subject in subjects:
            keyboard.add(InlineKeyboardButton(subject, callback_data=subject.lower()))
        await callback_query.message.answer('Выберите предмет для оценки:', reply_markup=keyboard)
        await ProfileStates.CHOOSING_SUBJECT.set()


@dp.callback_query_handler(state=ProfileStates.CHOOSING_SUBJECT)
async def choose_subject(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(subject=callback_query.data)
    keyboard = InlineKeyboardMarkup(row_width=5)
    for grade in range(1, 11):
        keyboard.add(InlineKeyboardButton(str(grade), callback_data=str(grade)))
    await callback_query.message.answer('Выберите оценку от 1 до 10:', reply_markup=keyboard)
    await ProfileStates.SETTING_GRADE.set()

@dp.callback_query_handler(state=ProfileStates.SETTING_GRADE)
async def set_grade(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_data = await state.get_data()
    subject = user_data['subject']
    grade = int(callback_query.data)

    if subject not in VALID_SUBJECTS:
        await callback_query.message.answer('Неизвестный предмет.')
        return

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    if cursor.fetchone() is None:
        cursor.execute(f'INSERT INTO users (user_id, {VALID_SUBJECTS[subject]}) VALUES (?, ?)', (user_id, grade))
    else:
        cursor.execute(f'UPDATE users SET {VALID_SUBJECTS[subject]} = ? WHERE user_id = ?', (grade, user_id))

    conn.commit()
    await callback_query.message.answer(f'Оценка по предмету "{subject.capitalize()}" была обновлена на {grade}.')
    await state.finish()

@dp.message_handler(state=ProfileStates.SETTING_NAME)
async def set_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    name = message.text

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO users (user_id, name) VALUES (?, ?)', (user_id, name))
    else:
        cursor.execute('UPDATE users SET name = ? WHERE user_id = ?', (name, user_id))

    conn.commit()
    await message.answer(f'Ваше имя было обновлено на {name}.')
    await state.finish()

@dp.message_handler(state=ProfileStates.SETTING_FACULTY)
async def distribute_faculty(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    faculty_name, faculty_code = random.choice(list(FACULTIES.items()))

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO users (user_id, faculty) VALUES (?, ?)', (user_id, faculty_name))
    else:
        cursor.execute('UPDATE users SET faculty = ? WHERE user_id = ?', (faculty_name, user_id))

    conn.commit()

    photo = InputFile(f'img/{faculty_code}.jpg')
    await message.answer_photo(photo=photo, caption=f'Вы были распределены в {faculty_name}!')
    await state.finish()

@dp.callback_query_handler(state=ProfileStates.SETTING_YEAR)
async def set_year(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    year = int(callback_query.data)

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO users (user_id, year) VALUES (?, ?)', (user_id, year))
    else:
        cursor.execute('UPDATE users SET year = ? WHERE user_id = ?', (year, user_id))

    conn.commit()
    await callback_query.message.answer(f'Ваш курс был обновлен на {year}.')
    await state.finish()


@dp.callback_query_handler(state=ProfileStates.SETTING_QUIDDITCH_ROLE)
async def set_quidditch_role(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    quidditch_role = callback_query.data

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO users (user_id, quidditch_role) VALUES (?, ?)', (user_id, quidditch_role))
    else:
        cursor.execute('UPDATE users SET quidditch_role = ? WHERE user_id = ?', (quidditch_role, user_id))

    conn.commit()
    await callback_query.message.answer(f'Ваша роль в Квиддиче была обновлена на {quidditch_role}.')
    await state.finish()

@dp.message_handler(lambda message: message.text == 'Редактировать профиль')
async def edit_profile(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Имя", callback_data='edit_name'),
                 InlineKeyboardButton("Факультет", callback_data='edit_faculty'),
                 InlineKeyboardButton("Курс", callback_data='edit_year'),
                 InlineKeyboardButton("Роль в Квиддиче", callback_data='edit_quidditch_role'))
    await message.answer('Выберите, что вы хотите редактировать:', reply_markup=keyboard)
    await ProfileStates.EDITING_PROFILE.set()


@dp.callback_query_handler(state=ProfileStates.EDITING_PROFILE)
async def process_profile_editing(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == 'edit_name':
        await callback_query.message.answer('Введите новое имя:')
        await ProfileStates.EDIT_NAME.set()
    elif callback_query.data == 'edit_faculty':
        await callback_query.message.answer('Хммм... куда же тебя распределить? 🤔')
        await distribute_faculty(callback_query.message, state)
    elif callback_query.data == 'edit_year':
        keyboard = InlineKeyboardMarkup(row_width=2)
        for year in range(1, 8):
            keyboard.add(InlineKeyboardButton(str(year), callback_data=str(year)))
        await callback_query.message.answer('Выберите ваш новый курс:', reply_markup=keyboard)
        await ProfileStates.EDIT_YEAR.set()
    elif callback_query.data == 'edit_quidditch_role':
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(InlineKeyboardButton("Охотник", callback_data='Chaser'),
                     InlineKeyboardButton("Ловец", callback_data='Seeker'),
                     InlineKeyboardButton("Загонщик", callback_data='Beater'),
                     InlineKeyboardButton("Вратарь", callback_data='Keeper'),
                     InlineKeyboardButton("Не играю", callback_data='None'))
        await callback_query.message.answer('Выберите вашу новую роль в квиддиче:', reply_markup=keyboard)
        await ProfileStates.EDIT_QUIDDITCH_ROLE.set()

@dp.message_handler(state=ProfileStates.EDIT_NAME)
async def update_name(message: types.Message, state: FSMContext):
    name = message.text
    cursor.execute('UPDATE users SET name = ? WHERE user_id = ?', (name, message.from_user.id))
    conn.commit()
    await message.answer(f'Ваше имя изменено на {name}')
    await state.finish()


@dp.callback_query_handler(lambda c: c.data.isdigit(), state=ProfileStates.EDIT_YEAR)
async def update_year(callback_query: types.CallbackQuery, state: FSMContext):
    year = int(callback_query.data)
    cursor.execute('UPDATE users SET year = ? WHERE user_id = ?', (year, callback_query.from_user.id))
    conn.commit()
    await callback_query.message.answer(f'Ваш курс изменен на {year}')
    await state.finish()


@dp.callback_query_handler(lambda c: c.data in ['Chaser', 'Seeker', 'Beater', 'Keeper', 'None'], state=ProfileStates.EDIT_QUIDDITCH_ROLE)
async def update_quidditch_role(callback_query: types.CallbackQuery, state: FSMContext):
    role = callback_query.data
    cursor.execute('UPDATE users SET quidditch_role = ? WHERE user_id = ?', (role, callback_query.from_user.id))

    await callback_query.message.answer(f'Ваша роль в квиддиче изменена на: {PLAYER_ROLE[role]}')
    await state.finish()

@dp.message_handler(lambda message: message.text == 'Просмотреть информацию о себе')
async def view_profile(message: types.Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user_data = cursor.fetchone()

    if user_data:
        user_info = (
            f"Имя: {user_data[1]}\n"
            f"Факультет: {user_data[2]}\n"
            f"Курс: {user_data[3]}\n"
            f"Роль в Квиддиче: {PLAYER_ROLE[user_data[4]]}\n"
            f"Астрономия: {user_data[5]}\n"
            f"Заклинания: {user_data[6]}\n"
            f"Защита от Тёмных искусств: {user_data[7]}\n"
            f"Зельеварение: {user_data[8]}\n"
            f"История магии: {user_data[9]}\n"
            f"Травология: {user_data[10]}\n"
            f"Трансфигурация: {user_data[11]}\n"
            f"Полёты на мётлах: {user_data[12]}"
        )
    else:
        user_info = "Ваш профиль не найден. Пожалуйста, настройте его сначала."

    await message.answer(user_info)


@dp.message_handler(lambda message: message.text == 'Редактировать профиль')
async def edit_profile(message: types.Message):
    await message.answer('Редактирование профиля пока не реализовано.')


@dp.message_handler(lambda message: message.text == 'Удалить профиль')
async def delete_profile(message: types.Message):
    user_id = message.from_user.id
    cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    conn.commit()
    await message.answer('Ваш профиль был удален.')