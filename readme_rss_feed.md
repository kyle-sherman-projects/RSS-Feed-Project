# Academic RSS Feed Aggregator

A Python-based RSS feed reader designed for tracking academic journal publications with keyword-based relevance filtering. Built to help PhD researchers and academics stay current with literature in their field.

## Features

- Fetches and parses RSS feeds from academic journals
- Keyword-based relevance scoring system
- SQLite database storage with duplicate prevention
- Configurable feed sources and search terms
- Automated scheduling support (Windows Task Scheduler, cron)
- Exports results to text file for easy review

## Requirements

- Python 3.7+
- feedparser library

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/academic-rss-aggregator.git
cd academic-rss-aggregator
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Edit `academic_feed_reader.py` to customize for your research:

### 1. Add RSS Feeds

Update the `self.feeds` list with your journal RSS URLs:
```python
self.feeds = [
    'https://www.journals.elsevier.com/computers-and-education/rss',
    'https://onlinelibrary.wiley.com/feed/14678535/most-recent',
    # Add more feeds here
]
```

**Finding RSS Feeds:**
- Most journal websites have RSS icons or "Alerts" sections
- Publisher feed directories (Springer, Elsevier, Wiley, etc.)
- ERIC database search alerts
- PubMed saved search RSS feeds
- Google Scholar alerts (can be converted to RSS)

### 2. Configure Keywords

Modify keyword dictionaries with terms relevant to your research:

```python
self.primary_keywords = {
    'your keyword': 3,  # Higher weight = more important
    'another term': 2,
}

self.context_keywords = {
    'contextual term': 2,
    'related concept': 1,
}
```

### 3. Set Relevance Threshold

Adjust the minimum score for articles to be stored:
```python
self.min_score = 3  # Increase for stricter filtering
```

## Usage

### Basic Usage

Run the script manually:
```bash
python academic_feed_reader.py
```

Results will be displayed in the console and saved to `feed_output.txt`.

### Automated Scheduling

**Windows (Task Scheduler):**

1. Create a batch file `run_feed_reader.bat`:
```batch
@echo off
cd /d "C:\path\to\your\project"
call venv\Scripts\activate.bat
python academic_feed_reader.py > feed_output.txt 2>&1
```

2. Open Task Scheduler and create a new task
3. Set trigger (e.g., daily at 8:00 AM)
4. Set action to run your batch file

**macOS/Linux (cron):**

1. Edit crontab:
```bash
crontab -e
```

2. Add daily job (example: 8 AM daily):
```bash
0 8 * * * cd /path/to/project && ./venv/bin/python academic_feed_reader.py > feed_output.txt 2>&1
```

## Database

Articles are stored in `academic_feeds.db` (SQLite). View with:
- [DB Browser for SQLite](https://sqlitebrowser.org/)
- DataGrip or other database tools
- SQLite command line

### Database Schema

```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE,
    title TEXT,
    link TEXT,
    authors TEXT,
    abstract TEXT,
    published TEXT,
    feed_source TEXT,
    relevance_score INTEGER,
    keywords_matched TEXT,
    fetched_date TEXT
)
```

## Customization Ideas

- **Export to BibTeX**: Add citation export functionality using CrossRef API
- **Email Digests**: Integrate `smtplib` to send weekly summaries
- **Full-text Retrieval**: Fetch complete articles from open-access sources
- **Advanced Filtering**: Add author tracking, journal ranking filters
- **Web Interface**: Build Flask/FastAPI dashboard for browsing articles

## Example Use Case

This tool was originally developed for tracking research on AI adoption in K-12 education, monitoring journals in educational technology, computer science education, and school administration.

Sample configuration includes keywords like:
- artificial intelligence, machine learning, ChatGPT
- teacher, pedagogy, classroom instruction
- administrator, principal, school leadership
- K-12, secondary education

## Troubleshooting

**No articles found:**
- Verify RSS feed URLs are accessible
- Check keyword spelling and relevance
- Lower `min_score` threshold temporarily
- Ensure feeds contain recent content

**Database errors:**
- Delete `academic_feeds.db` to reset
- Check write permissions in project directory

**Import errors:**
- Verify virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

## Contributing

Contributions welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

MIT License - feel free to use and modify for your research needs.

## Acknowledgments

Built for academic researchers who need efficient literature monitoring without subscription to expensive alerting services.
