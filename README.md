# Academic Hub Bot

A Telegram bot that serves as a resource hub for students, providing quick access to course materials organized by quarter and course. Students can browse exams, syllabi, quizzes, tests, lecture notes, and more through an interactive menu.

## Features

- **Quarter-based navigation** -- browse courses by Quarters
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

## Usage Guide

Here is how the bot works from a student's perspective:

### User Flow

```
/start
  |
  v
Welcome message + photo
  |
  v
Main Menu: [ Quarter 1 ] [ Quarter 2 ]
  |
  v  (tap "Quarter 1")
Course List: [ Calculus I ] [ Physics I ] [ Chemistry I ] [ English Composition ]
             [ Hub links ] [ Main menu ]
  |
  v  (tap "Calculus I")
Course Menu: [ Exams ] [ Syllabus ] [ Quizzes ] [ Tests ]
             [ Overview ] [ More files ]
             [ << Courses ] [ Main menu ]
  |
  v  (tap "Exams")
Bot sends all exam PDFs as documents to the chat
  |
  v  (tap "Overview")
Bot displays a course overview card:
  - Goal, Grading breakdown, Key dates, Tools, Focus areas
  |
  v  (tap "More files")
Extra Categories: [ Lecture recordings ] [ Homework ] [ Lecture notes ]
                  [ Breakout notes ] [ Assignments ]
                  [ << Courses ] [ Main menu ]
```

### Bot Commands

| Command | Description |
|---|---|
| `/start` | Opens the hub with a welcome message and main menu |
| `/menu` | Returns to the main menu from any screen |

### What Students See

1. **Main menu** -- two buttons: "Quarter 1" and "Quarter 2"
2. **Course list** -- buttons for each course in the selected quarter, plus "Hub links" and "Main menu"
3. **Course menu** -- six action buttons: Exams, Syllabus, Quizzes, Tests, Overview, More files
4. **File delivery** -- tapping Exams/Syllabus/Quizzes/Tests sends the matching PDFs directly into the chat
5. **Overview card** -- a formatted text card with grading, dates, tools, and focus areas
6. **More files** -- extra categories like lecture recordings, homework, lecture notes, breakout notes, and assignments

Navigation buttons (`<< Courses`, `Main menu`) are always available to go back.

## Architecture Overview

```
+-----------------+       +-----------------+       +-----------------+
|   hub_bot.py    | ----> |   hub_data.py   | ----> |  hub_format.py  |
|                 |       |                 |       |                 |
| Telegram        |       | Course records  |       | HTML helpers    |
| handlers &      |       | (COURSES dict)  |       | (bold, mono,    |
| FSM states      |       |                 |       |  blockquote,    |
|                 |       | File iterators  |       |  overview cards)|
| Reply keyboards |       | (exams, quizzes,|       |                 |
|                 |       |  syllabus, etc) |       | SIT color       |
| Document batch  |       |                 |       | palette         |
| sending         |       | Path helpers    |       +-----------------+
+-----------------+       | (quarter_dir,   |
                          |  course_dir)    |
                          +-----------------+
                                  |
                                  v
                          +-----------------+
                          |   resources/    |
                          |  Quarter_1/     |
                          |    Course/      |
                          |      exams/     |
                          |      quizzes/   |
                          |      ...        |
                          |  Quarter_2/     |
                          |    ...          |
                          +-----------------+
```

### How the Modules Interact

- **`hub_bot.py`** is the entry point. It creates the `Bot` and `Dispatcher`, defines all message handlers, and manages user navigation with aiogram's **Finite State Machine (FSM)**.
- **`hub_data.py`** holds all course data (titles, folders, overview HTML, topic links) and provides file-iteration functions that scan the `resources/` directory tree.
- **`hub_format.py`** provides Telegram HTML formatting utilities (bold headings, monospace, blockquotes, overview card builders).

### State Management

The bot uses aiogram's FSM with `MemoryStorage` to track where each user is in the navigation:

| State | Description |
|---|---|
| `main` | User is at the main menu (choosing a quarter) |
| `quarter_courses` | User is viewing the course list for a quarter |
| `course_menu` | User has selected a course and is choosing an action |
| `pick_more_category` | User is browsing extra file categories |

State data stores the current `quarter` (1 or 2) and `course_id` (e.g. `"calculus_i"`). Each handler reads this data to know which files to send or which keyboard to display.

> **Note:** `MemoryStorage` means all user states are lost when the bot restarts. Users simply need to tap `/start` again.

### Handler Flow

1. `/start` or `/menu` --> clears state, shows main menu
2. "Quarter 1" / "Quarter 2" --> sets `quarter` in state, shows course list
3. Course title button --> sets `course_id` in state, shows course action menu
4. Action button (Exams/Syllabus/etc.) --> reads state, iterates files from disk, sends documents
5. `<< Courses` / `Main menu` --> navigates back by updating the FSM state

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

## Contributing

Contributions are welcome! Here's how to get involved:

### How to Submit Changes

1. **Fork** the repository
2. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** and test them locally
4. **Commit** with a clear message describing what you changed and why:
   ```bash
   git commit -m "Add: brief description of your change"
   ```
5. **Push** to your fork and open a **Pull Request** against `main`

### What You Can Contribute

- **Course materials** -- add PDFs for new or existing courses
- **New courses** -- add a new `Course` entry in `hub_data.py` and update `QUARTER_COURSES`
- **Bug fixes** -- found something broken? Fix it and submit a PR
- **New features** -- ideas like search, bookmarks, or inline queries are welcome
- **Documentation** -- improve this README or add inline code comments

### Coding Standards

- **Python 3.10+** -- use type hints and `from __future__ import annotations`
- **Follow existing patterns** -- look at how existing handlers and data entries are structured before adding new ones
- **HTML escaping** -- always use `html.escape()` for user-facing text sent via Telegram
- **Keep it simple** -- this bot is meant to be lightweight and easy to maintain
- **Test locally** -- run the bot with a test token and verify your changes work before submitting

### Adding a New Course

1. Add the course data to the `COURSES` dict in `hub_data.py`:
   ```python
   "your_course_id": Course(
       title="Course Name",
       quarter=1,  # or 2
       folder="Course_Folder_Name",
       topic_key="relevant_topic",
       overview_html=_overview_card(
           "Course Name",
           "Course goal description.",
           ["Grading item 1 -- weight%", ...],
           ["Key date 1", ...],
           ["Tool 1", ...],
           ["Focus area 1", ...],
       ),
       hub_links_blurb=_hub_blurb("relevant_topic"),
   )
   ```
2. Add the course ID to the appropriate quarter list in `QUARTER_COURSES`
3. Add the course code mapping to `PREFIX_MAP` in `tools/organize_resource_pdfs.py`
4. Create the resource directory: `resources/Quarter_N/Course_Folder_Name/`

## License

MIT License

Copyright (c) 2025 Solomon Dawit

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
