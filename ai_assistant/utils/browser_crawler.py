"""
Browser crawling utility for the AI Assistant.
"""

import time
import logging
import base64
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re

logger = logging.getLogger("ai_assistant")

class BrowserCrawler:
    """
    Utility for crawling and extracting information from browser windows.
    
    Attributes:
        driver (webdriver.Chrome): Selenium WebDriver instance
        cached_content (dict): Cached content from browser tabs
        last_capture_time (float): Timestamp of the last capture
    """
    
    def __init__(self):
        """Initialize the browser crawler utility."""
        self.driver = None
        self.cached_content = {}
        self.last_capture_time = 0
        
    def _initialize_driver(self):
        """Initialize the WebDriver if not already initialized."""
        if self.driver is not None:
            return
            
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")
            
            # Initialize the Chrome WebDriver
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            logger.info("WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"WebDriver initialization error: {e}")
            raise
    
    def _clean_text(self, text):
        """
        Clean and normalize text content.
        
        Args:
            text (str): Text to clean
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
            
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove non-printable characters
        text = re.sub(r'[^\x20-\x7E\n]', '', text)
        return text.strip()
    
    def _extract_content(self, html):
        """
        Extract meaningful content from HTML.
        
        Args:
            html (str): HTML content
            
        Returns:
            dict: Extracted content
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Extract title
        title = soup.title.string if soup.title else "No title"
        
        # Extract meta description
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag and "content" in meta_tag.attrs:
            meta_desc = meta_tag["content"]
        
        # Extract main content
        # First try to find main content areas
        main_content = ""
        main_tags = soup.find_all(["main", "article", "section", "div"], class_=re.compile(r'(content|main|article)'))
        
        if main_tags:
            for tag in main_tags:
                main_content += tag.get_text(separator=' ', strip=True) + "\n\n"
        else:
            # Fallback to body content
            main_content = soup.body.get_text(separator=' ', strip=True) if soup.body else ""
        
        # Extract headings for structure
        headings = []
        for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            headings.append(f"{h.name}: {h.get_text(strip=True)}")
        
        # Extract links
        links = []
        for link in soup.find_all("a", href=True):
            link_text = link.get_text(strip=True)
            if link_text:
                links.append(f"{link_text} - {link['href']}")
        
        return {
            "title": self._clean_text(title),
            "meta_description": self._clean_text(meta_desc),
            "headings": [self._clean_text(h) for h in headings],
            "main_content": self._clean_text(main_content),
            "links": links[:20]  # Limit to 20 links to avoid overwhelming
        }
    
    def capture(self, force_new=False):
        """
        Capture content from currently open browser tabs.
        
        Args:
            force_new (bool): Force a new capture even if a recent one exists
            
        Returns:
            dict: Captured browser content
        """
        current_time = time.time()
        # Use cached content if it's less than 10 seconds old
        if not force_new and self.cached_content and current_time - self.last_capture_time < 10:
            return self.cached_content
            
        try:
            self._initialize_driver()
            
            # Get all browser windows/tabs
            browser_content = {}
            
            # Try to connect to Chrome
            self.driver.get("chrome://newtab/")
            
            # Get list of open tabs (this is a simplified approach)
            # In a real implementation, you'd need to use browser-specific APIs
            # or browser extensions to get a list of open tabs
            
            # For demonstration, we'll just capture the current active tab
            current_url = self.driver.current_url
            if current_url and not current_url.startswith("chrome://"):
                html_content = self.driver.page_source
                browser_content[current_url] = self._extract_content(html_content)
            
            self.cached_content = browser_content
            self.last_capture_time = current_time
            return browser_content
            
        except Exception as e:
            logger.error(f"Browser crawl error: {e}")
            return {"error": str(e)}
    
    def close(self):
        """Close the WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
