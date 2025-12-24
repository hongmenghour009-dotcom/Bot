import os
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

# ========== CONFIG ==========
BOT_TOKEN = os.getenv("8364057675:AAEIkZWpwKh8CEOIPntSM4ANYtbPMr-RAmI")
if not BOT_TOKEN:
    BOT_TOKEN = "8364057675:AAEIkZWpwKh8CEOIPntSM4ANYtbPMr-RAmI"

PDF_DIR = "pdf_lessons"
TOOL_DIR = "tools"

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(TOOL_DIR, exist_ok=True)

# ========== START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📘 ចែករំលែកមេរៀន (PDF)"],
        ["🛠️ ចែករំលែក Tool / Program"],
        ["📂 List Files"],
    ]
    await update.message.reply_text(
        "សូមជ្រើសរើសមុខងារ 👇",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )

# ========== MENU ==========
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "មេរៀន" in text:
        context.user_data["type"] = "pdf"
        await update.message.reply_text("📤 សូម Upload File PDF")

    elif "Tool" in text:
        context.user_data["type"] = "tool"
        await update.message.reply_text("📤 សូម Upload Tool / Program")

    elif "List" in text:
        await list_files(update, context)

# ========== UPLOAD ==========
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file = await doc.get_file()

    ftype = context.user_data.get("type")

    if ftype == "pdf":
        path = f"{PDF_DIR}/{doc.file_name}"
        await file.download_to_drive(path)
        await update.message.reply_text("✅ PDF Upload ជោគជ័យ!")

    elif ftype == "tool":
        path = f"{TOOL_DIR}/{doc.file_name}"
        await file.download_to_drive(path)
        await update.message.reply_text("✅ Tool Upload ជោគជ័យ!")

    else:
        await update.message.reply_text("❌ សូមជ្រើសរើសប្រភេទជាមុន")

# ========== LIST FILES ==========
async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pdfs = os.listdir(PDF_DIR)
    tools = os.listdir(TOOL_DIR)

    msg = "📂 បណ្ដុំឯកសារ\n\n"

    msg += "📘 PDF Lessons:\n"
    msg += "\n".join([f"• {p}" for p in pdfs]) if pdfs else " (គ្មាន)"

    msg += "\n\n🛠️ Tools:\n"
    msg += "\n".join([f"• {t}" for t in tools]) if tools else " (គ្មាន)"

    await update.message.reply_text(msg)

# ========== SEARCH ==========
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ ប្រើ /search keyword")
        return

    keyword = " ".join(context.args).lower()
    files = os.listdir(PDF_DIR)

    results = [f for f in files if keyword in f.lower()]

    if not results:
        await update.message.reply_text("❌ រកមិនឃើញមេរៀន")
        return

    buttons = []
    for f in results:
        buttons.append([
            InlineKeyboardButton(
                text=f,
                callback_data=f"download|{f}"
            )
        ])

    await update.message.reply_text(
        "🔍 Search Result (ចុចដើម្បី Download):",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

# ========== DOWNLOAD ==========
async def download_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, filename = query.data.split("|")
    path = f"{PDF_DIR}/{filename}"

    await query.message.reply_document(
        document=open(path, "rb"),
        filename=filename
    )

# ========== MAIN ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(download_file))

    print("🤖 Bot is running (NO OpenAI)...")
    app.run_polling()

if __name__ == "__main__":
    main()