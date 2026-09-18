import os
import json
import logging
import tempfile

from openai import AsyncOpenAI

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# =========================================================
# 1. ENVIRONMENT VARIABLES
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

ADMIN_ID = 8329773836

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is missing.")


# OpenAI Client
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)


# =========================================================
# 2. LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# 3. USER DATABASE
# =========================================================

USERS_FILE = "users.json"


def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return {
        "unique_users": {},
        "total_views": 0
    }


def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def track_user(user):

    data = load_users()

    user_id = str(user.id)

    is_new = False

    if "unique_users" not in data:
        data["unique_users"] = {}

    if user_id not in data["unique_users"]:

        is_new = True

        data["unique_users"][user_id] = {
            "name": user.first_name,
            "username": (
                f"@{user.username}"
                if user.username
                else "N/A"
            ),
            "phone": "N/A"
        }

    else:

        data["unique_users"][user_id]["name"] = user.first_name

        data["unique_users"][user_id]["username"] = (
            f"@{user.username}"
            if user.username
            else "N/A"
        )

    data["total_views"] = data.get("total_views", 0) + 1

    save_users(data)

    return (
        is_new,
        len(data["unique_users"]),
        data["total_views"]
    )


# =========================================================
# 4. AI CONVERSATION MEMORY
# =========================================================

CHAT_HISTORY_FILE = "chat_history.json"


def load_chat_history():

    if os.path.exists(CHAT_HISTORY_FILE):

        try:
            with open(
                CHAT_HISTORY_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        except Exception:
            pass

    return {}


def save_chat_history(data):

    with open(
        CHAT_HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def get_user_history(user_id):

    data = load_chat_history()

    return data.get(
        str(user_id),
        []
    )


def add_to_history(
    user_id,
    role,
    content
):

    data = load_chat_history()

    user_id = str(user_id)

    if user_id not in data:
        data[user_id] = []

    data[user_id].append({
        "role": role,
        "content": content
    })

    # সর্বোচ্চ 20টি message রাখা
    data[user_id] = data[user_id][-20:]

    save_chat_history(data)


def clear_user_history(user_id):

    data = load_chat_history()

    user_id = str(user_id)

    if user_id in data:
        del data[user_id]

    save_chat_history(data)


# =========================================================
# 5. LINKS
# =========================================================

WEBSITE = "https://subirbiswasbd.blogspot.com"

TELEGRAM = "https://t.me/subir_biswas_bd"

WHATSAPP_NUMBER = "https://wa.me/8801577063015"

WA_VORVIXA = (
    "https://whatsapp.com/channel/"
    "0029VbD7ULYF1Ylc2HjQPq0h"
)

WA_NATYOCHITRO = (
    "https://whatsapp.com/channel/"
    "0029VbDyek7KAwElYsh11Y2A"
)

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


# =========================================================
# 6. AI SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
তুমি SUBIR BISWAS BD-এর AI Assistant।

তুমি একজন বন্ধুত্বপূর্ণ, ভদ্র এবং সহায়ক AI assistant।

ব্যবহারকারী বাংলায় প্রশ্ন করলে বাংলায় উত্তর দেবে।
ইংরেজিতে প্রশ্ন করলে ইংরেজিতে উত্তর দিতে পারো।

উত্তর সহজ, পরিষ্কার এবং প্রয়োজন অনুযায়ী সংক্ষিপ্ত রাখবে।

Technology, AI, programming, Telegram bot,
website, Blogger, HTML, CSS, JavaScript,
Python, freelancing, digital skills এবং
সাধারণ জ্ঞান সম্পর্কিত প্রশ্নে সাহায্য করবে।

নিজেকে OpenAI-এর official assistant হিসেবে পরিচয় দেবে না।
নিজেকে SUBIR BISWAS BD-এর AI Assistant হিসেবে পরিচয় দিতে পারো।

যে তথ্য নিশ্চিতভাবে জানা নেই সেটি বানিয়ে বলবে না।
"""


# =========================================================
# 7. AI CHAT FUNCTION
# =========================================================

async def ask_ai(user_id, question):

    history = get_user_history(user_id)

    input_messages = []

    input_messages.append({
        "role": "developer",
        "content": SYSTEM_PROMPT
    })

    for item in history:

        input_messages.append({
            "role": item["role"],
            "content": item["content"]
        })

    input_messages.append({
        "role": "user",
        "content": question
    })

    response = await openai_client.responses.create(
        model="gpt-5.4-mini",
        input=input_messages
    )

    answer = response.output_text

    add_to_history(
        user_id,
        "user",
        question
    )

    add_to_history(
        user_id,
        "assistant",
        answer
    )

    return answer


# =========================================================
# 8. START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    user_id = user.id

    name = user.first_name

    username = (
        f"@{user.username}"
        if user.username
        else "নাই (No Username)"
    )

    is_new, total_unique, total_views = track_user(user)

    # নতুন ইউজার হলে Admin notification

    if is_new:

        try:

            await context.bot.send_message(
                chat_id=ADMIN_ID,

                text=(
                    "🔔 <b>নতুন ভিজিটর!</b>\n\n"

                    f"👤 <b>নাম:</b> {name}\n"
                    f"🏷️ <b>Username:</b> {username}\n"
                    f"🆔 <b>ID:</b> "
                    f"<code>{user_id}</code>\n"
                    f"📊 <b>মোট ইউজার:</b> "
                    f"{total_unique}"
                ),

                parse_mode="HTML"
            )

        except Exception as e:

            logger.error(
                f"Admin notification error: {e}"
            )


    text = (
        f"👋 <b>স্বাগতম, {name}!</b>\n\n"

        "🌐 <b>SUBIR BISWAS BD</b>\n"

        "আপনার ব্যক্তিগত তথ্য, Social Media "
        "এবং Digital Content-এর Official Hub।\n\n"

        "✨ <b>AI Features:</b>\n"

        "🤖 AI Chatbot — যেকোনো প্রশ্ন করুন\n"
        "🎙️ Voice Assistant — Voice Message পাঠান\n"
        "🧠 Conversation Memory\n"
        "🔊 AI Voice Reply\n\n"

        "👇 নিচের Menu ব্যবহার করুন।"
    )


    keyboard = [

        [
            InlineKeyboardButton(
                "🤖 AI Chat",
                callback_data="ai_chat"
            ),

            InlineKeyboardButton(
                "🎙️ Voice Assistant",
                callback_data="voice"
            )
        ],

        [
            InlineKeyboardButton(
                "📋 Main Menu",
                callback_data="menu"
            ),

            InlineKeyboardButton(
                "💬 WhatsApp Us",
                url=WHATSAPP_NUMBER
            )
        ],

        [
            InlineKeyboardButton(
                "🌐 Official Website",
                url=WEBSITE
            ),

            InlineKeyboardButton(
                "▶️ YouTube",
                url=YOUTUBE
            )
        ],

        [
            InlineKeyboardButton(
                "📢 Telegram",
                url=TELEGRAM
            ),

            InlineKeyboardButton(
                "🟢 WA Channels",
                callback_data="wa_channels"
            )
        ]
    ]


    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# 9. AI CHAT COMMAND
# =========================================================

async def chat_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🤖 <b>AI Chatbot চালু হয়েছে!</b>\n\n"
        "আপনার প্রশ্ন লিখে পাঠান।\n\n"
        "🧹 Conversation মুছতে /clear লিখুন।",
        parse_mode="HTML"
    )


# =========================================================
# 10. CLEAR CHAT
# =========================================================

async def clear_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    clear_user_history(user_id)

    await update.message.reply_text(
        "🧹 <b>Conversation Memory পরিষ্কার করা হয়েছে।</b>\n\n"
        "নতুন করে AI-এর সাথে কথা বলতে পারেন।",
        parse_mode="HTML"
    )


# =========================================================
# 11. VOICE COMMAND
# =========================================================

async def voice_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🎙️ <b>Voice Assistant চালু আছে!</b>\n\n"
        "আমাকে একটি Voice Message পাঠান।\n\n"
        "আমি:\n"
        "🎧 আপনার কথা শুনব\n"
        "📝 কথাকে Text-এ বুঝব\n"
        "🤖 AI দিয়ে উত্তর তৈরি করব\n"
        "🔊 Voice Reply পাঠাব।",
        parse_mode="HTML"
    )


# =========================================================
# 12. TEXT MESSAGE → AI
# =========================================================

async def text_message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not update.message.text:
        return

    question = update.message.text.strip()

    if not question:
        return

    # Command হলে এখানে AI-তে পাঠানো হবে না
    if question.startswith("/"):
        return

    user = update.effective_user

    track_user(user)

    thinking = await update.message.reply_text(
        "🤔 <b>AI ভাবছে...</b>",
        parse_mode="HTML"
    )

    try:

        answer = await ask_ai(
            user.id,
            question
        )

        await thinking.edit_text(
            answer
        )

    except Exception as e:

        logger.exception(
            f"AI error: {e}"
        )

        await thinking.edit_text(
            "⚠️ এই মুহূর্তে AI উত্তর দিতে পারছে না।\n\n"
            "কিছুক্ষণ পর আবার চেষ্টা করুন।"
        )


# =========================================================
# 13. VOICE MESSAGE → AI → VOICE
# =========================================================

async def voice_message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    voice = update.message.voice

    if not voice:
        return

    user = update.effective_user

    track_user(user)

    processing = await update.message.reply_text(
        "🎙️ আপনার Voice Message বুঝছি..."
    )

    temp_input = None
    temp_output = None

    try:

        # Telegram voice download

        telegram_file = await context.bot.get_file(
            voice.file_id
        )

        with tempfile.NamedTemporaryFile(
            suffix=".ogg",
            delete=False
        ) as f:

            temp_input = f.name

        await telegram_file.download_to_drive(
            temp_input
        )


        # Speech → Text

        with open(
            temp_input,
            "rb"
        ) as audio_file:

            transcription = (
                await openai_client
                .audio
                .transcriptions
                .create(
                    model="gpt-4o-mini-transcribe",
                    file=audio_file,
                    language="bn"
                )
            )

        question = transcription.text.strip()


        if not question:

            await processing.edit_text(
                "❌ Voice Message থেকে কোনো কথা বুঝতে পারিনি।"
            )

            return


        # AI Answer

        answer = await ask_ai(
            user.id,
            question
        )


        # প্রথমে Text Answer

        await processing.edit_text(
            f"🎙️ <b>আপনি বলেছেন:</b>\n"
            f"{question}\n\n"
            f"🤖 <b>AI:</b>\n"
            f"{answer}",
            parse_mode="HTML"
        )


        # Text → Speech

        tts_response = await openai_client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=answer,
            response_format="mp3"
        )


        with tempfile.NamedTemporaryFile(
            suffix=".mp3",
            delete=False
        ) as f:

            temp_output = f.name

            f.write(
                tts_response.content
            )


        # Voice Reply

        with open(
            temp_output,
            "rb"
        ) as audio:

            await update.message.reply_audio(
                audio=audio,
                title="SUBIR BISWAS BD AI Assistant"
            )


    except Exception as e:

        logger.exception(
            f"Voice AI error: {e}"
        )

        await processing.edit_text(
            "⚠️ Voice Assistant-এ সমস্যা হয়েছে।\n\n"
            "কিছুক্ষণ পর আবার চেষ্টা করুন।"
        )


    finally:

        if temp_input and os.path.exists(
            temp_input
        ):

            os.remove(temp_input)

        if temp_output and os.path.exists(
            temp_output
        ):

            os.remove(temp_output)


# =========================================================
# 14. PHONE
# =========================================================

async def request_phone(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    contact_keyboard = [[
        KeyboardButton(
            text="📱 আমার ফোন নম্বর শেয়ার করুন",
            request_contact=True
        )
    ]]

    markup = ReplyKeyboardMarkup(
        contact_keyboard,
        one_time_keyboard=True,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "যোগাযোগ ও ভেরিফিকেশনের জন্য "
        "নিচের বাটনে ক্লিক করে আপনার ফোন নম্বরটি শেয়ার করুন:",
        reply_markup=markup
    )


# =========================================================
# 15. CONTACT
# =========================================================

async def contact_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    contact = update.message.contact

    phone_number = contact.phone_number

    user = update.effective_user

    user_id = str(user.id)

    name = user.first_name

    username = (
        f"@{user.username}"
        if user.username
        else "N/A"
    )

    data = load_users()

    if user_id in data.get(
        "unique_users",
        {}
    ):

        data["unique_users"][user_id]["phone"] = (
            phone_number
        )

        save_users(data)


    try:

        await context.bot.send_message(

            chat_id=ADMIN_ID,

            text=(
                "📞 <b>নতুন নম্বর পাওয়া গেছে!</b>\n\n"

                f"👤 <b>নাম:</b> {name}\n"
                f"🏷️ <b>Username:</b> {username}\n"
                f"📱 <b>ফোন:</b> "
                f"<code>+{phone_number}</code>\n"
                f"🆔 <b>ID:</b> "
                f"<code>{user_id}</code>"
            ),

            parse_mode="HTML"
        )

    except Exception as e:

        logger.error(
            f"Phone notification error: {e}"
        )


    await update.message.reply_text(
        "✅ ধন্যবাদ! আপনার ফোন নম্বরটি গ্রহণ করা হয়েছে।"
    )


# =========================================================
# 16. STATS
# =========================================================

async def stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    if user_id != ADMIN_ID:

        await update.message.reply_text(
            "❌ এই কমান্ডটি শুধু Admin-এর জন্য।"
        )

        return


    data = load_users()

    users = data.get(
        "unique_users",
        {}
    )

    total_unique = len(users)

    total_views = data.get(
        "total_views",
        0
    )


    user_list = ""

    count = 1

    for _, info in users.items():

        user_list += (
            f"{count}. "
            f"{info.get('name', 'N/A')} | "
            f"{info.get('username', 'N/A')} | "
            f"📱 {info.get('phone', 'N/A')}\n"
        )

        count += 1

        if count > 15:

            user_list += "...\n"

            break


    msg = (
        "📊 <b>SUBIR BISWAS BD — Analytics</b>\n\n"

        f"👤 <b>মোট ইউনিক ইউজার:</b> "
        f"{total_unique}\n"

        f"👁️ <b>মোট ভিজিট:</b> "
        f"{total_views}\n\n"

        "📋 <b>Users:</b>\n"

        f"{user_list or 'কোনো ইউজার নেই।'}"
    )


    await update.message.reply_text(
        msg,
        parse_mode="HTML"
    )


# =========================================================
# 17. MAIN MENU
# =========================================================

async def menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "📋 <b>SUBIR BISWAS BD — Main Menu</b>\n\n"
        "প্রয়োজনীয় বিভাগ নির্বাচন করুন:"
    )


    keyboard = [

        [
            InlineKeyboardButton(
                "🤖 AI Chat",
                callback_data="ai_chat"
            ),

            InlineKeyboardButton(
                "🎙️ Voice Assistant",
                callback_data="voice"
            )
        ],

        [
            InlineKeyboardButton(
                "👤 About Me",
                callback_data="about"
            ),

            InlineKeyboardButton(
                "🟢 WA Channels",
                callback_data="wa_channels"
            )
        ],

        [
            InlineKeyboardButton(
                "📱 Social Networks",
                callback_data="social"
            ),

            InlineKeyboardButton(
                "💬 WhatsApp",
                url=WHATSAPP_NUMBER
            )
        ],

        [
            InlineKeyboardButton(
                "▶️ YouTube",
                url=YOUTUBE
            ),

            InlineKeyboardButton(
                "🤖 AI YouTube",
                url=AI_YOUTUBE
            )
        ],

        [
            InlineKeyboardButton(
                "📢 Telegram",
                url=TELEGRAM
            ),

            InlineKeyboardButton(
                "🎵 TikTok",
                url=TIKTOK
            )
        ],

        [
            InlineKeyboardButton(
                "💻 GitHub",
                url=GITHUB
            ),

            InlineKeyboardButton(
                "𝕏 X",
                url=X_PROFILE
            )
        ],

        [
            InlineKeyboardButton(
                "🛠️ AI Tools",
                callback_data="tools"
            ),

            InlineKeyboardButton(
                "❓ Help",
                callback_data="help"
            )
        ]
    ]


    if update.callback_query:

        await update.callback_query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:

        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# =========================================================
# 18. VOICE INFO
# =========================================================

async def voice_info(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "🎙️ <b>SUBIR BISWAS BD Voice Assistant</b>\n\n"

        "আপনি আমাকে সরাসরি Voice Message পাঠাতে পারেন।\n\n"

        "🎧 Voice শুনবে\n"
        "📝 কথাকে Text-এ রূপান্তর করবে\n"
        "🤖 AI উত্তর তৈরি করবে\n"
        "🔊 Voice Reply পাঠাবে\n\n"

        "এখন একটি Voice Message পাঠিয়ে দেখুন।"
    )


    keyboard = [[
        InlineKeyboardButton(
            "⬅️ Back to Menu",
            callback_data="menu"
        )
    ]]


    await update.callback_query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# 19. ABOUT
# =========================================================

async def about(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "👤 <b>About Subir Biswas</b>\n\n"

        "আমি <b>Subir Biswas</b>।\n"

        "Technology, AI, Digital Skills, "
        "Content Creation এবং Online Tools নিয়ে কাজ করি।\n\n"

        "🎓 Tech Enthusiast & Learner\n"
        "🤖 AI & Innovation\n"
        "🎬 Digital Content Creator\n\n"

        f"🌐 <b>Website:</b> {WEBSITE}\n"
        f"📞 <b>WhatsApp:</b> +8801577063015"
    )


    keyboard = [[
        InlineKeyboardButton(
            "⬅️ Back to Menu",
            callback_data="menu"
        )
    ]]


    await update.callback_query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# 20. SOCIAL
# =========================================================

async def social(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "📱 <b>Social Media Networks</b>\n\n"
        "সবগুলো প্ল্যাটফর্মে যুক্ত হতে নিচের "
        "বাটনগুলোতে ক্লিক করুন:"
    )


    keyboard = [

        [
            InlineKeyboardButton(
                "💬 WhatsApp",
                url=WHATSAPP_NUMBER
            ),

            InlineKeyboardButton(
                "🟢 WA Channels",
                callback_data="wa_channels"
            )
        ],

        [
            InlineKeyboardButton(
                "▶️ YouTube",
                url=YOUTUBE
            ),

            InlineKeyboardButton(
                "🤖 AI YouTube",
                url=AI_YOUTUBE
            )
        ],

        [
            InlineKeyboardButton(
                "🎬 Bangla Solve",
                url=BANGLA_SOLVE
            ),

            InlineKeyboardButton(
                "📢 Telegram",
                url=TELEGRAM
            )
        ],

        [
            InlineKeyboardButton(
                "🎵 TikTok",
                url=TIKTOK
            ),

            InlineKeyboardButton(
                "𝕏 X",
                url=X_PROFILE
            )
        ],

        [
            InlineKeyboardButton(
                "💻 GitHub",
                url=GITHUB
            ),

            InlineKeyboardButton(
                "✍️ Medium",
                url=MEDIUM
            )
        ],

        [
            InlineKeyboardButton(
                "❓ Quora",
                url=QUORA
            ),

            InlineKeyboardButton(
                "👽 Reddit",
                url=REDDIT
            )
        ],

        [
            InlineKeyboardButton(
                "📌 Pinterest",
                url=PINTEREST
            )
        ],

        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="menu"
            )
        ]
    ]


    await update.callback_query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# 21. WHATSAPP CHANNELS
# =========================================================

async def wa_channels(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "🟢 <b>WhatsApp Channels & Contact</b>\n\n"

        "আমাদের অফিসিয়াল WhatsApp Channel-গুলোতে "
        "যুক্ত থাকুন।"
    )


    keyboard = [

        [
            InlineKeyboardButton(
                "💬 Direct WhatsApp",
                url=WHATSAPP_NUMBER
            )
        ],

        [
            InlineKeyboardButton(
                "📢 Vorvixa Channel",
                url=WA_VORVIXA
            )
        ],

        [
            InlineKeyboardButton(
                "🎬 নাট্যচিত্র Channel",
                url=WA_NATYOCHITRO
            )
        ],

        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="menu"
            )
        ]
    ]


    await update.callback_query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# 22. AI TOOLS
# =========================================================

async def tools(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "🛠️ <b>AI & Online Tools Hub</b>\n\n"

        "এখানে AI Tools, Utility Apps এবং "
        "Digital Resources যুক্ত করা যাবে।"
    )


    keyboard = [[
        InlineKeyboardButton(
            "⬅️ Back",
            callback_data="menu"
        )
    ]]


    await update.callback_query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# 23. HELP
# =========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "❓ <b>Help & Commands</b>\n\n"

        "/start — বট শুরু\n"
        "/menu — Main Menu\n"
        "/chat — AI Chatbot\n"
        "/voice — Voice Assistant\n"
        "/clear — AI Memory Clear\n"
        "/phone — Phone Share\n"
        "/about — About\n"
        "/social — Social Links\n"
        "/stats — Admin Analytics\n"
        "/help — Help"
    )


    keyboard = [[
        InlineKeyboardButton(
            "📋 Main Menu",
            callback_data="menu"
        )
    ]]


    if update.callback_query:

        await update.callback_query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:

        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# =========================================================
# 24. BUTTON HANDLER
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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

    elif query.data == "ai_chat":

        await query.edit_message_text(
            "🤖 <b>AI Chatbot Ready!</b>\n\n"
            "এখন আপনার প্রশ্ন লিখে পাঠান।\n\n"
            "উদাহরণ:\n"
            "• HTML কী?\n"
            "• Python কীভাবে শিখব?\n"
            "• Telegram bot কীভাবে বানাব?\n"
            "• AI কী?",
            parse_mode="HTML"
        )

    elif query.data == "voice":

        await voice_info(update, context)


# =========================================================
# 25. MAIN
# =========================================================

def main():

    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )


    # Commands

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "menu",
            menu
        )
    )

    application.add_handler(
        CommandHandler(
            "chat",
            chat_command
        )
    )

    application.add_handler(
        CommandHandler(
            "voice",
            voice_command
        )
    )

    application.add_handler(
        CommandHandler(
            "clear",
            clear_command
        )
    )

    application.add_handler(
        CommandHandler(
            "about",
            about
        )
    )

    application.add_handler(
        CommandHandler(
            "social",
            social
        )
    )

    application.add_handler(
        CommandHandler(
            "phone",
            request_phone
        )
    )

    application.add_handler(
        CommandHandler(
            "stats",
            stats
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )


    # Contact

    application.add_handler(
        MessageHandler(
            filters.CONTACT,
            contact_handler
        )
    )


    # Voice

    application.add_handler(
        MessageHandler(
            filters.VOICE,
            voice_message_handler
        )
    )


    # Text → AI

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_message_handler
        )
    )


    # Inline buttons

    application.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )


    print(
        "SUBIR BISWAS BD AI Bot is running..."
    )


    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
