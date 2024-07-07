import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold
import asyncio
import aiohttp
import ssl
import certifi

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен вашего бота и ключ API для сервиса ФНС
API_TOKEN = 'token'
API_KEY = 'token'

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Привет, {hbold(message.from_user.full_name)}!\n"
                         f"Пожалуйста, введите ИНН компании или ИП для получения выписки.")


@dp.message()
async def handle_message(message: types.Message) -> None:
    inn = message.text.strip()
    logger.info(f"Получен ИНН: {inn}")

    if inn.isdigit() and (len(inn) == 10 or len(inn) == 12):
        logger.info("ИНН прошел проверку формата")
        # Создание SSL контекста
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
            url = f'https://api-fns.ru/api/vyp?req={inn}&key={API_KEY}'
            logger.info(f"Отправка запроса к API: {url}")
            try:
                async with session.get(url) as response:
                    logger.info(f"Получен ответ от API. Статус: {response.status}")
                    if response.status == 200:
                        pdf_content = await response.read()
                        logger.info("PDF получен, отправка документа пользователю")
                        await message.reply_document(types.BufferedInputFile(pdf_content, filename=f'{inn}_info.pdf'))
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка API: {error_text}")
                        await message.reply("Не удалось получить информацию. Пожалуйста, попробуйте позже.")
            except Exception as e:
                logger.error(f"Произошла ошибка при запросе к API: {e}")
                await message.reply("Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.")
    else:
        logger.info("Некорректный формат ИНН")
        await message.reply("Пожалуйста, введите корректный ИНН (10 или 12 цифр).")


async def main() -> None:
    logger.info("Запуск бота")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
