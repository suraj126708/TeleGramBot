from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import requests
import os

# Get tokens from environment variables (best practice for deployment)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OMDB_API_KEY = os.getenv('OMDB_API_KEY')

# Function to search movies
def search_movies(query: str):
    url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={query}"
    response = requests.get(url).json()
    if response.get("Response") == "True":
        results = response.get("Search", [])[:3]  # Top 3 results
        movies = []
        for movie in results:
            imdb_id = movie['imdbID']
            title = movie['Title']
            year = movie['Year']
            imdb_url = f"https://www.imdb.com/title/{imdb_id}/"
            movies.append((title, year, imdb_url))
        return movies
    else:
        return []

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! Send me the *name of a movie*, and I’ll fetch IMDb details for you!\n\n"
        "Example: `Inception`",
        parse_mode='Markdown'
    )

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    movies = search_movies(query)

    if not movies:
        await update.message.reply_text("❌ No results found. Try another movie name.")
        return

    for title, year, imdb_url in movies:
        keyboard = [
            [
                InlineKeyboardButton("🎬 IMDb Page", url=imdb_url),
                InlineKeyboardButton(
                    "▶️ Trailer (YouTube)",
                    url=f"https://www.youtube.com/results?search_query={title.replace(' ', '+')}+trailer"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"🎬 *{title}* ({year})",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

# Main function
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running…")
    app.run_polling()

if __name__ == "__main__":
    main()
