import os
import time
import requests
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from groq import Groq

# ================= CONFIG =================
BOT_TOKEN = os.getenv("8364057675:AAEIkZWpwKh8CEOIPntSM4ANYtbPMr-RAmI")
if not BOT_TOKEN:
    BOT_TOKEN = "8364057675:AAEIkZWpwKh8CEOIPntSM4ANYtbPMr-RAmI"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

PDF_DIR = "pdf_lessons"
TOOL_DIR = "tools"

ADMIN_IDS = [8123867543]  # 🔴 ប្ដូរទៅ Telegram ID របស់អ្នក

HISTORY_TTL = 60 * 60 * 24  # 24 hours
HF_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(TOOL_DIR, exist_ok=True)

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# ================= AI HISTORY (MEMORY) =================
AI_HISTORY = {}
# key = "chat_id:user_id"
# value = {"messages": [...], "last_updated": timestamp}

# ================= UTILS =================
def auto_clear_history():
    now = time.time()
    expired = []
    for key, data in AI_HISTORY.items():
        if now - data["last_updated"] > HISTORY_TTL:
            expired.append(key)
    for key in expired:
        del AI_HISTORY[key]

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in ADMIN_IDS:
        keyboard = [
            ["📘 ចែករំលែកមេរៀន (PDF)"],
            ["🛠️ ចែករំលែក Tool / Program"],
            ["📂 List Files"],
        ]
    else:
        keyboard = [["📂 List Files"]]

    await update.message.reply_text(
        "សូមជ្រើសរើស 👇",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )

# ================= MENU =================
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "📂 List Files":
        await list_files(update, context)

    elif text == "📘 ចែករំលែកមេរៀន (PDF)":
        context.user_data["type"] = "pdf"
        await update.message.reply_text("📤 សូម Upload File PDF")

    elif text == "🛠️ ចែករំលែក Tool / Program":
        context.user_data["type"] = "tool"
        await update.message.reply_text("📤 សូម Upload Tool / Program")

    else:
        await update.message.reply_text("សូមចុច Button ខាងក្រោម 👇")

# ================= UPLOAD =================
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file = await doc.get_file()
    ftype = context.user_data.get("type")

    if ftype == "pdf":
        if not doc.file_name.lower().endswith(".pdf"):
            await update.message.reply_text("❌ សូម Upload តែ PDF ប៉ុណ្ណោះ")
            return
        await file.download_to_drive(f"{PDF_DIR}/{doc.file_name}")
        await update.message.reply_text("✅ PDF Upload ជោគជ័យ!")

    elif ftype == "tool":
        await file.download_to_drive(f"{TOOL_DIR}/{doc.file_name}")
        await update.message.reply_text("✅ Tool Upload ជោគជ័យ!")

    else:
        await update.message.reply_text("❌ សូមជ្រើសរើសប្រភេទជាមុន")

# ================= LIST FILES =================
async def list_files(update: Update, context: 
    ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    buttons = []

    for pdf in os.listdir(PDF_DIR):
        if pdf.lower().endswith(".pdf"):
            continue
            row = [InlineKeyboardButton(f"📘 {pdf}", callback_data=f"download_pdf|{pdf}")]
            if user_id in ADMIN_IDS:
                row.append(InlineKeyboardButton("🗑️", callback_data=f"delete_confirm|pdf|{pdf}"))
            buttons.append(row)

    for tool in os.listdir(TOOL_DIR):
        row = [InlineKeyboardButton(f"🛠️ {tool}", callback_data=f"download_tool|{tool}")]
        if user_id in ADMIN_IDS:
            row.append(InlineKeyboardButton("🗑️", callback_data=f"delete_confirm|tool|{tool}"))
        buttons.append(row)
        if not buttons:
         await update.message.reply_text("📂 បណ្ដុំឯកសារ (គ្មាន)")
        return

    await update.message.reply_text(
        "📂 បណ្ដុំឯកសារ (ចុចដើម្បី Download):",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

# ================= DOWNLOAD =================
async def download_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, name = query.data.split("|")
    await query.message.reply_document(open(f"{PDF_DIR}/{name}", "rb"))

async def download_tool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, name = query.data.split("|")
    await query.message.reply_document(open(f"{TOOL_DIR}/{name}", "rb"))

# ================= DELETE (ADMIN) =================
async def delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, ftype, name = query.data.split("|")

    kb = [[
        InlineKeyboardButton("✅ Yes", callback_data=f"delete_yes|{ftype}|{name}"),
        InlineKeyboardButton("❌ Cancel", callback_data="delete_cancel"),
    ]]

    await query.message.reply_text(
        f"⚠️ លុប {name} មែនទេ?",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )

async def delete_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in ADMIN_IDS:
        await query.message.reply_text("❌ អ្នកមិនមានសិទ្ធិ")
        return

    _, ftype, name = query.data.split("|")
    path = f"{PDF_DIR}/{name}" if ftype == "pdf" else f"{TOOL_DIR}/{name}"

    if os.path.exists(path):
        os.remove(path)
        await query.message.reply_text("🗑️ លុបជោគជ័យ!")
    else:
        await query.message.reply_text("❌ File មិនមាន")

async def delete_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("❎ បានបោះបង់")

# ================= SEARCH =================
async def search_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ ប្រើ /search keyword")
        return

    key = " ".join(context.args).lower()
    buttons = []

    for pdf in os.listdir(PDF_DIR):
        if key in pdf.lower():
            buttons.append([InlineKeyboardButton(f"📘 {pdf}", callback_data=f"download_pdf|{pdf}")])

    for tool in os.listdir(TOOL_DIR):
        if key in tool.lower():
            buttons.append([InlineKeyboardButton(f"🛠️ {tool}", callback_data=f"download_tool|{tool}")])

    if not buttons:
        await update.message.reply_text("❌ រកមិនឃើញ File")
        return

    await update.message.reply_text("🔍 Search Result:", reply_markup=InlineKeyboardMarkup(buttons))

# ================= GROQ AI =================
async def ask_groq(prompt: str, chat_id: int, user_id: int) -> str:
    if not groq_client:
        return "❌ AI មិនបានកំណត់ API Key"

    auto_clear_history()
    key = f"{chat_id}:{user_id}"
    now = time.time()

    data = AI_HISTORY.get(key, {"messages": [], "last_updated": now})
    messages = data["messages"]

    messages.append({"role": "user", "content": prompt})

    completion = groq_client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "system", "content": "You are a helpful assistant."}] + messages,
        temperature=0.6,
        max_tokens=800,
    )

    answer = completion.choices[0].message.content
    messages.append({"role": "assistant", "content": answer})

    AI_HISTORY[key] = {"messages": messages[-10:], "last_updated": now}
    return answer

async def group_ai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    if update.message.chat.type not in ["group", "supergroup"]:
        return

    text = update.message.text or ""
    if not text.startswith("/ask"):
        returnquestion = text.replace("/ask", "").strip()
    if not returnquestion:
        await update.message.reply_text("❗ ប្រើ /ask សំណួរ")
        return

    chat_id = update.message.chat.id
    user_id = update.message.from_user.id

    await update.message.reply_text("🤖 កំពុងគិត...")
    answer = await ask_groq(returnquestion, chat_id, user_id)
    await update.message.reply_text(answer)

# ================= IMAGE GENERATOR (HF) =================
def generate_image(prompt: str):
    if not HF_API_KEY:
        return None

    url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt}

    r = requests.post(url, headers=headers, json=payload, timeout=120)
    if r.status_code == 200:
        return r.content
    return None

async def image_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ ប្រើ /image description")
        return

    prompt = " ".join(context.args)
    await update.message.reply_text("🖼️ កំពុង Generate រូបភាព...")

    img = generate_image(prompt)
    if not img:
        await update.message.reply_text("❌ Generate មិនបាន (limit ឬ key ខុស)")
        return

    await update.message.reply_photo(photo=img, caption=f"🖼️ {prompt}")

# ================= CLEAR HISTORY =================
async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = f"{update.message.chat.id}:{update.message.from_user.id}"
    if key in AI_HISTORY:
        del AI_HISTORY[key]
        await update.message.reply_text("🧹 ប្រវត្តិ AI ត្រូវបានលុប!")
    else:
        await update.message.reply_text("ℹ️ មិនមានប្រវត្តិ AI")

# ================= MAIN =================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search_files))
    app.add_handler(CommandHandler("clearhistory", clear_history))
    app.add_handler(CommandHandler("image", image_command))

    # Group AI
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, group_ai_handler))

    # Callbacks
    app.add_handler(CallbackQueryHandler(download_pdf, pattern="^download_pdf\\|"))
    app.add_handler(CallbackQueryHandler(download_tool, pattern="^download_tool\\|"))
    app.add_handler(CallbackQueryHandler(delete_confirm, pattern="^delete_confirm\\|"))
    app.add_handler(CallbackQueryHandler(delete_yes, pattern="^delete_yes\\|"))
    app.add_handler(CallbackQueryHandler(delete_cancel, pattern="^delete_cancel$"))

    # Upload + Menu
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()