import os
import json
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo, MenuButtonWebApp
)
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN", "8772760363:AAEJzb-RqoMeQHkaEjoaSP61-Wqv5vPeby0")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1066867845"))
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://khaan-dyt.bothost.tech")

# ===== LOGGING =====
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("chalama_bot")

# ===== SETUP =====
bot = Bot(token=BOT_TOKEN, default=types.DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Welcome message with WebApp button"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🏨 Открыть сайт Чалама",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )],
        [InlineKeyboardButton(
            text="📞 Позвонить нам",
            url="tel:+73942221082"
        )],
    ])

    await message.answer(
        "🏨 <b>Добро пожаловать в ООО «Чалама»!</b>\n\n"
        "Мы объединяем лучшие места для отдыха в Республике Тыва:\n\n"
        "🏨 <b>Отель «Чалама»</b> — комфортные номера в центре Кызыла\n"
        "⛺ <b>Юрточный отель «Хаан-Дыт»</b> — загородный отдых\n"
        "🍽 <b>Ресторан «Чалама»</b> — лучшая кухня Тувы\n"
        "🍸 <b>Бар «Скала»</b> — атмосферное место\n\n"
        "👇 Нажмите кнопку ниже, чтобы забронировать:",
        reply_markup=keyboard
    )


@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    """Process booking data from WebApp"""
    try:
        data = json.loads(message.web_app_data.data)
        logger.info(f"Booking received: {data}")

        type_label = "🏨 Отель «Чалама»" if data.get("type") == "hotel" else "⛺ Юрты «Хаан-Дыт»"

        admin_text = (
            f"📌 <b>Новая бронь через Mini App!</b>\n\n"
            f"{type_label}\n"
            f"🛏 <b>{data.get('room', '—')}</b>\n"
            f"📅 {data.get('checkIn', '—')} — {data.get('checkOut', '—')} ({data.get('nights', '?')} ноч.)\n"
            f"👤 {data.get('guest', '—')}\n"
            f"📞 {data.get('phone', '—')}\n"
        )
        if data.get("addons"):
            admin_text += f"➕ {', '.join(data['addons'])}\n"
        admin_text += f"\n💰 <b>Итого: {data.get('total', '—')} ₽</b>"
        admin_text += f"\n🔖 ID: <code>{data.get('id', '—')}</code>"
        admin_text += f"\n👤 TG: @{message.from_user.username or '—'} (ID: {message.from_user.id})"

        try:
            await bot.send_message(ADMIN_ID, admin_text)
            logger.info(f"Admin notified: {ADMIN_ID}")
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")

        await message.answer(
            "✅ <b>Ваша бронь принята!</b>\n\n"
            f"{type_label}\n"
            f"🛏 {data.get('room', '—')}\n"
            f"📅 {data.get('checkIn', '—')} — {data.get('checkOut', '—')}\n"
            f"💰 <b>Итого: {data.get('total', '—')} ₽</b>\n\n"
            "Наш менеджер свяжется с вами в течение 15 минут. Спасибо! 🙏"
        )

    except json.JSONDecodeError:
        logger.error("Invalid JSON from webapp")
        await message.answer("❌ Ошибка обработки данных.")
    except Exception as e:
        logger.error(f"Webapp data error: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@dp.message(F.text == "/help")
async def cmd_help(message: types.Message):
    await message.answer(
        "ℹ️ <b>Помощь</b>\n\n"
        "/start — Открыть меню бронирования\n"
        "/help — Показать справку\n\n"
        "📞 +7 (394) 222-10-82\n"
        "📧 info@chalamahotel.ru\n"
        "📍 г. Кызыл, Интернациональная, 12"
    )


@dp.message(F.text == "/admin")
async def cmd_admin(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(
            f"⚙️ <b>Админ-панель</b>\n\n"
            f"🤖 Бот активен\n"
            f"🌐 WebApp: {WEBAPP_URL}\n"
            f"👤 Admin ID: {ADMIN_ID}"
        )
    else:
        await message.answer("❌ Нет доступа.")


async def on_startup():
    """Set menu button on startup"""
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="🏨 Бронирование",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        )
        logger.info("Menu button configured")
    except Exception as e:
        logger.error(f"Menu button error: {e}")

    me = await bot.get_me()
    logger.info(f"Bot started: @{me.username}")


async def main():
    dp.startup.register(on_startup)
    logger.info("Starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
