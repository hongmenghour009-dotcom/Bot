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

# ================= CONFIG =================
BOT_TOKEN = os.getenv("8364057675:AAEIkZWpwKh8CEOIPntSM4ANYtbPMr-RAmI")
if not BOT_TOKEN:
    BOT_TOKEN = "8364057675:AAEIkZWpwKh8CEOIPntSM4ANYtbPMr-RAmI"  # Local test only

PDF_DIR = "pdf_lessons"
TOOL_DIR = "tools"

ADMIN_IDS = [8123867543]  # 👉 ដាក់ Telegram User ID Admin

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(TOOL_DIR, exist_ok=True)

# ================= START =================
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

# ================= MENU =================
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "PDF" in text:
        context.user_data["type"] = "pdf"
        await update.message.reply_text("📤 សូម Upload File PDF")

    elif "Tool" in text:
        context.user_data["type"] = "tool"
        await update.message.reply_text("📤 សូម Upload Tool / Program")

    elif "List" in text:
        await list_files(update, context)

# ================= UPLOAD =================
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file = await doc.get_file()
    ftype = context.user_data.get("type")
    filename = doc.file_name.lower()

    if ftype == "pdf":
        if not filename.endswith(".pdf"):
            await update.message.reply_text("❌ សូម Upload តែ PDF ប៉ុណ្ណោះ")
            return
        path = f"{PDF_DIR}/{doc.file_name}"
        await file.download_to_drive(path)
        await update.message.reply_text("✅ PDF Upload ជោគជ័យ!")

    elif ftype == "tool":
        path = f"{TOOL_DIR}/{doc.file_name}"
        await file.download_to_drive(path)
        await update.message.reply_text("✅ Tool Upload ជោគជ័យ!")

    else:
        await update.message.reply_text("❌ សូមជ្រើសរើសប្រភេទជាមុន")

# ================= LIST FILES =================
async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    pdfs = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    tools = os.listdir(TOOL_DIR)

    buttons = []

    for pdf in pdfs:
        row = [
            InlineKeyboardButton(f"📘 {pdf}", callback_data=f"download_pdf|{pdf}")
        ]
        if user_id in ADMIN_IDS:
            row.append(
                InlineKeyboardButton("🗑️", callback_data=f"delete_confirm|pdf|{pdf}")
            )
        buttons.append(row)

    for tool in tools:
        row = [
            InlineKeyboardButton(f"🛠️ {tool}", callback_data=f"download_tool|{tool}")
        ]
        if user_id in ADMIN_IDS:
            row.append(
                InlineKeyboardButton("🗑️", callback_data=f"delete_confirm|tool|{tool}")
            )
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
    _, filename = query.data.split("|")
    await query.message.reply_document(open(f"{PDF_DIR}/{filename}", "rb"))

async def download_tool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, filename = query.data.split("|")
    await query.message.reply_document(open(f"{TOOL_DIR}/{filename}", "rb"))# ================= SEARCH =================
async def search_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ ប្រើ /search keyword")
        return

    keyword = " ".join(context.args).lower()
    pdfs = [f for f in os.listdir(PDF_DIR) if keyword in f.lower()]
    tools = [f for f in os.listdir(TOOL_DIR) if keyword in f.lower()]

    buttons = []
    for f in pdfs:
        buttons.append([InlineKeyboardButton(f"📘 {f}", callback_data=f"download_pdf|{f}")])
    for f in tools:
        buttons.append([InlineKeyboardButton(f"🛠️ {f}", callback_data=f"download_tool|{f}")])

    if not buttons:
        await update.message.reply_text("❌ រកមិនឃើញ File")
        return

    await update.message.reply_text(
        "🔍 Search Result:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

# ================= DELETE (ADMIN) =================
async def delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, ftype, filename = query.data.split("|")

    buttons = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"delete_yes|{ftype}|{filename}"),
            InlineKeyboardButton("❌ Cancel", callback_data="delete_cancel"),
        ]
    ]

    await query.message.reply_text(
        f"⚠️ លុប {filename} មែនទេ?",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )

async def delete_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in ADMIN_IDS:
        await query.message.reply_text("❌ អ្នកមិនមានសិទ្ធិ")
        return

    _, ftype, filename = query.data.split("|")
    path = f"{PDF_DIR}/{filename}" if ftype == "pdf" else f"{TOOL_DIR}/{filename}"

    if os.path.exists(path):
        os.remove(path)
        await query.message.reply_text(f"🗑️ លុប {filename} ជោគជ័យ!", parse_mode="Markdown")
    else:
        await query.message.reply_text("❌ File មិនមាន")

async def delete_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("❎ បានបោះបង់")

# ================= MAIN =================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search_files))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    app.add_handler(CallbackQueryHandler(download_pdf, pattern="^download_pdf\\|"))
    app.add_handler(CallbackQueryHandler(download_tool, pattern="^download_tool\\|"))
    app.add_handler(CallbackQueryHandler(delete_confirm, pattern="^delete_confirm\\|"))
    app.add_handler(CallbackQueryHandler(delete_yes, pattern="^delete_yes\\|"))
    app.add_handler(CallbackQueryHandler(delete_cancel, pattern="^delete_cancel$"))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()