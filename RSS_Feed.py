import feedparser
import sqlite3
from datetime import datetime
from collections import defaultdict
import re
import time


class AcademicFeedReader:
    def __init__(self, db_path='academic_feeds.db'):
        self.db_path = db_path
        self.init_database()

        # Configure your feeds here
        self.feeds = [
            'https://www.journals.elsevier.com/computers-and-education/rss',
            'https://onlinelibrary.wiley.com/feed/14678535/most-recent',
            'https://rss.sciencedirect.com/publication/science/2666920X'
            # Add more journal feeds here
        ]

        # Configure keyword weights
        # Higher weight = more important
        self.primary_keywords = {
            'artificial intelligence': 3,
            'machine learning': 3,
            'AI': 2,
            'ChatGPT': 2,
            'generative AI': 3,
            'large language model': 3,
            'LLM': 2,
            'deep learning': 2,
            'educational technology adoption': 2,
            'decision support system': 2
        }

        self.context_keywords = {
            'administrator': 2,
            'principal': 2,
            'school leadership': 2,
            'decision making': 2,
            'teacher': 2,
            'pedagogy': 2,
            'instruction': 2,
            'classroom': 1,
            'secondary school': 2,
            'K-12': 2,
            'high school': 2,
            'professional development': 1,
            'adoption': 2,
            'implementation': 1,
        }

        # Minimum score threshold to show article
        self.min_score = 2

    def init_database(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS articles (
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
        ''')
        conn.commit()
        conn.close()

    def calculate_relevance(self, text):
        """Calculate relevance score based on keyword matches"""
        text_lower = text.lower()
        score = 0
        matched_keywords = []

        # Check primary keywords
        for keyword, weight in self.primary_keywords.items():
            if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', text_lower):
                score += weight
                matched_keywords.append(keyword)

        # Check context keywords
        for keyword, weight in self.context_keywords.items():
            if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', text_lower):
                score += weight
                matched_keywords.append(keyword)

        return score, matched_keywords

    def fetch_feeds(self):
        """Fetch and parse all configured feeds"""
        new_articles = []

        for feed_url in self.feeds:
            print(f"Fetching: {feed_url}")
            try:
                feed = feedparser.parse(feed_url)

                for entry in feed.entries:
                    # Extract relevant fields
                    guid = entry.get('id', entry.get('link', ''))
                    title = entry.get('title', 'No title')
                    link = entry.get('link', '')

                    # Get abstract/summary
                    abstract = entry.get('summary', entry.get('description', ''))

                    # Get authors
                    authors = ', '.join([a.get('name', '') for a in entry.get('authors', [])])
                    if not authors:
                        authors = entry.get('author', '')

                    # Get publication date
                    pub_date = entry.get('published', entry.get('updated', ''))

                    # Calculate relevance
                    search_text = f"{title} {abstract}"
                    score, keywords = self.calculate_relevance(search_text)

                    # Only process if meets minimum score
                    if score >= self.min_score:
                        article = {
                            'guid': guid,
                            'title': title,
                            'link': link,
                            'authors': authors,
                            'abstract': abstract,
                            'published': pub_date,
                            'feed_source': feed_url,
                            'relevance_score': score,
                            'keywords_matched': ', '.join(keywords)
                        }
                        new_articles.append(article)

                # Be respectful to servers
                time.sleep(1)

            except Exception as e:
                print(f"Error fetching {feed_url}: {e}")

        return new_articles

    def save_articles(self, articles):
        """Save articles to database, avoiding duplicates"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        saved_count = 0
        for article in articles:
            try:
                c.execute('''
                    INSERT INTO articles 
                    (guid, title, link, authors, abstract, published, 
                     feed_source, relevance_score, keywords_matched, fetched_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article['guid'],
                    article['title'],
                    article['link'],
                    article['authors'],
                    article['abstract'],
                    article['published'],
                    article['feed_source'],
                    article['relevance_score'],
                    article['keywords_matched'],
                    datetime.now().isoformat()
                ))
                saved_count += 1
            except sqlite3.IntegrityError:
                # Article already exists
                pass

        conn.commit()
        conn.close()
        return saved_count

    def get_recent_articles(self, limit=20, min_score=None):
        """Retrieve recent articles from database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        if min_score:
            c.execute('''
                SELECT title, authors, link, relevance_score, keywords_matched, published
                FROM articles
                WHERE relevance_score >= ?
                ORDER BY fetched_date DESC, relevance_score DESC
                LIMIT ?
            ''', (min_score, limit))
        else:
            c.execute('''
                SELECT title, authors, link, relevance_score, keywords_matched, published
                FROM articles
                ORDER BY fetched_date DESC, relevance_score DESC
                LIMIT ?
            ''', (limit,))

        articles = c.fetchall()
        conn.close()
        return articles

    def display_articles(self, articles):
        """Display articles in readable format"""
        for i, article in enumerate(articles, 1):
            title, authors, link, score, keywords, pub_date = article
            print(f"\n{i}. [{score} pts] {title}")
            if authors:
                print(f"   Authors: {authors}")
            print(f"   Link: {link}")
            print(f"   Keywords: {keywords}")
            if pub_date:
                print(f"   Published: {pub_date}")
            print("-" * 80)

    def run(self):
        """Main execution: fetch, save, and display articles"""
        print("Fetching feeds...")
        articles = self.fetch_feeds()
        print(f"\nFound {len(articles)} relevant articles")

        saved = self.save_articles(articles)
        print(f"Saved {saved} new articles to database")

        print(f"\n{'=' * 80}")
        print("TOP RECENT ARTICLES")
        print(f"{'=' * 80}")
        recent = self.get_recent_articles(limit=20)
        self.display_articles(recent)


# Usage
if __name__ == "__main__":
    reader = AcademicFeedReader()
    reader.run()