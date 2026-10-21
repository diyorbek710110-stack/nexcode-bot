import asyncio
import datetime
import html
import logging
import random
import sqlite3
import sys
import time

from aiogram import Bot, Dispatcher, F, BaseMiddleware
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    TelegramObject,
)
from typing import Callable, Dict, Any, Awaitable

# ============================================================
# ⚙️ SOZLAMALAR
# ============================================================

TOKEN = "8638814634:AAGC6DjZes33T40xn9crUrYe185MKFSPVQU"

OWNER_USERNAME = "@D778s"

ADMIN_IDS = {
    8703647047,
    8256060918,
}

PRIMARY_ADMIN_ID = 8703647047

DB_FILE = "nexcode_menedjer.db"

DAILY_REWARD = 100
WORK_COOLDOWN = 60
DAILY_COOLDOWN = 86400

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s 🌟 %(levelname)s 🌟 %(name)s 🌟 %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger("NexcodeMenedjerBot")
dp = Dispatcher(storage=MemoryStorage())


# ============================================================
# 🎮 FSM (HOLATLAR)
# ============================================================

class GameState(StatesGroup):
    waiting_for_currency = State()
    waiting_for_amount = State()
    waiting_for_choice = State()


# ============================================================
# ⌨️ ASOSIY MENYU TUGMALARI
# ============================================================

main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤 𝑃𝑅𝑂𝐹𝐼𝐿"), KeyboardButton(text="🏢 𝐵𝐼𝑍𝑁𝐸𝑆")],
        [KeyboardButton(text="🛒 𝐷𝑂'𝐾𝑂𝑁"), KeyboardButton(text="🎁 𝐾𝑈𝑁𝐿𝐼𝐾 𝐵𝑂𝑁𝑈𝑆")],
        [KeyboardButton(text="🎮 𝑂'𝑌𝐼𝑁𝐿𝐴𝑅 𝑀𝐸𝑁𝑌𝑈𝑆𝐼"), KeyboardButton(text="🏆 𝑇𝑂𝑃 𝑅𝐸𝑌𝑇𝐼𝑁𝐺")],
    ],
    resize_keyboard=True,
)


# ============================================================
# 🗄 MA’LUMOTLAR BAZASI
# ============================================================

class Database:
    def __init__(self, db_file=DB_FILE):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL DEFAULT '',
                messages INTEGER DEFAULT 0,
                karma INTEGER DEFAULT 0,
                balance INTEGER DEFAULT 250,
                almaz INTEGER DEFAULT 0,
                gender TEXT DEFAULT 'Aniqlanmagan ❓',
                points INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                draws INTEGER DEFAULT 0,
                last_bonus REAL DEFAULT 0,
                last_work REAL DEFAULT 0,
                last_daily REAL DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                inventory TEXT DEFAULT 'Yo''q',
                xp INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                energy_count INTEGER DEFAULT 0,
                charm_count INTEGER DEFAULT 0,
                shield_count INTEGER DEFAULT 0,
                vip_status INTEGER DEFAULT 0,
                double_win_count INTEGER DEFAULT 0,
                lucky_dice_count INTEGER DEFAULT 0,
                xp_boost_count INTEGER DEFAULT 0,
                business_level INTEGER DEFAULT 0,
                project_level INTEGER DEFAULT 0,
                last_business_collect REAL DEFAULT 0,
                referrals INTEGER DEFAULT 0,
                referred INTEGER DEFAULT 0,
                is_blocked INTEGER DEFAULT 0,
                partner_id INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

        for col, default_val in [("partner_id", 0), ("project_level", 0), ("vip_status", 0), ("double_win_count", 0), ("lucky_dice_count", 0)]:
            try:
                self.conn.execute(f"ALTER TABLE users ADD COLUMN {col} DEFAULT {default_val}")
                self.conn.commit()
            except sqlite3.OperationalError:
                pass

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS giveaways (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_name TEXT DEFAULT '',
                currency TEXT,
                total_amount INTEGER,
                amount_per_claim INTEGER,
                max_claims INTEGER,
                claimed_users TEXT DEFAULT '',
                chat_id INTEGER
            )
        """)
        self.conn.commit()

        try:
            self.conn.execute("ALTER TABLE giveaways ADD COLUMN sender_name TEXT DEFAULT ''")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS random_giveaways (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER,
                creator_name TEXT,
                total_amount INTEGER,
                max_participants INTEGER,
                participants TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                chat_id INTEGER
            )
        """)
        self.conn.commit()

    def get_user(self, user_id: int, full_name: str = None):
        row = self.conn.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()

        if row is None:
            safe_name = html.escape(full_name or "Foydalanuvchi")
            self.conn.execute(
                "INSERT INTO users (user_id, name) VALUES (?, ?)",
                (user_id, safe_name),
            )
            self.conn.commit()
            row = self.conn.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()

        elif full_name and full_name.strip():
            safe_name = html.escape(full_name)
            self.conn.execute(
                "UPDATE users SET name = ? WHERE user_id = ?",
                (safe_name, user_id),
            )
            self.conn.commit()
            row = self.conn.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()

        return dict(row)

    def update(self, user_id: int, **kwargs):
        if not kwargs:
            return

        allowed = {
            "name", "messages", "karma", "balance", "almaz",
            "gender", "points", "losses", "draws", 
            "last_bonus", "last_work", "last_daily", "warnings", "inventory", 
            "xp", "games_played", "games_won", "streak", "energy_count", 
            "charm_count", "shield_count", "vip_status", "double_win_count", "lucky_dice_count",
            "xp_boost_count", "business_level",
            "project_level", "last_business_collect", "referrals", "referred",
            "is_blocked", "partner_id"
        }

        for key in kwargs:
            if key not in allowed:
                raise ValueError(f"Ruxsat etilmagan ma'lumotlar bazasi ustuni: {key}")

        fields = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [user_id]

        self.conn.execute(
            f"UPDATE users SET {fields} WHERE user_id = ?",
            values,
        )
        self.conn.commit()

    def fetchone(self, query, params=()):
        return self.conn.execute(query, params).fetchone()

    def fetchall(self, query, params=()):
        return self.conn.execute(query, params).fetchall()


db = Database()


# ============================================================
# 🛡️ BLOK MIDDLEWARE
# ============================================================

class BlockCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user:
            if user.id not in ADMIN_IDS:
                user_data = db.get_user(user.id, user.full_name)
                if user_data.get("is_blocked", 0) == 1:
                    if isinstance(event, CallbackQuery):
                        await event.answer("❌ Siz botdan bloklangansiz!", show_alert=True)
                        return
                    elif isinstance(event, Message):
                        await event.answer("❌ Siz bot tomonidan bloklangansiz va botdan foydalana olmaysiz!")
                        return
        return await handler(event, data)


dp.message.middleware(BlockCheckMiddleware())
dp.callback_query.middleware(BlockCheckMiddleware())


# ============================================================
# 🎨 YORDAMCHI FUNKSIYALAR
# ============================================================

def clean_text(text: str) -> str:
    if not text:
        return ""
    import unicodedata
    normalized = unicodedata.normalize('NFKD', text)
    ascii_text = "".join([c for c in normalized if not unicodedata.combining(c)])
    return "".join(c.lower() for c in ascii_text if c.isalnum())


def user_level(xp: int):
    xp = max(0, xp)
    level = (xp // 500) + 1
    current_xp = xp % 500
    return level, current_xp


def update_game_result(user_id: int, result: str):
    user = db.get_user(user_id)
    games = user["games_played"] + 1

    if result == "win":
        db.update(user_id, games_played=games, games_won=user["games_won"] + 1)
    elif result == "loss":
        db.update(user_id, games_played=games, losses=user["losses"] + 1)
    elif result == "draw":
        db.update(user_id, games_played=games, draws=user["draws"] + 1)


def apply_charm_bonus(user_id: int, base_reward: int):
    if base_reward <= 0:
        return base_reward, False

    user = db.get_user(user_id)
    if user["charm_count"] > 0:
        db.update(user_id, charm_count=user["charm_count"] - 1)
        return base_reward * 2, True

    return base_reward, False


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def require_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Bu buyruq faqat bot adminlari uchun!")
        return False
    return True


async def resolve_target(message: Message, target_text: str = None):
    if message.reply_to_message:
        u = message.reply_to_message.from_user
        if u:
            db.get_user(u.id, u.full_name)
            return u.id, u.full_name

    if not target_text:
        return None, None

    target_text = target_text.strip()
    if target_text.lstrip("-").isdigit():
        target_id = int(target_text)
        row = db.fetchone("SELECT user_id, name FROM users WHERE user_id = ?", (target_id,))
        if row:
            return row["user_id"], row["name"]
        try:
            chat = await message.bot.get_chat(target_id)
            name = getattr(chat, "full_name", None) or getattr(chat, "first_name", None) or "Foydalanuvchi"
            db.get_user(chat.id, name)
            return chat.id, name
        except Exception:
            return None, None

    username = target_text
    if not username.startswith("@"):
        username = "@" + username

    try:
        chat = await message.bot.get_chat(username)
        name = getattr(chat, "full_name", None) or getattr(chat, "first_name", None) or "Foydalanuvchi"
        db.get_user(chat.id, name)
        return chat.id, name
    except Exception:
        return None, None


# ============================================================
# 👤 PROFIL HANDLER
# ============================================================

async def send_profile_to_user(message: Message, user_id: int, full_name: str):
    user = db.get_user(user_id, full_name)
    level, current_xp = user_level(user["xp"])

    games = user["games_played"]
    wins = user["games_won"]
    losses = user["losses"]
    draws = user["draws"]
    win_rate = int(wins / games * 100) if games else 0
    business_lvl = user["business_level"]
    project_lvl = user.get("project_level", 0)

    safe_name = html.escape(user["name"])
    user_mention = f'<a href="tg://user?id={user_id}">{safe_name}</a>'
    
    username_str = "Mavjud emas"
    try:
        chat_member = await message.bot.get_chat(user_id)
        if chat_member.username:
            username_str = f"@{chat_member.username}"
    except Exception:
        pass

    partner_str = "Sizda para yo'q. 💔"
    partner_id = user.get("partner_id") or 0
    if partner_id and partner_id > 0:
        partner = db.get_user(partner_id)
        if partner:
            p_safe_name = html.escape(partner["name"])
            partner_str = f'<a href="tg://user?id={partner["user_id"]}">{p_safe_name}</a> 💍'

    items = []
    if user["energy_count"] > 0:
        items.append(f"⚡ Energetik: {user['energy_count']} ta")
    if user["charm_count"] > 0:
        items.append(f"🍀 Omad tilsimi: {user['charm_count']} ta")
    if user["shield_count"] > 0:
        items.append(f"🛡️ Himoya qalqoni: {user['shield_count']} ta")
    if user.get("double_win_count", 0) > 0:
        items.append(f"🎁 Ikki karra yutuq: {user['double_win_count']} ta")
    if user.get("lucky_dice_count", 0) > 0:
        items.append(f"🎲 Omadli zar: {user['lucky_dice_count']} ta")
    if user.get("vip_status", 0) == 1:
        items.append("👑 VIP Maqom: Faol ✅")

    inventory_str = ", ".join(items) if items else "Bo'sh"

    profile_text = (
        f"👤 <b>{user_mention}</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"🆔 ID: <b>{user_id}</b>\n"
        f"🔗 Username: <b>{username_str}</b>\n"
        f"❤️ Param: <b>{partner_str}</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"🎖 Daraja: <b>{level}</b>\n"
        f"⭐ XP: <b>{current_xp}/500</b>\n"
        f"🏆 Ball: <b>{user['points']}</b>\n"
        f"💵 Dollar: <b>{user['balance']}</b>\n"
        f"💎 Almaz: <b>{user['almaz']}</b>\n"
        f"🎒 Inventar: <b>{inventory_str}</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"🏢 Biznes darajasi: <b>{business_lvl}</b>\n"
        f"📊 Biznes loyiha darajasi: <b>{project_lvl}</b>\n"
        f"🎮 O'yinlar: <b>{games}</b>\n"
        f"🏆 G'alabalar: <b>{wins}</b>\n"
        f"💔 Mag'lubiyatlar: <b>{losses}</b>\n"
        f"🤝 Duranglar: <b>{draws}</b>\n"
        f"📊 G'alaba foizi: <b>{win_rate}%</b>"
    )

    await message.answer(profile_text, parse_mode=ParseMode.HTML)


@dp.message(StateFilter("*"), F.text.func(lambda t: t and clean_text(t) in ["profil", "profile"]))
async def profile_handler_main(message: Message, state: FSMContext):
    await state.clear()
    await send_profile_to_user(message, message.from_user.id, message.from_user.full_name)


@dp.message(F.text.lower().in_({"/nprofile", "nprofile", ".nprofile", "/profile", "profile", ".profile", "/profil", "profil", ".profil"}))
async def group_nprofile_command(message: Message):
    await send_profile_to_user(message, message.from_user.id, message.from_user.full_name)


# ============================================================
# 🚀 START
# ============================================================

@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    if message.chat.type in ("group", "supergroup"):
        await message.answer("❌ Bu buyruq va menyu faqat botning shaxsiy xabarlarida (lichkada) ishlaydi!")
        return

    user_id = message.from_user.id
    user = db.get_user(user_id, message.from_user.full_name)
    safe_name = html.escape(user["name"])

    if user["gender"] == "Aniqlanmagan ❓":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="👨‍💼 𝐸𝑅𝐾𝐴𝐾", callback_data=f"gender_male_{user_id}"),
                    InlineKeyboardButton(text="👩‍💼 𝐴𝑌𝑂𝐿", callback_data=f"gender_female_{user_id}"),
                ]
            ]
        )
        await message.answer(
            f"✨ <b>BOTGA XUSH KELIBSIZ!</b> ✨\n\n"
            f"Hurmatli <b>{safe_name}</b>, "
            f"ro'yxatdan o'tish uchun jinsingizni tanlang: 👇",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
        return

    level, current_xp = user_level(user["xp"])
    await message.answer(
        f"╔══════════════════════════╗\n"
        f"  💎 <b><i>NEXCODE MENEDJER</i></b> 💎\n"
        f"╚══════════════════════════╝\n\n"
        f"👋 Assalomu alaykum, <b>{safe_name}</b>!\n\n"
        f"⭐ Daraja: <b>{level}</b> <i>({current_xp} XP / 500 XP)</i>\n"
        f"💵 Dollar: <b>{user['balance']}</b>\n"
        f"💎 Almaz: <b>{user['almaz']}</b>\n\n"
        f"👇 Quyidagi tugmalar orqali botni boshqaring:",
        reply_markup=main_menu_keyboard,
        parse_mode=ParseMode.HTML,
    )


@dp.callback_query(F.data.startswith("gender_"))
async def gender_callback_handler(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    gender_type = parts[1]
    owner_id = int(parts[2]) if len(parts) > 2 else callback.from_user.id

    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu tugma siz uchun emas!", show_alert=True)
        return

    gender_text = "Erkak 👨‍💼" if gender_type == "male" else "Ayol 👩‍💼"
    db.update(owner_id, gender=gender_text)

    user = db.get_user(owner_id)
    level, current_xp = user_level(user["xp"])
    safe_name = html.escape(user["name"])

    try:
        await callback.message.edit_text(
            f"✅ Jinsingiz saqlandi: <b>{gender_text}</b>\n\n"
            f"╔══════════════════════════╗\n"
            f"  💎 <b><i>NEXCODE MENEDJER</i></b> 💎\n"
            f"╚══════════════════════════╝\n\n"
            f"👋 Xush kelibsiz, <b>{safe_name}</b>!\n\n"
            f"⭐ Daraja: <b>{level}</b> <i>({current_xp} XP / 500 XP)</i>\n"
            f"💵 Dollar: <b>{user['balance']}</b>\n"
            f"💎 Almaz: <b>{user['almaz']}</b>\n\n"
            f"👇 Quyidagi tugmalar orqali botni boshqaring:",
            reply_markup=main_menu_keyboard,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass
    await callback.answer("Saqlandi!")


# ============================================================
# ❤️ PARAM
# ============================================================

@dp.message(F.text.lower().startswith(("mypara", "/mypara", ".mypara")))
async def my_para_command(message: Message):
    user_id = message.from_user.id
    user = db.get_user(user_id, message.from_user.full_name)
    partner_id = user.get("partner_id") or 0

    if not partner_id or partner_id == 0:
        await message.answer("Sizda para yo'q. 💔", parse_mode=ParseMode.HTML)
        return

    partner = db.get_user(partner_id)
    partner_name = html.escape(partner.get("name", "Foydalanuvchi") if partner else "Foydalanuvchi")
    partner_mention = f'<a href="tg://user?id={partner_id}">{partner_name}</a>'

    await message.answer(
        f"Sizning parangiz: {partner_mention} 💍",
        parse_mode=ParseMode.HTML
    )


@dp.message(F.text.lower().startswith(("dpara", "/dpara", ".dpara")))
async def delete_para_command(message: Message):
    user_id = message.from_user.id
    user = db.get_user(user_id, message.from_user.full_name)
    partner_id = user.get("partner_id") or 0

    if not partner_id or partner_id == 0:
        await message.answer("❌ Sizda bekor qilish uchun paramiz yo'q!", parse_mode=ParseMode.HTML)
        return

    partner = db.get_user(partner_id)
    p_safe_name = html.escape(partner["name"] if partner else "Foydalanuvchi")
    partner_mention = f'<a href="tg://user?id={partner_id}">{p_safe_name}</a>'

    db.update(user_id, partner_id=0)
    db.update(partner_id, partner_id=0)

    await message.answer(
        f"💔 <b>PARAM BEKOR QILINDI!</b>\n\n"
        f"Siz va {partner_mention} o'rtasidagi munosabatlar uzildi.",
        parse_mode=ParseMode.HTML
    )


@dp.message(F.text.lower().startswith(("para", "/para", ".para")))
async def make_para_command(message: Message):
    sender_id = message.from_user.id
    sender = db.get_user(sender_id, message.from_user.full_name)

    if (sender.get("partner_id") or 0) > 0:
        partner = db.get_user(sender["partner_id"])
        p_safe_name = html.escape(partner["name"] if partner else "Foydalanuvchi")
        p_mention = f'<a href="tg://user?id={sender["partner_id"]}">{p_safe_name}</a>'
        await message.answer(f"⚠️ Siz allaqachon {p_mention} bilan paramsiz! Avval paramni bekor qiling (<code>/dpara</code>).", parse_mode=ParseMode.HTML)
        return

    parts = (message.text or "").split()
    target_text = parts[1] if len(parts) >= 2 else None
    target_id, target_name = await resolve_target(message, target_text)

    if not target_id:
        await message.answer("❌ Param bo'lish uchun foydalanuvchini tanlang (javob yozish, ID yoki foydalanuvchi nomi orqali).", parse_mode=ParseMode.HTML)
        return

    if target_id == sender_id:
        await message.answer("❌ O'zingiz bilan param bo'la olmaysiz!", parse_mode=ParseMode.HTML)
        return

    target_user = db.get_user(target_id, target_name)
    if (target_user.get("partner_id") or 0) > 0:
        await message.answer(f"❌ <b>{html.escape(target_name)}</b> allaqachon boshqa inson bilan param!", parse_mode=ParseMode.HTML)
        return

    s_safe_name = html.escape(sender["name"])
    t_safe_name = html.escape(target_name)
    sender_mention = f'<a href="tg://user?id={sender_id}">{s_safe_name}</a>'
    target_mention = f'<a href="tg://user?id={target_id}">{t_safe_name}</a>'

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ 𝑃𝐴𝑅𝐴𝑀 𝐵𝑂'𝐿𝐼𝑆𝐻 ❤️", callback_data=f"pa_a_{sender_id}_{target_id}"),
                InlineKeyboardButton(text="❌ 𝑅𝐴𝐷 𝐸𝑇𝐼𝑆𝐻 💔", callback_data=f"pa_r_{sender_id}_{target_id}")
            ]
        ]
    )

    await message.answer(
        f"❤️ <b>PARAM SO'ROVI!</b>\n\n"
        f"{sender_mention}, {target_mention} ga siz bilan param bo'lish taklifini yubordi!\n\n"
        f"Rozimisiz? 👇",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data.startswith("pa_a_"))
async def accept_para_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    sender_id = int(parts[2])
    target_id = int(parts[3])

    if callback.from_user.id != target_id:
        await callback.answer("❌ Bu taklif siz uchun emas!", show_alert=True)
        return

    sender = db.get_user(sender_id)
    target = db.get_user(target_id, callback.from_user.full_name)

    sender_p = sender.get("partner_id") or 0 if sender else 0
    target_p = target.get("partner_id") or 0 if target else 0

    if sender_p > 0 or target_p > 0:
        await callback.answer("⚠️ Ikkala tomondan birida allaqachon param bor!", show_alert=True)
        return

    db.update(sender_id, partner_id=target_id)
    db.update(target_id, partner_id=sender_id)

    sender_name = html.escape(sender.get("name", "Foydalanuvchi") if sender else "Foydalanuvchi")
    target_name = html.escape(target.get("name", callback.from_user.full_name) if target else callback.from_user.full_name)

    sender_mention = f'<a href="tg://user?id={sender_id}">{sender_name}</a>'
    target_mention = f'<a href="tg://user?id={target_id}">{target_name}</a>'

    try:
        if callback.message:
            await callback.message.edit_text(
                f"🎉 <b>TABRIKLAYMIZ!</b> ❤️\n\n"
                f"{sender_mention} va {target_mention} muvaffaqiyatli param bo'lishdi! 💍✨",
                parse_mode=ParseMode.HTML,
                reply_markup=None
            )
    except Exception as e:
        logger.error(f"Xabarni tahrirlashda xatolik: {e}")
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass

    await callback.answer("Taklif qabul qilindi!", show_alert=False)


@dp.callback_query(F.data.startswith("pa_r_"))
async def reject_para_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    sender_id = int(parts[2])
    target_id = int(parts[3])

    if callback.from_user.id != target_id:
        await callback.answer("❌ Bu taklif sizga yuborilmagan!", show_alert=True)
        return

    target_mention = f'<a href="tg://user?id={target_id}">{html.escape(callback.from_user.full_name)}</a>'

    try:
        if callback.message:
            await callback.message.edit_text(
                f"💔 {target_mention} param bo'lish taklifini rad etdi.",
                parse_mode=ParseMode.HTML,
                reply_markup=None
            )
    except Exception as e:
        logger.error(f"Xabarni tahrirlashda xatolik: {e}")
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass

    await callback.answer("Taklif rad etildi.", show_alert=False)


# ============================================================
# 👑 ADMIN BUYRUQLARI
# ============================================================

@dp.message(F.text.lower().startswith(("admin", "/admin")))
async def admin_panel_command(message: Message):
    if not await require_admin(message):
        return
    await message.answer(
        "👑 <b>Admin paneli</b>\n\n"
        "Mavjud admin buyruqlari:\n"
        "• <code>Statistika</code> - Qancha odam botdan foydalanayotgani va umumiy statistika\n"
        "• <code>statik</code> - Botdan foydalanayotgan barcha foydalanuvchilar ro'yxati (mention bilan)\n"
        "• <code>/elon</code>, <code>.elon</code>, <code>e'lon [matn]</code> - Hammaga xabar yuborish\n"
        "• <code>/blok</code>, <code>.blok</code>, <code>blok [@foydalanuvchi / ID / javob]</code> - Foydalanuvchini bloklash\n"
        "• <code>/unblok</code>, <code>.unblok</code>, <code>unblok [@foydalanuvchi / ID / javob]</code> - Blokdan chiqarish\n"
        "• <code>Adgive [miqdor] [@foydalanuvchi / ID / javob]</code> - Almaz berish\n"
        "• <code>Admoney [miqdor] [@foydalanuvchi / ID / javob]</code> - Dollar berish\n"
        "• <code>Addaraja [daraja] [xp] [@foydalanuvchi / ID / javob]</code> - Daraja va XP berish\n"
        "• <code>Adball [miqdor] [@foydalanuvchi / ID / javob]</code> - Ball berish\n"
        "• <code>/bust1</code>, <code>.bust1</code>, <code>bust1</code> — Dollar hisobini 0 qilish\n"
        "• <code>/bust2</code>, <code>.bust2</code>, <code>bust2</code> — Almaz hisobini 0 qilish\n"
        "• <code>/bust3</code>, <code>.bust3</code>, <code>bust3</code> — Darajani bankrot qilish\n"
        "• <code>/bust4</code>, <code>.bust4</code>, <code>bust4</code> — Hisobni to'liq bankrot qilish\n"
        "• <code>/foydalanuvchi</code> - Foydalanuvchi paneliga o'tish",
        parse_mode=ParseMode.HTML,
    )


@dp.message(F.text.lower().startswith(("elon", "/elon", ".elon", "e'lon")))
async def admin_elon_command(message: Message):
    if not await require_admin(message):
        return

    text_parts = message.text.split(maxsplit=1)
    if len(text_parts) < 2:
        await message.answer("❌ E'lon matnini kiriting!\nFoydalanish: <code>/elon [xabar matni]</code>", parse_mode=ParseMode.HTML)
        return

    announcement_text = text_parts[1]
    users = db.fetchall("SELECT user_id FROM users WHERE is_blocked = 0")
    
    success_count = 0
    blocked_count = 0

    sent_msg = await message.answer("📢 E'lon yuborilmoqda...")

    for row in users:
        uid = row["user_id"]
        try:
            await message.bot.send_message(
                chat_id=uid,
                text=f"📢 <b>E'LON:</b>\n\n{announcement_text}",
                parse_mode=ParseMode.HTML
            )
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            blocked_count += 1

    await sent_msg.edit_text(
        f"✅ <b>E'lon muvaffaqiyatli tarqatildi!</b>\n\n"
        f"📤 Yuborildi: <b>{success_count}</b> ta kishiga\n"
        f"⚠️ Xatolik / Bloklaganlar: <b>{blocked_count}</b> ta",
        parse_mode=ParseMode.HTML
    )


@dp.message(F.text.lower().startswith(("statistika", "/statistika")))
async def admin_statistika_command(message: Message):
    if not await require_admin(message):
        return

    total_users_row = db.fetchone("SELECT COUNT(*) FROM users")
    total_users = total_users_row[0] if total_users_row else 0

    played_users_row = db.fetchone("SELECT COUNT(*) FROM users WHERE games_played > 0")
    played_users = played_users_row[0] if played_users_row else 0

    balance_row = db.fetchone("SELECT SUM(balance) FROM users")
    total_balance = balance_row[0] if balance_row and balance_row[0] else 0

    almaz_row = db.fetchone("SELECT SUM(almaz) FROM users")
    total_almaz = almaz_row[0] if almaz_row and almaz_row[0] else 0

    await message.answer(
        f"📊 <b>BOT STATISTIKASI</b>\n\n"
        f"👥 Hozirda botdan foydalanayotganlar: <b>{total_users}</b> kishi\n"
        f"🎮 O'yin o'ynaganlar: <b>{played_users}</b> kishi\n"
        f"💵 Jami dollar: <b>{total_balance:,}</b> 💵\n"
        f"💎 Jami Almaz: <b>{total_almaz:,}</b>",
        parse_mode=ParseMode.HTML
    )


@dp.message(F.text.lower() == "statik")
async def admin_statik_command(message: Message):
    if not await require_admin(message):
        return

    rows = db.fetchall("SELECT user_id, name FROM users ORDER BY user_id DESC")
    if not rows:
        await message.answer("❌ Hali botda foydalanuvchilar yo'q.")
        return

    total = len(rows)
    text = f"👥 <b>BOTDAN FOYDALANAYOTGANLAR RO'YXATI (Jami: {total} ta):</b>\n\n"
    
    chunk = ""
    for idx, row in enumerate(rows, 1):
        safe_name = html.escape(row["name"])
        mention = f'<a href="tg://user?id={row["user_id"]}">{safe_name}</a>'
        line = f"{idx}. {mention} (ID: <code>{row['user_id']}</code>)\n"
        
        if len(text) + len(chunk) + len(line) > 4000:
            await message.answer(text + chunk, parse_mode=ParseMode.HTML)
            chunk = ""
        chunk += line

    if chunk:
        await message.answer(text + chunk, parse_mode=ParseMode.HTML)


@dp.message(F.text.lower().startswith(("blok", "/blok", ".blok")))
async def admin_block_handler(message: Message):
    if not await require_admin(message):
        return
    parts = (message.text or "").split()
    target_text = parts[1] if len(parts) >= 2 else None
    target_id, target_name = await resolve_target(message, target_text)

    if not target_id:
        await message.answer("❌ Foydalanuvchi topilmadi (foydalanuvchi nomi, ID yoki javob orqali).", parse_mode=ParseMode.HTML)
        return

    if is_admin(target_id):
        await message.answer("❌ Adminni bloklab bo'lmaydi!", parse_mode=ParseMode.HTML)
        return

    db.get_user(target_id, target_name)
    db.update(target_id, is_blocked=1)
    await message.answer(f"🔒 <b>Foydalanuvchi bloklandi!</b>\n👤 {html.escape(target_name)} (ID: <code>{target_id}</code>)", parse_mode=ParseMode.HTML)


@dp.message(F.text.lower().startswith(("unblok", "/unblok", ".unblok")))
async def admin_unblock_handler(message: Message):
    if not await require_admin(message):
        return
    parts = (message.text or "").split()
    target_text = parts[1] if len(parts) >= 2 else None
    target_id, target_name = await resolve_target(message, target_text)

    if not target_id:
        await message.answer("❌ Foydalanuvchi topilmadi (foydalanuvchi nomi, ID yoki javob orqali).", parse_mode=ParseMode.HTML)
        return

    db.get_user(target_id, target_name)
    db.update(target_id, is_blocked=0)
    await message.answer(f"🔓 <b>Foydalanuvchi blokdan chiqarildi!</b>\n👤 {html.escape(target_name)} (ID: <code>{target_id}</code>)", parse_mode=ParseMode.HTML)


@dp.message(F.text.lower().startswith(("foydalanuvchi", "/foydalanuvchi")))
async def user_panel_command(message: Message):
    await message.answer(
        "👤 <b>Foydalanuvchi paneli</b>",
        reply_markup=main_menu_keyboard,
        parse_mode=ParseMode.HTML,
    )


@dp.message(F.text.lower().startswith("adgive"))
async def admin_give_almaz(message: Message):
    if not await require_admin(message):
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("❌ Foydalanish: <code>Adgive 100 [@foydalanuvchi/ID]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        amount = int(parts[1])
    except ValueError:
        return
    target_id, target_name = await resolve_target(message, parts[2] if len(parts) >= 3 else None)
    if not target_id:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return
    user = db.get_user(target_id, target_name)
    db.update(target_id, almaz=user["almaz"] + amount)
    await message.answer(f"👑 <b>Admin amali</b>\n👤 {html.escape(target_name)}\n💎 +{amount} Almaz", parse_mode=ParseMode.HTML)


@dp.message(F.text.lower().startswith("admoney"))
async def admin_give_money(message: Message):
    if not await require_admin(message):
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("❌ Foydalanish: <code>Admoney 1000 [@foydalanuvchi/ID]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        amount = int(parts[1])
    except ValueError:
        return
    target_id, target_name = await resolve_target(message, parts[2] if len(parts) >= 3 else None)
    if not target_id:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return
    user = db.get_user(target_id, target_name)
    db.update(target_id, balance=user["balance"] + amount)
    await message.answer(f"👑 <b>Admin amali</b>\n👤 {html.escape(target_name)}\n💵 +{amount} dollar", parse_mode=ParseMode.HTML)


@dp.message(F.text.lower().startswith("addaraja"))
async def admin_add_daraja(message: Message):
    if not await require_admin(message):
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("❌ Foydalanish: <code>Addaraja [daraja] [xp] [@foydalanuvchi/ID]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        lvl = int(parts[1])
        xp_val = int(parts[2]) if len(parts) > 2 and parts[2].lstrip("-").isdigit() else 0
        target_str_idx = 3 if len(parts) > 2 and parts[2].lstrip("-").isdigit() else 2
        target_text = parts[target_str_idx] if len(parts) > target_str_idx else None
    except ValueError:
        await message.answer("❌ Xato format.")
        return

    target_id, target_name = await resolve_target(message, target_text)
    if not target_id:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return

    total_xp = (lvl - 1) * 500 + max(0, xp_val)
    db.update(target_id, xp=total_xp)
    await message.answer(f"👑 <b>Admin amali</b>\n👤 {html.escape(target_name)}\n🎖️ Daraja: {lvl} (XP: {total_xp}) etib belgilandi!", parse_mode=ParseMode.HTML)


@dp.message(F.text.lower().startswith("adball"))
async def admin_give_ball(message: Message):
    if not await require_admin(message):
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("❌ Foydalanish: <code>Adball [ball] [@foydalanuvchi/ID]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        amount = int(parts[1])
    except ValueError:
        return
    target_text = parts[2] if len(parts) >= 3 else None
    target_id, target_name = await resolve_target(message, target_text)
    if not target_id:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return
    user = db.get_user(target_id, target_name)
    db.update(target_id, points=user["points"] + amount)
    await message.answer(f"👑 <b>Admin amali</b>\n👤 {html.escape(target_name)}\n🏆 +{amount} ball", parse_mode=ParseMode.HTML)


@dp.message(F.text.lower().startswith(("bust1", "/bust1", ".bust1")))
async def admin_bust1(message: Message):
    if not await require_admin(message):
        return
    parts = (message.text or "").split()
    target_text = parts[1] if len(parts) >= 2 else None
    target_id, target_name = await resolve_target(message, target_text)
    if not target_id:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return
    db.update(target_id, balance=0)
    mention = f'<a href="tg://user?id={target_id}">{html.escape(target_name)}</a>'
    await message.answer(f"💥 {mention}ning <b>dollar</b> hisobi bankrot qilindi!", parse_mode=ParseMode.HTML)


@dp.message(F.text.lower().startswith(("bust2", "/bust2", ".bust2")))
async def admin_bust2(message: Message):
    if not await require_admin(message):
        return
    parts = (message.text or "").split()
    target_text = parts[1] if len(parts) >= 2 else None
    target_id, target_name = await resolve_target(message, target_text)
    if not target_id:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return
    db.update(target_id, almaz=0)
    mention = f'<a href="tg://user?id={target_id}">{html.escape(target_name)}</a>'
    await message.answer(f"💥 {mention}ning <b>Almaz</b> hisobi bankrot qilindi!", parse_mode=ParseMode.HTML)


@dp.message(F.text.lower().startswith(("bust3", "/bust3", ".bust3")))
async def admin_bust3(message: Message):
    if not await require_admin(message):
        return
    parts = (message.text or "").split()
    target_text = parts[1] if len(parts) >= 2 else None
    target_id, target_name = await resolve_target(message, target_text)
    if not target_id:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return
    db.update(target_id, xp=0)
    mention = f'<a href="tg://user?id={target_id}">{html.escape(target_name)}</a>'
    await message.answer(f"💥 {mention}ning <b>daraja</b> hisobi bankrot qilindi!", parse_mode=ParseMode.HTML)


@dp.message(F.text.lower().startswith(("bust4", "/bust4", ".bust4")))
async def admin_bust4(message: Message):
    if not await require_admin(message):
        return
    parts = (message.text or "").split()
    target_text = parts[1] if len(parts) >= 2 else None
    target_id, target_name = await resolve_target(message, target_text)
    if not target_id:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return
    db.update(
        target_id,
        balance=0,
        almaz=0,
        points=0,
        xp=0,
        business_level=0,
        project_level=0,
        energy_count=0,
        charm_count=0,
        shield_count=0,
        vip_status=0,
        double_win_count=0,
        lucky_dice_count=0,
        xp_boost_count=0
    )
    mention = f'<a href="tg://user?id={target_id}">{html.escape(target_name)}</a>'
    await message.answer(f"💥 {mention}ning <b>hisobi</b> to'liq bankrot qilindi!", parse_mode=ParseMode.HTML)


# ============================================================
# 🎲 CHANGE (TASODIFIY SOVG'A)
# ============================================================

@dp.message(F.text.lower().startswith(("change", "/change", ".change")))
@dp.channel_post(F.text.lower().startswith(("change", "/change", ".change")))
async def change_giveaway_handler(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer(
            "❌ Foydalanish:\n"
            "<code>change [miqdor] [kishilar soni]</code> (masalan: <code>change 100 1</code>)",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        total_amount = int(parts[1])
        max_participants = int(parts[2])
        if total_amount <= 0 or max_participants <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Miqdor va kishilar soni musbat raqam bo'lishi kerak.")
        return

    if message.chat.type == "channel" or not message.from_user:
        creator_id = PRIMARY_ADMIN_ID
        admin_user = db.get_user(PRIMARY_ADMIN_ID)
        creator_name = admin_user.get("name", "Admin")
    else:
        creator_id = message.from_user.id
        creator_name = message.from_user.full_name

    user = db.get_user(creator_id, creator_name)
    if user["almaz"] < total_amount:
        await message.answer(f"❌ Almazingiz yetarli emas! Sizda: {user['almaz']} 💎")
        return

    db.update(creator_id, almaz=user["almaz"] - total_amount)

    cursor = db.conn.cursor()
    cursor.execute(
        "INSERT INTO random_giveaways (creator_id, creator_name, total_amount, max_participants, participants, is_active, chat_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (creator_id, creator_name, total_amount, max_participants, "", 1, message.chat.id)
    )
    db.conn.commit()
    giveaway_id = cursor.lastrowid

    creator_mention = f'<a href="tg://user?id={creator_id}">{html.escape(creator_name)}</a>'

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎉 𝑄𝐴𝑇𝑁𝐴𝑆𝐻𝐼𝑆𝐻 (0 𝑘𝑖𝑠ℎ𝑖)", callback_data=f"join_rnd_{giveaway_id}")],
            [InlineKeyboardButton(text="🏁 𝐺'𝑂𝐿𝐼𝐵𝑁𝐼 𝐴𝑁𝐼𝑄𝐿𝐴𝑆𝐻", callback_data=f"stop_rnd_{giveaway_id}")]
        ]
    )

    await message.answer(
        f"🎲 <b>TASODIFIY ALMAZ SOVG'ASI!</b>\n\n"
        f"👤 Tarqatuvchi: {creator_mention}\n"
        f"💎 Sovg'a miqdori: <b>{total_amount} Almaz</b>\n"
        f"👥 Qatnashuvchilar: <b>0 kishi</b>\n\n"
        f"Pastdagi 'Qatnashish' tugmasini bosing!\n"
        f"<i>(Sovg'a beruvchi tugmani bosib g'olibni aniqlaydi)</i>",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


@dp.callback_query(F.data.startswith("join_rnd_"))
async def join_random_giveaway_callback(callback: CallbackQuery):
    giveaway_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    db.get_user(user_id, callback.from_user.full_name)

    row = db.fetchone("SELECT * FROM random_giveaways WHERE id = ?", (giveaway_id,))
    if not row or row["is_active"] == 0:
        await callback.answer("❌ Bu sovg'a tugagan yoki o'chirilgan!", show_alert=True)
        return

    participants_str = row["participants"] or ""
    participants_list = [int(uid) for uid in participants_str.split(",") if uid.strip().isdigit()]

    if user_id in participants_list:
        await callback.answer("⚠️ Siz allaqachon qatnashgansiz!", show_alert=True)
        return

    participants_list.append(user_id)
    new_participants_str = ",".join(map(str, participants_list))
    db.conn.execute("UPDATE random_giveaways SET participants = ? WHERE id = ?", (new_participants_str, giveaway_id))
    db.conn.commit()

    current_count = len(participants_list)
    total_amount = row["total_amount"]
    creator_id = row["creator_id"]
    creator_mention = f'<a href="tg://user?id={creator_id}">{html.escape(row["creator_name"])}</a>'

    part_mentions = []
    for uid in participants_list:
        u = db.get_user(uid)
        part_mentions.append(f'<a href="tg://user?id={uid}">{html.escape(u["name"])}</a>')

    part_text = "\n".join(f"{i+1}. {m}" for i, m in enumerate(part_mentions))

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🎉 𝑄𝐴𝑇𝑁𝐴𝑆𝐻𝐼𝑆𝐻 ({current_count} 𝑘𝑖𝑠ℎ𝑖)", callback_data=f"join_rnd_{giveaway_id}")],
            [InlineKeyboardButton(text="🏁 𝐺'𝑂𝐿𝐼𝐵𝑁𝐼 𝐴𝑁𝐼𝑄𝐿𝐴𝑆𝐻", callback_data=f"stop_rnd_{giveaway_id}")]
        ]
    )

    try:
        await callback.message.edit_text(
            f"🎲 <b>TASODIFIY ALMAZ SOVG'ASI!</b>\n\n"
            f"👤 Tarqatuvchi: {creator_mention}\n"
            f"💎 Sovg'a miqdori: <b>{total_amount} Almaz</b>\n"
            f"👥 Qatnashuvchilar (<b>{current_count} kishi</b>):\n"
            f"{part_text}\n\n"
            f"<i>(Sovg'a beruvchi tugmani bosib g'olibni aniqlaydi)</i>",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

    await callback.answer("✅ Siz muvaffaqiyatli qatnashdingiz!", show_alert=True)


@dp.callback_query(F.data.startswith("stop_rnd_"))
async def stop_random_giveaway_callback(callback: CallbackQuery):
    giveaway_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    row = db.fetchone("SELECT * FROM random_giveaways WHERE id = ?", (giveaway_id,))
    if not row or row["is_active"] == 0:
        await callback.answer("❌ Bu sovg'a allaqachon to'xtatilgan!", show_alert=True)
        return

    if user_id != row["creator_id"] and user_id not in ADMIN_IDS:
        await callback.answer("❌ Faqat sovg'ani tarqatgan kishi to'xtata oladi!", show_alert=True)
        return

    db.conn.execute("UPDATE random_giveaways SET is_active = 0 WHERE id = ?", (giveaway_id,))
    db.conn.commit()

    participants_str = row["participants"] or ""
    participants_list = [int(uid) for uid in participants_str.split(",") if uid.strip().isdigit()]
    total_amount = row["total_amount"]

    if not participants_list:
        creator_user = db.get_user(row["creator_id"])
        db.update(row["creator_id"], almaz=creator_user["almaz"] + total_amount)
        try:
            await callback.message.edit_text(
                f"🎲 <b>TASODIFIY ALMAZ SOVG'ASI (TO'XTATILDI)</b>\n\n"
                f"❌ Ishtirokchilar bo'lmagani uchun sovg'a bekor qilindi va Almazlar egasiga qaytarildi.",
                reply_markup=None,
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass
        await callback.answer("Sovg'a to'xtatildi, Almazlar qaytarildi.")
        return

    winner_id = random.choice(participants_list)
    winner_user = db.get_user(winner_id)
    db.update(winner_id, almaz=winner_user["almaz"] + total_amount)

    winner_mention = f'<a href="tg://user?id={winner_id}">{html.escape(winner_user["name"])}</a>'
    creator_mention = f'<a href="tg://user?id={row["creator_id"]}">{html.escape(row["creator_name"])}</a>'

    try:
        await callback.message.edit_text(
            f"🎲 <b>TASODIFIY ALMAZ SOVG'ASI (YAKUNLANDI)</b>\n\n"
            f"👤 Tarqatuvchi: {creator_mention}\n"
            f"💎 Sovg'a miqdori: <b>{total_amount} Almaz</b>\n"
            f"👥 Ishtirokchilar: <b>{len(participants_list)} kishi</b>\n\n"
            f"🎉 <b>G'OLIB:</b> {winner_mention}\n"
            f"🏆 Yutuq: <b>+{total_amount} Almaz</b>",
            reply_markup=None,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

    await callback.answer(f"G'olib aniqlandi: {winner_user['name']}!", show_alert=True)


# ============================================================
# 💱 VALYUTA VA O'TKAZMALAR
# ============================================================

@dp.message(F.text.lower().startswith(("dgive", "/dgive")))
async def dgive_handler(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(
            "❌ Foydalanish:\n"
            "<code>Dgive 5</code> (5 ta Almaz olish uchun dollar sarflanadi)\n"
            "Kurs: <b>1500 Dollar = 1 Almaz</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        almaz_amount = int(parts[1])
        if almaz_amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Miqdor musbat raqam bo'lishi kerak.")
        return

    dollar_cost = almaz_amount * 1500
    user = db.get_user(message.from_user.id, message.from_user.full_name)

    if user["balance"] < dollar_cost:
        await message.answer(
            f"❌ Dollar yetarli emas!\nKerak: <b>{dollar_cost}</b> 💵\nSizda: <b>{user['balance']}</b> 💵",
            parse_mode=ParseMode.HTML,
        )
        return

    db.update(message.from_user.id, balance=user["balance"] - dollar_cost, almaz=user["almaz"] + almaz_amount)
    await message.answer(
        f"✅ <b>Valyuta ayirboshlash muvaffaqiyatli!</b>\n\n💵 Sarflandi: <b>{dollar_cost} dollar</b>\n💎 Qo'shildi: <b>{almaz_amount} Almaz</b>",
        parse_mode=ParseMode.HTML,
    )


@dp.message(F.text.lower().startswith(("dmoney", "/dmoney")))
async def dmoney_handler(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(
            "❌ Foydalanish:\n"
            "<code>Dmoney 2</code> (2 ta Almazni dollarga almashtirish)\n"
            "Kurs: <b>1 Almaz = 1000 Dollar</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        almaz_amount = int(parts[1])
        if almaz_amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Miqdor musbat raqam bo'lishi kerak.")
        return

    user = db.get_user(message.from_user.id, message.from_user.full_name)
    if user["almaz"] < almaz_amount:
        await message.answer(f"❌ Almaz yetarli emas!\nSizda: <b>{user['almaz']}</b> 💎", parse_mode=ParseMode.HTML)
        return

    dollar_gain = almaz_amount * 1000
    db.update(message.from_user.id, almaz=user["almaz"] - almaz_amount, balance=user["balance"] + dollar_gain)
    await message.answer(
        f"✅ <b>Valyuta ayirboshlash muvaffaqiyatli!</b>\n\n💎 Sarflandi: <b>{almaz_amount} Almaz</b>\n💵 Qo'shildi: <b>{dollar_gain} dollar</b>",
        parse_mode=ParseMode.HTML,
    )


@dp.message(F.text.lower().startswith(("money", "/money")))
async def money_transfer_handler(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(
            "❌ Foydalanish:\n"
            "<code>Money 100 @username</code> yoki xabarga javob berib <code>Money 100</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        amount_str = parts[1].replace("+", "")
        amount = int(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Miqdor musbat raqam bo'lishi kerak.")
        return

    target_text = parts[2] if len(parts) >= 3 else None
    target_id, target_name = await resolve_target(message, target_text)

    if not target_id:
        await message.answer("❌ Qabul qiluvchi topilmadi (foydalanuvchi nomi, ID yoki javob orqali).")
        return

    sender_id = message.from_user.id
    if sender_id == target_id:
        await message.answer("❌ O'zingizga dollar yubora olmaysiz!")
        return

    sender = db.get_user(sender_id, message.from_user.full_name)
    if sender["balance"] < amount:
        await message.answer(f"❌ Dollaringiz yetarli emas! Sizda: {sender['balance']} 💵")
        return

    target = db.get_user(target_id, target_name)

    db.update(sender_id, balance=sender["balance"] - amount)
    db.update(target_id, balance=target["balance"] + amount)

    await message.answer(
        f"✅ Muvaffaqiyatli o'tkazildi!\n\n"
        f"👤 Qabul qiluvchi: <b>{html.escape(target_name)}</b>\n"
        f"💵 Miqdor: <b>{amount} dollar</b>",
        parse_mode=ParseMode.HTML,
    )


@dp.message(F.text.lower().startswith(("give", "/give")))
async def give_transfer_handler(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(
            "❌ Foydalanish:\n"
            "<code>Give 5 @username</code> yoki xabarga javob berib <code>Give 5</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        amount_str = parts[1].replace("+", "")
        amount = int(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Miqdor musbat raqam bo'lishi kerak.")
        return

    target_text = parts[2] if len(parts) >= 3 else None
    target_id, target_name = await resolve_target(message, target_text)

    if not target_id:
        await message.answer("❌ Qabul qiluvchi topilmadi (foydalanuvchi nomi, ID yoki javob orqali).")
        return

    sender_id = message.from_user.id
    if sender_id == target_id:
        await message.answer("❌ O'zingizga Almaz yubora olmaysiz!")
        return

    sender = db.get_user(sender_id, message.from_user.full_name)
    if sender["almaz"] < amount:
        await message.answer(f"❌ Almazingiz yetarli emas! Sizda: {sender['almaz']} 💎")
        return

    target = db.get_user(target_id, target_name)

    db.update(sender_id, almaz=sender["almaz"] - amount)
    db.update(target_id, almaz=target["almaz"] + amount)

    await message.answer(
        f"✅ Muvaffaqiyatli o'tkazildi!\n\n"
        f"👤 Qabul qiluvchi: <b>{html.escape(target_name)}</b>\n"
        f"💎 Miqdor: <b>{amount} Almaz</b>",
        parse_mode=ParseMode.HTML,
    )


# ============================================================
# 🎁 SOVG'ALAR (SEND & MGIVE)
# ============================================================

@dp.message(F.text.lower().startswith(("send", "/send")))
@dp.channel_post(F.text.lower().startswith(("send", "/send")))
async def send_giveaway_handler(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer(
            "❌ Foydalanish:\n"
            "<code>Send 10 5</code> (10 ta Almazni 5 kishiga bo'lib berish)",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        total_amount = int(parts[1])
        max_claims = int(parts[2])
        if total_amount <= 0 or max_claims <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Miqdor va kishilar soni musbat raqam bo'lishi kerak.")
        return

    if message.chat.type == "channel" or not message.from_user:
        sender_id = PRIMARY_ADMIN_ID
        admin_user = db.get_user(PRIMARY_ADMIN_ID)
        sender_name = admin_user.get("name", "Admin")
    else:
        sender_id = message.from_user.id
        sender_name = message.from_user.full_name

    sender = db.get_user(sender_id, sender_name)

    if sender["almaz"] < total_amount:
        await message.answer(f"❌ Almazingiz yetarli emas! Sizda: {sender['almaz']} 💎")
        return

    amount_per_claim = max(1, total_amount // max_claims)
    actual_total = amount_per_claim * max_claims

    if sender["almaz"] < actual_total:
        await message.answer(f"❌ Almazingiz yetarli emas! Kerak: {actual_total} 💎")
        return

    db.update(sender_id, almaz=sender["almaz"] - actual_total)

    cursor = db.conn.cursor()
    cursor.execute(
        "INSERT INTO giveaways (sender_name, currency, total_amount, amount_per_claim, max_claims, claimed_users, chat_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (sender_name, "almaz", actual_total, amount_per_claim, max_claims, "", message.chat.id)
    )
    db.conn.commit()
    giveaway_id = cursor.lastrowid

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🎁 𝑂𝐿𝐼𝑆𝐻 (0/{max_claims})", callback_data=f"claim_gw_{giveaway_id}")]
        ]
    )

    await message.answer(
        f"🎁 <b>ALMAZ SOVG'ASI!</b>\n\n"
        f"👤 Tarqatuvchi: <b>{html.escape(sender_name)}</b>\n"
        f"💎 Jami: <b>{actual_total} Almaz</b>\n"
        f"👥 Limit: <b>{max_claims} kishi</b>\n"
        f"🏷 Har biriga: <b>{amount_per_claim} Almaz</b>\n\n"
        f"<b>Olgarlar ro'yxati (0 ta):</b>\n<i>Hali hech kim olmadi</i>\n\n"
        f"Pastdagi tugmani bosing va sovg'ani oling! 👇",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


@dp.message(F.text.lower().startswith(("mgive", "/mgive")))
@dp.channel_post(F.text.lower().startswith(("mgive", "/mgive")))
async def mgive_giveaway_handler(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer(
            "❌ Foydalanish:\n"
            "<code>MGive 500 5</code> (500 dollarni 5 kishiga bo'lib berish)",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        total_amount = int(parts[1])
        max_claims = int(parts[2])
        if total_amount <= 0 or max_claims <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Miqdor va kishilar soni musbat raqam bo'lishi kerak.")
        return

    if message.chat.type == "channel" or not message.from_user:
        sender_id = PRIMARY_ADMIN_ID
        admin_user = db.get_user(PRIMARY_ADMIN_ID)
        sender_name = admin_user.get("name", "Admin")
    else:
        sender_id = message.from_user.id
        sender_name = message.from_user.full_name

    sender = db.get_user(sender_id, sender_name)

    if sender["balance"] < total_amount:
        await message.answer(f"❌ Dollaringiz yetarli emas! Sizda: {sender['balance']} 💵")
        return

    amount_per_claim = max(1, total_amount // max_claims)
    actual_total = amount_per_claim * max_claims

    if sender["balance"] < actual_total:
        await message.answer(f"❌ Dollaringiz yetarli emas! Kerak: {actual_total} 💵")
        return

    db.update(sender_id, balance=sender["balance"] - actual_total)

    cursor = db.conn.cursor()
    cursor.execute(
        "INSERT INTO giveaways (sender_name, currency, total_amount, amount_per_claim, max_claims, claimed_users, chat_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (sender_name, "dollar", actual_total, amount_per_claim, max_claims, "", message.chat.id)
    )
    db.conn.commit()
    giveaway_id = cursor.lastrowid

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🎁 𝑂𝐿𝐼𝑆𝐻 (0/{max_claims})", callback_data=f"claim_gw_{giveaway_id}")]
        ]
    )

    await message.answer(
        f"🎁 <b>DOLLAR SOVG'ASI!</b>\n\n"
        f"👤 Tarqatuvchi: <b>{html.escape(sender_name)}</b>\n"
        f"💵 Jami: <b>{actual_total} dollar</b>\n"
        f"👥 Limit: <b>{max_claims} kishi</b>\n"
        f"🏷 Har biriga: <b>{amount_per_claim} dollar</b>\n\n"
        f"<b>Olgarlar ro'yxati (0 ta):</b>\n<i>Hali hech kim olmadi</i>\n\n"
        f"Pastdagi tugmani bosing va sovg'ani oling! 👇",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


@dp.callback_query(F.data.startswith("claim_gw_"))
async def claim_giveaway_callback(callback: CallbackQuery):
    giveaway_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    user_name = callback.from_user.full_name

    row = db.fetchone("SELECT * FROM giveaways WHERE id = ?", (giveaway_id,))
    if not row:
        await callback.answer("❌ Sovg'a topilmadi yoki tugagan!", show_alert=True)
        return

    currency = row["currency"]
    amount_per_claim = row["amount_per_claim"]
    max_claims = row["max_claims"]
    claimed_users_str = row["claimed_users"] or ""
    claimed_list = [int(uid) for uid in claimed_users_str.split(",") if uid.strip().isdigit()]

    if user_id in claimed_list:
        await callback.answer("⚠️ Siz allaqachon bu sovg'ani olgansiz!", show_alert=True)
        return

    if len(claimed_list) >= max_claims:
        await callback.answer("❌ Bu sovg'a allaqachon tugagan!", show_alert=True)
        return

    user = db.get_user(user_id, user_name)
    if currency == "almaz":
        db.update(user_id, almaz=user["almaz"] + amount_per_claim)
        prize_str = f"{amount_per_claim} Almaz"
    else:
        db.update(user_id, balance=user["balance"] + amount_per_claim)
        prize_str = f"{amount_per_claim} 💵 dollar"

    claimed_list.append(user_id)
    new_claimed_str = ",".join(map(str, claimed_list))
    db.conn.execute("UPDATE giveaways SET claimed_users = ? WHERE id = ?", (new_claimed_str, giveaway_id))
    db.conn.commit()

    current_claims = len(claimed_list)
    finished = current_claims >= max_claims

    mentions_list = []
    for uid in claimed_list:
        u = db.get_user(uid)
        mentions_list.append(f'<a href="tg://user?id={uid}">{html.escape(u["name"])}</a>')

    claimed_text = "\n".join(f"{idx+1}. {m}" for idx, m in enumerate(mentions_list))

    sender_name = html.escape(row["sender_name"] or "Foydalanuvchi")
    actual_total = row["total_amount"]
    curr_title = "ALMAZ SOVG'ASI!" if currency == "almaz" else "DOLLAR SOVG'ASI!"
    curr_icon = "💎" if currency == "almaz" else "💵"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🎁 𝑂𝐿𝐼𝑆𝐻 ({current_claims}/{max_claims})", callback_data=f"claim_gw_{giveaway_id}")]
        ]
    )

    try:
        await callback.message.edit_text(
            f"🎁 <b>{curr_title}</b>\n\n"
            f"👤 Tarqatuvchi: <b>{sender_name}</b>\n"
            f"{curr_icon} Jami: <b>{actual_total} {currency}</b>\n"
            f"👥 Limit: <b>{max_claims} kishi</b>\n"
            f"🏷 Har biriga: <b>{amount_per_claim} {currency}</b>\n\n"
            f"<b>Olgarlar ro'yxati ({current_claims}/{max_claims}):</b>\n{claimed_text}"
            + ("\n\n✅ <b>Sovg'a to'liq tarqatib bo'lindi!</b>" if finished else "\n\nPastdagi tugmani bosing va sovg'ani oling! 👇"),
            reply_markup=keyboard if not finished else None,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

    await callback.answer(f"🎉 Tabriklaymiz! Siz {prize_str} yutib oldingiz!", show_alert=True)


# ============================================================
# 🏢 BIZNES VA BIZNES LOYIHA
# ============================================================

async def business_handler_direct(message: Message, user_id: int, full_name: str):
    user = db.get_user(user_id, full_name)
    lvl = user["business_level"]
    project_lvl = user.get("project_level", 0)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏢 𝐵𝐼𝑍𝑁𝐸𝑆 𝐾𝐸𝑁𝐺𝐴𝑌𝑇𝐼𝑅𝐼𝑆𝐻 (10 Almaz)", callback_data=f"upgrade_business_{user_id}")],
            [InlineKeyboardButton(text="📊 𝐵𝐼𝑍𝑁𝐸𝑆 𝐿𝑂𝑌𝐼𝐻𝐴 (25 Almaz)", callback_data=f"upgrade_project_{user_id}")],
            [InlineKeyboardButton(text="💵 𝐹𝑂𝑌𝐷𝐴𝑁𝐼 𝑌𝐼𝐺'𝐼𝑆𝐻", callback_data=f"collect_business_{user_id}")],
        ]
    )
    await message.answer(
        f"🏢 <b><i>Biznes markazi</i></b>\n\n"
        f"Biznes darajangiz: <b>{lvl}</b>\n"
        f"Har 5 soatdagi daromad: <b>{500 * lvl} dollar</b> (1 daraja = 500💵)\n"
        f"Biznes loyiha darajasi: <b>{project_lvl}</b>",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


@dp.message(StateFilter("*"), F.text.func(lambda t: "biznes" in clean_text(t)))
async def business_handler(message: Message, state: FSMContext):
    await state.clear()
    await business_handler_direct(message, message.from_user.id, message.from_user.full_name)


@dp.callback_query(F.data.startswith("upgrade_business_"))
async def upgrade_business_cb(callback: CallbackQuery):
    parts = callback.data.split("_")
    owner_id = int(parts[2]) if len(parts) > 2 else callback.from_user.id
    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu tugma siz uchun emas!", show_alert=True)
        return

    user = db.get_user(callback.from_user.id, callback.from_user.full_name)
    if user["almaz"] < 10:
        await callback.answer("❌ Almaz yetarli emas! (10 ta kerak)", show_alert=True)
        return

    new_lvl = user["business_level"] + 1
    db.update(callback.from_user.id, almaz=user["almaz"] - 10, business_level=new_lvl)
    
    project_lvl = user.get("project_level", 0)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏢 𝐵𝐼𝑍𝑁𝐸𝑆 𝐾𝐸𝑁𝐺𝐴𝑌𝑇𝐼𝑅𝐼𝑆𝐻 (10 Almaz)", callback_data=f"upgrade_business_{owner_id}")],
            [InlineKeyboardButton(text="📊 𝐵𝐼𝑍𝑁𝐸𝑆 𝐿𝑂𝑌𝐼𝐻𝐴 (25 Almaz)", callback_data=f"upgrade_project_{owner_id}")],
            [InlineKeyboardButton(text="💵 𝐹𝑂𝑌𝐷𝐴𝑁𝐼 𝑌𝐼𝐺'𝐼𝑆𝐻", callback_data=f"collect_business_{owner_id}")],
        ]
    )
    try:
        await callback.message.edit_text(
            f"🏢 <b><i>Biznes markazi</i></b>\n\n"
            f"Biznes darajangiz: <b>{new_lvl}</b>\n"
            f"Har 5 soatdagi daromad: <b>{500 * new_lvl} dollar</b> (1 daraja = 500💵)\n"
            f"Biznes loyiha darajasi: <b>{project_lvl}</b>",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

    await callback.answer("🎉 Biznes kengaytirildi (10 Almaz sarflandi)!", show_alert=True)


@dp.callback_query(F.data.startswith("upgrade_project_"))
async def upgrade_project_cb(callback: CallbackQuery):
    parts = callback.data.split("_")
    owner_id = int(parts[2]) if len(parts) > 2 else callback.from_user.id
    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu tugma siz uchun emas!", show_alert=True)
        return

    user = db.get_user(callback.from_user.id, callback.from_user.full_name)
    if user["almaz"] < 25:
        await callback.answer("❌ Almaz yetarli emas! (25 ta kerak)", show_alert=True)
        return

    new_proj_lvl = user.get("project_level", 0) + 1
    db.update(callback.from_user.id, almaz=user["almaz"] - 25, project_level=new_proj_lvl)

    lvl = user["business_level"]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏢 𝐵𝐼𝑍𝑁𝐸𝑆 𝐾𝐸𝑁𝐺𝐴𝑌𝑇𝐼𝑅𝐼𝑆𝐻 (10 Almaz)", callback_data=f"upgrade_business_{owner_id}")],
            [InlineKeyboardButton(text="📊 𝐵𝐼𝑍𝑁𝐸𝑆 𝐿𝑂𝑌𝐼𝐻𝐴 (25 Almaz)", callback_data=f"upgrade_project_{owner_id}")],
            [InlineKeyboardButton(text="💵 𝐹𝑂𝑌𝐷𝐴𝑁𝐼 𝑌𝐼𝐺'𝐼𝑆𝐻", callback_data=f"collect_business_{owner_id}")],
        ]
    )
    try:
        await callback.message.edit_text(
            f"🏢 <b><i>Biznes markazi</i></b>\n\n"
            f"Biznes darajangiz: <b>{lvl}</b>\n"
            f"Har 5 soatdagi daromad: <b>{500 * lvl} dollar</b> (1 daraja = 500💵)\n"
            f"Biznes loyiha darajasi: <b>{new_proj_lvl}</b>",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

    await callback.answer("🚀 Biznes loyiha darajasi oshirildi!", show_alert=True)


@dp.callback_query(F.data.startswith("collect_business_"))
async def collect_business_cb(callback: CallbackQuery):
    parts = callback.data.split("_")
    owner_id = int(parts[2]) if len(parts) > 2 else callback.from_user.id
    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu tugma siz uchun emas!", show_alert=True)
        return

    user = db.get_user(callback.from_user.id, callback.from_user.full_name)
    lvl = user["business_level"]
    if lvl == 0:
        await callback.answer("❌ Sizda biznes yo'q!", show_alert=True)
        return

    now = time.time()
    last = user["last_business_collect"]
    cooldown = 5 * 3600  # 5 soat

    if last and now - last < cooldown:
        remaining = int(cooldown - (now - last))
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        await callback.answer(f"⏳ Foydani olish uchun yana {hours} soat {minutes} daqiqa kuting.", show_alert=True)
        return

    profit = 500 * lvl
    db.update(callback.from_user.id, balance=user["balance"] + profit, last_business_collect=now)
    await callback.answer(f"💵 +{profit} dollar olindi (Har 5 soatlik foyda)!", show_alert=True)


# ============================================================
# 🛒 DO'KON
# ============================================================

async def shop_handler_msg(message: Message):
    uid = message.from_user.id
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💎 50 𝐴𝑙𝑚𝑎𝑧 — 50,000 💵", callback_data=f"buy_item_2_{uid}")],
            [InlineKeyboardButton(text="⚡ 𝐸𝑛𝑒𝑟𝑔𝑒𝑡𝑖𝑘 — 200 💵 / 1 💎", callback_data=f"buy_opt_energy_{uid}")],
            [InlineKeyboardButton(text="🍀 𝑂𝑚𝑎𝑑 𝑡𝑖𝑙𝑠𝑖𝑚𝑖 — 5,000 💵 / 2 💎", callback_data=f"buy_opt_charm_{uid}")],
            [InlineKeyboardButton(text="🛡️ 𝐻𝑖𝑚𝑜𝑦𝑎 𝑞𝑎𝑙𝑞𝑜𝑛𝑖 — 10,000 💵 / 5 💎", callback_data=f"buy_opt_shield_{uid}")],
            [InlineKeyboardButton(text="🎁 𝐼𝑘𝑘𝑖 𝑘𝑎𝑟𝑟𝑎 𝑦𝑢𝑡𝑢𝑞 — 20,000 💵 / 10 💎", callback_data=f"buy_opt_double_{uid}")],
            [InlineKeyboardButton(text="🎲 𝑂𝑚𝑎𝑑𝑙𝑖 𝑧𝑎𝑟 — 15,000 💵 / 8 💎", callback_data=f"buy_opt_dice_{uid}")],
            [InlineKeyboardButton(text="👑 𝑉𝐼𝑃 𝑀𝑎𝑞𝑜𝑚 — 100,000 💵 / 50 💎", callback_data=f"buy_opt_vip_{uid}")],
        ]
    )
    await message.answer("🛒 <b>O'yin va Asboblar Do'koni</b>\n\nSotib olmoqchi bo'lgan mahsulotingizni tanlang:", reply_markup=keyboard, parse_mode=ParseMode.HTML)


@dp.message(StateFilter("*"), F.text.func(lambda t: "dokon" in clean_text(t)))
async def shop_text_handler(message: Message, state: FSMContext):
    await state.clear()
    await shop_handler_msg(message)


@dp.callback_query(F.data.startswith("buy_opt_"))
async def buy_options_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    item_type = parts[2]
    owner_id = int(parts[3]) if len(parts) > 3 else callback.from_user.id

    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu tugma siz uchun emas!", show_alert=True)
        return

    keyboard = None
    text = ""

    if item_type == "energy":
        text = "⚡ <b>Energetik</b> sotib olish valyutasini tanlang:"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💵 200 𝐷𝑜𝑙𝑙𝑎𝑟", callback_data=f"do_buy_energy_dollar_{owner_id}"),
             InlineKeyboardButton(text="💎 1 𝐴𝑙𝑚𝑎𝑧", callback_data=f"do_buy_energy_almaz_{owner_id}")],
            [InlineKeyboardButton(text="🔙 𝑂𝑟𝑞𝑎𝑔𝑎", callback_data=f"back_to_shop_{owner_id}")]
        ])
    elif item_type == "charm":
        text = "🍀 <b>Omad tilsimi</b> sotib olish valyutasini tanlang:"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💵 5,000 𝐷𝑜𝑙𝑙𝑎𝑟", callback_data=f"do_buy_charm_dollar_{owner_id}"),
             InlineKeyboardButton(text="💎 2 𝐴𝑙𝑚𝑎𝑧", callback_data=f"do_buy_charm_almaz_{owner_id}")],
            [InlineKeyboardButton(text="🔙 𝑂𝑟𝑞𝑎𝑔𝑎", callback_data=f"back_to_shop_{owner_id}")]
        ])
    elif item_type == "shield":
        text = "🛡️ <b>Himoya qalqoni</b> sotib olish valyutasini tanlang:"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💵 10,000 𝐷𝑜𝑙𝑙𝑎𝑟", callback_data=f"do_buy_shield_dollar_{owner_id}"),
             InlineKeyboardButton(text="💎 5 𝐴𝑙𝑚𝑎𝑧", callback_data=f"do_buy_shield_almaz_{owner_id}")],
            [InlineKeyboardButton(text="🔙 𝑂𝑟𝑞𝑎𝑔𝑎", callback_data=f"back_to_shop_{owner_id}")]
        ])
    elif item_type == "double":
        text = "🎁 <b>Ikki karra yutuq</b> sotib olish valyutasini tanlang:"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💵 20,000 𝐷𝑜𝑙𝑙𝑎𝑟", callback_data=f"do_buy_double_dollar_{owner_id}"),
             InlineKeyboardButton(text="💎 10 𝐴𝑙𝑚𝑎𝑧", callback_data=f"do_buy_double_almaz_{owner_id}")],
            [InlineKeyboardButton(text="🔙 𝑂𝑟𝑞𝑎𝑔𝑎", callback_data=f"back_to_shop_{owner_id}")]
        ])
    elif item_type == "dice":
        text = "🎲 <b>Omadli zar</b> sotib olish valyutasini tanlang:"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💵 15,000 𝐷𝑜𝑙𝑙𝑎𝑟", callback_data=f"do_buy_dice_dollar_{owner_id}"),
             InlineKeyboardButton(text="💎 8 𝐴𝑙𝑚𝑎𝑧", callback_data=f"do_buy_dice_almaz_{owner_id}")],
            [InlineKeyboardButton(text="🔙 𝑂𝑟𝑞𝑎𝑔𝑎", callback_data=f"back_to_shop_{owner_id}")]
        ])
    elif item_type == "vip":
        text = "👑 <b>VIP Maqom</b> sotib olish valyutasini tanlang:"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💵 100,000 𝐷𝑜𝑙𝑙𝑎𝑟", callback_data=f"do_buy_vip_dollar_{owner_id}"),
             InlineKeyboardButton(text="💎 50 𝐴𝑙𝑚𝑎𝑧", callback_data=f"do_buy_vip_almaz_{owner_id}")],
            [InlineKeyboardButton(text="🔙 𝑂𝑟𝑞𝑎𝑔𝑎", callback_data=f"back_to_shop_{owner_id}")]
        ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except Exception:
        pass
    await callback.answer()


@dp.callback_query(F.data.startswith("back_to_shop_"))
async def back_to_shop_cb(callback: CallbackQuery):
    parts = callback.data.split("_")
    owner_id = int(parts[3]) if len(parts) > 3 else callback.from_user.id
    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu tugma siz uchun emas!", show_alert=True)
        return

    uid = callback.from_user.id
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💎 50 𝐴𝑙𝑚𝑎𝑧 — 50,000 💵", callback_data=f"buy_item_2_{uid}")],
            [InlineKeyboardButton(text="⚡ 𝐸𝑛𝑒𝑟𝑔𝑒𝑡𝑖𝑘 — 200 💵 / 1 💎", callback_data=f"buy_opt_energy_{uid}")],
            [InlineKeyboardButton(text="🍀 𝑂𝑚𝑎𝑑 𝑡𝑖𝑙𝑠𝑖𝑚𝑖 — 5,000 💵 / 2 💎", callback_data=f"buy_opt_charm_{uid}")],
            [InlineKeyboardButton(text="🛡️ 𝐻𝑖𝑚𝑜𝑦𝑎 𝑞𝑎𝑙𝑞𝑜𝑛𝑖 — 10,000 💵 / 5 💎", callback_data=f"buy_opt_shield_{uid}")],
            [InlineKeyboardButton(text="🎁 𝐼𝑘𝑘𝑖 𝑘𝑎𝑟𝑟𝑎 𝑦𝑢𝑡𝑢𝑞 — 20,000 💵 / 10 💎", callback_data=f"buy_opt_double_{uid}")],
            [InlineKeyboardButton(text="🎲 𝑂𝑚𝑎𝑑𝑙𝑖 𝑧𝑎𝑟 — 15,000 💵 / 8 💎", callback_data=f"buy_opt_dice_{uid}")],
            [InlineKeyboardButton(text="👑 𝑉𝐼𝑃 𝑀𝑎𝑞𝑜𝑚 — 100,000 💵 / 50 💎", callback_data=f"buy_opt_vip_{uid}")],
        ]
    )
    try:
        await callback.message.edit_text("🛒 <b>O'yin va Asboblar Do'koni</b>\n\nSotib olmoqchi bo'lgan mahsulotingizni tanlang:", reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except Exception:
        pass
    await callback.answer()


@dp.callback_query(F.data.startswith("do_buy_"))
async def execute_buy_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    item_type = parts[2]
    currency = parts[3]
    owner_id = int(parts[4]) if len(parts) > 4 else callback.from_user.id

    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu tugma siz uchun emas!", show_alert=True)
        return

    user = db.get_user(callback.from_user.id, callback.from_user.full_name)

    if item_type == "energy":
        if currency == "dollar":
            if user["balance"] >= 200:
                db.update(owner_id, balance=user["balance"] - 200, energy_count=user["energy_count"] + 1)
                await callback.answer("✅ ⚡ Energetik sotib olindi!", show_alert=True)
            else:
                await callback.answer("❌ Dollar yetarli emas!", show_alert=True)
        elif currency == "almaz":
            if user["almaz"] >= 1:
                db.update(owner_id, almaz=user["almaz"] - 1, energy_count=user["energy_count"] + 1)
                await callback.answer("✅ ⚡ Energetik sotib olindi!", show_alert=True)
            else:
                await callback.answer("❌ Almaz yetarli emas!", show_alert=True)

    elif item_type == "charm":
        if currency == "dollar":
            if user["balance"] >= 5000:
                db.update(owner_id, balance=user["balance"] - 5000, charm_count=user["charm_count"] + 1)
                await callback.answer("✅ 🍀 Omad tilsimi sotib olindi!", show_alert=True)
            else:
                await callback.answer("❌ Dollar yetarli emas!", show_alert=True)
        elif currency == "almaz":
            if user["almaz"] >= 2:
                db.update(owner_id, almaz=user["almaz"] - 2, charm_count=user["charm_count"] + 1)
                await callback.answer("✅ 🍀 Omad tilsimi sotib olindi!", show_alert=True)
            else:
                await callback.answer("❌ Almaz yetarli emas!", show_alert=True)

    elif item_type == "shield":
        if currency == "dollar":
            if user["balance"] >= 10000:
                db.update(owner_id, balance=user["balance"] - 10000, shield_count=user["shield_count"] + 1)
                await callback.answer("✅ 🛡️ Himoya qalqoni sotib olindi!", show_alert=True)
            else:
                await callback.answer("❌ Dollar yetarli emas!", show_alert=True)
        elif currency == "almaz":
            if user["almaz"] >= 5:
                db.update(owner_id, almaz=user["almaz"] - 5, shield_count=user["shield_count"] + 1)
                await callback.answer("✅ 🛡️ Himoya qalqoni sotib olindi!", show_alert=True)
            else:
                await callback.answer("❌ Almaz yetarli emas!", show_alert=True)

    elif item_type == "double":
        if currency == "dollar":
            if user["balance"] >= 20000:
                db.update(owner_id, balance=user["balance"] - 20000, double_win_count=user["double_win_count"] + 1)
                await callback.answer("✅ 🎁 Ikki karra yutuq asbobi olindi!", show_alert=True)
            else:
                await callback.answer("❌ Dollar yetarli emas!", show_alert=True)
        elif currency == "almaz":
            if user["almaz"] >= 10:
                db.update(owner_id, almaz=user["almaz"] - 10, double_win_count=user["double_win_count"] + 1)
                await callback.answer("✅ 🎁 Ikki karra yutuq asbobi olindi!", show_alert=True)
            else:
                await callback.answer("❌ Almaz yetarli emas!", show_alert=True)

    elif item_type == "dice":
        if currency == "dollar":
            if user["balance"] >= 15000:
                db.update(owner_id, balance=user["balance"] - 15000, lucky_dice_count=user["lucky_dice_count"] + 1)
                await callback.answer("✅ 🎲 Omadli zar asbobi olindi!", show_alert=True)
            else:
                await callback.answer("❌ Dollar yetarli emas!", show_alert=True)
        elif currency == "almaz":
            if user["almaz"] >= 8:
                db.update(owner_id, almaz=user["almaz"] - 8, lucky_dice_count=user["lucky_dice_count"] + 1)
                await callback.answer("✅ 🎲 Omadli zar asbobi olindi!", show_alert=True)
            else:
                await callback.answer("❌ Almaz yetarli emas!", show_alert=True)

    elif item_type == "vip":
        if user.get("vip_status", 0) == 1:
            await callback.answer("⚠️ Sizda allaqachon VIP Maqom faol!", show_alert=True)
            return

        if currency == "dollar":
            if user["balance"] >= 100000:
                db.update(owner_id, balance=user["balance"] - 100000, vip_status=1)
                await callback.answer("✅ 👑 VIP Maqom faollashtirildi!", show_alert=True)
            else:
                await callback.answer("❌ Dollar yetarli emas!", show_alert=True)
        elif currency == "almaz":
            if user["almaz"] >= 50:
                db.update(owner_id, almaz=user["almaz"] - 50, vip_status=1)
                await callback.answer("✅ 👑 VIP Maqom faollashtirildi!", show_alert=True)
            else:
                await callback.answer("❌ Almaz yetarli emas!", show_alert=True)


@dp.callback_query(F.data.startswith("buy_item_"))
async def buy_item_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    item_id = int(parts[2])
    owner_id = int(parts[3]) if len(parts) > 3 else callback.from_user.id

    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu tugma siz uchun emas!", show_alert=True)
        return

    user = db.get_user(callback.from_user.id, callback.from_user.full_name)

    if item_id == 2 and user["balance"] >= 50000:
        db.update(callback.from_user.id, balance=user["balance"] - 50000, almaz=user["almaz"] + 50)
        await callback.answer("✅ 50 ta Almaz qo'shildi!", show_alert=True)
    else:
        await callback.answer("❌ Balans yetarli emas!", show_alert=True)


# ============================================================
# 🎮 O'YINLAR ZALI
# ============================================================

def games_keyboard(owner_id: int = 0):
    sfx = f"_{owner_id}" if owner_id else ""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎰 𝐾𝐴𝑍𝐼𝑁𝑂", callback_data=f"game_start_casino{sfx}"),
             InlineKeyboardButton(text="🎯 𝑅𝑈𝐿𝐸𝑇𝐾𝐴", callback_data=f"game_start_ruletka{sfx}")],
            [InlineKeyboardButton(text="🎲 𝑍𝐴𝑅", callback_data=f"game_start_zar{sfx}"),
             InlineKeyboardButton(text="🪙 𝑇𝐴𝑁𝐺𝐴 (𝑂'𝑦𝑖𝑛)", callback_data=f"game_start_tanga{sfx}")],
            [InlineKeyboardButton(text="✊ 𝑇𝑂𝑆𝐻-𝑄𝐴𝑌𝐶𝐻𝐼", callback_data=f"game_start_rps{sfx}"),
             InlineKeyboardButton(text="❌⭕ 𝑋-𝑂", callback_data=f"game_start_tictactoe{sfx}")],
            [InlineKeyboardButton(text="⚽ 𝑃𝐸𝑁𝐴𝐿𝑇𝐼", callback_data=f"game_start_penalty{sfx}"),
             InlineKeyboardButton(text="🏴‍☠️ 𝑋𝐴𝑍𝐼𝑁𝐴", callback_data=f"game_start_treasure{sfx}")],
            [InlineKeyboardButton(text="🎣 𝐵𝐴𝐿𝐼𝑄", callback_data=f"game_start_fishing{sfx}"),
             InlineKeyboardButton(text="🧠 𝑉𝐼𝐾𝑇𝑂𝑅𝐼𝑁𝐴", url="https://t.me/Nexcode_ViktorinaBot")],
            [InlineKeyboardButton(text="💣 𝑀𝐼𝑁𝐴𝑀𝐴-𝑀𝐼𝑁", callback_data=f"game_start_mines{sfx}")],
        ]
    )


@dp.message(StateFilter("*"), F.text.func(lambda t: "oyinlar" in clean_text(t)))
async def games_menu_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🎮 <b>O'YINLAR ZALI</b>\n\nO'yinni tanlang: 👇", reply_markup=games_keyboard(message.from_user.id), parse_mode=ParseMode.HTML)


@dp.callback_query(F.data.startswith("back_to_games"))
async def back_to_games_cb(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    owner_id = int(parts[3]) if len(parts) > 3 else callback.from_user.id
    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu tugma siz uchun emas!", show_alert=True)
        return
    await state.clear()
    try:
        await callback.message.edit_text("🎮 <b>O'YINLAR ZALI</b>\n\nO'yinni tanlang: 👇", reply_markup=games_keyboard(owner_id), parse_mode=ParseMode.HTML)
    except Exception:
        pass
    await callback.answer()


# ============================================================
# ❌⭕ HAQIQIY X-O O'YINI (SUNIY INTELEKT/BOT BOSH_KATAKNI O'YNAYDI)
# ============================================================

def check_ttt_winner(board):
    lines = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    ]
    for a, b, c in lines:
        if board[a] != " " and board[a] == board[b] == board[c]:
            return board[a]
    if " " not in board:
        return "DRAW"
    return None

@dp.callback_query(F.data.startswith("game_start_tictactoe"))
async def start_tictactoe(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    owner_id = int(parts[3]) if len(parts) > 3 else callback.from_user.id
    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu tugma siz uchun emas!", show_alert=True)
        return

    board = [" " for _ in range(9)]
    await state.update_data(board=board, owner_id=owner_id)
    await show_tictactoe_board(callback.message, board, "Sizning navbatingiz (❌). Katakni tanlang:", edit=True, owner_id=owner_id)
    await callback.answer()


async def show_tictactoe_board(message: Message, board: list, text: str, edit: bool = False, owner_id: int = 0):
    buttons = []
    for r in range(3):
        row = []
        for c in range(3):
            idx = r * 3 + c
            val = board[idx]
            symbol = "❌" if val == "X" else "⭕" if val == "O" else "⬜"
            row.append(InlineKeyboardButton(text=symbol, callback_data=f"ttt_{idx}_{owner_id}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="🔙 𝐶𝐻𝐼𝑄𝐼𝑆𝐻", callback_data=f"back_to_games_{owner_id}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    if edit:
        try:
            await message.edit_text(f"❌⭕ <b>X-O o'yini</b>\n\n{text}", reply_markup=keyboard, parse_mode=ParseMode.HTML)
        except Exception:
            pass
    else:
        await message.answer(f"❌⭕ <b>X-O o'yini</b>\n\n{text}", reply_markup=keyboard, parse_mode=ParseMode.HTML)


@dp.callback_query(F.data.startswith("ttt_"))
async def process_tictactoe_move(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    idx = int(parts[1])
    owner_id = int(parts[2]) if len(parts) > 2 else callback.from_user.id

    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu o'yin sizniki emas!", show_alert=True)
        return

    data = await state.get_data()
    if "board" not in data:
        await callback.answer("O'yin tugagan!", show_alert=True)
        return

    board = data["board"]
    if board[idx] != " ":
        await callback.answer("Bu katak band!", show_alert=True)
        return

    # User yurishi
    board[idx] = "X"
    winner = check_ttt_winner(board)

    if not winner:
        # Bot yurishi (bo'sh kataklar orasidan tasodifiy tanlaydi)
        empty_indices = [i for i, x in enumerate(board) if x == " "]
        if empty_indices:
            bot_idx = random.choice(empty_indices)
            board[bot_idx] = "O"
            winner = check_ttt_winner(board)

    await state.update_data(board=board)

    if winner == "X":
        user = db.get_user(callback.from_user.id, callback.from_user.full_name)
        reward = 150
        if user["double_win_count"] > 0:
            db.update(callback.from_user.id, double_win_count=user["double_win_count"] - 1)
            reward *= 2

        db.update(callback.from_user.id, balance=user["balance"] + reward, points=user["points"] + 15)
        update_game_result(callback.from_user.id, "win")

        await show_tictactoe_board(callback.message, board, f"🎉 <b>Tabriklaymiz! Siz g'alaba qozondingiz!</b>\n+{reward} dollar 💵", edit=True, owner_id=owner_id)
        await state.clear()

    elif winner == "O":
        update_game_result(callback.from_user.id, "loss")
        await show_tictactoe_board(callback.message, board, "😢 <b>Afsuski, bot g'alaba qozondi!</b>", edit=True, owner_id=owner_id)
        await state.clear()

    elif winner == "DRAW":
        update_game_result(callback.from_user.id, "draw")
        await show_tictactoe_board(callback.message, board, "🤝 <b>Durang! Ajoyib o'yin bo'ldi.</b>", edit=True, owner_id=owner_id)
        await state.clear()

    else:
        await show_tictactoe_board(callback.message, board, "Sizning navbatingiz (❌):", edit=True, owner_id=owner_id)

    await callback.answer()


# ============================================================
# 🎰 STAVKALI O'YINLAR
# ============================================================

@dp.callback_query(F.data.startswith("game_start_") & ~F.data.startswith("game_start_tictactoe"))
async def start_custom_bet_game(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    game_type = parts[2]
    owner_id = int(parts[3]) if len(parts) > 3 else callback.from_user.id

    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu o'yin sizniki emas!", show_alert=True)
        return

    await state.update_data(game_type=game_type, owner_id=owner_id)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💵 𝐷𝑂𝐿𝐿𝐴𝑅", callback_data=f"gval_balance_{owner_id}"), InlineKeyboardButton(text="💎 𝐴𝐿𝑀𝐴𝑍", callback_data=f"gval_almaz_{owner_id}")],
            [InlineKeyboardButton(text="🔙 𝑂𝑅𝑄𝐴𝐺𝐴", callback_data=f"back_to_games_{owner_id}")],
        ]
    )
    try:
        await callback.message.edit_text("💰 Qaysi valyutada tikishni xohlaysiz?", reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except Exception:
        pass
    await state.set_state(GameState.waiting_for_currency)
    await callback.answer()


@dp.callback_query(GameState.waiting_for_currency, F.data.startswith("gval_"))
async def process_game_currency(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    currency = parts[1]
    owner_id = int(parts[2]) if len(parts) > 2 else callback.from_user.id

    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu tugma siz uchun emas!", show_alert=True)
        return

    await state.update_data(currency=currency)
    icon = "💵" if currency == "balance" else "💎"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"{icon} 50", callback_data=f"gamt_50_{owner_id}"),
                InlineKeyboardButton(text=f"{icon} 100", callback_data=f"gamt_100_{owner_id}"),
                InlineKeyboardButton(text=f"{icon} 150", callback_data=f"gamt_150_{owner_id}"),
            ],
            [
                InlineKeyboardButton(text=f"{icon} 200", callback_data=f"gamt_200_{owner_id}"),
                InlineKeyboardButton(text=f"{icon} 250", callback_data=f"gamt_250_{owner_id}"),
                InlineKeyboardButton(text=f"{icon} 300", callback_data=f"gamt_300_{owner_id}"),
            ],
            [
                InlineKeyboardButton(text=f"{icon} 500", callback_data=f"gamt_500_{owner_id}"),
                InlineKeyboardButton(text=f"{icon} 1000", callback_data=f"gamt_1000_{owner_id}"),
            ],
            [InlineKeyboardButton(text="🔙 𝑂𝑅𝑄𝐴𝐺𝐴", callback_data=f"back_to_games_{owner_id}")],
        ]
    )
    try:
        await callback.message.edit_text(f"Tanlangan valyuta: <b>{'DOLLAR' if currency=='balance' else 'ALMAZ'}</b>\nTikish miqdorini tanlang yoki raqam yuboring:", reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except Exception:
        pass
    await state.set_state(GameState.waiting_for_amount)
    await callback.answer()


@dp.callback_query(GameState.waiting_for_amount, F.data.startswith("gamt_"))
async def process_amount_callback(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    amount = int(parts[1])
    owner_id = int(parts[2]) if len(parts) > 2 else callback.from_user.id

    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu tugma siz uchun emas!", show_alert=True)
        return

    await execute_game_logic(callback.message, state, amount, callback.from_user.id, callback.from_user.full_name, True)
    await callback.answer()


@dp.message(GameState.waiting_for_amount)
async def process_amount_text(message: Message, state: FSMContext):
    try:
        amount = int((message.text or "").strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Faqat musbat raqam kiriting:")
        return
    await execute_game_logic(message, state, amount, message.from_user.id, message.from_user.full_name, False)


async def execute_game_logic(msg, state: FSMContext, amount: int, user_id: int, full_name: str, is_callback: bool):
    data = await state.get_data()
    if "currency" not in data or "game_type" not in data:
        await msg.answer("❌ O'yin holati topilmadi.")
        await state.clear()
        return

    currency = data["currency"]
    game_type = data["game_type"]
    user = db.get_user(user_id, full_name)
    
    balance = user["balance"] if currency == "balance" else user["almaz"]
    curr_name = "dollar" if currency == "balance" else "Almaz"

    if amount > balance:
        await msg.answer(f"❌ Balans yetarli emas!\nSizda: {balance}")
        return

    def update_currency(value):
        if currency == "balance":
            db.update(user_id, balance=value)
        else:
            db.update(user_id, almaz=value)

    if game_type == "casino":
        # Kazino animatsiyasi uchun Telegramning rasmiy Slot Machine emojisi
        slot_msg = await msg.bot.send_dice(chat_id=msg.chat.id, emoji="🎰")
        val = slot_msg.dice.value
        await asyncio.sleep(2.5)

        # 64 - Uchta bir xil belgi (Jackpot / Yutuq)
        if val in [1, 22, 43, 64]:
            reward, _ = apply_charm_bonus(user_id, amount * 2)
            if user["double_win_count"] > 0:
                db.update(user_id, double_win_count=user["double_win_count"] - 1)
                reward *= 2
            update_currency(balance + reward)
            update_game_result(user_id, "win")
            text = f"🎰 <b>Kazino:</b>\n🎉 Tabriklaymiz! 777 tushdi! +{reward} {curr_name}"
        else:
            update_currency(max(0, balance - amount))
            update_game_result(user_id, "loss")
            text = f"🎰 <b>Kazino:</b>\n😢 Omad kelmadi! -{amount} {curr_name}"
        await finish_game_result(msg, state, text, True, f"game_start_casino_{user_id}", user_id)

    elif game_type == "ruletka":
        # Ruletka adolatli sonlar orqali aniqlanadi (1 dan 36 gacha)
        landed_number = random.randint(1, 36)
        win = (landed_number % 2 == 0) # Juft son tushsa yutadi

        if win:
            reward, _ = apply_charm_bonus(user_id, int(amount * 1.5))
            if user["double_win_count"] > 0:
                db.update(user_id, double_win_count=user["double_win_count"] - 1)
                reward *= 2
            update_currency(balance + reward)
            update_game_result(user_id, "win")
            text = f"🎯 <b>Ruletka ({landed_number}):</b>\n🎉 Juft son tushdi! Yutdingiz! +{reward} {curr_name}"
        else:
            update_currency(max(0, balance - amount))
            update_game_result(user_id, "loss")
            text = f"🎯 <b>Ruletka ({landed_number}):</b>\n😢 Toq son tushdi! Yutqazdingiz! -{amount} {curr_name}"
        await finish_game_result(msg, state, text, is_callback, f"game_start_ruletka_{user_id}", user_id)

    elif game_type == "zar":
        dice_msg = await msg.bot.send_dice(chat_id=msg.chat.id, emoji="🎲")
        val = dice_msg.dice.value
        await asyncio.sleep(2.5)
        
        # Zar natijasi: 4, 5, 6 tushsa yutuq
        win = val >= 4
        if user["lucky_dice_count"] > 0 and not win:
            db.update(user_id, lucky_dice_count=user["lucky_dice_count"] - 1)
            win = True

        if win:
            reward, _ = apply_charm_bonus(user_id, int(amount * 1.3))
            if user["double_win_count"] > 0:
                db.update(user_id, double_win_count=user["double_win_count"] - 1)
                reward *= 2
            update_currency(balance + reward)
            update_game_result(user_id, "win")
            text = f"🎲 <b>Zar ({val}):</b>\n🎉 Yutdingiz! +{reward} {curr_name}"
        else:
            update_currency(max(0, balance - amount))
            update_game_result(user_id, "loss")
            text = f"🎲 <b>Zar ({val}):</b>\n😢 Yutqazdingiz! -{amount} {curr_name}"
        await finish_game_result(msg, state, text, True, f"game_start_zar_{user_id}", user_id)

    elif game_type == "fishing":
        catch = random.choice(["empty", "small", "big", "golden"])
        if catch == "empty":
            update_currency(max(0, balance - amount))
            update_game_result(user_id, "loss")
            text = f"🎣 <b>Baliq ovlash:</b>\nHech narsa ilinmadi! -{amount} {curr_name}"
        elif catch == "small":
            reward, _ = apply_charm_bonus(user_id, int(amount * 0.8))
            if user["double_win_count"] > 0:
                db.update(user_id, double_win_count=user["double_win_count"] - 1)
                reward *= 2
            update_currency(balance + reward)
            update_game_result(user_id, "win")
            text = f"🎣 <b>Baliq ovlash:</b>\nKichkina baliq! +{reward} {curr_name}"
        elif catch == "big":
            reward, _ = apply_charm_bonus(user_id, int(amount * 1.5))
            if user["double_win_count"] > 0:
                db.update(user_id, double_win_count=user["double_win_count"] - 1)
                reward *= 2
            update_currency(balance + reward)
            update_game_result(user_id, "win")
            text = f"🎣 <b>Baliq ovlash:</b>\nKatta baliq! +{reward} {curr_name}"
        else:
            reward, _ = apply_charm_bonus(user_id, amount * 3)
            if user["double_win_count"] > 0:
                db.update(user_id, double_win_count=user["double_win_count"] - 1)
                reward *= 2
            update_currency(balance + reward)
            update_game_result(user_id, "win")
            text = f"🎣 <b>Baliq ovlash:</b>\n🌟 Oltin baliq! +{reward} {curr_name} (3x)"
        await finish_game_result(msg, state, text, is_callback, f"game_start_fishing_{user_id}", user_id)

    elif game_type == "tanga":
        await state.update_data(amount=amount)
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🪙 𝑂𝑅𝑂𝐿", callback_data=f"tchoice_1_{user_id}"), InlineKeyboardButton(text="🦅 𝐺𝐸𝑅𝐵", callback_data=f"tchoice_2_{user_id}")],
                [InlineKeyboardButton(text="🔙 𝑂𝑅𝑄𝐴𝐺𝐴", callback_data=f"back_to_games_{user_id}")],
            ]
        )
        await state.set_state(GameState.waiting_for_choice)
        text = "🪙 Tanga o'yini: qaysi tomoniga tushishini tanlang:"
        if is_callback:
            await msg.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        else:
            await msg.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    elif game_type == "rps":
        await state.update_data(amount=amount)
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🪨 𝑇𝑂𝑆𝐻", callback_data=f"rps_tosh_{user_id}"), InlineKeyboardButton(text="📄 𝑄𝑂𝐺'𝑂𝑍", callback_data=f"rps_qogoz_{user_id}"), InlineKeyboardButton(text="✂️ 𝑄𝐴𝑌𝐶𝐻𝐼", callback_data=f"rps_qaychi_{user_id}")],
                [InlineKeyboardButton(text="🔙 𝑂𝑅𝑄𝐴𝐺𝐴", callback_data=f"back_to_games_{user_id}")],
            ]
        )
        await state.set_state(GameState.waiting_for_choice)
        text = "✊ Variantingizni tanlang:"
        if is_callback:
            await msg.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        else:
            await msg.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    elif game_type == "penalty":
        await state.update_data(amount=amount)
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="👈 𝐶𝐻𝐴𝑃𝐺𝐴", callback_data=f"pen_left_{user_id}"),
                    InlineKeyboardButton(text="⚽ 𝑂'𝑅𝑇𝐴", callback_data=f"pen_center_{user_id}"),
                    InlineKeyboardButton(text="👉 𝑂'𝑁𝐺𝐺𝐴", callback_data=f"pen_right_{user_id}")
                ],
                [InlineKeyboardButton(text="🔙 𝑂𝑅𝑄𝐴𝐺𝐴", callback_data=f"back_to_games_{user_id}")],
            ]
        )
        await state.set_state(GameState.waiting_for_choice)
        text = "⚽ <b>Penalti (3 talik tanlov):</b>\nZarba yo'nalishini tanlang:"
        if is_callback:
            await msg.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        else:
            await msg.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    elif game_type == "treasure":
        await state.update_data(amount=amount)
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="📦 1-𝑆𝐴𝑁𝐷𝐼𝑄", callback_data=f"trea_1_{user_id}"),
                    InlineKeyboardButton(text="📦 2-𝑆𝐴𝑁𝐷𝐼𝑄", callback_data=f"trea_2_{user_id}"),
                    InlineKeyboardButton(text="📦 3-𝑆𝐴𝑁𝐷𝐼𝑄", callback_data=f"trea_3_{user_id}")
                ],
                [InlineKeyboardButton(text="🔙 𝑂𝑅𝑄𝐴𝐺𝐴", callback_data=f"back_to_games_{user_id}")],
            ]
        )
        await state.set_state(GameState.waiting_for_choice)
        text = "🏴‍☠️ <b>Xazina (3 ta sandiq):</b>\nQaysi sandiqni ochmoqchisiz?"
        if is_callback:
            await msg.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        else:
            await msg.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    elif game_type == "mines":
        update_currency(balance - amount)
        mines = random.sample(range(9), 3)
        await state.update_data(
            mines=mines,
            opened=[],
            multiplier=1.0,
            amount=amount,
            currency=currency,
            owner_id=user_id
        )
        await state.set_state(GameState.waiting_for_choice)
        symbol = "💎" if currency == "almaz" else "💵"
        await show_mines_board_msg(msg, [], 1.0, f"💣 <b>Minama-min o'yini boshlandi! (3 ta mina)</b>\nMinaga tegmasdan {symbol} larni oching:", is_callback, user_id, currency)


async def show_mines_board_msg(msg, opened, multiplier, text, is_callback=False, owner_id: int = 0, currency: str = "balance"):
    symbol = "💎" if currency == "almaz" else "💵"
    buttons = []
    for r in range(3):
        row = []
        for c in range(3):
            idx = r * 3 + c
            if idx in opened:
                sym = symbol
                cb = f"mine_noop_{idx}_{owner_id}"
            else:
                sym = "🟩"
                cb = f"mine_click_{idx}_{owner_id}"
            row.append(InlineKeyboardButton(text=sym, callback_data=cb))
        buttons.append(row)
    
    if opened:
        buttons.append([InlineKeyboardButton(text=f"💰 𝑁𝐴𝑄𝐷 𝑄𝐼𝐿𝐼𝑆𝐻 ({multiplier:.1f}x)", callback_data=f"mine_cashout_{owner_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 𝐶𝐻𝐼𝑄𝐼𝑆𝐻", callback_data=f"back_to_games_{owner_id}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    full_text = f"{text}\n\n📊 Joriy koeffitsiyent: <b>{multiplier:.1f}x</b>"
    
    if is_callback:
        try:
            await msg.edit_text(full_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        except Exception:
            await msg.answer(full_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        await msg.answer(full_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


@dp.callback_query(GameState.waiting_for_choice, F.data.startswith("mine_click_"))
async def process_mine_click(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    idx = int(parts[2])
    owner_id = int(parts[3]) if len(parts) > 3 else callback.from_user.id

    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu o'yin sizniki emas!", show_alert=True)
        return

    data = await state.get_data()
    if "mines" not in data:
        await callback.answer("O'yin tugagan!", show_alert=True)
        return

    mines = data["mines"]
    opened = data["opened"]
    multiplier = data["multiplier"]
    amount = data["amount"]
    currency = data["currency"]
    user_id = callback.from_user.id
    user = db.get_user(user_id, callback.from_user.full_name)
    
    curr_name = "dollar" if currency == "balance" else "Almaz"
    symbol = "💎" if currency == "almaz" else "💵"

    if idx in mines:
        if user["shield_count"] > 0:
            db.update(user_id, shield_count=user["shield_count"] - 1)
            await callback.answer("🛡️ Himoya qalqoni portlashdan saqlab qoldi!", show_alert=True)
            return

        update_game_result(user_id, "loss")
        buttons = []
        for r in range(3):
            row = []
            for c in range(3):
                i = r * 3 + c
                if i in mines:
                    sym = "💣"
                elif i in opened:
                    sym = symbol
                else:
                    sym = "🟩"
                row.append(InlineKeyboardButton(text=sym, callback_data=f"mine_noop_{i}_{owner_id}"))
            buttons.append(row)
        buttons.append([InlineKeyboardButton(text="🔄 𝑄𝐴𝑌𝑇𝐴 𝑂'𝑌𝐼𝑁𝐴𝑆𝐻", callback_data=f"game_start_mines_{owner_id}"), InlineKeyboardButton(text="🔙 𝑀𝐸𝑁𝑌𝑈", callback_data=f"back_to_games_{owner_id}")])

        await state.clear()
        await callback.message.edit_text(
            f"💥 <b>Minaga bosdingiz!</b>\nAfsuski yutqazdingiz: -{amount} {curr_name}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode=ParseMode.HTML,
        )
        await callback.answer("BOOM! Mina portladi!", show_alert=True)
        return

    if idx not in opened:
        opened.append(idx)
        multiplier = round(multiplier + 0.35, 1)

    if len(opened) >= 6:
        reward = int(amount * multiplier)
        if user["double_win_count"] > 0:
            db.update(user_id, double_win_count=user["double_win_count"] - 1)
            reward *= 2

        if currency == "balance":
            db.update(user_id, balance=user["balance"] + reward)
        else:
            db.update(user_id, almaz=user["almaz"] + reward)
        update_game_result(user_id, "win")

        await state.clear()
        await callback.message.edit_text(
            f"🎉 <b>Tabriklaymiz! {symbol} larni muvaffaqiyatli oldingiz!</b>\n\n💰 Yutuq: <b>+{reward} {curr_name}</b> ({multiplier}x)",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 𝑄𝐴𝑌𝑇𝐴 𝑂'𝑌𝐼𝑁𝐴𝑆𝐻", callback_data=f"game_start_mines_{owner_id}"), InlineKeyboardButton(text="🔙 𝑀𝐸𝑁𝑌𝑈", callback_data=f"back_to_games_{owner_id}")]]) ,
            parse_mode=ParseMode.HTML,
        )
        await callback.answer("Ajoyib g'alaba!", show_alert=True)
        return

    await state.update_data(opened=opened, multiplier=multiplier)

    buttons = []
    for r in range(3):
        row = []
        for c in range(3):
            i = r * 3 + c
            if i in opened:
                sym = symbol
                cb = f"mine_noop_{i}_{owner_id}"
            else:
                sym = "🟩"
                cb = f"mine_click_{i}_{owner_id}"
            row.append(InlineKeyboardButton(text=sym, callback_data=cb))
        buttons.append(row)

    win_preview = int(amount * multiplier)
    buttons.append([InlineKeyboardButton(text=f"💰 𝑁𝐴𝑄𝐷 𝑄𝐼𝐿𝐼𝑆𝐻 (+{win_preview} {curr_name})", callback_data=f"mine_cashout_{owner_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 𝐶𝐻𝐼𝑄𝐼𝑆𝐻", callback_data=f"back_to_games_{owner_id}")])

    await callback.message.edit_text(
        f"💣 <b>Minama-min o'yini (3 ta mina)</b>\n{symbol} topildi! Davom eting yoki pulni oling.\n\n📊 Joriy koeffitsiyent: <b>{multiplier}x</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode=ParseMode.HTML,
    )
    await callback.answer(f"Topildi! {symbol}")


@dp.callback_query(GameState.waiting_for_choice, F.data.startswith("mine_cashout_"))
async def process_mine_cashout(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    owner_id = int(parts[2]) if len(parts) > 2 else callback.from_user.id

    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu o'yin sizniki emas!", show_alert=True)
        return

    data = await state.get_data()
    if "mines" not in data or not data["opened"]:
        await callback.answer("Hali katak ochmadingiz!", show_alert=True)
        return

    multiplier = data["multiplier"]
    amount = data["amount"]
    currency = data["currency"]
    user_id = callback.from_user.id
    user = db.get_user(user_id, callback.from_user.full_name)
    curr_name = "dollar" if currency == "balance" else "Almaz"

    reward = int(amount * multiplier)
    if user["double_win_count"] > 0:
        db.update(user_id, double_win_count=user["double_win_count"] - 1)
        reward *= 2

    if currency == "balance":
        db.update(user_id, balance=user["balance"] + reward)
    else:
        db.update(user_id, almaz=user["almaz"] + reward)
    update_game_result(user_id, "win")

    await state.clear()
    await callback.message.edit_text(
        f"💰 <b>Muvaffaqiyatli naqd qilindi!</b>\n\n🎉 Yutuq: <b>+{reward} {curr_name}</b> ({multiplier}x)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 𝑄𝐴𝑌𝑇𝐴 𝑂'𝑌𝐼𝑁𝐴𝑆𝐻", callback_data=f"game_start_mines_{owner_id}"), InlineKeyboardButton(text="🔙 𝑀𝐸𝑁𝑌𝑈", callback_data=f"back_to_games_{owner_id}")]]) ,
        parse_mode=ParseMode.HTML,
    )
    await callback.answer("Pul muvaffaqiyatli olindi!", show_alert=True)


async def finish_game_result(msg, state, text, is_callback, restart_cb, owner_id: int):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 𝑄𝐴𝑌𝑇𝐴 𝑂'𝑌𝐼𝑁𝐴𝑆𝐻", callback_data=restart_cb)],
            [InlineKeyboardButton(text="🔙 𝑀𝐸𝑁𝑌𝑈", callback_data=f"back_to_games_{owner_id}")],
        ]
    )
    await state.clear()
    if is_callback:
        try:
            await msg.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        except Exception:
            await msg.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        await msg.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


@dp.callback_query(GameState.waiting_for_choice, F.data.startswith("tchoice_"))
async def process_tanga_choice(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    choice = int(parts[1])
    owner_id = int(parts[2]) if len(parts) > 2 else callback.from_user.id

    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu o'yin sizniki emas!", show_alert=True)
        return

    data = await state.get_data()
    currency = data["currency"]
    amount = data["amount"]
    user_id = callback.from_user.id
    user = db.get_user(user_id, callback.from_user.full_name)
    
    balance = user["balance"] if currency == "balance" else user["almaz"]
    curr_name = "dollar" if currency == "balance" else "Almaz"

    result = random.choice([1, 2])
    win = (choice == result)

    if win:
        reward, _ = apply_charm_bonus(user_id, amount)
        if user["double_win_count"] > 0:
            db.update(user_id, double_win_count=user["double_win_count"] - 1)
            reward *= 2

        if currency == "balance":
            db.update(user_id, balance=balance + reward)
        else:
            db.update(user_id, almaz=balance + reward)
        update_game_result(user_id, "win")
        result_text = "Orol" if result == 1 else "Gerb"
        text = f"🪙 Tanga natijasi: {result_text}\n🎉 Omadli! Yutdingiz! +{reward} {curr_name}"
    else:
        new_value = max(0, balance - amount)
        if currency == "balance":
            db.update(user_id, balance=new_value)
        else:
            db.update(user_id, almaz=new_value)
        update_game_result(user_id, "loss")
        result_text = "Orol" if result == 1 else "Gerb"
        text = f"🪙 Tanga natijasi: {result_text}\n😢 Omad kelmadi! Yutqazdingiz! -{amount} {curr_name}"

    await state.clear()
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 𝑄𝐴𝑌𝑇𝐴 𝑂'𝑌𝐼𝑁𝐴𝑆𝐻", callback_data=f"game_start_tanga_{owner_id}")], [InlineKeyboardButton(text="🔙 𝑀𝐸𝑁𝑌𝑈", callback_data=f"back_to_games_{owner_id}")]]) ,
        parse_mode=ParseMode.HTML,
    )
    await callback.answer()


@dp.callback_query(GameState.waiting_for_choice, F.data.startswith("rps_"))
async def process_rps_choice(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    user_choice = parts[1]
    owner_id = int(parts[2]) if len(parts) > 2 else callback.from_user.id

    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu o'yin sizniki emas!", show_alert=True)
        return

    data = await state.get_data()
    currency = data["currency"]
    amount = data["amount"]
    user_id = callback.from_user.id
    user = db.get_user(user_id, callback.from_user.full_name)
    balance = user["balance"] if currency == "balance" else user["almaz"]
    curr_name = "dollar" if currency == "balance" else "Almaz"

    choices = ["tosh", "qogoz", "qaychi"]
    bot_choice = random.choice(choices)

    # Qoidalar boyicha taqqoslash
    if user_choice == bot_choice:
        outcome = "draw"
    elif (user_choice == "tosh" and bot_choice == "qaychi") or \
         (user_choice == "qogoz" and bot_choice == "tosh") or \
         (user_choice == "qaychi" and bot_choice == "qogoz"):
        outcome = "win"
    else:
        outcome = "loss"

    if outcome == "draw":
        update_game_result(user_id, "draw")
        text = f"🤝 Durang!\nBot ham <b>{bot_choice}</b> tanladi."
    elif outcome == "win":
        reward, _ = apply_charm_bonus(user_id, amount)
        if user["double_win_count"] > 0:
            db.update(user_id, double_win_count=user["double_win_count"] - 1)
            reward *= 2

        if currency == "balance":
            db.update(user_id, balance=balance + reward)
        else:
            db.update(user_id, almaz=balance + reward)
        update_game_result(user_id, "win")
        text = f"🎉 Bot <b>{bot_choice}</b> tanladi.\nOmad sizda! Yutdingiz! +{reward} {curr_name}"
    else:
        new_value = max(0, balance - amount)
        if currency == "balance":
            db.update(user_id, balance=new_value)
        else:
            db.update(user_id, almaz=new_value)
        update_game_result(user_id, "loss")
        text = f"😢 Bot <b>{bot_choice}</b> tanladi.\nOmad kelmadi! Yutqazdingiz! -{amount} {curr_name}"

    await state.clear()
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 𝑄𝐴𝑌𝑇𝐴 𝑂'𝑌𝐼𝑁𝐴𝑆𝐻", callback_data=f"game_start_rps_{owner_id}")], [InlineKeyboardButton(text="🔙 𝑀𝐸𝑁𝑌𝑈", callback_data=f"back_to_games_{owner_id}")]]) ,
        parse_mode=ParseMode.HTML,
    )
    await callback.answer()


@dp.callback_query(GameState.waiting_for_choice, F.data.startswith("pen_"))
async def process_penalty_choice(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    user_choice = parts[1]
    owner_id = int(parts[2]) if len(parts) > 2 else callback.from_user.id

    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu o'yin sizniki emas!", show_alert=True)
        return

    data = await state.get_data()
    currency = data["currency"]
    amount = data["amount"]
    user_id = callback.from_user.id
    user = db.get_user(user_id, callback.from_user.full_name)
    balance = user["balance"] if currency == "balance" else user["almaz"]
    curr_name = "dollar" if currency == "balance" else "Almaz"

    keeper_choice = random.choice(["left", "center", "right"])
    win = (user_choice != keeper_choice)

    if win:
        reward, _ = apply_charm_bonus(user_id, int(amount * 1.5))
        if user["double_win_count"] > 0:
            db.update(user_id, double_win_count=user["double_win_count"] - 1)
            reward *= 2

        if currency == "balance":
            db.update(user_id, balance=balance + reward)
        else:
            db.update(user_id, almaz=balance + reward)
        update_game_result(user_id, "win")
        text = f"⚽ <b>Penalti natijasi:</b>\nDarvozabon {keeper_choice} tomonga sakradi!\n\n🎉 GOL! +{reward} {curr_name} (1.5x)"
    else:
        new_value = max(0, balance - amount)
        if currency == "balance":
            db.update(user_id, balance=new_value)
        else:
            db.update(user_id, almaz=new_value)
        update_game_result(user_id, "loss")
        text = f"⚽ <b>Penalti natijasi:</b>\nDarvozabon to'pni ushlab qoldi!\n\n❌ SEYV! -{amount} {curr_name}"

    await state.clear()
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 𝑄𝐴𝑌𝑇𝐴 𝑂'𝑌𝐼𝑁𝐴𝑆𝐻", callback_data=f"game_start_penalty_{owner_id}")], [InlineKeyboardButton(text="🔙 𝑀𝐸𝑁𝑌𝑈", callback_data=f"back_to_games_{owner_id}")]]) ,
        parse_mode=ParseMode.HTML,
    )
    await callback.answer()


@dp.callback_query(GameState.waiting_for_choice, F.data.startswith("trea_"))
async def process_treasure_choice(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    choice = int(parts[1])
    owner_id = int(parts[2]) if len(parts) > 2 else callback.from_user.id

    if callback.from_user.id != owner_id:
        await callback.answer("❌ Bu o'yin sizniki emas!", show_alert=True)
        return

    data = await state.get_data()
    currency = data["currency"]
    amount = data["amount"]
    user_id = callback.from_user.id
    user = db.get_user(user_id, callback.from_user.full_name)
    balance = user["balance"] if currency == "balance" else user["almaz"]
    curr_name = "dollar" if currency == "balance" else "Almaz"

    winning_chest = random.randint(1, 3)
    win = (choice == winning_chest)

    if win:
        reward, _ = apply_charm_bonus(user_id, int(amount * 2))
        if user["double_win_count"] > 0:
            db.update(user_id, double_win_count=user["double_win_count"] - 1)
            reward *= 2

        if currency == "balance":
            db.update(user_id, balance=balance + reward)
        else:
            db.update(user_id, almaz=balance + reward)
        update_game_result(user_id, "win")
        text = f"🏴‍☠️ <b>Xazina:</b>\nYutuqli sandiq: <b>{winning_chest}-sandiq</b>\n\n🎉 Yutdingiz! +{reward} {curr_name} (2x)"
    else:
        new_value = max(0, balance - amount)
        if currency == "balance":
            db.update(user_id, balance=new_value)
        else:
            db.update(user_id, almaz=new_value)
        update_game_result(user_id, "loss")
        text = f"🏴‍☠️ <b>Xazina:</b>\nYutuqli sandiq: <b>{winning_chest}-sandiq</b>\n\n💥 Omad kelmadi! -{amount} {curr_name}"

    await state.clear()
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 𝑄𝐴𝑌𝑇𝐴 𝑂'𝑌𝐼𝑁𝐴𝑆𝐻", callback_data=f"game_start_treasure_{owner_id}")], [InlineKeyboardButton(text="🔙 𝑀𝐸𝑁𝑌𝑈", callback_data=f"back_to_games_{owner_id}")]]) ,
        parse_mode=ParseMode.HTML,
    )
    await callback.answer()


# ============================================================
# 🎁 KUNLIK BONUS VA REYTING
# ============================================================

async def daily_handler_direct(message: Message, user_id: int, full_name: str):
    user = db.get_user(user_id, full_name)
    now = time.time()

    if now - user["last_daily"] < DAILY_COOLDOWN:
        remaining = int(DAILY_COOLDOWN - (now - user["last_daily"]))
        hours = max(1, remaining // 3600)
        await message.answer(f"⏳ Kunlik bonus allaqachon olingan!\nYana taxminan {hours} soat kuting.")
        return

    db.update(user_id, balance=user["balance"] + DAILY_REWARD, points=user["points"] + 10, last_daily=now)
    await message.answer(f"🎁 Kunlik bonus olindi!\n+{DAILY_REWARD} dollar 💵\n+10 ball 🏆")


@dp.message(StateFilter("*"), F.text.func(lambda t: "bonus" in clean_text(t)))
async def daily_handler(message: Message, state: FSMContext):
    await state.clear()
    await daily_handler_direct(message, message.from_user.id, message.from_user.full_name)


async def top_menu_handler(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏆 𝑇𝑂𝑃 7", callback_data="top_list_7"),
                InlineKeyboardButton(text="🏆 𝑇𝑂𝑃 10", callback_data="top_list_10"),
                InlineKeyboardButton(text="🏆 𝑇𝑂𝑃 20", callback_data="top_list_20"),
            ]
        ]
    )
    await message.answer("🏆 <b>Reyting turini tanlang:</b>", reply_markup=keyboard, parse_mode=ParseMode.HTML)


@dp.message(StateFilter("*"), F.text.func(lambda t: "top" in clean_text(t)))
async def top_handler(message: Message, state: FSMContext):
    await state.clear()
    await top_menu_handler(message)


@dp.callback_query(F.data.startswith("top_list_"))
async def show_top_list_callback(callback: CallbackQuery):
    limit = int(callback.data.split("_")[2])
    bot_id = callback.bot.id
    
    rows = db.fetchall(
        """SELECT user_id, name, balance, almaz FROM users 
           WHERE user_id > 0 AND user_id != ? 
           AND (balance > 0 OR almaz > 0)
           AND LOWER(name) NOT LIKE '%bot%' 
           ORDER BY balance DESC LIMIT ?""",
        (bot_id, limit)
    )
    
    text = f"🏆 <b>TOP-{limit} BADAVLATLAR</b>\n\n"
    if not rows:
        text += "Hali faol foydalanuvchilar yo'q."
    else:
        for idx, row in enumerate(rows, 1):
            safe_name = html.escape(row["name"])
            u_mention = f'<a href="tg://user?id={row["user_id"]}">{safe_name}</a>'
            text += f"{idx}. {u_mention} — <b>{row['balance']}</b> 💵 | <b>{row['almaz']}</b> Almaz\n"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏆 𝑇𝑂𝑃 7", callback_data="top_list_7"),
                InlineKeyboardButton(text="🏆 𝑇𝑂𝑃 10", callback_data="top_list_10"),
                InlineKeyboardButton(text="🏆 𝑇𝑂𝑃 20", callback_data="top_list_20"),
            ]
        ]
    )
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    await callback.answer()


@dp.errors()
async def global_error_handler(event):
    logger.exception("Xatolik: %s", event.exception)
    return True


async def main():
    bot = Bot(token=TOKEN)
    logger.info("Bot ishga tushmoqda...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi!")
