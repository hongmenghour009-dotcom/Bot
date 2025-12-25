import os
import asyncio
from typing import Dict

from telegram import (
    Update,
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

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("8364057675:AAEIkZWpwKh8CEOIPntSM4ANYtbPMr-RAmI")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

PDF_DIR = "pdf_lessons"
TOOL_DIR = "tools"

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(TOOL_DIR, exist_ok=True)

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN not found")
if not GROQ_API_KEY:
    raise RuntimeError("❌ GROQ_API_KEY not found")

# ================== GROQ CLIENT ==================
groq_client = Groq(api_key=GROQ_API_KEY)

# ================== AI MEMORY (AUTO CLEAR) ==================
chat_memory: Dict[int, list] = {}
MAX_HISTORY = 6  # auto clear old history

async def ask_groq(question: str, chat_id: int) -> str:
    history = chat_memory.get(chat_id, [])

    history.append({"role": "user", "content": question})
    history = history[-MAX_HISTORY:]

    try:
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=history,
        )
        answer = response.choices[0].message.content
        history.append({"role": "assistant", "content": answer})
        chat_memory[chat_id] = history[-MAX_HISTORY:]
        return answer
    except Exception as e:
        return f"❌ AI Error: {e}"

# ================== COMMANDS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 Upload PDF", callback_data="upload_pdf")],
        [InlineKeyboardButton("🛠 Upload Tool", callback_data="upload_tool")],
        [InlineKeyboardButton("📂 List Files", callback_data="list_files")],
    ]
    await update.message.reply_text(
        "សូមជ្រើសរើស 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ================== FILE UPLOAD ==================
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc:
        return

    if doc.mime_type == "application/pdf":
        path = os.path.join(PDF_DIR, doc.file_name)
    else:
        path = os.path.join(TOOL_DIR, doc.file_name)

    file = await doc.get_file()
    await file.download_to_drive(path)

    await update.message.reply_text("✅ Upload ជោគជ័យ!")

# ================== LIST FILES ==================
async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = []

    for f in os.listdir(PDF_DIR):
        buttons.append([
            InlineKeyboardButton(f"📄 {f}", callback_data=f"pdf|{f}")
        ])

    for f in os.listdir(TOOL_DIR):
        buttons.append([
            InlineKeyboardButton(f"🛠 {f}", callback_data=f"tool|{f}")
        ])

    if not buttons:
        await update.message.reply_text("📂 មិនទាន់មានឯកសារ")
        return

    await update.message.reply_text(
        "📂 Files:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

# ================== DOWNLOAD ==================
async def download_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    kind, name = query.data.split("|")
    folder = PDF_DIR if kind == "pdf" else TOOL_DIR
    path = os.path.join(folder, name)

    if not os.path.exists(path):
        await query.message.reply_text("❌ File not found")
        return

    await query.message.reply_document(open(path, "rb"))

# ================== AI /ask (GROUP ONLY) ==================
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

    await update.message.reply_text("🤖 កំពុងគិត...")

    answer = await ask_groq(returnquestion, update.message.chat.id)
    await update.message.reply_text(answer)

# ================== CALLBACK ROUTER ==================
async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "list_files":
        await list_files(update, context)

# ================== MAIN ==================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, group_ai_handler))
    app.add_handler(CallbackQueryHandler(download_file, pattern="^(pdf|tool)\\|"))
    app.add_handler(CallbackQueryHandler(button_router))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()