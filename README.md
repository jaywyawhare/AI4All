# Warpspeed Scraper

## Project Structure
```
warpspeed/
├── scrapy.cfg
├── requirements.txt
└── scheme_scraper/
    ├── __init__.py
    ├── settings.py
    └── spiders/
        ├── __init__.py
        └── myscheme_extractor.py
```

## Requirements
- Python 3.8 or higher
- pip (Python package installer)

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Scraper

Make sure you are in the project root directory (warpspeed) where scrapy.cfg is located, then run:
```bash
scrapy crawl find_scheme
```

This will start the scraper and extract scheme information from myscheme.gov.in.

## Output
The scraper will extract:
- Scheme name
- URL
- Tags
- State
- Category
- Description
- Age requirements
- Benefits
- Exclusions
- Application process
- Eligibility criteria
- Required documents

## Note
Make sure all environment variables are properly set up before running the scraper.