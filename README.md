# Academic Hub Bot

Academic Hub Bot is a Telegram bot for browsing institution-specific course materials from a manifest-driven resource library. The project has been migrated to the `academic_hub/` package structure, so the old root-level bot modules are no longer the primary application entry point.

## Features

- Institution-aware resource browsing
- Manifest-driven categories, courses, and metadata
- Telegram inline navigation and document delivery
- Repository validation during startup
- Structured logging for warnings, validation issues, and runtime events
- Tools for ingesting, migrating, organizing, and validating resource files

## Current Architecture

The active application lives under `academic_hub/`:

```text
academic_hub/
  app.py                       # Main runtime entry point
  config.py                    # Environment/config loading
  clients/telegram/            # Telegram UI, handlers, keyboards, sessions
  domain/                      # Core models, service contracts, business logic
  infrastructure/              # Manifest loading, repository, validation
  manifests/                   # Institution/course/category definitions
  utils/                       # Formatting, parsing, logging helpers
```

High-level flow:

1. `academic_hub.app` loads configuration
2. `FilesystemContentRepository` builds and validates the in-memory index
3. Telegram dispatcher and handlers are created from `academic_hub.clients.telegram`
4. The bot starts polling and serves documents from `resources/`

## Project Structure

```text
academic-hub-bot/
  academic_hub/
  resources/
    institutions/
      sit/
        Quarter_1/
        Quarter_2/
  tests/
  tools/
  README.md
```

Legacy root-level files from the earlier single-module layout may still exist temporarily during migration, but the package-based structure above is the maintained implementation.

## Requirements

- Python 3.10+
- Telegram bot token from [@BotFather](https://t.me/BotFather)

## Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/astrosol7/academic-hub-bot.git
   cd academic-hub-bot
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

   On Linux/macOS:

   ```bash
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install aiogram python-dotenv
   ```

4. Create a `.env` file in the project root:

   ```env
   TELEGRAM_BOT_TOKEN=your_token_here
   HUB_INSTITUTION_SLUG=sit
   HUB_INSTITUTION_NAME=Shaggar Institute of Technology
   ACADEMIC_HUB_LOG_LEVEL=INFO
   ACADEMIC_HUB_MAX_INDEX_MEMORY_MB=32
   ```

5. Add your documents under:

   ```text
   resources/institutions/<institution_slug>/
   ```

## Running the Bot

Run the package entry point:

```bash
python -m academic_hub.app
```

## Resource and Manifest Model

The bot expects two main data sources:

- `academic_hub/manifests/` for institution, course, and category definitions
- `resources/institutions/<slug>/` for the actual PDF/resource files

Example resource layout:

```text
resources/
  institutions/
    sit/
      Quarter_1/
        Calculus_I/
        Physics_I/
      Quarter_2/
        Python/
        Calculus_II/
```

## Utility Scripts

The repository includes helper scripts under `tools/` for migration and content maintenance:

- `tools/organize_resource_pdfs.py`
- `tools/ingest_lms_to_resources.py`
- `tools/migrate_resources_layout.py`
- `tools/validate_resources.py`
- `tools/download_moodle_pdfs.py`

Run a script directly with Python, for example:

```bash
python tools/validate_resources.py
```

## Testing

Run the test suite with:

```bash
python -m pytest
```

## Contributing

1. Create a feature branch
2. Make and test your changes
3. Commit with a clear message
4. Open a pull request

## License

MIT License

Copyright (c) 2025 Solomon Dawit
