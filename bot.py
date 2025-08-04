import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from database import TodoItem, get_db
from sqlalchemy.orm import Session

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "📝 Welcome to your Todo List Bot!\n\n"
        "Here's what you can do:\n"
        "/add <task> - Add a new task\n"
        "/list - Show all tasks\n"
        "/done <number> - Mark a task as done\n"
        "/delete <number> - Delete a task\n"
        "/help - Show this help message"
    )

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a new task to the todo list."""
    user_id = update.message.from_user.id
    task_text = ' '.join(context.args)
    
    if not task_text:
        await update.message.reply_text("Please provide a task. Example: /add Buy milk")
        return
    
    db: Session = next(get_db())
    new_task = TodoItem(user_id=user_id, task=task_text)
    db.add(new_task)
    db.commit()
    
    await update.message.reply_text(f"✅ Task added: {task_text}")

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all tasks."""
    user_id = update.message.from_user.id
    db: Session = next(get_db())
    
    tasks = db.query(TodoItem).filter(TodoItem.user_id == user_id).order_by(TodoItem.id).all()
    
    if not tasks:
        await update.message.reply_text("Your todo list is empty! Add a task with /add")
        return
    
    message = "📋 Your Todo List:\n\n"
    for i, task in enumerate(tasks, start=1):
        status = "✓" if task.completed else "✗"
        message += f"{i}. [{status}] {task.task}\n"
    
    # Add action buttons
    keyboard = [
        [
            InlineKeyboardButton("Mark Done", callback_data="action_done"),
            InlineKeyboardButton("Delete", callback_data="action_delete")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def mark_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mark a task as done."""
    user_id = update.message.from_user.id
    if not context.args:
        await update.message.reply_text("Please specify the task number. Example: /done 1")
        return
    
    try:
        task_num = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")
        return
    
    db: Session = next(get_db())
    tasks = db.query(TodoItem).filter(TodoItem.user_id == user_id).order_by(TodoItem.id).all()
    
    if 1 <= task_num <= len(tasks):
        task = tasks[task_num - 1]
        task.completed = True
        db.commit()
        await update.message.reply_text(f"🎉 Task marked as done: {task.task}")
    else:
        await update.message.reply_text("Invalid task number.")

async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a task."""
    user_id = update.message.from_user.id
    if not context.args:
        await update.message.reply_text("Please specify the task number. Example: /delete 1")
        return
    
    try:
        task_num = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")
        return
    
    db: Session = next(get_db())
    tasks = db.query(TodoItem).filter(TodoItem.user_id == user_id).order_by(TodoItem.id).all()
    
    if 1 <= task_num <= len(tasks):
        task = tasks[task_num - 1]
        db.delete(task)
        db.commit()
        await update.message.reply_text(f"🗑️ Task deleted: {task.task}")
    else:
        await update.message.reply_text("Invalid task number.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "action_done":
        await query.edit_message_text("Please reply with the task number to mark as done. Example: /done 1")
    elif query.data == "action_delete":
        await query.edit_message_text("Please reply with the task number to delete. Example: /delete 1")

def main():
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("add", add_task))
    application.add_handler(CommandHandler("list", list_tasks))
    application.add_handler(CommandHandler("done", mark_done))
    application.add_handler(CommandHandler("delete", delete_task))
    
    # Button handler
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Start the Bot
    application.run_polling()

if __name__ == "__main__":
    main()
