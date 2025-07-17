# Movie Suggestion Bot

A Telegram bot that suggests movies, provides detailed information, and lets users save favorites! Powered by [python-telegram-bot](https://python-telegram-bot.org/) and [OMDb API](https://www.omdbapi.com/).

## Features

- 🎬 Get random movie suggestions with `/suggest`
- 🔍 Search for movies by name with `/movie <name>` or by sending a message
- 📝 View detailed info for any movie with `/imdb <imdb_id>`
- ⭐ Save your favorite movies with `/favorite <imdb_id>` and list them with `/favorites`
- 🤖 Inline queries: Search for movies directly from any chat
- 📋 `/help` and `/about` commands
- 🎞️ Movie posters, genres, directors, and plots
- User-friendly error handling

## Setup

1. **Clone the repo:**
   ```bash
   git clone <your-repo-url>
   cd <project-folder>
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Get your API keys:**
   - [Telegram Bot Token](https://t.me/BotFather)
   - [OMDb API Key](https://www.omdbapi.com/apikey.aspx)
4. **Set environment variables:**
   ```bash
   export TELEGRAM_TOKEN=your-telegram-token-here
   export OMDB_API_KEY=your-omdb-api-key-here
   ```
   (On Windows Command Prompt, use `set` instead of `export`)
5. **Run the bot:**
   ```bash
   python app.py
   ```

## Deployment

- Use the provided `Procfile` and `start.sh` for deployment on Render, Heroku, etc.
- Set your environment variables in the deployment dashboard.

## Usage

- `/start` — Welcome message
- `/help` — List all commands
- `/about` — About the bot
- `/suggest` — Get a random movie suggestion
- `/movie <name>` — Search for a movie
- `/imdb <imdb_id>` — Get details for a specific IMDb ID
- `/favorite <imdb_id>` — Add a movie to your favorites
- `/favorites` — List your favorite movies
- Inline queries: Type `@YourBotName <movie>` in any chat

## License

MIT
