import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ১. টোকেন সেটআপ
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN and os.path.exists("server.txt"):
    try:
        with open("server.txt", "r") as f:
            for line in f:
                if line.startswith("TOKEN="):
                    BOT_TOKEN = line.strip().split("=", 1)[1]
    except Exception as e:
        print(f"Error reading server.txt: {e}")

if not BOT_TOKEN:
    BOT_TOKEN = "8802385584:AAFEdek5FYAMnotYFTgrHiAUbCJdLSgBCnQ"

# ২. অ্যাডমিন Telegram User ID (আপনার নতুন আইডি আপডেট করা হয়েছে)
ADMIN_ID = 8643401658  

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ইউজার তথ্য ট্র্যাকিং ফাইল ব্যবস্থা
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {"unique_users": {}, "total_views": 0}
    return {"unique_users": {}, "total_views": 0}

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def track_user(user):
    data = load_users()
    user_id = str(user.id)
    is_new = False
    
    if "unique_users" not in data or isinstance(data["unique_users"], list):
        data["unique_users"] = {}

    if user_id not in data["unique_users"]:
        is_new = True
        data["unique_users"][user_id] = {
            "name": user.first_name,
            "username": f"@{user.username}" if user.username else "N/A",
            "phone": "N/A"
        }
    else:
        # ইউজারনেম আপডেট থাকলে তা সিঙ্ক করা
        data["unique_users"][user_id]["name"] = user.first_name
        data["unique_users"][user_id]["username"] = f"@{user.username}" if user.username else "N/A"

    data["total_views"] = data.get("total_views", 0) + 1
    save_users(data)
    return is_new, len(data["unique_users"]), data["total_views"]

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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    name = user.first_name
    username = f"@{user.username}" if user.username else "নাই (No Username)"

    # ইউজার ট্র্যাকিং
    is_new, total_unique, total_views = track_user(user)

    # নতুন ইউজার এলে অ্যাডমিনকে বিস্তারিত মেসেজ দেওয়া
    if is_new and ADMIN_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔔 <b>নতুন ভিজিটর বোট ব্যবহার শুরু করেছেন!</b>\n\n"
                     f"👤 <b>নাম:</b> {name}\n"
                     f"🏷️ <b>Username:</b> {username}\n"
                     f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
                     f"📊 <b>মোট ইউজার:</b> {total_unique}",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Failed to notify admin: {e}")

    text = (
        f"👋 <b>স্বাগতম, {name}!</b>\n\n"
        "🌐 <b>SUBIR BISWAS BD</b>\n"
        "আপনার ব্যক্তিগত তথ্য, Social Media এবং ডিজিটাল Content-এর অফিশিয়াল Hub।\n\n"
        "✨ <b>আমাদের মূল সেবাসমূহ:</b>\n"
        "▫️ 🤖 AI & Emerging Technology\n"
        "▫️ 🎨 AI Photo & Video Editing\n"
        "▫️ 📱 Useful Apps & Software Tools\n"
        "▫️ 💡 Tech Tips & Tricks\n"
        "▫️ 🎬 Exclusive Content & Updates\n\n"
        "💬 <b>সরাসরি চ্যাট করতে চান?</b>\n"
        "এখানে যেকোনো প্রশ্ন বা মেসেজ টাইপ করে পাঠিয়ে দিন, আমরা সরাসরি উত্তর দেবো!\n\n"
        "👉 নেভিগেট করতে নিচের রেসপন্সিভ বাটনগুলো ব্যবহার করুন।"
    )

    keyboard = [
        [
            InlineKeyboardButton("📋 Main Menu", callback_data="menu"),
            InlineKeyboardButton("💬 WhatsApp Us", url=WHATSAPP_NUMBER),
        ],
        [
            InlineKeyboardButton("🌐 Official Website", url=WEBSITE),
            InlineKeyboardButton("▶️ YouTube", url=YOUTUBE),
        ],
        [
            InlineKeyboardButton("📢 Telegram", url=TELEGRAM),
            InlineKeyboardButton("🟢 WA Channels", callback_data="wa_channels"),
        ],
    ]

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def request_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact_keyboard = [[KeyboardButton(text="📱 আমার ফোন নম্বর শেয়ার করুন", request_contact=True)]]
    markup = ReplyKeyboardMarkup(contact_keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "যোগাযোগ ও ভেরিফিকেশনের জন্য নিচের বাটনে ক্লিক করে আপনার ফোন নম্বরটি শেয়ার করুন:",
        reply_markup=markup
    )


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    phone_number = contact.phone_number
    user = update.effective_user
    user_id = str(user.id)
    name = user.first_name
    username = f"@{user.username}" if user.username else "N/A"

    # ডেটাবেজে ফোন নম্বর আপডেট
    data = load_users()
    if user_id in data.get("unique_users", {}):
        data["unique_users"][user_id]["phone"] = phone_number
        save_users(data)

    # অ্যাডমিনকে সরাসরি নম্বর জানানো
    if ADMIN_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📞 <b>নতুন নম্বর পাওয়া গেছে!</b>\n\n"
                     f"👤 <b>নাম:</b> {name}\n"
                     f"🏷️ <b>Username:</b> {username}\n"
                     f"📱 <b>ফোন নম্বর:</b> <code>+{phone_number}</code>\n"
                     f"🆔 <b>ID:</b> <code>{user_id}</code>",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Failed to send phone to admin: {e}")

    await update.message.reply_text("✅ ধন্যবাদ! আপনার ফোন নম্বরটি সফলভাবে গ্রহণ করা হয়েছে।")


# --- লাইভ চ্যাট ফিচার (ইউজার ও অ্যাডমিন যোগাযোগ) ---
async def handle_user_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # যদি অ্যাডমিন অন্য কারো মেসেজের উত্তর দেন
    if user_id == ADMIN_ID:
        if update.message.reply_to_message:
            original_msg = update.message.reply_to_message.text or update.message.reply_to_message.caption or ""
            # অরিজিনাল মেসেজ থেকে ইউজারের ID খুঁজে বের করা
            if "🆔 ID:" in original_msg or "User ID:" in original_msg:
                try:
                    target_id = None
                    for line in original_msg.split("\n"):
                        if "ID:" in line:
                            target_id = int(line.split(":")[-1].replace("<code>", "").replace("</code>", "").strip())
                            break
                    if target_id:
                        await context.bot.copy_message(
                            chat_id=target_id,
                            from_chat_id=update.effective_chat.id,
                            message_id=update.message.message_id
                        )
                        await update.message.reply_text("✅ আপনার উত্তরটি সফলভাবে ইউজারের কাছে পাঠানো হয়েছে।")
                        return
                except Exception as e:
                    await update.message.reply_text(f"❌ রিপ্লাই পাঠাতে সমস্যা হয়েছে: {e}")
                    return
        return

    # ইউজার মেসেজ পাঠালে তা সরাসরি অ্যাডমিনের কাছে রিলে করা
    username = f"@{user.username}" if user.username else "নাই"
    header = (
        f"📩 <b>নতুন লাইভ চ্যাট মেসেজ!</b>\n"
        f"👤 <b>নাম:</b> {user.first_name}\n"
        f"🏷️ <b>Username:</b> {username}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"-----------------------------------\n\n"
    )

    if ADMIN_ID:
        try:
            # মেসেজটি অ্যাডমিনের ইনবক্সে ফরওয়ার্ড / কপি করা
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=header,
                parse_mode="HTML"
            )
            await context.bot.copy_message(
                chat_id=ADMIN_ID,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            await update.message.reply_text("✅ আপনার মেসেজটি অ্যাডমিনের কাছে পাঠানো হয়েছে। খুব শীঘ্রই উত্তর দেওয়া হবে।")
        except Exception as e:
            print(f"Failed to forward message to admin: {e}")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ এই কমান্ডটি শুধু মাত্র অ্যাডমিনের জন্য সংরক্ষিত।")
        return

    data = load_users()
    users = data.get("unique_users", {})
    total_unique = len(users)
    total_views = data.get("total_views", 0)

    user_list_text = ""
    count = 1
    for u_id, info in users.items():
        uname = info.get("username", "N/A")
        phone = info.get("phone", "N/A")
        user_list_text += f"{count}. {info.get('name')} | {uname} | 📱 {phone}\n"
        count += 1
        if count > 15: # সেরা ১৫ জনের লিস্ট
            user_list_text += "...এবং আরও অনেকে।"
            break

    msg = (
        "📊 <b>SUBIR BISWAS BD — Bot Analytics</b>\n\n"
        f"👤 <b>মোট ইউনিক ইউজার:</b> {total_unique} জন\n"
        f"👁️ <b>মোট ভিজিট সংখ্যা:</b> {total_views} বার\n\n"
        f"📋 <b>ইউজারদের তালিকা:</b>\n"
        f"{user_list_text if user_list_text else 'কোনো ইউজার পাওয়া যায়নি।'}"
    )
    await update.message.reply_text(msg, parse_mode="HTML")


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📋 <b>SUBIR BISWAS BD — Main Menu</b>\n\n"
        "প্রয়োজনীয় বিভাগ নির্বাচন করুন:"
    )

    keyboard = [
        [
            InlineKeyboardButton("👤 About Me", callback_data="about"),
            InlineKeyboardButton("🟢 WA Channels", callback_data="wa_channels"),
        ],
        [
            InlineKeyboardButton("📱 Social Networks", callback_data="social"),
            InlineKeyboardButton("💬 WhatsApp", url=WHATSAPP_NUMBER),
        ],
        [
            InlineKeyboardButton("▶️ YouTube Main", url=YOUTUBE),
            InlineKeyboardButton("🤖 AI YouTube", url=AI_YOUTUBE),
        ],
        [
            InlineKeyboardButton("📢 Telegram", url=TELEGRAM),
            InlineKeyboardButton("🎵 TikTok", url=TIKTOK),
        ],
        [
            InlineKeyboardButton("💻 GitHub", url=GITHUB),
            InlineKeyboardButton("𝕏 X (Twitter)", url=X_PROFILE),
        ],
        [
            InlineKeyboardButton("🛠️ AI Tools", callback_data="tools"),
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


async def wa_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🟢 <b>WhatsApp Channels & Contact</b>\n\n"
        "আমাদের অফিসিয়াল হোয়াটসঅ্যাপ চ্যানেলগুলোতে যুক্ত থাকুন এবং যেকোনো প্রয়োজনে সরাসরি যোগাযোগ করুন:"
    )

    keyboard = [
        [
            InlineKeyboardButton("💬 Direct WhatsApp Chat", url=WHATSAPP_NUMBER)
        ],
        [
            InlineKeyboardButton("📢 Vorvixa WA Channel", url=WA_VORVIXA)
        ],
        [
            InlineKeyboardButton("🎬 নাট্যচিত্র | NatyoChitro Channel", url=WA_NATYOCHITRO)
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


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👤 <b>About Subir Biswas</b>\n\n"
        "আমি <b>Subir Biswas</b>।\n"
        "Technology, AI, Digital Skills, Content Creation এবং Online Tools নিয়ে কাজ করি।\n\n"
        "🎓 Tech Enthusiast & Learner\n"
        "🤖 AI & Innovation Specialist\n"
        "🎬 Digital Content Creator\n\n"
        f"🌐 <b>Website:</b> {WEBSITE}\n"
        f"📞 <b>WhatsApp:</b> +8801577063015"
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
        "📱 <b>Social Media Networks</b>\n\n"
        "সবগুলো প্ল্যাটফর্মে যুক্ত হতে নিচের বাটনগুলোতে ক্লিক করুন:"
    )

    keyboard = [
        [
            InlineKeyboardButton("💬 WhatsApp Chat", url=WHATSAPP_NUMBER),
            InlineKeyboardButton("🟢 WA Channels", callback_data="wa_channels"),
        ],
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
            InlineKeyboardButton("𝕏 X Profile", url=X_PROFILE),
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
        "🛠️ <b>AI & Online Tools Hub</b>\n\n"
        "এখানে প্রফেশনাল AI Tools, Utility Apps এবং ডিজিটাল রিসোর্স আপডেট করা হবে।"
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
        "❓ <b>Help & Command List</b>\n\n"
        "/start — বট শুরু করুন\n"
        "/menu — মেইন মেনু ওপেন করুন\n"
        "/phone — ফোন নম্বর শেয়ার করুন\n"
        "/about — প্রোফাইল তথ্য\n"
        "/social — সকল সোশ্যাল মিডিয়া লিঙ্ক\n"
        "/stats — ভিজিটর ও নম্বর ট্র্যাকিং (অ্যাডমিন)\n"
        "/help — সহায়তা"
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
    elif query.data == "wa_channels":
        await wa_channels(update, context)


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("social", social))
    application.add_handler(CommandHandler("phone", request_phone))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("help", help_command))

    # Handlers
    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    # লাইভ চ্যাট হ্যান্ডলার (যেকোনো সাধারণ টেক্সট/মেসেজের জন্য)
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_user_messages))
    
    application.add_handler(CallbackQueryHandler(button_handler))

    print("SUBIR BISWAS BD Telegram Bot is running with Live Chat and Analytics...")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
