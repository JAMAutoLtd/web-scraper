# MaxiSys Web Scraper

A modern web scraper built with Playwright for automating interactions with the MaxiSys website.

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv .venv
.\.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On Unix/MacOS
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

## Usage

Run the scraper:
```bash
python scraper_playwright.py
```

The scraper will:
1. Open a Chromium browser window
2. Navigate to the MaxiSys website
3. Interact with various dropdowns to select options
4. Capture debug information in the `debug_info` directory

## Debug Information

Debug information (screenshots and HTML) is automatically captured in the `debug_info` directory when:
- The page is initially loaded
- Any dropdown interaction fails
- An unexpected error occurs
- The final state is reached

## Notes

- The scraper runs in non-headless mode by default (you can see the browser window)
- Random delays are added between interactions to make the behavior more human-like
- All interactions are logged to the console 