📦 File Cleaner – Safe Quarantine, Restore & Duplicate Detection

A powerful, safe, and extendable File Cleaner Utility built in Python.
It can detect and quarantine empty files, safely restore them later, identify duplicate files, and optionally move duplicates to a separate folder.
Supports YAML/JSON config, scheduler mode, preserved folder structure, and full dry-run support.

✨ Features
🗃️ Empty File Cleaner

Scan any folder (recursive by default)

Automatically move empty files into timestamped quarantine-YYYYMMDD-HHMMSS folders

Stores details in metadata.json

Optional preserved folder structure

♻️ One-Click Restore

Restore files from latest or specific quarantine folder

Safe overwrite protection (fallback to unique renaming)

Dry-run restore supported

🔍 Duplicate Detection (SHA-256)

Find duplicate files recursively

Move duplicate copies (keeping the original file intact)

Custom duplicate destination folder

Minimum size filter

⚙️ Config File Support (Optional)

Use cleaner.yml to set defaults such as:

ignore_hidden

preserve_structure

quarantine_base

duplicate detection defaults

scheduler interval

⏳ Scheduler Mode

Run automatic cleanup at scheduled intervals using the schedule package.

🧪 Dry-Run Mode

Preview every operation without modifying any file.

📁 Folder Structure (Example)
File_cleaner/
│
├── cleaner.py
├── cleaner.yml           # optional
├── README.md
└── quarantines/
    ├── quarantine-20250101-130210/
    │    ├── somefile.txt
    │    └── metadata.json

🛠️ Installation
1. Clone the repository
git clone https://github.com/yourusername/file-cleaner.git
cd file-cleaner

2. Install dependencies

(Optional but recommended)

pip install pyyaml schedule

🚀 Usage

All commands use:

python cleaner.py [target_folder] [options]

🔹 Basic Commands
Scan and quarantine empty files (interactive):
python cleaner.py .

Auto-confirm (no prompt):
python cleaner.py "C:\Users\Armaan\Downloads" --yes

Dry-run (preview only):
python cleaner.py "C:\path\to\target" --dry-run

Preserve folder structure inside quarantine:
python cleaner.py "C:\path" --preserve-structure --yes

🔹 Restore Commands
Restore from latest quarantine:
python cleaner.py --restore

Restore from specific quarantine:
python cleaner.py --restore --quarantine "path/to/quarantine-folder"

Dry-run restore:
python cleaner.py --restore --dry-run

🔹 Duplicate Detection
Find duplicates:
python cleaner.py "C:\path\to\target" --find-duplicates

Find duplicates only (skip empty-file scan):
python cleaner.py "C:\path\to\target" --find-duplicates-only

Move duplicate copies:
python cleaner.py "C:\path\to\target" --move-duplicates --yes

Move duplicates to custom folder:
python cleaner.py "C:\path" --move-duplicates --duplicates-dir "C:\duplicates" --yes

🔹 Scheduler Mode

Runs the clean operation periodically.

Run automatically every 24 hours (default):
python cleaner.py "C:\path\to\target" --run-scheduler

Every 60 minutes:
python cleaner.py "C:\path\to\target" --run-scheduler --schedule-interval-minutes 60


(Stop with CTRL + C)

⚙️ Config File (Optional)

Create a file named cleaner.yml:

ignore_hidden: true
preserve_structure: true
quarantine_base: ./quarantines

duplicates:
  enabled: false
  min_size: 1
  duplicates_dir: ./duplicates

schedule_interval_minutes: 1440


Run using:

python cleaner.py . --config cleaner.yml

📌 Metadata System

Every quarantine folder includes:

metadata.json


which contains:

[
  {
    "original": "C:/path/to/file.txt",
    "moved_to": "C:/quarantine/file.txt",
    "size": 0,
    "time": "2025-01-01 13:02:10",
    "action": "moved"
  }
]


This enables safe and reversible restore.

🧪 Testing

Quick test:

mkdir test_cleaner
cd test_cleaner
type nul > empty1.txt
type nul > empty2.txt
cd ..
python cleaner.py ".\test_cleaner" --yes
python cleaner.py --restore --yes

🧑‍💻 Contributing

Feel free to:

Open issues

Suggest new features

Contribute PRs

Ideas:

GUI using Tkinter

Multi-threaded hashing for faster duplicate detection

Trash bin mode instead of quarantine

Web dashboard

📜 License

MIT License — free to use, modify, and distribute.

🙌 Author

Armaan Shirgaonkar
Python & Java Developer
AI/Automation Enthusiast