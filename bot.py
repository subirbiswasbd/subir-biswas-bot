# -*- coding: utf-8 -*-
"""
SUBIR BISWAS BD — Telegram Bot (v2)

Requires: python-telegram-bot >= 21.5
    pip install -U "python-telegram-bot>=21.5"
"""
import asyncio
import csv
import html
import io
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from functools import wraps

from telegram import (
    BotCommand,
    BotCommandScopeChat,
    InlineKeyboardButton as B,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden, RetryAfter, TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    Defaults,
    MessageHandler,
    TypeHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("subir_bot")

# ─────────────────────────── Config ───────────────────────────

# আপনার টোকেনটি এখানে সরাসরি সেট করা আছে
HARDCODED_TOKEN = "8802385584:AAFEdek5FYAMnotYFTgrHiAUbCJdLSgBCnQ"

def load_token():
    token = os.getenv("BOT_TOKEN")
    if token:
        return token.strip()
    if os.path.exists("server.txt"):
        try:
            with open("server.txt", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("TOKEN="):
                        return line.split("=", 1)[1].strip()
        except OSError as e:
            log.error("server.txt পড়তে সমস্যা: %s", e)
    return HARDCODED_TOKEN


def load_admin_ids():
    raw = os.getenv("ADMIN_ID", "8329773836")
    return {int(p) for p in raw.replace(" ", "").split(",") if p.isdigit()}


ADMIN_IDS = load_admin_ids()
USERS_FILE = "users.json"
PAGE_SIZE = 10
BD_TZ = timezone(timedelta(hours=6))  # বাংলাদেশ সময়

# লিংক ও কন্ট্রাক্ট ইনফরমেশন
WEBSITE = "https://subirbiswasbd.blogspot.com"
TELEGRAM = "https://t.me/subir_biswas_bd"
WHATSAPP_NUMBER = "https://wa.me/8801577063015"

WA_VORVIXA = "https://whatsapp.com/channel/0029VbD7ULYF1Ylc2HjQPq0h"
WA_NATYOCHITRO = "https://whatsapp.com/channel/0029VbDyek7KAwElYsh11Y2A"

YOUTUBE = "https://youtube.com/@subirbiswasbd"
AI_YOUTUBE = "https://youtube.com/@aispacesubir"
BANGLA_SOLVE = "https://youtube.com/@banglasolvex"
GITHUB = "https://github.com/subirbiswasbd"
MEDIUM = "https://medium.com/@subirbiswasbd"
QUORA = "https://bn.quora.com/profile/Subir-Biswas-74"
REDDIT = "https://reddit.com/u/subirbiswasbd"
PINTEREST = "https://pinterest.com/subirbiswasbd"
TIKTOK = "https://tiktok.com/@subirbiswasbd"
X_PROFILE = "https://x.com/subirbiswasbd"

# ─────────────────────────── Helpers ───────────────────────────

esc = html.escape


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fmt_time(iso):
    if not iso:
        return "—"
    try:
        return datetime.fromisoformat(iso).astimezone(BD_TZ).strftime("%d %b %Y, %I:%M %p")
    except (TypeError, ValueError):
        return "—"


def within_hours(iso, hours):
    try:
        return datetime.now(timezone.utc) - datetime.fromisoformat(iso) <= timedelta(hours=hours)
    except (TypeError, ValueError):
        return False


def fmt_phone(phone):
    if not phone or phone == "N/A":
        return "—"
    return "+" + str(phone).lstrip("+")


def safe_cell(value):
    """CSV/Excel formula injection থেকে রক্ষা।"""
    s = str(value or "")
    return "'" + s if s and s[0] in "=+-@\t\r" else s


# ─────────────────────────── User database ───────────────────────────


class UserDB:
    """ইন-মেমোরি + অ্যাটমিক JSON সেভ। পুরনো users.json ফরম্যাটের সাথে সামঞ্জস্যপূর্ণ।"""

    def __init__(self, path):
        self.path = path
        self.users = {}
        self.total_views = 0
        self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            log.error("users.json লোড হয়নি (%s) — ব্যাকআপ রেখে নতুন করে শুরু হচ্ছে", e)
            try:
                os.replace(self.path, self.path + ".corrupt")
            except OSError:
                pass
            return

        users = data.get("unique_users", {})
        if isinstance(users, list):
            users = {str(u): {} for u in users}
        for uid, info in users.items():
            info = info if isinstance(info, dict) else {}
            self.users[str(uid)] = {
                "name": info.get("name") or "Unknown",
                "username": info.get("username") or "N/A",
                "phone": info.get("phone") or "N/A",
                "first_seen": info.get("first_seen"),
                "last_seen": info.get("last_seen"),
                "visits": int(info.get("visits", 0) or 0),
                "blocked": bool(info.get("blocked", False)),
            }
        self.total_views = int(data.get("total_views", 0) or 0)

    def save(self):
        tmp = self.path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(
                    {"unique_users": self.users, "total_views": self.total_views},
                    f, ensure_ascii=False, indent=2,
                )
            os.replace(tmp, self.path)
        except OSError as e:
            log.error("users.json সেভ হয়নি: %s", e)

    @staticmethod
    def _identity(user):
        return {
            "name": user.full_name or user.first_name or "Unknown",
            "username": f"@{user.username}" if user.username else "N/A",
        }

    def _get_or_create(self, user):
        uid = str(user.id)
        ident = self._identity(user)
        if uid not in self.users:
            ts = now_iso()
            self.users[uid] = {
                **ident, "phone": "N/A", "first_seen": ts,
                "last_seen": ts, "visits": 0, "blocked": False,
            }
            return uid, self.users[uid], True, True
        rec = self.users[uid]
        changed = False
        for k, v in ident.items():
            if rec.get(k) != v:
                rec[k] = v
                changed = True
        return uid, rec, False, changed

    def track_start(self, user):
        _, rec, is_new, _ = self._get_or_create(user)
        rec["visits"] += 1
        rec["last_seen"] = now_iso()
        rec["blocked"] = False
        self.total_views += 1
        self.save()
        return is_new, len(self.users), self.total_views

    def touch(self, user):
        """নাম/ইউজারনেম বদলালে সিঙ্ক করে (ভিউ কাউন্ট বাড়ায় না)।"""
        if str(user.id) not in self.users:
            return
        _, _, _, changed = self._get_or_create(user)
        if changed:
            self.save()

    def set_phone(self, user, phone):
        _, rec, _, _ = self._get_or_create(user)
        rec["phone"] = phone
        self.save()

    def mark_blocked(self, uid):
        rec = self.users.get(str(uid))
        if rec and not rec["blocked"]:
            rec["blocked"] = True
            self.save()

    def sorted_users(self):
        """নতুন ইউজার আগে।"""
        return sorted(self.users.items(), key=lambda kv: kv[1].get("first_seen") or "", reverse=True)

    def search(self, query, limit=10):
        q = query.strip().lower().lstrip("@")
        if not q:
            return []
        digits = "".join(c for c in q if c.isdigit())
        out = []
        for uid, rec in self.sorted_users():
            hay = f"{uid} {rec['name']} {rec['username']}".lower()
            phone_digits = "".join(c for c in rec["phone"] if c.isdigit())
            if q in hay or (len(digits) >= 4 and digits in phone_digits):
                out.append((uid, rec))
                if len(out) >= limit:
                    break
        return out

    def summary(self):
        recs = list(self.users.values())
        return {
            "total": len(recs),
            "views": self.total_views,
            "new_24h": sum(within_hours(r.get("first_seen"), 24) for r in recs),
            "active_24h": sum(within_hours(r.get("last_seen"), 24) for r in recs),
            "with_phone": sum(r["phone"] != "N/A" for r in recs),
            "blocked": sum(r["blocked"] for r in recs),
        }


db = UserDB(USERS_FILE)

# ─────────────────────────── UI helpers ───────────────────────────


def is_admin(update: Update):
    u = update.effective_user
    return bool(u and u.id in ADMIN_IDS)


def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update):
            if update.callback_query:
                await update.callback_query.answer("❌ শুধুমাত্র অ্যাডমিনের জন্য", show_alert=True)
            elif update.effective_message:
                await update.effective_message.reply_text("❌ এই কমান্ডটি শুধুমাত্র অ্যাডমিনের জন্য সংরক্ষিত।")
            return
        return await func(update, context)
    return wrapper


async def show(update: Update, text, rows=None):
    """বাটনে ক্লিক করলে মেসেজ এডিট, কমান্ড দিলে নতুন মেসেজ — দুটোই একই ফাংশনে।"""
    markup = InlineKeyboardMarkup(rows) if rows else None
    q = update.callback_query
    if q:
        try:
            await q.edit_message_text(text, reply_markup=markup)
            return
        except BadRequest as e:
            if "not modified" in str(e).lower():
                return
            log.warning("Edit ব্যর্থ (%s) — নতুন মেসেজ পাঠানো হচ্ছে", e)
    msg = update.effective_message
    if msg:
        await msg.reply_text(text, reply_markup=markup)


async def notify_admins(context: ContextTypes.DEFAULT_TYPE, text):
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=text)
        except TelegramError as e:
            log.warning("অ্যাডমিন %s কে নোটিফাই করা যায়নি: %s", admin_id, e)


def back_row():
    return [B("⬅️ Back to Menu", callback_data="menu")]


# ─────────────────────────── User screens ───────────────────────────


def screen_start(update):
    name = esc(update.effective_user.first_name or "বন্ধু")
    text = (
        f"👋 <b>স্বাগতম, {name}!</b>\n\n"
        "🌐 <b>SUBIR BISWAS BD</b>\n"
        "আপনার ব্যক্তিগত তথ্য, Social Media এবং ডিজিটাল Content-এর অফিশিয়াল Hub।\n\n"
        "✨ <b>আমাদের মূল সেবাসমূহ:</b>\n"
        "▫️ 🤖 AI & Emerging Technology\n"
        "▫️ 🎨 AI Photo & Video Editing\n"
        "▫️ 📱 Useful Apps & Software Tools\n"
        "▫️ 💡 Tech Tips & Tricks\n"
        "▫️ 🎬 Exclusive Content & Updates\n\n"
        "👉 নেভিগেট করতে নিচের বাটনগুলো ব্যবহার করুন।"
    )
    rows = [
        [B("📋 Main Menu", callback_data="menu"), B("💬 WhatsApp Us", url=WHATSAPP_NUMBER)],
        [B("🌐 Official Website", url=WEBSITE), B("▶️ YouTube", url=YOUTUBE)],
        [B("📢 Telegram", url=TELEGRAM), B("🟢 WA Channels", callback_data="wa_channels")],
    ]
    if is_admin(update):
        rows.append([B("🛠 Admin Panel", callback_data="adm:home")])
    return text, rows


def screen_menu(update):
    text = "📋 <b>SUBIR BISWAS BD — Main Menu</b>\n\nপ্রয়োজনীয় বিভাগ নির্বাচন করুন:"
    rows = [
        [B("👤 About Me", callback_data="about"), B("🟢 WA Channels", callback_data="wa_channels")],
        [B("📱 Social Networks", callback_data="social"), B("💬 WhatsApp", url=WHATSAPP_NUMBER)],
        [B("▶️ YouTube Main", url=YOUTUBE), B("🤖 AI YouTube", url=AI_YOUTUBE)],
        [B("📢 Telegram", url=TELEGRAM), B("🎵 TikTok", url=TIKTOK)],
        [B("💻 GitHub", url=GITHUB), B("𝕏 X (Twitter)", url=X_PROFILE)],
        [B("🛠️ AI Tools", callback_data="tools"), B("❓ Help", callback_data="help")],
        [B("📞 ফোন নম্বর শেয়ার", callback_data="phone")],
    ]
    if is_admin(update):
        rows.append([B("🛠 Admin Panel", callback_data="adm:home")])
    return text, rows


def screen_wa(update):
    text = (
        "🟢 <b>WhatsApp Channels & Contact</b>\n\n"
        "আমাদের অফিসিয়াল হোয়াটসঅ্যাপ চ্যানেলগুলোতে যুক্ত থাকুন এবং যেকোনো প্রয়োজনে সরাসরি যোগাযোগ করুন:"
    )
    rows = [
        [B("💬 Direct WhatsApp Chat", url=WHATSAPP_NUMBER)],
        [B("📢 Vorvixa WA Channel", url=WA_VORVIXA)],
        [B("🎬 নাট্যচিত্র | NatyoChitro Channel", url=WA_NATYOCHITRO)],
        back_row(),
    ]
    return text, rows


def screen_about(update):
    text = (
        "👤 <b>About Subir Biswas</b>\n\n"
        "আমি <b>Subir Biswas</b>।\n"
        "Technology, AI, Digital Skills, Content Creation এবং Online Tools নিয়ে কাজ করি।\n\n"
        "🎓 Tech Enthusiast & Learner\n"
        "🤖 AI & Innovation Specialist\n"
        "🎬 Digital Content Creator\n\n"
        f"🌐 <b>Website:</b> {WEBSITE}\n"
        "📞 <b>WhatsApp:</b> +8801577063015"
    )
    return text, [back_row()]


def screen_social(update):
    text = "📱 <b>Social Media Networks</b>\n\nসবগুলো প্ল্যাটফর্মে যুক্ত হতে নিচের বাটনগুলোতে ক্লিক করুন:"
    rows = [
        [B("💬 WhatsApp Chat", url=WHATSAPP_NUMBER), B("🟢 WA Channels", callback_data="wa_channels")],
        [B("▶️ YouTube", url=YOUTUBE), B("🤖 AI YouTube", url=AI_YOUTUBE)],
        [B("🎬 Bangla Solve", url=BANGLA_SOLVE), B("📢 Telegram", url=TELEGRAM)],
        [B("🎵 TikTok", url=TIKTOK), B("𝕏 X Profile", url=X_PROFILE)],
        [B("💻 GitHub", url=GITHUB), B("✍️ Medium", url=MEDIUM)],
        [B("❓ Quora", url=QUORA), B("👽 Reddit", url=REDDIT)],
        [B("📌 Pinterest", url=PINTEREST)],
        back_row(),
    ]
    return text, rows


def screen_tools(update):
    text = (
        "🛠️ <b>AI & Online Tools Hub</b>\n\n"
        "এখানে প্রফেশনাল AI Tools, Utility Apps এবং ডিজিটাল রিসোর্স আপডেট করা হবে।"
    )
    return text, [back_row()]


def screen_help(update):
    text = (
        "❓ <b>Help & Command List</b>\n\n"
        "/start — বট শুরু করুন\n"
        "/menu — মেইন মেনু ওপেন করুন\n"
        "/phone — ফোন নম্বর শেয়ার করুন\n"
        "/about — প্রোফাইল তথ্য\n"
        "/social — সকল সোশ্যাল মিডিয়া লিঙ্ক\n"
        "/wa — WhatsApp চ্যানেল\n"
        "/help — সহায়তা"
    )
    if is_admin(update):
        text += (
            "\n\n🛠 <b>অ্যাডমিন কমান্ড</b>\n"
            "/admin — অ্যাডমিন প্যানেল\n"
            "/stats — অ্যাডমিন প্যানেল (শর্টকাট)\n"
            "/find &lt;নাম / @username / ID / ফোন&gt; — ইউজার খুঁজুন\n"
            "/cancel — চলমান কাজ বাতিল"
        )
    return text, [[B("📋 Main Menu", callback_data="menu")]]


SCREENS = {
    "menu": screen_menu,
    "about": screen_about,
    "social": screen_social,
    "tools": screen_tools,
    "help": screen_help,
    "wa_channels": screen_wa,
}


def make_screen_command(key):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text, rows = SCREENS[key](update)
        await show(update, text, rows)
    return handler


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_new, total_unique, _ = db.track_start(user)

    text, rows = screen_start(update)
    await show(update, text, rows)

    if is_new:
        uname = f"@{esc(user.username)}" if user.username else "নাই (No Username)"
        await notify_admins(
            context,
            "🔔 <b>নতুন ভিজিটর বোট ব্যবহার শুরু করেছেন!</b>\n\n"
            f"👤 <b>নাম:</b> <a href=\"tg://user?id={user.id}\">{esc(user.full_name)}</a>\n"
            f"🏷️ <b>Username:</b> {uname}\n"
            f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
            f"📊 <b>মোট ইউজার:</b> {total_unique}",
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    key = q.data
    if key in SCREENS:
        text, rows = SCREENS[key](update)
        await show(update, text, rows)


async def request_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    markup = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 আমার ফোন নম্বর শেয়ার করুন", request_contact=True)], ["❌ বাতিল"]],
        one_time_keyboard=True,
        resize_keyboard=True,
    )
    await update.effective_message.reply_text(
        "যোগাযোগ ও ভেরিফিকেশনের জন্য নিচের বাটনে ক্লিক করে আপনার ফোন নম্বরটি শেয়ার করুন:",
        reply_markup=markup,
    )


async def phone_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await request_phone(update, context)


async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    contact = msg.contact
    user = update.effective_user

    if contact.user_id and contact.user_id != user.id:
        await msg.reply_text(
            "⚠️ অনুগ্রহ করে শুধু আপনার নিজের ফোন নম্বর শেয়ার করুন।",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    phone = "+" + contact.phone_number.lstrip("+")
    db.set_phone(user, phone)

    await msg.reply_text(
        "✅ ধন্যবাদ! আপনার ফোন নম্বরটি সফলভাবে গ্রহণ করা হয়েছে।",
        reply_markup=ReplyKeyboardRemove(),
    )
    uname = f"@{esc(user.username)}" if user.username else "নাই"
    await notify_admins(
        context,
        "📞 <b>নতুন নম্বর পাওয়া গেছে!</b>\n\n"
        f"👤 <b>নাম:</b> <a href=\"tg://user?id={user.id}\">{esc(user.full_name)}</a>\n"
        f"🏷️ <b>Username:</b> {uname}\n"
        f"📱 <b>ফোন নম্বর:</b> <code>{esc(phone)}</code>\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>",
    )


# ─────────────────────────── Admin panel ───────────────────────────


def user_block(idx, uid, rec, detailed=False):
    name = esc(rec.get("name") or "Unknown")
    uname = rec.get("username") or "N/A"
    uname_txt = esc(uname) if uname != "N/A" else "নাই"
    flag = " 🚫" if rec.get("blocked") else ""
    lines = [
        f"<b>{idx}.</b> <a href=\"tg://user?id={uid}\">{name}</a>{flag}",
        f"    🏷 {uname_txt} · 📱 <code>{esc(fmt_phone(rec.get('phone')))}</code>",
        f"    🆔 <code>{uid}</code>",
    ]
    if detailed:
        lines.append(
            f"    👁 ভিজিট: {rec.get('visits', 0)} · 📅 জয়েন: {fmt_time(rec.get('first_seen'))}"
        )
    lines.append(f"    🕒 শেষ অ্যাক্টিভ: {fmt_time(rec.get('last_seen'))}")
    return "\n".join(lines)


def admin_home_screen():
    s = db.summary()
    now = datetime.now(BD_TZ).strftime("%d %b %Y, %I:%M:%S %p")
    text = (
        "🛠 <b>SUBIR BISWAS BD — Admin Panel</b>\n\n"
        f"👤 <b>মোট ইউনিক ইউজার:</b> {s['total']} জন\n"
        f"👁 <b>মোট ভিজিট (/start):</b> {s['views']} বার\n"
        f"🆕 <b>গত ২৪ ঘণ্টায় নতুন:</b> {s['new_24h']} জন\n"
        f"🔥 <b>গত ২৪ ঘণ্টায় অ্যাক্টিভ:</b> {s['active_24h']} জন\n"
        f"📱 <b>ফোন নম্বর দিয়েছেন:</b> {s['with_phone']} জন\n"
        f"🚫 <b>বট ব্লক করেছেন:</b> {s['blocked']} জন\n\n"
        f"🕒 <i>আপডেট: {now}</i>"
    )
    rows = [
        [B("👥 ইউজার লিস্ট", callback_data="adm:users:0"), B("📱 ফোন লিস্ট", callback_data="adm:phones:0")],
        [B("🔍 সার্চ", callback_data="adm:search"), B("📢 Broadcast", callback_data="adm:broadcast")],
        [B("📥 CSV Export", callback_data="adm:export"), B("🔄 Refresh", callback_data="adm:home")],
        back_row(),
    ]
    return text, rows


def list_screen(kind, page):
    items = db.sorted_users()
    if kind == "phones":
        items = [(u, r) for u, r in items if r["phone"] != "N/A"]
    total = len(items)
    pages = max(1, -(-total // PAGE_SIZE))
    page = max(0, min(page, pages - 1))
    chunk = items[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]

    title = "👥 <b>ইউজার লিস্ট</b>" if kind == "users" else "📱 <b>ফোন নম্বরসহ ইউজার</b>"
    lines = [f"{title} — {total} জন\n"]
    if not chunk:
        lines.append("কোনো ইউজার পাওয়া যায়নি।")
    for i, (uid, rec) in enumerate(chunk, start=page * PAGE_SIZE + 1):
        lines.append(user_block(i, uid, rec))
    text = "\n\n".join([lines[0]] + lines[1:]) if len(lines) > 1 else lines[0]

    nav = []
    if page > 0:
        nav.append(B("⬅️ আগের", callback_data=f"adm:{kind}:{page - 1}"))
    nav.append(B(f"{page + 1}/{pages}", callback_data="adm:noop"))
    if page < pages - 1:
        nav.append(B("পরের ➡️", callback_data=f"adm:{kind}:{page + 1}"))
    rows = [nav, [B("🛠 Admin Panel", callback_data="adm:home")]]
    return text, rows


def search_screen(query):
    results = db.search(query)
    if not results:
        text = f"🔍 “{esc(query)}” — কোনো ইউজার পাওয়া যায়নি।"
    else:
        blocks = [user_block(i, uid, rec, detailed=True) for i, (uid, rec) in enumerate(results, 1)]
        text = f"🔍 <b>সার্চ রেজাল্ট:</b> “{esc(query)}” ({len(results)})\n\n" + "\n\n".join(blocks)
    rows = [
        [B("🔍 আবার খুঁজুন", callback_data="adm:search")],
        [B("🛠 Admin Panel", callback_data="adm:home")],
    ]
    return text, rows


def build_csv():
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["id", "name", "username", "phone", "first_seen", "last_seen", "visits", "blocked"])
    for uid, r in db.sorted_users():
        w.writerow([
            uid, safe_cell(r["name"]), safe_cell(r["username"]), fmt_phone(r["phone"]).replace("—", ""),
            r.get("first_seen") or "", r.get("last_seen") or "", r.get("visits", 0), r.get("blocked", False),
        ])
    return out.getvalue().encode("utf-8-sig")


async def run_broadcast(app: Application, admin_chat_id, text):
    sent = blocked = failed = 0
    app.bot_data["broadcasting"] = True
    try:
        for uid, rec in list(db.users.items()):
            if rec.get("blocked"):
                continue
            try:
                await app.bot.send_message(chat_id=int(uid), text=text)
                sent += 1
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after + 1)
                try:
                    await app.bot.send_message(chat_id=int(uid), text=text)
                    sent += 1
                except TelegramError:
                    failed += 1
            except Forbidden:
                db.mark_blocked(uid)
                blocked += 1
            except TelegramError as e:
                log.warning("Broadcast %s ব্যর্থ: %s", uid, e)
                failed += 1
            await asyncio.sleep(0.05)
    finally:
        app.bot_data["broadcasting"] = False
    await app.bot.send_message(
        chat_id=admin_chat_id,
        text=(
            "📢 <b>Broadcast সম্পন্ন!</b>\n\n"
            f"✅ পাঠানো হয়েছে: {sent}\n"
            f"🚫 ব্লক করেছেন: {blocked}\n"
            f"⚠️ ব্যর্থ: {failed}"
        ),
    )


@admin_only
async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("awaiting", None)
    text, rows = admin_home_screen()
    await show(update, text, rows)


@admin_only
async def cmd_find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args).strip()
    if not query:
        context.user_data["awaiting"] = "search"
        await update.effective_message.reply_text(
            "🔍 নাম, @username, ID বা ফোন নম্বরের অংশ লিখে পাঠান।\n(বাতিল করতে /cancel)"
        )
        return
    text, rows = search_screen(query)
    await show(update, text, rows)


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("awaiting", None)
    context.user_data.pop("bc_text", None)
    await update.effective_message.reply_text("❎ বাতিল করা হয়েছে।", reply_markup=ReplyKeyboardRemove())


@admin_only
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    parts = q.data.split(":")
    action = parts[1] if len(parts) > 1 else "home"

    if action == "noop":
        return

    if action == "home":
        context.user_data.pop("awaiting", None)
        text, rows = admin_home_screen()
        await show(update, text, rows)

    elif action in ("users", "phones"):
        page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
        text, rows = list_screen(action, page)
        await show(update, text, rows)

    elif action == "search":
        context.user_data["awaiting"] = "search"
        await show(
            update,
            "🔍 <b>ইউজার সার্চ</b>\n\nনাম, @username, ID বা ফোন নম্বরের অংশ লিখে পাঠান।",
            [[B("❌ বাতিল", callback_data="adm:cancel")]],
        )

    elif action == "broadcast":
        if context.application.bot_data.get("broadcasting"):
            await show(update, "⏳ একটি Broadcast এখনো চলছে। শেষ হলে আবার চেষ্টা করুন।",
                       [[B("🛠 Admin Panel", callback_data="adm:home")]])
            return
        context.user_data["awaiting"] = "broadcast"
        await show(
            update,
            "📢 <b>Broadcast</b>\n\nসব ইউজারকে যে বার্তাটি পাঠাতে চান সেটি এখন লিখে পাঠান "
            "(Bold/Italic ফরম্যাটিং কাজ করবে)।",
            [[B("❌ বাতিল", callback_data="adm:cancel")]],
        )

    elif action == "bc_send":
        text = context.user_data.pop("bc_text", None)
        if not text:
            await show(update, "⚠️ কোনো বার্তা পাওয়া যায়নি।", [[B("🛠 Admin Panel", callback_data="adm:home")]])
            return
        if context.application.bot_data.get("broadcasting"):
            await show(update, "⏳ একটি Broadcast এখনো চলছে।", [[B("🛠 Admin Panel", callback_data="adm:home")]])
            return
        recipients = sum(1 for r in db.users.values() if not r.get("blocked"))
        await show(
            update,
            f"🚀 Broadcast শুরু হয়েছে ({recipients} জনকে)। শেষ হলে রিপোর্ট পাঠানো হবে।\n"
            "এর মধ্যে আপনি বট স্বাভাবিকভাবে ব্যবহার করতে পারবেন।",
            [[B("🛠 Admin Panel", callback_data="adm:home")]],
        )
        context.application.create_task(run_broadcast(context.application, update.effective_chat.id, text))

    elif action == "cancel":
        context.user_data.pop("awaiting", None)
        context.user_data.pop("bc_text", None)
        text, rows = admin_home_screen()
        await show(update, text, rows)

    elif action == "export":
        fname = f"users_{datetime.now(BD_TZ).strftime('%Y%m%d_%H%M')}.csv"
        buf = io.BytesIO(build_csv())
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=buf,
            filename=fname,
            caption=f"📥 মোট {len(db.users)} জন ইউজারের তালিকা",
        )


# ─────────────────────────── Text / misc handlers ───────────────────────────


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    text = (msg.text or "").strip()

    if text == "❌ বাতিল":
        await msg.reply_text("বাতিল করা হয়েছে।", reply_markup=ReplyKeyboardRemove())
        return

    mode = context.user_data.get("awaiting") if is_admin(update) else None

    if mode == "search":
        context.user_data.pop("awaiting", None)
        out, rows = search_screen(text)
        await msg.reply_text(out, reply_markup=InlineKeyboardMarkup(rows))

    elif mode == "broadcast":
        html_text = msg.text_html
        if len(html_text) > 3500:
            await msg.reply_text("⚠️ বার্তাটি খুব বড়। ৩৫০০ অক্ষরের মধ্যে রাখুন এবং আবার পাঠান।")
            return
        context.user_data.pop("awaiting", None)
        context.user_data["bc_text"] = html_text
        recipients = sum(1 for r in db.users.values() if not r.get("blocked"))
        await msg.reply_text(
            f"📢 <b>প্রিভিউ</b>\n\n{html_text}\n\n━━━━━━━━━━\n"
            f"👥 <b>{recipients} জন</b> ইউজারের কাছে যাবে। নিশ্চিত?",
            reply_markup=InlineKeyboardMarkup([
                [B("✅ পাঠান", callback_data="adm:bc_send"), B("❌ বাতিল", callback_data="adm:cancel")],
            ]),
        )

    else:
        await msg.reply_text(
            "🤖 আমি শুধু কমান্ড ও বাটন বুঝি। মেনু খুলতে নিচের বাটনে ট্যাপ করুন।",
            reply_markup=InlineKeyboardMarkup([[B("📋 Main Menu", callback_data="menu")]]),
        )


async def on_any_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user and not user.is_bot:
        db.touch(user)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error("Unhandled exception", exc_info=context.error)


async def post_init(app: Application):
    public = [
        BotCommand("start", "বট শুরু করুন"),
        BotCommand("menu", "মেইন মেনু"),
        BotCommand("about", "প্রোফাইল তথ্য"),
        BotCommand("social", "সোশ্যাল মিডিয়া লিঙ্ক"),
        BotCommand("wa", "WhatsApp চ্যানেল"),
        BotCommand("phone", "ফোন নম্বর শেয়ার"),
        BotCommand("help", "সহায়তা"),
    ]
    await app.bot.set_my_commands(public)
    admin_cmds = public + [
        BotCommand("admin", "অ্যাডমিন প্যানেল"),
        BotCommand("find", "ইউজার খুঁজুন"),
        BotCommand("cancel", "চলমান কাজ বাতিল"),
    ]
    for admin_id in ADMIN_IDS:
        try:
            await app.bot.set_my_commands(admin_cmds, scope=BotCommandScopeChat(admin_id))
        except TelegramError as e:
            log.warning("অ্যাডমিন কমান্ড মেনু সেট হয়নি (%s): অ্যাডমিন একবার /start দিন", e)


def build_defaults():
    try:
        from telegram import LinkPreviewOptions
        return Defaults(parse_mode=ParseMode.HTML, link_preview_options=LinkPreviewOptions(is_disabled=True))
    except Exception:
        return Defaults(parse_mode=ParseMode.HTML, disable_web_page_preview=True)


def main():
    token = load_token()
    if not token:
        raise SystemExit(
            "❌ BOT_TOKEN পাওয়া যায়নি।\n"
            "   export BOT_TOKEN=xxxx  অথবা server.txt ফাইলে  TOKEN=xxxx  লিখুন।"
        )

    app = (
        Application.builder()
        .token(token)
        .defaults(build_defaults())
        .concurrent_updates(True)
        .post_init(post_init)
        .build()
    )

    app.add_handler(TypeHandler(Update, on_any_update), group=-1)

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", make_screen_command("menu")))
    app.add_handler(CommandHandler("about", make_screen_command("about")))
    app.add_handler(CommandHandler("social", make_screen_command("social")))
    app.add_handler(CommandHandler("wa", make_screen_command("wa_channels")))
    app.add_handler(CommandHandler("tools", make_screen_command("tools")))
    app.add_handler(CommandHandler("help", make_screen_command("help")))
    app.add_handler(CommandHandler("phone", request_phone))
    app.add_handler(CommandHandler(["admin", "stats"], cmd_admin))
    app.add_handler(CommandHandler("find", cmd_find))
    app.add_handler(CommandHandler("cancel", cmd_cancel))

    # Buttons
    app.add_handler(CallbackQueryHandler(admin_callback, pattern=r"^adm:"))
    app.add_handler(CallbackQueryHandler(phone_button, pattern=r"^phone$"))
    app.add_handler(CallbackQueryHandler(button_handler, pattern=r"^(menu|about|social|tools|help|wa_channels)$"))

    # Messages
    app.add_handler(MessageHandler(filters.CONTACT, on_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, on_text))

    app.add_error_handler(on_error)

    print(f"SUBIR BISWAS BD Telegram Bot চলছে... (Admin IDs: {sorted(ADMIN_IDS)})")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
