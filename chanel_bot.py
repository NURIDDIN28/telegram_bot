import logging
import sqlite3
from aiogram.utils.callback_data import CallbackData
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Sozlashlar
logging.basicConfig(level=logging.INFO)
API_TOKEN = '7923528667:AAFlyGHwS7fTami2N1Wtm3-t-LNJYgNg8pc'
CHANNEL_ID = -1002676385216
ADMIN_ID = 5768770275  # O'z ID raqamingizni qo'ying

# Botni ishga tushirish
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Ma'lumotlar bazasi
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users
                (user_id INTEGER PRIMARY KEY,
                 username TEXT,
                 full_name TEXT,
                 phone TEXT,
                 subscribed INTEGER DEFAULT 0)''')
conn.commit()

# Holatlar
class RegistrationStates(StatesGroup):
    waiting_for_phone = State()

# Kanalga obuna keyboard
def subscribe_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Kanalga a'zo bo'lish", url="https://t.me/Kampyuter_bilimlari_0dan"))
    markup.add(types.InlineKeyboardMarkup("📢 Kanalga a'zo bo'lish||YouTube", url=""))
    markup.add(types.InlineKeyboardButton("✅ A'zo bo'ldim", callback_data="check_sub"))
    return markup

# Telefon raqam so'rash uchun keyboard
def phone_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True))
    return markup

# YouTube tugmalari uchun linklar va klaviatura
youtube_cb = CallbackData('yt', 'video_id')

youtube_links = {
    "g_oOlj7JK08Y4d0_": "https://youtu.be/KzR7HwA9r7I?si=g_oOlj7JK08Y4d0_",
    "gs5oMRNybdyv-REU": "https://youtu.be/X5OooiC8zv4?si=gs5oMRNybdyv-REU",
    "9A1-HDrSZn0v-6E0": "https://youtu.be/fazdrArbn1A?si=9A1-HDrSZn0v-6E0",
    "2x73JdJiLx-Iv1Nj": "https://youtu.be/p5dulktDpKw?si=2x73JdJiLx-Iv1Nj"
}

def youtube_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.insert(types.InlineKeyboardButton("Office va Windows Activatsiya", callback_data=youtube_cb.new(video_id="g_oOlj7JK08Y4d0_")))
    markup.insert(types.InlineKeyboardButton("Virus xakerligi 😱", callback_data=youtube_cb.new(video_id="gs5oMRNybdyv-REU")))
    markup.insert(types.InlineKeyboardButton("Yo'qolgan Telefonni topish📱🔘", callback_data=youtube_cb.new(video_id="9A1-HDrSZn0v-6E0")))
    markup.insert(types.InlineKeyboardButton("Wifi Parolni Ochish", callback_data=youtube_cb.new(video_id="2x73JdJiLx-Iv1Nj")))
    return markup

# Obuna tekshirish
async def check_subscription(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"Obunani tekshirishda xatolik: {e}")
        return False

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    is_subscribed = await check_subscription(user_id)
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if is_subscribed:
        if user:
            await message.answer("Siz allaqachon ro'yxatdan o'tgansiz! Quyidagi darslardan foydalanishingiz mumkin:", reply_markup=youtube_keyboard())
        else:
            await message.answer("Iltimos, telefon raqamingizni yuboring:", reply_markup=phone_keyboard())
            await RegistrationStates.waiting_for_phone.set()
    else:
        await message.answer("Botdan foydalanish uchun avval kanalga a'zo bo'ling:", reply_markup=subscribe_keyboard())

@dp.callback_query_handler(lambda c: c.data == 'check_sub')
async def check_subscription_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    is_subscribed = await check_subscription(user_id)

    if is_subscribed:
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        if cursor.fetchone():
            await callback.message.edit_text("Siz allaqachon ro'yxatdan o'tgansiz! Quyidagi darslardan foydalanishingiz mumkin:")
            await callback.message.answer("Videolar:", reply_markup=youtube_keyboard())
        else:
            await callback.message.edit_text("Iltimos, telefon raqamingizni yuboring:")
            await callback.message.answer("Telefon raqamingizni yuboring:", reply_markup=phone_keyboard())
            await RegistrationStates.waiting_for_phone.set()
    else:
        await callback.answer("Siz hali kanalga a'zo bo'lmagansiz!", show_alert=True)

@dp.message_handler(state=RegistrationStates.waiting_for_phone, content_types=types.ContentType.CONTACT)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    user_id = message.from_user.id

    try:
        cursor.execute("INSERT INTO users (user_id, username, full_name, phone, subscribed) VALUES (?, ?, ?, ?, ?)",
                       (user_id, message.from_user.username, message.from_user.full_name, phone, 1))
        conn.commit()
        await message.answer("Ro'yxatdan muvaffaqiyatli o'tdingiz! Quyidagi darslardan foydalanishingiz mumkin:", reply_markup=types.ReplyKeyboardRemove())
        await message.answer("Videolar:", reply_markup=youtube_keyboard())
        await state.finish()
    except Exception as e:
        logging.error(f"Xato yuz berdi: {e}")
        await message.answer("Ro'yxatdan o'tishda xato yuz berdi. Iltimos, qayta urunib ko'ring.")

@dp.callback_query_handler(youtube_cb.filter())
async def youtube_callback_handler(callback_query: types.CallbackQuery, callback_data: dict):
    video_id = callback_data['video_id']
    link = youtube_links.get(video_id)
    if link:
        await callback_query.answer()
        await callback_query.message.answer(link)
    else:
        await callback_query.answer("Video topilmadi!", show_alert=True)

@dp.message_handler(commands=['users'])
async def show_users(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ Sizda bu buyruqdan foydalanishga ruxsat yo'q.")
        return

    cursor.execute("SELECT user_id, full_name, username, phone FROM users")
    users = cursor.fetchall()

    if not users:
        await message.answer("📭 Foydalanuvchilar ro'yxati hali bo'sh.")
        return

    text = "📋 <b>Ro'yxatdan o'tgan foydalanuvchilar:</b>\n\n"
    for i, (user_id, full_name, username, phone) in enumerate(users, start=1):
        text += f"{i}. 👤 <b>{full_name}</b>\n"
        text += f"   🆔 ID: {user_id}\n"
        if username:
            text += f"   🔗 @{username}\n"
        text += f"   📱 {phone}\n\n"

    # Agar ro'yxat juda uzun bo'lsa bo'lib yuboramiz
    for i in range(0, len(text), 4000):
        await message.answer(text[i:i+4000], parse_mode='HTML')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)