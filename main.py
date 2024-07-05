from aiogram.utils.executor import start_polling
from handlers import dp
from db import create_tables, update_columns

if __name__ == '__main__':
    create_tables()
    update_columns()
    start_polling(dp, skip_updates=True)