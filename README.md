# ImpactLog

Track your daily wins. Own your career. Built for engineers who want to be review-ready every day.

## Setup

1. Clone the repo and enter the folder
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Add your Claude API key to `.env`:
   ```
   ANTHROPIC_API_KEY=your_key_here
   ```
5. Run:
   ```bash
   python main.py
   ```

## Features (Phase 1)
- Daily standup logging via CLI
- Claude-powered win extraction and tagging
- Weekly digest generation
- Local SQLite storage — your data stays on your machine
