# Academic Hub Bot

A Telegram bot that serves as a resource hub for students, providing quick access to course materials organized by quarter and course. Students can browse exams, syllabi, quizzes, tests, lecture notes, and more through an interactive menu.

## Features

- **Quarter-based navigation** -- browse courses by Quarter 1 or Quarter 2
- **Course materials** -- access exams, syllabus, quizzes, tests, and additional files per course
- **Course overviews** -- view grading breakdowns, key dates, tools, and focus areas at a glance
- **File delivery** -- PDFs are sent directly to the chat via Telegram's `sendDocument`
- **Hub links** -- quick access to the Academic Hub forum, resource index, and announcements

### Supported Courses

| Quarter 1 | Quarter 2 |
|---|---|
| Calculus I | Python |
| Physics I | Chemistry Lab |
| Chemistry I | Writing & Rhetoric II |
| English Composition | Calculus II |
| | Physics II |
| | Seminar |

## Project Structure

```
academic-hub-bot/
  hub_bot.py              # Main bot: handlers, keyboards, state machine
  hub_data.py             # Course data, file paths, overview cards
  hub_format.py           # Telegram HTML formatting helpers
  tools/
    organize_resource_pdfs.py   # Utility to sort loose PDFs into the resource tree
  resources/              # (gitignored) Course materials organized by quarter
    Quarter_1/
      Calculus_I/
        exams/
        quizzes/
        tests/
        readings/
        ...
      Physics_I/
      ...
    Quarter_2/
      ...
```

## Setup

### Prerequisites

- Python 3.10+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/astrosol7/academic-hub-bot.git
   cd academic-hub-bot
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   .venv\Scripts\activate      # Windows
   ```

3. Install dependencies:

   ```bash
   pip install aiogram python-dotenv
   ```

4. Create a `.env` file in the project root with your bot token:

   ```
   TELEGRAM_BOT_TOKEN=your_token_here
   ```

5. Add course material PDFs under the `resources/` directory following the structure shown above.

### Running the Bot

```bash
python hub_bot.py
```

The bot registers two commands:
- `/start` -- opens the hub with a welcome message
- `/menu` -- returns to the main menu

## Organizing PDFs

A utility script is included to automatically sort loose PDF files into the correct course folders based on filename conventions.

### Filename Format

PDFs should follow the pattern: `<COURSE_CODE>_Q<quarter>_<description>.pdf`

Examples:
- `MATH_1110_Q1_Syllabus.pdf` --> `Quarter_1/Calculus_I/syllabus/`
- `PHYS_1310_Q1_Quiz_01.pdf` --> `Quarter_1/Physics_I/quizzes/`
- `CHEM_1210_Q1_Test_02.pdf` --> `Quarter_1/Chemistry_I/tests/`
- `MATH_1120_Q2_Exam_1.pdf` --> `Quarter_2/Calculus_II/exams/Exam_1/`

### Running the Organizer

```bash
python tools/organize_resource_pdfs.py
```

This scans the `resources/` directory for PDFs not already in a `Quarter_*` subdirectory and moves them to the appropriate location.

### Supported Course Codes

| Code | Course |
|---|---|
| `MATH_1110` | Calculus I |
| `PHYS_1310` | Physics I |
| `CHEM_1210` | Chemistry I |
| `ENGL_1610` | English Composition |
| `COMP_1210` | Python |
| `CHEML_1211` | Chemistry Lab |
| `ENGL_1720` | Writing & Rhetoric II |
| `MATH_1120` | Calculus II |
| `PHYS_1320` | Physics II |
| `SEM_100` | Seminar |

## License

This project is for educational use within the Academic Hub community.
