from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputTextMessageContent, InlineQueryResultArticle, CallbackQuery
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, InlineQueryHandler, CallbackQueryHandler
import requests
import os
import json
import random
from datetime import datetime, timedelta
import asyncio
from typing import List, Dict, Optional
from flask import Flask, request, Response
import telegram
import logging
import threading

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OMDB_API_KEY = os.getenv('OMDB_API_KEY')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')  # Optional for enhanced features

# Constants
GENRES = {
    'action': 28, 'adventure': 12, 'animation': 16, 'comedy': 35,
    'crime': 80, 'documentary': 99, 'drama': 18, 'family': 10751,
    'fantasy': 14, 'history': 36, 'horror': 27, 'music': 10402,
    'mystery': 9648, 'romance': 10749, 'scifi': 878, 'thriller': 53,
    'war': 10752, 'western': 37
}

class MovieBot:
    def __init__(self):
        self.user_preferences = {}  # Store user preferences in memory
        
    def get_movie_details(self, imdb_id: str) -> Optional[Dict]:
        """Get detailed movie information from OMDB API"""
        url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}&plot=full"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None
    
    def search_movies(self, query: str, page: int = 1) -> List[Dict]:
        """Search movies using OMDB API"""
        url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={query}&page={page}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("Response") == "True":
                return data.get("Search", [])
            return []
        except requests.RequestException:
            return []
    
    def get_popular_movies(self) -> List[Dict]:
        """Get popular movies (fallback list if TMDB not available)"""
        popular_movies = [
            "The Shawshank Redemption", "The Godfather", "The Dark Knight",
            "Pulp Fiction", "The Lord of the Rings", "Forrest Gump",
            "Inception", "The Matrix", "Goodfellas", "The Silence of the Lambs",
            "Saving Private Ryan", "Schindler's List", "Interstellar",
            "The Avengers", "Titanic", "Avatar", "Jurassic Park",
            "Star Wars", "Back to the Future", "Casablanca"
        ]
        
        results = []
        for movie in random.sample(popular_movies, min(5, len(popular_movies))):
            search_results = self.search_movies(movie)
            if search_results:
                results.append(search_results[0])
        return results
    
    def get_movies_by_genre(self, genre: str) -> List[Dict]:
        """Search OMDB for movies by genre, fallback to hardcoded list if needed."""
        genre_searches = {
            'action': ['John Wick', 'Mad Max: Fury Road', 'Die Hard', 'Terminator 2', 'Mission Impossible'],
            'adventure': ['Indiana Jones', 'Pirates of the Caribbean', 'Jurassic Park', 'The Revenant', 'Life of Pi'],
            'animation': ['Toy Story', 'Spirited Away', 'Finding Nemo', 'The Lion King', 'Up'],
            'comedy': ['The Hangover', 'Anchorman', 'Superbad', 'Dumb and Dumber', 'Borat'],
            'crime': ['The Godfather', 'Pulp Fiction', 'Goodfellas', 'The Departed', 'Se7en'],
            'documentary': ['March of the Penguins', 'Free Solo', 'The Last Dance', 'Blackfish', '13th'],
            'drama': ['The Shawshank Redemption', 'Forrest Gump', 'Fight Club', 'A Beautiful Mind', 'Whiplash'],
            'family': ['Home Alone', 'Paddington', 'The Incredibles', 'Matilda', 'Mary Poppins'],
            'fantasy': ['The Lord of the Rings', 'Harry Potter', 'Pan\'s Labyrinth', 'The Princess Bride', 'Stardust'],
            'history': ['Schindler\'s List', '12 Years a Slave', 'Lincoln', 'Dunkirk', 'The King\'s Speech'],
            'horror': ['The Shining', 'Halloween', 'Scream', 'The Exorcist', 'It'],
            'music': ['La La Land', 'Whiplash', 'Bohemian Rhapsody', 'A Star is Born', 'Amadeus'],
            'mystery': ['Gone Girl', 'Zodiac', 'Prisoners', 'The Girl with the Dragon Tattoo', 'Knives Out'],
            'romance': ['Titanic', 'The Notebook', 'Casablanca', 'When Harry Met Sally', 'Pretty Woman'],
            'scifi': ['Star Wars', 'Blade Runner', 'The Matrix', 'Interstellar', 'Alien'],
            'thriller': ['Se7en', 'The Silence of the Lambs', 'Zodiac', 'Gone Girl', 'Shutter Island'],
            'war': ['Saving Private Ryan', 'Dunkirk', '1917', 'Hacksaw Ridge', 'Full Metal Jacket'],
            'western': ['The Good, the Bad and the Ugly', 'Django Unchained', 'Unforgiven', 'True Grit', 'No Country for Old Men']
        }
        genre_key = genre.lower()
        # Step 1: Try OMDB search and filter by genre
        search_results = self.search_movies(genre)
        filtered = []
        for movie in search_results:
            imdb_id = movie.get('imdbID')
            if imdb_id:
                details = self.get_movie_details(imdb_id)
                if details and 'Genre' in details:
                    genres = [g.strip().lower() for g in details['Genre'].split(',')]
                    if genre_key in genres:
                        filtered.append(movie)
            if len(filtered) >= 3:
                break
        # Step 2: If not enough, fill from hardcoded list
        if len(filtered) < 3 and genre_key in genre_searches:
            needed = 3 - len(filtered)
            # Avoid duplicates
            already_titles = {m.get('Title') for m in filtered}
            for title in genre_searches[genre_key]:
                if title not in already_titles:
                    search = self.search_movies(title)
                    if search:
                        filtered.append(search[0])
                        if len(filtered) >= 3:
                            break
        return filtered
    
    def format_movie_info(self, movie_data: Dict) -> str:
        """Format movie information for display"""
        if not movie_data or movie_data.get("Response") == "False":
            return "❌ Movie information not available"
        
        title = movie_data.get('Title', 'N/A')
        year = movie_data.get('Year', 'N/A')
        director = movie_data.get('Director', 'N/A')
        genre = movie_data.get('Genre', 'N/A')
        imdb_rating = movie_data.get('imdbRating', 'N/A')
        runtime = movie_data.get('Runtime', 'N/A')
        plot = movie_data.get('Plot', 'N/A')
        actors = movie_data.get('Actors', 'N/A')
        
        # Truncate plot if too long
        if len(plot) > 300:
            plot = plot[:300] + "..."
        
        return f"""🎬 *{title}* ({year})
        
🎭 *Genre:* {genre}
🎪 *Director:* {director}
⭐ *IMDb Rating:* {imdb_rating}/10
⏱️ *Runtime:* {runtime}
🎭 *Cast:* {actors}

📖 *Plot:* {plot}"""
    
    def create_movie_keyboard(self, imdb_id: str, title: str) -> InlineKeyboardMarkup:
        """Create inline keyboard for movie options"""
        keyboard = [
            [
                InlineKeyboardButton("🎬 IMDb Page", url=f"https://www.imdb.com/title/{imdb_id}/"),
                InlineKeyboardButton("▶️ Trailer", url=f"https://www.youtube.com/results?search_query={title.replace(' ', '+')}+trailer")
            ],
            [
                InlineKeyboardButton("ℹ️ Full Details", callback_data=f"details_{imdb_id}"),
                InlineKeyboardButton("💾 Save to Watchlist", callback_data=f"save_{imdb_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Create main menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("🔍 Search Movies", callback_data="search_movies"),
                InlineKeyboardButton("🔥 Popular Movies", callback_data="popular_movies")
            ],
            [
                InlineKeyboardButton("🎭 Browse by Genre", callback_data="browse_genre"),
                InlineKeyboardButton("🎲 Random Movie", callback_data="random_movie")
            ],
            [
                InlineKeyboardButton("📋 My Watchlist", callback_data="my_watchlist"),
                InlineKeyboardButton("⚙️ Preferences", callback_data="preferences")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_genre_keyboard(self) -> InlineKeyboardMarkup:
        """Create genre selection keyboard"""
        keyboard = []
        genre_items = list(GENRES.keys())
        
        # Create rows of 3 genres each
        for i in range(0, len(genre_items), 3):
            row = []
            for j in range(i, min(i + 3, len(genre_items))):
                genre = genre_items[j]
                row.append(InlineKeyboardButton(
                    genre.capitalize(), 
                    callback_data=f"genre_{genre}"
                ))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")])
        return InlineKeyboardMarkup(keyboard)

# Initialize bot instance
movie_bot = MovieBot()

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user_id = update.effective_user.id
    movie_bot.user_preferences[user_id] = {
        'watchlist': [],
        'favorite_genres': [],
        'last_search': None
    }
    
    welcome_message = """🎬 *Welcome to CineBot!* 🎬

Your ultimate movie companion! I can help you:

🔍 Search for any movie
🔥 Discover popular movies
🎭 Browse movies by genre
🎲 Get random movie suggestions
📋 Manage your personal watchlist
⚙️ Set your preferences

*Choose an option below to get started:*"""
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=movie_bot.get_main_menu_keyboard(),
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler"""
    help_text = (
        "*Movie Suggestion Bot Commands:*\n\n"
        "/start - Welcome message\n"
        "/help - Show this help\n"
        "/about - About this bot\n"
        "/suggest - Suggest a random popular movie\n"
        "/movie <name> - Search for a movie\n"
        "/imdb <imdb_id> - Get details for a specific IMDb ID\n"
        "/favorite <imdb_id> - Add a movie to your favorites\n"
        "/favorites - List your favorite movies\n"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search command handler"""
    if not context.args:
        await update.message.reply_text("Please provide a movie name to search.\nExample: `/search inception`", parse_mode='Markdown')
        return
    
    query = ' '.join(context.args)
    await process_search(update, query)

async def popular_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Popular movies command handler"""
    await update.message.reply_text("🔥 *Getting popular movies...*", parse_mode='Markdown')
    
    popular_movies = movie_bot.get_popular_movies()
    
    if not popular_movies:
        await update.message.reply_text("❌ Unable to fetch popular movies. Please try again later.")
        return
    
    await update.message.reply_text("🔥 *Popular Movies:*", parse_mode='Markdown')
    
    for movie in popular_movies:
        title = movie.get('Title', 'Unknown')
        year = movie.get('Year', 'Unknown')
        imdb_id = movie.get('imdbID', '')
        
        if imdb_id:
            keyboard = movie_bot.create_movie_keyboard(imdb_id, title)
            await update.message.reply_text(
                f"🎬 *{title}* ({year})",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )

async def random_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Random movie command handler"""
    await update.message.reply_text("🎲 *Finding a random movie for you...*", parse_mode='Markdown')
    
    popular_movies = movie_bot.get_popular_movies()
    
    if not popular_movies:
        await update.message.reply_text("❌ Unable to get random movie. Please try again later.")
        return
    
    random_movie = random.choice(popular_movies)
    title = random_movie.get('Title', 'Unknown')
    year = random_movie.get('Year', 'Unknown')
    imdb_id = random_movie.get('imdbID', '')
    
    if imdb_id:
        movie_details = movie_bot.get_movie_details(imdb_id)
        if movie_details:
            formatted_info = movie_bot.format_movie_info(movie_details)
            keyboard = movie_bot.create_movie_keyboard(imdb_id, title)
            
            await update.message.reply_text(
                f"🎲 *Random Movie Suggestion:*\n\n{formatted_info}",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )

async def watchlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's watchlist"""
    user_id = update.effective_user.id
    
    if user_id not in movie_bot.user_preferences:
        movie_bot.user_preferences[user_id] = {'watchlist': [], 'favorite_genres': [], 'last_search': None}
    
    watchlist = movie_bot.user_preferences[user_id]['watchlist']
    
    if not watchlist:
        await update.message.reply_text("📋 Your watchlist is empty. Start adding movies!")
        return
    
    await update.message.reply_text(f"📋 *Your Watchlist ({len(watchlist)} movies):*", parse_mode='Markdown')
    
    for imdb_id in watchlist:
        movie_details = movie_bot.get_movie_details(imdb_id)
        if movie_details:
            title = movie_details.get('Title', 'Unknown')
            year = movie_details.get('Year', 'Unknown')
            keyboard = movie_bot.create_movie_keyboard(imdb_id, title)
            
            await update.message.reply_text(
                f"🎬 *{title}* ({year})",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )

async def clear_watchlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear user's watchlist"""
    user_id = update.effective_user.id
    
    if user_id in movie_bot.user_preferences:
        movie_bot.user_preferences[user_id]['watchlist'] = []
        await update.message.reply_text("✅ Your watchlist has been cleared!")
    else:
        await update.message.reply_text("📋 Your watchlist is already empty.")

# Message handlers
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (movie searches)"""
    query = update.message.text
    
    # Check if it's a movie search
    if len(query.strip()) > 0 and not query.startswith('/'):
        await process_search(update, query)
    else:
        await update.message.reply_text(
            "Please use the menu buttons or type a movie name to search!",
            reply_markup=movie_bot.get_main_menu_keyboard()
        )

async def process_search(update, query: str):
    """Process movie search"""
    await update.message.reply_text(f"🔍 *Searching for '{query}'...*", parse_mode='Markdown')
    
    movies = movie_bot.search_movies(query)
    
    if not movies:
        await update.message.reply_text(
            f"❌ No results found for '{query}'. Try a different movie name.",
            reply_markup=movie_bot.get_main_menu_keyboard()
        )
        return
    
    await update.message.reply_text(f"🔍 *Search Results for '{query}':*", parse_mode='Markdown')
    
    # Show top 5 results
    for movie in movies[:5]:
        title = movie.get('Title', 'Unknown')
        year = movie.get('Year', 'Unknown')
        imdb_id = movie.get('imdbID', '')
        
        if imdb_id:
            keyboard = movie_bot.create_movie_keyboard(imdb_id, title)
            await update.message.reply_text(
                f"🎬 *{title}* ({year})",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )

# Callback query handlers
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboards"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    # Initialize user preferences if not exists
    if user_id not in movie_bot.user_preferences:
        movie_bot.user_preferences[user_id] = {'watchlist': [], 'favorite_genres': [], 'last_search': None}
    
    if data == "main_menu":
        await query.edit_message_text(
            "🎬 *CineBot Main Menu*\n\nChoose an option:",
            reply_markup=movie_bot.get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    elif data == "search_movies":
        await query.edit_message_text(
            "🔍 *Search Movies*\n\nJust type the name of any movie and I'll find it for you!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]),
            parse_mode='Markdown'
        )
    
    elif data == "popular_movies":
        await query.edit_message_text("🔥 *Getting popular movies...*", parse_mode='Markdown')
        
        popular_movies = movie_bot.get_popular_movies()
        
        if popular_movies:
            await query.edit_message_text(
                "🔥 *Popular Movies:*\n\nCheck out these trending movies:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]),
                parse_mode='Markdown'
            )
            
            for movie in popular_movies:
                title = movie.get('Title', 'Unknown')
                year = movie.get('Year', 'Unknown')
                imdb_id = movie.get('imdbID', '')
                
                if imdb_id:
                    keyboard = movie_bot.create_movie_keyboard(imdb_id, title)
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=f"🎬 *{title}* ({year})",
                        reply_markup=keyboard,
                        parse_mode='Markdown'
                    )
        else:
            await query.edit_message_text(
                "❌ Unable to fetch popular movies. Please try again later.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]),
                parse_mode='Markdown'
            )
    
    elif data == "browse_genre":
        await query.edit_message_text(
            "🎭 *Browse by Genre*\n\nSelect a genre to explore:",
            reply_markup=movie_bot.get_genre_keyboard(),
            parse_mode='Markdown'
        )
    
    elif data.startswith("genre_"):
        genre = data.split("_")[1]
        await query.edit_message_text(f"🎭 *Getting {genre.capitalize()} movies...*", parse_mode='Markdown')
        
        genre_movies = movie_bot.get_movies_by_genre(genre)
        
        if genre_movies:
            await query.edit_message_text(
                f"🎭 *{genre.capitalize()} Movies:*",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Genres", callback_data="browse_genre")]]),
                parse_mode='Markdown'
            )
            
            for movie in genre_movies:
                title = movie.get('Title', 'Unknown')
                year = movie.get('Year', 'Unknown')
                imdb_id = movie.get('imdbID', '')
                
                if imdb_id:
                    keyboard = movie_bot.create_movie_keyboard(imdb_id, title)
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=f"🎬 *{title}* ({year})",
                        reply_markup=keyboard,
                        parse_mode='Markdown'
                    )
        else:
            await query.edit_message_text(
                f"❌ Unable to fetch {genre} movies. Please try again later.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Genres", callback_data="browse_genre")]]),
                parse_mode='Markdown'
            )
    
    elif data == "random_movie":
        await query.edit_message_text("🎲 *Finding a random movie for you...*", parse_mode='Markdown')
        
        popular_movies = movie_bot.get_popular_movies()
        
        if popular_movies:
            random_movie = random.choice(popular_movies)
            title = random_movie.get('Title', 'Unknown')
            year = random_movie.get('Year', 'Unknown')
            imdb_id = random_movie.get('imdbID', '')
            
            if imdb_id:
                movie_details = movie_bot.get_movie_details(imdb_id)
                if movie_details:
                    formatted_info = movie_bot.format_movie_info(movie_details)
                    keyboard = movie_bot.create_movie_keyboard(imdb_id, title)
                    
                    await query.edit_message_text(
                        f"🎲 *Random Movie Suggestion:*\n\n{formatted_info}",
                        reply_markup=keyboard,
                        parse_mode='Markdown'
                    )
        else:
            await query.edit_message_text(
                "❌ Unable to get random movie. Please try again later.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]),
                parse_mode='Markdown'
            )
    
    elif data == "my_watchlist":
        watchlist = movie_bot.user_preferences[user_id]['watchlist']
        
        if not watchlist:
            await query.edit_message_text(
                "📋 *Your Watchlist*\n\nYour watchlist is empty. Start adding movies!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                f"📋 *Your Watchlist ({len(watchlist)} movies):*",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🗑️ Clear Watchlist", callback_data="clear_watchlist")],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
                ]),
                parse_mode='Markdown'
            )
            
            for imdb_id in watchlist:
                movie_details = movie_bot.get_movie_details(imdb_id)
                if movie_details:
                    title = movie_details.get('Title', 'Unknown')
                    year = movie_details.get('Year', 'Unknown')
                    keyboard = movie_bot.create_movie_keyboard(imdb_id, title)
                    
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=f"🎬 *{title}* ({year})",
                        reply_markup=keyboard,
                        parse_mode='Markdown'
                    )
    
    elif data == "clear_watchlist":
        movie_bot.user_preferences[user_id]['watchlist'] = []
        await query.edit_message_text(
            "✅ *Watchlist Cleared*\n\nYour watchlist has been cleared!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]),
            parse_mode='Markdown'
        )
    
    elif data == "preferences":
        watchlist_count = len(movie_bot.user_preferences[user_id]['watchlist'])
        await query.edit_message_text(
            f"⚙️ *Your Preferences*\n\n📋 Movies in Watchlist: {watchlist_count}\n\n*More preference options coming soon!*",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]),
            parse_mode='Markdown'
        )
    
    elif data.startswith("details_"):
        imdb_id = data.split("_")[1]
        movie_details = movie_bot.get_movie_details(imdb_id)
        
        if movie_details:
            formatted_info = movie_bot.format_movie_info(movie_details)
            title = movie_details.get('Title', 'Unknown')
            keyboard = movie_bot.create_movie_keyboard(imdb_id, title)
            
            await query.edit_message_text(
                formatted_info,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            await query.answer("❌ Unable to fetch movie details.")
    
    elif data.startswith("save_"):
        imdb_id = data.split("_")[1]
        
        if imdb_id not in movie_bot.user_preferences[user_id]['watchlist']:
            movie_bot.user_preferences[user_id]['watchlist'].append(imdb_id)
            await query.answer("✅ Movie added to your watchlist!")
        else:
            await query.answer("ℹ️ Movie is already in your watchlist.")

# Helper: Send movie info (short)
async def send_movie_info(update, movie):
    imdb_id = movie['imdbID']
    title = movie['Title']
    year = movie['Year']
    poster = movie.get('Poster')
    url = f"https://www.imdb.com/title/{imdb_id}/"
    keyboard = [[
        InlineKeyboardButton("🎬 IMDb Page", url=url),
        InlineKeyboardButton("▶️ Trailer (YouTube)", url=f"https://www.youtube.com/results?search_query={title.replace(' ', '+')}+trailer")
    ], [
        InlineKeyboardButton("⭐ Add to Watchlist", callback_data=f"addfav:{imdb_id}")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"🎬 *{title}* ({year})\n[IMDb Page]({url})"
    if poster and poster != 'N/A':
        await update.message.reply_photo(photo=poster, caption=text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# Callback handler for 'Add to Watchlist' button
async def add_to_watchlist_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: CallbackQuery = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("addfav:"):
        imdb_id = data.split(":", 1)[1]
        user_id = query.from_user.id
        details = movie_bot.get_movie_details(imdb_id)
        if not details:
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text("❌ No details found for that IMDb ID.")
            return
        user_favs = movie_bot.user_preferences.setdefault(user_id, {'watchlist': set(), 'favorite_genres': [], 'last_search': None})['watchlist']
        if imdb_id in user_favs:
            await query.answer("Already in your watchlist!", show_alert=True)
        else:
            user_favs.add(imdb_id)
            await query.answer("Added to your watchlist! ⭐", show_alert=True)

# Create a single event loop for the whole app
loop = asyncio.new_event_loop()

def run_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Main function
def main():
    """Main function to run the bot"""
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN not found. Please set it in environment variables.")
        return
    
    if not OMDB_API_KEY:
        print("❌ OMDB_API_KEY not found. Please set it in environment variables.")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("popular", popular_command))
    application.add_handler(CommandHandler("random", random_command))
    application.add_handler(CommandHandler("watchlist", watchlist_command))
    application.add_handler(CommandHandler("clear_watchlist", clear_watchlist_command))

    # Message and callback handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(CallbackQueryHandler(add_to_watchlist_callback, pattern=r"^addfav:"))

    # Flask app for webhook
    flask_app = Flask(__name__)

    @flask_app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
    def webhook():
        if request.method == "POST":
            update = telegram.Update.de_json(request.get_json(force=True), application.bot)
            try:
                # Schedule the coroutine in the global event loop
                future = asyncio.run_coroutine_threadsafe(application.process_update(update), loop)
                future.result()  # Wait for completion and raise exceptions if any
                return Response("ok", status=200)
            except Exception as e:
                print("Webhook error:", e)
                return Response("error", status=500)
        else:
            return Response("not found", status=404)

    # Health check route for '/'
    @flask_app.route("/")
    def health():
        return "CineBot is running! Use the Telegram bot to interact.", 200

    # Set webhook and initialize application
    WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://telegrambot-53po.onrender.com')
    async def setup():
        await application.initialize()
        await application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook/{TELEGRAM_TOKEN}")
    loop.run_until_complete(setup())

    print("🎬 CineBot is running with Flask webhook server...")
    print("# For production, consider using a WSGI server like gunicorn or waitress instead of Flask's built-in server.")

    # Start the event loop in a background thread before starting Flask
    threading.Thread(target=run_loop, args=(loop,), daemon=True).start()
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    main()