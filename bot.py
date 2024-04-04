# # TELEFESS BETA # #

import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from config import TOKEN, OWNER_ID, MONGO_URI, DB_NAME, BANNED_USERS_COLLECTION

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client[DB_NAME]
banned_users_collection = db[BANNED_USERS_COLLECTION]

async def is_user_banned(user_id):
    """Check if a user is banned."""
    user_data = await banned_users_collection.find_one({'user_id': user_id})
    return bool(user_data)

async def ban_user_db(user_id):
    """Ban a user by adding to the database."""
    await banned_users_collection.insert_one({'user_id': user_id})

async def unban_user_db(user_id):
    """Unban a user by removing from the database."""
    await banned_users_collection.delete_one({'user_id': user_id})

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    """Send a welcome message with an inline keyboard."""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('Confess Anonymously', callback_data='confess'))
    await message.reply("Hi! Kirimkan pengakuanmu dan akan kami post secara anonim.", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'confess')
async def process_callback_confess(callback_query: types.CallbackQuery):
    """Process the confess button press."""
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Silakan kirim pengakuan Anda.")

@dp.message_handler(commands=['ban', 'unban', 'stats'])
async def manage_users(message: types.Message):
    """Manage users with ban, unban, and stats commands."""
    if message.from_user.id == int(OWNER_ID):
        command, *args = message.text.split()
        user_id = args[0] if args else None
        if command == '/stats':
            count = await banned_users_collection.count_documents({})
            await message.reply(f"Total banned users: {count}")
        elif user_id and user_id.isdigit():
            user_id = int(user_id)
            if command == '/ban' and not await is_user_banned(user_id):
                await ban_user_db(user_id)
                await message.reply(f"User dengan ID {user_id} telah dibanned.")
            elif command == '/unban':
                await unban_user_db(user_id)
                await message.reply(f"User dengan ID {user_id} telah diunban.")
        else:
            await message.reply("Mohon masukkan ID user yang valid.")
    else:
        await message.reply("Anda tidak memiliki izin untuk menggunakan perintah ini.")

@dp.message_handler()
async def confess(message: types.Message):
    """Handle anonymous confessions."""
    if await is_user_banned(message.from_user.id):
        await message.reply("Maaf, Anda tidak dapat menggunakan bot ini.")
    elif message.from_user.id == int(OWNER_ID):
        await message.reply("Halo Owner! Apa yang ingin Anda lakukan hari ini?")
    else:
        await bot.copy_message(chat_id='TARGET_CHANNEL_ID', from_chat_id=message.chat.id, message_id=message.message_id)
        await message.reply('Pengakuanmu telah diposting secara anonim.')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

# # UNDER TESTING # #
