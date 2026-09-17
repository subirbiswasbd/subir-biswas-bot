import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ১. এনভায়রনমেন্ট ভ্যারিয়েবল অথবা নতুন টোকেন থেকে পড়বে
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ২. যদি এনভায়রনমেন্টে না থাকে, তবে server.txt ফাইল চেক করবে
if not BOT_TOKEN and os.path.exists("server.txt"):
    try:
        with open("server.txt", "r") as f:
            for line in f:
                if line.startswith("TOKEN="):
                    BOT_TOKEN = line.strip().split("=", 1)[1]
    except Exception as e:
        print(f"Error reading server.txt: {e}")

# ৩. ফাইল বা এনভায়রনমেন্টে না পেলে সরাসরি আপনার নতুন টোকেনটি ব্যবহার করবে
if not BOT_TOKEN:
    BOT_TOKEN = "8802385584:AAFEdek5FYAMnotYFTgrHiAUbCJdLSgBCnQ"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

WEBSITE = "https://subirbiswasbd.blogspot.com"
TELEGRAM = "https://t.me/subir_biswas_bd"

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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name

    text = (
        f"👋 <b>স্বাগতম, {name}!</b>\n\n"
        "🌐 <b>SUBIR BISWAS BD</b>\n"
        "আপনার ব্যক্তিগত তথ্য, Social Media এবং "
        "ডিজিটাল Content-এর সহজ Hub।\n\n"
        "✨ এখানে পাবেন:\n"
        "• 🤖 AI ও Technology\n"
        "• 🎨 AI Photo & Video Editing\n"
        "• 📱 দরকারি Apps ও Tools\n"
        "• 💡 Tips & Tricks\n"
        "• 🌐 Online & Digital তথ্য\n"
        "• 🎬 নতুন ভিডিও ও Updates\n\n"
        "নিচের Menu থেকে আপনার প্রয়োজনীয় অপশন নির্বাচন করুন।"
    )

    keyboard = [
        [
            InlineKeyboardButton("📋 Main Menu", callback_data="menu"),
            InlineKeyboardButton("🌐 Website", url=WEBSITE),
        ],
        [
            InlineKeyboardButton("📱 Social Media", callback_data="social"),
            InlineKeyboardButton("▶️ YouTube", url=YOUTUBE),
        ],
        [
            InlineKeyboardButton("📢 Telegram Channel", url=TELEGRAM),
        ],
    ]

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📋 <b>SUBIR BISWAS BD — Main Menu</b>\n\n"
        "নিচের অপশন থেকে নির্বাচন করুন:"
    )

    keyboard = [
        [
            InlineKeyboardButton("👤 About Me", callback_data="about"),
            InlineKeyboardButton("🌐 Website", url=WEBSITE),
        ],
        [
            InlineKeyboardButton("📱 Social Media", callback_data="social"),
        ],
        [
            InlineKeyboardButton("▶️ YouTube", url=YOUTUBE),
            InlineKeyboardButton("🤖 AI Channel", url=AI_YOUTUBE),
        ],
        [
            InlineKeyboardButton("📢 Telegram", url=TELEGRAM),
            InlineKeyboardButton("🎵 TikTok", url=TIKTOK),
        ],
        [
            InlineKeyboardButton("💻 GitHub", url=GITHUB),
            InlineKeyboardButton("𝕏 X", url=X_PROFILE),
        ],
        [
            InlineKeyboardButton("🛠️ AI & Tools", callback_data="tools"),
            InlineKeyboardButton("❓ Help", callback_data="help"),
        ],
    ]

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👤 <b>About Subir Biswas</b>\n\n"
        "আমি <b>Subir Biswas</b>।\n"
        "Technology, AI, Digital Skills, Content Creation "
        "এবং Online Tools নিয়ে শেখা ও কাজ করার চেষ্টা করি।\n\n"
        "🎓 শিক্ষার্থী\n"
        "🤖 AI & Technology enthusiast\n"
        "🎬 Content Creator\n"
        "💻 Digital Skills learner\n\n"
        "🌐 Personal Website:\n"
        f"{WEBSITE}"
    )

    keyboard = [
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")]
    ]

    await update.callback_query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def social(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📱 <b>Social Media</b>\n\n"
        "আমার বিভিন্ন Social Media Profile ও Channel:"
    )

    keyboard = [
        [
            InlineKeyboardButton("▶️ YouTube", url=YOUTUBE),
            InlineKeyboardButton("🤖 AI YouTube", url=AI_YOUTUBE),
        ],
        [
            InlineKeyboardButton("🎬 Bangla Solve", url=BANGLA_SOLVE),
            InlineKeyboardButton("📢 Telegram", url=TELEGRAM),
        ],
        [
            InlineKeyboardButton("🎵 TikTok", url=TIKTOK),
            InlineKeyboardButton("𝕏 X", url=X_PROFILE),
        ],
        [
            InlineKeyboardButton("💻 GitHub", url=GITHUB),
            InlineKeyboardButton("✍️ Medium", url=MEDIUM),
        ],
        [
            InlineKeyboardButton("❓ Quora", url=QUORA),
            InlineKeyboardButton("👽 Reddit", url=REDDIT),
        ],
        [
            InlineKeyboardButton("📌 Pinterest", url=PINTEREST),
        ],
        [
            InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")
        ],
    ]

    await update.callback_query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def tools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🛠️ <b>AI & Online Tools</b>\n\n"
        "এখানে ভবিষ্যতে দরকারি AI Tools, Websites, "
        "Apps এবং Online Resources যুক্ত করা যাবে।"
    )

    keyboard = [
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")]
    ]

    await update.callback_query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "❓ <b>Help & Commands</b>\n\n"
        "/start — Bot শুরু করুন\n"
        "/menu — Main Menu\n"
        "/about — আমার সম্পর্কে\n"
        "/social — Social Media\n"
        "/website — Personal Website\n"
        "/youtube — YouTube\n"
        "/telegram — Telegram Channel\n"
        "/tiktok — TikTok\n"
        "/github — GitHub\n"
        "/contact — যোগাযোগ\n"
        "/help — Help"
    )

    keyboard = [
        [InlineKeyboardButton("📋 Main Menu", callback_data="menu")]
    ]

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def website(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🌐 <b>Personal Website</b>\n\n{WEBSITE}",
        parse_mode="HTML",
    )


async def youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"▶️ <b>YouTube</b>\n\n{YOUTUBE}",
        parse_mode="HTML",
    )


async def telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📢 <b>Telegram Channel</b>\n\n{TELEGRAM}",
        parse_mode="HTML",
    )


async def tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🎵 <b>TikTok</b>\n\n{TIKTOK}",
        parse_mode="HTML",
    )


async def github(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💻 <b>GitHub</b>\n\n{GITHUB}",
        parse_mode="HTML",
    )


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📩 <b>Contact</b>\n\n{WEBSITE}",
        parse_mode="HTML",
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "menu":
        await menu(update, context)
    elif query.data == "social":
        await social(update, context)
    elif query.data == "about":
        await about(update, context)
    elif query.data == "tools":
        await tools(update, context)
    elif query.data == "help":
        await help_command(update, context)


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("social", social))
    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(CommandHandler("website", website))
    application.add_handler(CommandHandler("youtube", youtube))
    application.add_handler(CommandHandler("telegram", telegram))
    application.add_handler(CommandHandler("tiktok", tiktok))
    application.add_handler(CommandHandler("github", github))
    application.add_handler(CommandHandler("contact", contact))

    application.add_handler(
        CallbackQueryHandler(button_handler)
    )

    print("SUBIR BISWAS BD Telegram Bot is running...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
