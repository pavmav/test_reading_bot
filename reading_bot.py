import logging
import asyncio
import time
import urllib
from aiogram.utils.markdown import text, bold, italic, code, pre
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
import pickle
import os
from os import listdir
from os.path import isfile, join
from aiogram import Bot, Dispatcher, executor, types
from books_handler import tokenize_file_nltk
import config
import os

API_TOKEN = os.getenv('API_TOKEN', '') #config.API_TOKEN
DELAY_FOR_REMINDER_CHECK = 60
DELAY_FOR_REMINDER = 65
REMINDER_MESSAGES_NUMBER = 3

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

button_1 = KeyboardButton('/>')
button_2 = KeyboardButton('/>>')
button_3 = KeyboardButton('/>>>')
kb = ReplyKeyboardMarkup(resize_keyboard=True)
kb.add(button_1, button_2, button_3)


loop = asyncio.get_event_loop()

with open('portioned_books/OneCity_nltk.pickle', 'rb') as f:
    one_city_list = pickle.load(f)

with open('OneCityDictOfUsers.pickle', 'rb') as f:
    dict_of_users = pickle.load(f)

portioned_books_files = [f for f in listdir('portioned_books/') if isfile(join('portioned_books/', f))]
portioned_books_dict = {}
for pb_file in portioned_books_files:
    path_to_file = join('portioned_books/', pb_file)
    with open(path_to_file, 'rb') as f:
        book_list = pickle.load(f)
    portioned_books_dict[pb_file] = book_list

valid_extensions = ['.txt']


@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def scan_message(message: types.Message):
    filename, file_extension = os.path.splitext(message.document.file_name)
    if file_extension.lower() in valid_extensions:
        document_id = message.document.file_id
        file_info = await bot.get_file(document_id)
        fi = file_info.file_path
        name = join('raw_books/', message.document.file_name)
        urllib.request.urlretrieve(f'https://api.telegram.org/file/bot{API_TOKEN}/{fi}', f'./{name}')
        newpickle_name = join('portioned_books/', filename + '.pickle')
        with open(newpickle_name, 'wb') as f:
            tokenized = tokenize_file_nltk(name)
            pickle.dump(tokenized, f)

        portioned_books_dict[filename + '.pickle'] = tokenized
        dict_of_users[message.from_user.id] = {
            'filename': filename + '.pickle',
            'current_portion': 0
        }

        await bot.send_message(message.from_user.id, 'Файл успешно сохранён')
    else:
        extensions = ' '.join(valid_extensions)
        await bot.send_message(message.from_user.id, 'Я не знаю, что делать с такими файлами. Я могу работать ' +
                                                     f'с книжками вот таких форматов:{extensions}')


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    dict_of_users[message.from_user.id] = {
        'filename': 'OneCity_nltk.pickle',
        'current_portion': 0
    }
    await bot.send_message(message.from_user.id, "Привет. Это бот для чтения. Можешь отправить мне книгу, " +
                                                 "которую хочешь читать (пока только в .txt), можешь попробовать " +
                                                 "на книге по умолчанию. Кнопки внизу - размеры порций текста, " +
                                                 "которые я буду тебе присылать. Вроде, пока всё. Пробуй."
                                                 , reply_markup=kb)


@dp.message_handler(commands=['>', '>>', '>>>'])
async def next_portion_volume(message: types.Message):

    num_of_sentences = message.text.count('>')

    await send_next_portion(message.from_user.id, num_of_sentences)


@dp.message_handler(regexp='(^cat[s]?$|puss)')
async def cats(message: types.Message):
    with open('data/cats.jpg', 'rb') as photo:
        await message.reply_photo(photo, caption='Cats are here 😺')


@dp.message_handler()
async def echo(message: types.Message):

    await message.answer(text(message.text, '/next'))


async def send_next_portion(chat_id, portion_size, unread_messages_number=0):

    current_position = dict_of_users[chat_id]['current_portion']
    user_book_filename = dict_of_users[chat_id]['filename']
    user_book_list = portioned_books_dict[user_book_filename]

    portion = ' '.join(user_book_list[current_position:current_position + portion_size])

    await bot.send_message(chat_id, text(portion), reply_markup=kb)

    dict_of_users[chat_id]['current_portion'] += portion_size
    dict_of_users[chat_id]['last_sent'] = time.time()
    dict_of_users[chat_id]['unread_messages_number'] = unread_messages_number

    with open('OneCityDictOfUsers.pickle', 'wb') as f:
        pickle.dump(dict_of_users, f)


async def reminder_message():

    with open('OneCityDictOfUsers.pickle', 'rb') as f:
        local_dict_of_users = pickle.load(f)

    for user_id in local_dict_of_users.keys():
        if time.time() >= local_dict_of_users[user_id]['last_sent'] + DELAY_FOR_REMINDER:
            if local_dict_of_users[user_id]['unread_messages_number'] < REMINDER_MESSAGES_NUMBER:
                await send_next_portion(user_id, 2, local_dict_of_users[user_id]['unread_messages_number'] + 1)

    when_to_call = loop.time() + DELAY_FOR_REMINDER_CHECK
    loop.call_at(when_to_call, reminder_message_callback)


def reminder_message_callback():
    asyncio.ensure_future(reminder_message())


if __name__ == '__main__':

    reminder_message_callback()
    executor.start_polling(dp, skip_updates=True)

