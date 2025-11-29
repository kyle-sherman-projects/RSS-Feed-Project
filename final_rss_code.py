"""
Academic RSS Feed Aggregator
A keyword-based RSS feed reader for tracking academic publications.

Author: Sherman Wayfarer
License: MIT
"""

import feedparser
import sqlite3
from datetime import datetime
from collections import defaultdict
import re
import time


class AcademicFeedReader:
    """
    RSS feed aggregator with keyword-based relevance scoring for academic research.
    
    Fetches articles from configured RSS feeds, scores them based on keyword matches,
    and stores relevant articles in a SQLite database.
    """
    
    def __init__(self, db_path='academic_feeds.db'):
        """
        Initialize the feed reader.
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        self.init_database()
        
        # Configure your RSS feed URLs here
        # Examples provided - replace with your own journal feeds
        self.feeds = [
            'https://www.journals.elsevier.com/computers-and-education/rss',
            'https://onlinelibrary.wiley.com/feed/14678535/most-recent',
            # Add more feed URLs here
        ]
        
        # Primary keywords: Core concepts in your research area
        # Higher weight = more important to your research
        self.primary_keywords = {
            'artificial intelligence': 3,
            'machine learning': 3,
            'AI': 2,
            'ChatGPT': 2,
            'generative AI': 3,
            'large language model': 3,
            'LLM': 2,
            'deep learning': 2,
        }
        
        # Context keywords: Domain-specific and methodology terms
        # These add relevance when combined with primary keywords
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
        
        # Minimum relevance score required to save an article
        # Increase for stricter filtering, decrease to capture more articles
        self.min_score = 3
    
    def init_database(self):
        """Create database tables if they don't exist."""
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
        """
        Calculate relevance score based on keyword matches in text.
        
        Args:
            text (str): Text to analyze (typically title + abstract)
            
        Returns:
            tuple: (relevance_score, list of matched keywords)
        """
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
        """
        Fetch and parse all configured RSS feeds.
        
        Returns:
            list: Articles meeting minimum relevance threshold
        """
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
                    
                    # Calculate relevance based on title and abstract
                    search_text = f"{title} {abstract}"
                    score, keywords = self.calculate_relevance(search_text)
                    
                    # Only process if meets minimum relevance threshold
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
                
                # Be respectful to servers - delay between requests
                time.sleep(1)
                
            except Exception as e:
                print(f"Error fetching {feed_url}: {e}")
        
        return new_articles
    
    def save_articles(self, articles):
        """
        Save articles to database, avoiding duplicates.
        
        Args:
            articles (list): List of article dictionaries to save
            
        Returns:
            int: Number of new articles saved
        """
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
                # Article already exists in database
                pass
        
        conn.commit()
        conn.close()
        return saved_count
    
    def get_recent_articles(self, limit=20, min_score=None):
        """
        Retrieve recent articles from database.
        
        Args:
            limit (int): Maximum number of articles to return
            min_score (int, optional): Minimum relevance score filter
            
        Returns:
            list: Articles sorted by fetch date and relevance
        """
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
        """
        Display articles in readable format.
        
        Args:
            articles (list): List of article tuples from database
        """
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
        """
        Main execution: fetch feeds, save articles, and display results.
        """
        print("Fetching feeds...")
        articles = self.fetch_feeds()
        print(f"\nFound {len(articles)} relevant articles")
        
        saved = self.save_articles(articles)
        print(f"Saved {saved} new articles to database")
        
        print(f"\n{'='*80}")
        print("TOP RECENT ARTICLES")
        print(f"{'='*80}")
        recent = self.get_recent_articles(limit=20)
        self.display_articles(recent)


if __name__ == "__main__":
    reader = AcademicFeedReader()
    reader.run()
