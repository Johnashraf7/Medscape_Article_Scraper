import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import json
from urllib.parse import urljoin, urlparse
import re
import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import random
import hashlib
import base64
import zipfile
from io import BytesIO
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import logging
from fake_useragent import UserAgent
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedMedscapeScraper:
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.user_agents = self._generate_user_agents()
        self.setup_session()
        self.base_url = "https://emedicine.medscape.com"
        self.setup_pdf_styles()
        self.content_hash_tracker = set()
        self.request_count = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.user_agent_rotation_frequency = 3
        self.setup_retry_strategy()
        self.request_history = []
        self.start_time = datetime.now()
        
    def _generate_user_agents(self):
        """Generate a large pool of realistic user agents"""
        agents = []
        try:
            # Generate multiple user agents using fake_useragent
            for _ in range(100):
                agents.append(self.ua.random)
        except:
            # Fallback user agents if fake_useragent fails
            agents = [
                # Chrome - Various versions and platforms
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                
                # Firefox
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
                'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
                
                # Safari
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
                
                # Edge
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/119.0.0.0 Safari/537.36',
                
                # Mobile
                'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
                'Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
                'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.210 Mobile Safari/537.36',
                'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.210 Mobile Safari/537.36',
            ]
        return list(set(agents))  # Remove duplicates

    def setup_retry_strategy(self):
        """Setup retry strategy with exponential backoff"""
        retry_strategy = Retry(
            total=5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            backoff_factor=2,
            respect_retry_after_header=True
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def setup_session(self):
        """Setup session with advanced headers to mimic real browser"""
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/avif,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        })

    def rotate_user_agent(self):
        """Rotate user agent with intelligent selection"""
        self.request_count += 1
        
        if self.request_count % self.user_agent_rotation_frequency == 0:
            new_agent = random.choice(self.user_agents)
            self.session.headers.update({'User-Agent': new_agent})
            
            if st.session_state.get('debug_mode', False):
                st.write(f"🔄 Rotated to: {new_agent[:80]}...")

    def get_intelligent_delay(self, base_delay=3):
        """Get intelligent delay based on recent success rate"""
        if not self.request_history:
            return base_delay + random.uniform(0.5, 2.0)
        
        # Calculate success rate from recent requests
        recent_requests = self.request_history[-10:]  # Last 10 requests
        success_rate = sum(1 for r in recent_requests if r['success']) / len(recent_requests)
        
        # Adjust delay based on success rate
        if success_rate < 0.5:
            return base_delay + random.uniform(3, 6)  # Longer delay if many failures
        elif success_rate > 0.8:
            return base_delay + random.uniform(0.1, 1.0)  # Shorter delay if successful
        
        return base_delay + random.uniform(0.5, 2.0)

    def make_request(self, url, max_retries=8, delay=3):
        """Make request with advanced retry logic and intelligent delays"""
        for attempt in range(max_retries):
            try:
                self.rotate_user_agent()
                current_delay = self.get_intelligent_delay(delay)
                
                if st.session_state.get('debug_mode', False):
                    st.write(f"⏳ Delay: {current_delay:.2f}s (Attempt {attempt + 1}/{max_retries})")
                
                time.sleep(current_delay)
                
                response = self.session.get(
                    url, 
                    timeout=20,
                    verify=False,  # Bypass SSL verification for better compatibility
                    allow_redirects=True
                )
                
                # Record request attempt
                request_record = {
                    'timestamp': datetime.now(),
                    'url': url,
                    'attempt': attempt + 1,
                    'status_code': response.status_code,
                    'success': False
                }
                
                if response.status_code == 403:
                    st.warning(f"🔒 Access denied (403), retrying... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(10)
                    continue
                elif response.status_code == 429:
                    wait_time = 20 + (attempt * 5)
                    st.warning(f"⏳ Rate limited, waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                elif response.status_code == 503:
                    st.warning(f"🔧 Service unavailable, retrying... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(15)
                    continue
                elif response.status_code != 200:
                    st.warning(f"⚠️ Status {response.status_code}, retrying... (attempt {attempt + 1}/{max_retries})")
                    continue
                
                response.raise_for_status()
                
                # Check for blocking patterns
                if self.is_blocked(response.text):
                    st.warning(f"🚫 Blocking detected, rotating... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(12)
                    continue
                
                # Check if we got actual content
                if self.is_valid_content(response.text):
                    request_record['success'] = True
                    self.request_history.append(request_record)
                    self.successful_requests += 1
                    return response
                else:
                    st.warning(f"📄 Invalid content received, retrying... (attempt {attempt + 1}/{max_retries})")
                    
            except requests.exceptions.Timeout:
                st.warning(f"⏰ Timeout, retrying... (attempt {attempt + 1}/{max_retries})")
            except requests.exceptions.SSLError:
                st.warning(f"🔐 SSL Error, retrying... (attempt {attempt + 1}/{max_retries})")
            except requests.exceptions.RequestException as e:
                st.warning(f"❌ Request failed (attempt {attempt + 1}/{max_retries}): {str(e)[:100]}...")
            
            if attempt < max_retries - 1:
                backoff_delay = delay * (2 ** attempt)  # Exponential backoff
                time.sleep(backoff_delay)
        
        self.failed_requests += 1
        if 'request_record' in locals():
            self.request_history.append(request_record)
        st.error(f"💥 Failed to fetch {url} after {max_retries} attempts")
        return None

    def is_blocked(self, html_content):
        """Enhanced blocking detection"""
        blocked_indicators = [
            "access denied", "cloudflare", "captcha", "bot protection",
            "security check", "distil", "incapsula", "blocked",
            "please verify you are human", "unusual traffic"
        ]
        
        content_lower = html_content.lower()
        return any(indicator in content_lower for indicator in blocked_indicators)

    def is_valid_content(self, html_content):
        """Check if content is valid medical article content"""
        valid_indicators = [
            "medscape", "article", "medical", "treatment", "diagnosis",
            "symptoms", "overview", "background", "pathophysiology"
        ]
        
        content_lower = html_content.lower()
        valid_count = sum(1 for indicator in valid_indicators if indicator in content_lower)
        return valid_count >= 2  # At least 2 medical indicators

    def get_performance_metrics(self):
        """Get performance metrics for dashboard"""
        total_time = (datetime.now() - self.start_time).total_seconds()
        success_rate = (self.successful_requests / max(self.request_count, 1)) * 100 if self.request_count > 0 else 0
        
        recent_success = 0
        if self.request_history:
            recent_requests = self.request_history[-20:]  # Last 20 requests
            recent_success = sum(1 for r in recent_requests if r['success']) / len(recent_requests) * 100 if recent_requests else 0
        
        return {
            'total_requests': self.request_count,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': success_rate,
            'recent_success_rate': recent_success,
            'total_time_seconds': total_time,
            'requests_per_minute': (self.request_count / max(total_time/60, 1)),
            'user_agents_count': len(self.user_agents)
        }

    def setup_pdf_styles(self):
        """Setup enhanced PDF styles"""
        self.styles = getSampleStyleSheet()
        
        self.article_title_style = ParagraphStyle(
            name='ArticleTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=15,
            textColor=colors.HexColor('#2E86AB'),
            alignment=1  # Center
        )
        
        self.section_title_style = ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=8,
            textColor=colors.HexColor('#A23B72'),
            spaceBefore=12
        )
        
        self.subsection_style = ParagraphStyle(
            name='Subsection',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=6,
            textColor=colors.HexColor('#F18F01'),
            spaceBefore=8
        )
        
        self.normal_style = ParagraphStyle(
            name='NormalText',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leading=15,
            textColor=colors.HexColor('#2B2D42')
        )
        
        self.metadata_style = ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6C757D'),
            spaceAfter=3
        )
        
        self.analytics_style = ParagraphStyle(
            name='Analytics',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#28A745'),
            spaceAfter=4,
            backColor=colors.HexColor('#F8F9FA')
        )

    def extract_article_links(self, html_content):
        """Extract all article URLs with enhanced filtering"""
        soup = BeautifulSoup(html_content, 'html.parser')
        article_links = []
        
        st.info("🔍 Extracting articles from categorized sections...")
        
        # Multiple extraction strategies
        extraction_methods = [
            # Method 1: Topic sections
            lambda: soup.find_all('div', class_='topic-section'),
            # Method 2: Article grids
            lambda: soup.find_all('div', class_=re.compile(r'article|item|card')),
            # Method 3: Any div with links containing /article/
            lambda: [div for div in soup.find_all('div') if div.find('a', href=re.compile(r'/article/\d+'))]
        ]
        
        for method in extraction_methods:
            sections = method()
            for section in sections:
                category = "Unknown"
                category_elem = section.find(['h2', 'h3', 'div'], class_=re.compile(r'title|head|category'))
                if category_elem:
                    category = category_elem.get_text(strip=True)
                
                links = section.find_all('a', href=re.compile(r'/article/\d+'))
                for link in links:
                    href = link.get('href')
                    title = link.get_text(strip=True)
                    
                    if href and title and len(title) > 10:  # Filter out navigation links
                        full_url = urljoin(self.base_url, href)
                        article_links.append({
                            'url': full_url,
                            'title': title,
                            'category': category
                        })
            
            if article_links:  # Stop if we found articles
                break
        
        # Remove duplicates
        seen_urls = set()
        unique_links = []
        
        for article in article_links:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_links.append(article)
        
        st.success(f"✅ Found {len(unique_links)} unique articles")
        return unique_links

    def get_all_article_sections(self, overview_url):
        """Get URLs for all sections of an article with enhanced discovery"""
        response = self.make_request(overview_url)
        if not response:
            return {'Overview': overview_url}
            
        soup = BeautifulSoup(response.content, 'html.parser')
        sections = {}
        
        # Standard medical section order (priority)
        standard_order = [
            'Overview', 'Background', 'Pathophysiology', 'Etiology', 
            'Epidemiology', 'Prognosis', 'Presentation', 'History', 
            'Physical Examination', 'DDx', 'Differential Diagnoses',
            'Workup', 'Approach Considerations', 'Laboratory Studies', 
            'Imaging Studies', 'Treatment', 'Medical Care', 'Surgical Care', 
            'Prevention', 'Medication', 'Medication Summary',
            'Guidelines', 'Guidelines Summary', 'References'
        ]
        
        # Multiple navigation discovery strategies
        nav_selectors = [
            'div.sections-nav',
            'div#dd_nav',
            'div.sections-nav ul',
            'ul.nav-tabs',
            'div.tab-navigation',
            'div.article-nav'
        ]
        
        nav = None
        for selector in nav_selectors:
            nav = soup.select_one(selector)
            if nav:
                break
        
        if nav:
            links = nav.find_all('a', href=True)
            for link in links:
                section_name = link.get_text(strip=True)
                href = link['href']
                
                # Skip non-content links
                skip_keywords = ['Show All', 'Media Gallery', 'References', 'Share', 'Print', 'Feedback', 'Q&A']
                if any(keyword in section_name for keyword in skip_keywords):
                    continue
                
                if href.startswith('javascript:') or href.startswith('#'):
                    continue
                
                if href.startswith('/'):
                    full_url = urljoin(self.base_url, href)
                else:
                    full_url = urljoin(overview_url, href)
                
                if section_name and section_name not in sections:
                    sections[section_name] = full_url
        
        # Always include overview
        sections['Overview'] = overview_url
        
        # Order sections by priority
        ordered_sections = {}
        for section_name in standard_order:
            if section_name in sections:
                ordered_sections[section_name] = sections[section_name]
        
        # Add remaining sections
        for section_name, url in sections.items():
            if section_name not in ordered_sections:
                ordered_sections[section_name] = url
        
        return ordered_sections

    def create_content_hash(self, text):
        """Create hash of content to detect duplicates"""
        return hashlib.md5(text.strip().encode()).hexdigest()

    def scrape_section_content(self, section_url, section_name):
        """Scrape content from a specific section with enhanced extraction"""
        response = self.make_request(section_url)
        if not response:
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        content = []
        
        # Multiple content area discovery strategies
        content_selectors = [
            'div.drugdbsectioncontent',
            'div.article-content',
            'div.refsection_content',
            'div.drugdbmain',
            'div.content',
            'div.main-content',
            'article',
            'div.article-body'
        ]
        
        content_area = None
        for selector in content_selectors:
            content_area = soup.select_one(selector)
            if content_area:
                break
        
        if not content_area:
            return content
        
        # Extract content with enhanced filtering
        elements = content_area.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'p', 'ul', 'ol', 'table'])
        
        current_section = {'heading': section_name, 'content': []}
        seen_hashes = set()
        
        for element in elements:
            # Skip navigation and irrelevant elements
            if element.get('class'):
                class_names = ' '.join(element.get('class', []))
                skip_classes = ['action-items', 'back_next_btn', 'emed-logo', 'nav', 'menu', 'sidebar']
                if any(skip_class in class_names for skip_class in skip_classes):
                    continue
            
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                if current_section['content']:
                    content.append(current_section)
                
                heading_text = element.get_text(strip=True)
                if heading_text and len(heading_text) > 2:
                    current_section = {
                        'heading': heading_text,
                        'level': element.name,
                        'content': []
                    }
            
            elif element.name == 'p':
                text = element.get_text(strip=True)
                if text and len(text) > 15:  # Reduced minimum length
                    content_hash = self.create_content_hash(text)
                    if content_hash not in seen_hashes and not any(nav_text in text for nav_text in ['Previous', 'Next:', 'Show All']):
                        seen_hashes.add(content_hash)
                        current_section['content'].append({
                            'type': 'paragraph',
                            'text': text
                        })
            
            elif element.name in ['ul', 'ol']:
                list_items = []
                for li in element.find_all('li'):
                    item_text = li.get_text(strip=True)
                    if item_text and len(item_text) > 3:  # Reduced minimum length
                        list_items.append(item_text)
                
                if list_items:
                    list_hash = self.create_content_hash(''.join(list_items))
                    if list_hash not in seen_hashes:
                        seen_hashes.add(list_hash)
                        current_section['content'].append({
                            'type': 'list',
                            'style': 'unordered' if element.name == 'ul' else 'ordered',
                            'items': list_items
                        })
            
            elif element.name == 'table':
                # Extract table data
                table_data = []
                for row in element.find_all('tr'):
                    row_data = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                    if row_data:
                        table_data.append(row_data)
                
                if table_data and len(table_data) > 1:  # At least header + one row
                    current_section['content'].append({
                        'type': 'table',
                        'data': table_data
                    })
        
        if current_section['content']:
            content.append(current_section)
        
        return content

    def scrape_complete_article(self, article_url):
        """Enhanced article scraping with better error handling and progress tracking"""
        st.info(f"🎯 Starting advanced scraping: {article_url}")
        
        try:
            # Initialize scraping metrics
            scraping_metrics = {
                'sections_found': 0,
                'sections_scraped': 0,
                'content_blocks': 0,
                'start_time': datetime.now()
            }
            
            sections = self.get_all_article_sections(article_url)
            scraping_metrics['sections_found'] = len(sections)
            st.info(f"📑 Found {len(sections)} sections to scrape")
            
            complete_content = {}
            successful_sections = 0
            
            # Create detailed progress tracking
            if st.session_state.get('single_article_mode', False):
                progress_bar = st.progress(0)
                status_text = st.empty()
                metrics_text = st.empty()
                total_sections = len(sections)
            
            for i, (section_name, section_url) in enumerate(sections.items()):
                if st.session_state.get('single_article_mode', False):
                    progress = (i + 1) / total_sections
                    progress_bar.progress(progress)
                    status_text.text(f"🔍 Scraping section {i+1}/{total_sections}: {section_name}")
                    
                    # Update real-time metrics
                    metrics_text.text(
                        f"📊 Progress: {successful_sections}/{i+1} successful | "
                        f"Blocks: {scraping_metrics['content_blocks']} | "
                        f"Success Rate: {self.get_performance_metrics()['recent_success_rate']:.1f}%"
                    )
                
                section_content = self.scrape_section_content(section_url, section_name)
                
                if section_content:
                    complete_content[section_name] = section_content
                    successful_sections += 1
                    scraping_metrics['content_blocks'] += len(section_content)
                    
                    if st.session_state.get('single_article_mode', False):
                        st.success(f"✅ {section_name}: {len(section_content)} content blocks")
                else:
                    st.warning(f"⚠️ {section_name}: No content extracted")
                
                # Adaptive delay based on current performance
                time.sleep(self.get_intelligent_delay(1))
            
            # Clear progress indicators
            if st.session_state.get('single_article_mode', False):
                status_text.empty()
                progress_bar.empty()
                metrics_text.empty()
            
            # Get article info
            response = self.make_request(article_url)
            if not response:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title = self._extract_title(soup)
            authors = self._extract_authors(soup)
            updated_date = self._extract_updated_date(soup)
            
            total_content_blocks = sum(len(content) for content in complete_content.values())
            scraping_metrics['end_time'] = datetime.now()
            scraping_metrics['total_duration'] = (scraping_metrics['end_time'] - scraping_metrics['start_time']).total_seconds()
            
            return {
                'url': article_url,
                'title': title,
                'authors': authors,
                'last_updated': updated_date,
                'sections': complete_content,
                'total_sections': len(complete_content),
                'total_content_blocks': total_content_blocks,
                'successful_sections': successful_sections,
                'scraping_metrics': scraping_metrics,
                'performance_metrics': self.get_performance_metrics()
            }
            
        except Exception as e:
            st.error(f"💥 Advanced scraping failed: {e}")
            logger.error(f"Scraping error: {e}", exc_info=True)
            return None

    def _extract_title(self, soup):
        """Enhanced title extraction"""
        title_selectors = ['h1', 'div.article-title', 'title']
        for selector in title_selectors:
            title = soup.select_one(selector)
            if title:
                text = title.get_text(strip=True)
                if text and len(text) > 5:
                    return text
        return "Title not found"

    def _extract_authors(self, soup):
        """Enhanced author extraction"""
        authors = []
        author_selectors = [
            'div.condition-title-info',
            'div.authors',
            'div.article-authors',
            'meta[name="author"]'
        ]
        
        for selector in author_selectors:
            author_section = soup.select_one(selector)
            if author_section:
                if selector == 'meta[name="author"]':
                    author_content = author_section.get('content', '')
                    if author_content:
                        authors = [auth.strip() for auth in author_content.split(';') if auth.strip()]
                else:
                    author_text = author_section.get_text()
                    if 'Author:' in author_text:
                        author_part = author_text.split('Author:')[-1].split('more...')[0]
                        authors = [auth.strip() for auth in author_part.split(';') if auth.strip()]
                
                if authors:
                    break
        
        return authors if authors else ["Authors information not available"]

    def _extract_updated_date(self, soup):
        """Enhanced date extraction"""
        date_selectors = [
            'div.clinref_updated',
            'div.article-updated',
            'meta[property="article:modified_time"]',
            'div.update-date'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                if selector.startswith('meta'):
                    date_text = date_elem.get('content', '')
                else:
                    date_text = date_elem.get_text(strip=True)
                
                if date_text:
                    # Clean up date text
                    date_text = re.sub(r'Updated:\s*', '', date_text)
                    return date_text.strip()
        
        return "Date not available"

    def create_enhanced_pdf(self, article_data, output_dir="enhanced_pdfs"):
        """Create enhanced PDF with better formatting and analytics"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        safe_title = "".join(c for c in article_data['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title[:60]}_{datetime.now().strftime('%H%M%S')}.pdf"
        filepath = os.path.join(output_dir, filename)
        
        try:
            doc = SimpleDocTemplate(
                filepath,
                pagesize=letter,
                rightMargin=54,
                leftMargin=54,
                topMargin=72,
                bottomMargin=72,
                title=article_data['title'],
                author=", ".join(article_data['authors'])
            )
            
            story = []
            
            # Enhanced title page
            story.append(Paragraph(article_data['title'], self.article_title_style))
            story.append(Spacer(1, 20))
            
            # Analytics section
            story.append(Paragraph("Scraping Analytics", self.section_title_style))
            story.append(Spacer(1, 10))
            
            metrics = article_data.get('performance_metrics', {})
            scraping_metrics = article_data.get('scraping_metrics', {})
            
            analytics_data = [
                f"• Success Rate: {metrics.get('success_rate', 0):.1f}%",
                f"• Total Requests: {metrics.get('total_requests', 0)}",
                f"• Sections Scraped: {article_data['successful_sections']}/{article_data['total_sections']}",
                f"• Content Blocks: {article_data['total_content_blocks']}",
                f"• Scraping Duration: {scraping_metrics.get('total_duration', 0):.1f}s",
                f"• Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ]
            
            for item in analytics_data:
                story.append(Paragraph(item, self.analytics_style))
            
            story.append(Spacer(1, 20))
            
            # Metadata
            story.append(Paragraph("Document Information", self.section_title_style))
            story.append(Spacer(1, 10))
            
            metadata = [
                f"• Source: {article_data['url']}",
                f"• Authors: {', '.join(article_data['authors'])}",
                f"• Last Updated: {article_data['last_updated']}",
                f"• PDF Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ]
            
            for item in metadata:
                story.append(Paragraph(item, self.metadata_style))
            
            story.append(Spacer(1, 20))
            story.append(PageBreak())
            
            # Enhanced table of contents
            story.append(Paragraph("Detailed Table of Contents", self.section_title_style))
            story.append(Spacer(1, 15))
            
            for section_name, section_content in article_data['sections'].items():
                blocks_count = len(section_content)
                story.append(Paragraph(f"• {section_name} ({blocks_count} content blocks)", self.normal_style))
                story.append(Spacer(1, 5))
            
            story.append(Spacer(1, 20))
            story.append(PageBreak())
            
            # Enhanced content with better formatting
            for section_name, section_content in article_data['sections'].items():
                if section_content:
                    story.append(Paragraph(section_name, self.section_title_style))
                    story.append(Spacer(1, 12))
                    
                    for content_block in section_content:
                        if content_block['heading'] and content_block['heading'] != section_name:
                            story.append(Paragraph(content_block['heading'], self.subsection_style))
                            story.append(Spacer(1, 8))
                        
                        for item in content_block['content']:
                            if item['type'] == 'paragraph':
                                paragraphs = self._split_paragraph(item['text'])
                                for para in paragraphs:
                                    story.append(Paragraph(para, self.normal_style))
                                    story.append(Spacer(1, 6))
                            
                            elif item['type'] == 'list':
                                for list_item in item['items']:
                                    bullet = "•" if item['style'] == 'unordered' else f"{item['items'].index(list_item) + 1}."
                                    story.append(Paragraph(f"{bullet} {list_item}", self.normal_style))
                                    story.append(Spacer(1, 3))
                                story.append(Spacer(1, 8))
                    
                    story.append(Spacer(1, 15))
                    
                    # Add page break after major sections
                    if section_name in ['Overview', 'Presentation', 'Treatment', 'Medication', 'References']:
                        story.append(PageBreak())
            
            doc.build(story)
            file_size = os.path.getsize(filepath)
            
            # Add to download history
            download_record = {
                'title': article_data['title'],
                'filename': filename,
                'file_size_kb': file_size / 1024,
                'timestamp': datetime.now(),
                'sections': article_data['successful_sections'],
                'content_blocks': article_data['total_content_blocks']
            }
            
            st.session_state.download_history.append(download_record)
            
            st.success(f"🎉 Enhanced PDF created: {filename} ({file_size/1024:.1f} KB)")
            return filepath
            
        except Exception as e:
            st.error(f"💥 Enhanced PDF creation failed: {e}")
            logger.error(f"PDF creation error: {e}", exc_info=True)
            return None

    def _split_paragraph(self, text, max_chars=500):
        """Split long paragraphs intelligently"""
        if len(text) <= max_chars:
            return [text]
        
        # Split by sentences first
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        paragraphs = []
        current_para = ""
        
        for sentence in sentences:
            if len(current_para) + len(sentence) < max_chars:
                current_para += sentence + '. '
            else:
                if current_para:
                    paragraphs.append(current_para.strip())
                current_para = sentence + '. '
        
        if current_para:
            paragraphs.append(current_para.strip())
        
        return paragraphs if paragraphs else [text]

def create_dashboard_metrics(scraper):
    """Create a comprehensive dashboard with metrics"""
    metrics = scraper.get_performance_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Requests", metrics['total_requests'])
    with col2:
        st.metric("Success Rate", f"{metrics['success_rate']:.1f}%")
    with col3:
        st.metric("Recent Success", f"{metrics['recent_success_rate']:.1f}%")
    with col4:
        st.metric("Req/Min", f"{metrics['requests_per_minute']:.1f}")
    
    # Create performance chart
    if len(scraper.request_history) > 1:
        df = pd.DataFrame(scraper.request_history)
        df['success_numeric'] = df['success'].astype(int)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'], 
            y=df['success_numeric'].cumsum(),
            mode='lines',
            name='Successful Requests',
            line=dict(color='green', width=3)
        ))
        
        fig.update_layout(
            title="Request Success Over Time",
            xaxis_title="Time",
            yaxis_title="Cumulative Successful Requests",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)

def create_zip_file(pdf_paths, zip_filename="medscape_articles.zip"):
    """Create a ZIP file containing all PDFs"""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for pdf_path in pdf_paths:
            pdf_name = os.path.basename(pdf_path)
            zip_file.write(pdf_path, pdf_name)
    
    zip_buffer.seek(0)
    return zip_buffer

def create_combined_pdf(pdf_paths, output_filename="combined_articles.pdf"):
    """Create a single PDF combining all individual PDFs"""
    merger = PdfMerger()
    
    for pdf_path in pdf_paths:
        try:
            merger.append(pdf_path)
        except Exception as e:
            st.warning(f"⚠️ Could not merge {os.path.basename(pdf_path)}: {e}")
    
    combined_buffer = BytesIO()
    merger.write(combined_buffer)
    merger.close()
    combined_buffer.seek(0)
    
    return combined_buffer

def render_single_article_tab():
    """Render the enhanced single article tab"""
    st.session_state.single_article_mode = True
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        article_url = st.text_input(
            "🎯 Enter Article URL:",
            placeholder="https://emedicine.medscape.com/article/...",
            key="single_article_url"
        )
        
        # URL validation and preview
        if article_url:
            if re.match(r'https?://emedicine\.medscape\.com/article/\d+', article_url):
                st.success("✅ Valid Medscape URL detected")
            else:
                st.warning("⚠️ This doesn't look like a valid Medscape article URL")
    
    with col2:
        st.markdown("###")
        if st.button("🚀 Generate Enhanced PDF", key="single_article", type="primary", use_container_width=True):
            if article_url:
                handle_single_article_scraping(article_url)
            else:
                st.warning("⚠️ Please enter an article URL")

def handle_single_article_scraping(article_url):
    """Handle the single article scraping process"""
    with st.spinner("🎯 Initializing advanced scraper with AI-powered optimization..."):
        # Reset metrics for new session
        st.session_state.scraper.request_count = 0
        st.session_state.scraper.successful_requests = 0
        st.session_state.scraper.failed_requests = 0
        st.session_state.scraper.request_history = []
        st.session_state.scraper.start_time = datetime.now()
        
        # Create advanced progress container
        with st.container():
            st.info("🔮 Starting AI-optimized scraping session...")
            
            if st.session_state.debug_mode:
                current_agent = st.session_state.scraper.session.headers['User-Agent']
                st.write(f"🎭 Initial User Agent: {current_agent}")
                st.write(f"🎯 Total User Agents: {len(st.session_state.scraper.user_agents)}")
            
            article_data = st.session_state.scraper.scrape_complete_article(article_url)
        
        if article_data and article_data['sections']:
            display_enhanced_article_results(article_data)
        else:
            display_scraping_failure()

def display_enhanced_article_results(article_data):
    """Display enhanced results for successful scraping"""
    st.success(f"✅ Successfully scraped: {article_data['title']}")
    
    # Enhanced metrics display
    st.markdown("### 📊 Comprehensive Analytics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Sections", f"{article_data['successful_sections']}/{article_data['total_sections']}")
    with col2:
        st.metric("Content Blocks", article_data['total_content_blocks'])
    with col3:
        st.metric("Authors", len(article_data['authors']))
    with col4:
        st.metric("Scraping Time", f"{article_data['scraping_metrics']['total_duration']:.1f}s")
    
    # Performance metrics
    perf_metrics = article_data['performance_metrics']
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Requests", perf_metrics['total_requests'])
    with col2:
        st.metric("Success Rate", f"{perf_metrics['success_rate']:.1f}%")
    with col3:
        st.metric("Recent Success", f"{perf_metrics['recent_success_rate']:.1f}%")
    with col4:
        st.metric("Speed", f"{perf_metrics['requests_per_minute']:.1f}/min")
    
    # Sections overview
    with st.expander("📋 Detailed Sections Overview", expanded=True):
        for section_name, section_content in article_data['sections'].items():
            blocks_count = len(section_content)
            st.write(f"• **{section_name}**: {blocks_count} content blocks")
    
    # Generate enhanced PDF
    with st.spinner("📄 Creating enhanced PDF with advanced formatting..."):
        pdf_path = st.session_state.scraper.create_enhanced_pdf(article_data)
        
        if pdf_path:
            display_pdf_download_options(pdf_path, article_data)

def display_pdf_download_options(pdf_path, article_data):
    """Display enhanced PDF download options"""
    file_size = os.path.getsize(pdf_path) / 1024  # KB
    st.success("🎉 Enhanced PDF generated successfully!")
    
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        with open(pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
        
        st.download_button(
            label="📥 Download Enhanced PDF",
            data=pdf_bytes,
            file_name=os.path.basename(pdf_path),
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
    
    with col2:
        if st.button("⭐ Add to Favorites", use_container_width=True):
            if article_data['url'] not in [fav['url'] for fav in st.session_state.favorite_articles]:
                st.session_state.favorite_articles.append({
                    'url': article_data['url'],
                    'title': article_data['title'],
                    'added_date': datetime.now(),
                    'sections': article_data['successful_sections'],
                    'content_blocks': article_data['total_content_blocks']
                })
                st.success("✅ Added to favorites!")
    
    with col3:
        if st.button("🔄 Scrape Another", use_container_width=True):
            st.rerun()
    
    with col4:
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.show_analytics = True

def display_scraping_failure():
    """Display enhanced failure information"""
    st.error("❌ Failed to scrape article content. Please check the URL and try again.")
    
    st.info("💡 **Troubleshooting Tips:**")
    st.write("• Ensure the URL is correct and accessible")
    st.write("• Try again later if the server is busy")
    st.write("• Check if the article requires login")
    st.write("• Verify your internet connection")
    
    if st.session_state.debug_mode:
        with st.expander("🔍 Debug Information"):
            st.write(f"Total requests made: {st.session_state.scraper.request_count}")
            st.write(f"Successful requests: {st.session_state.scraper.successful_requests}")
            st.write(f"Failed requests: {st.session_state.scraper.failed_requests}")
            st.write(f"Current user agent: {st.session_state.scraper.session.headers['User-Agent'][:100]}...")

def render_multiple_articles_tab(delay, max_retries):
    """Render the multiple articles tab"""
    st.session_state.single_article_mode = False
    
    col1, col2 = st.columns(2)
    
    with col1:
        base_url = st.text_input(
            "Enter Base URL:",
            value="https://emedicine.medscape.com/pulmonology",
            placeholder="https://emedicine.medscape.com/specialty",
            key="multi_base_url"
        )
        
    with col2:
        st.markdown("###")
        if st.button("🔍 Discover Articles", key="discover", use_container_width=True):
            if base_url:
                with st.spinner("Discovering articles with enhanced extraction..."):
                    response = st.session_state.scraper.make_request(base_url)
                    if response:
                        st.session_state.articles_found = st.session_state.scraper.extract_article_links(response.text)
                        st.session_state.select_all = False
                        st.session_state.selected_articles = []
                    else:
                        st.error("❌ Failed to fetch the base URL.")
            else:
                st.warning("⚠️ Please enter a base URL.")
    
    # Display discovered articles
    if st.session_state.get('articles_found', []):
        display_articles_selection_interface()
        
        # Generate PDFs for selected articles
        if st.session_state.get('selected_articles', []):
            display_batch_generation_options(delay)

def display_articles_selection_interface():
    """Display the articles selection interface"""
    st.subheader(f"📋 Discovered Articles ({len(st.session_state.articles_found)})")
    
    # Show warning if many articles are found
    if len(st.session_state.articles_found) > 10:
        st.warning(f"⚠️ Found {len(st.session_state.articles_found)} articles. Generating PDFs for all of them may take a long time.")
    
    # Select all checkbox
    col1, col2 = st.columns([1, 4])
    with col1:
        select_all = st.checkbox("Select All Articles", 
                               value=st.session_state.get('select_all', False),
                               key="select_all_checkbox")
    
    # Update session state when select all changes
    if select_all != st.session_state.get('select_all', False):
        st.session_state.select_all = select_all
        st.rerun()
    
    with col2:
        if st.session_state.select_all:
            st.success(f"✅ All {len(st.session_state.articles_found)} articles selected")
        else:
            st.info("ℹ️ Select individual articles or use 'Select All'")
    
    # Track selected articles
    selected_articles = []
    
    # Create checkboxes for each article
    for i, article in enumerate(st.session_state.articles_found):
        col1, col2 = st.columns([1, 4])
        with col1:
            article_selected = st.checkbox(
                "Select",
                value=st.session_state.select_all,
                key=f"article_{i}"
            )
        with col2:
            st.write(f"**{article['title']}**")
            st.caption(f"Category: {article['category']}")
            st.caption(f"URL: {article['url'][:80]}...")
        
        if article_selected:
            selected_articles.append(article)
    
    # Store selected articles in session state
    st.session_state.selected_articles = selected_articles
    
    # Show selection summary
    st.markdown("---")
    if st.session_state.selected_articles:
        st.success(f"✅ {len(st.session_state.selected_articles)} article(s) selected for PDF generation")
        
        # Warning for large selections
        if len(st.session_state.selected_articles) > 5:
            estimated_time = len(st.session_state.selected_articles) * (3 + 5)  # 5 seconds per article for processing
            minutes = estimated_time // 60
            seconds = estimated_time % 60
            time_msg = f"{minutes} minutes and {seconds} seconds" if minutes > 0 else f"{seconds} seconds"
            st.warning(f"⏰ Generating {len(st.session_state.selected_articles)} PDFs may take approximately {time_msg}")
    else:
        st.info("🔘 No articles selected. Please select articles to generate PDFs.")

def display_batch_generation_options(delay):
    """Display batch generation options"""
    if st.button("🚀 Generate Selected PDFs", 
               key="generate_multiple", 
               type="primary",
               use_container_width=True):
        
        if not st.session_state.selected_articles:
            st.error("❌ No articles selected. Please select articles to generate PDFs.")
            return
        
        st.info(f"🚀 Generating PDFs for {len(st.session_state.selected_articles)} selected articles...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        metrics_text = st.empty()
        
        st.session_state.generated_pdfs = []
        failed_articles = []
        
        for i, article in enumerate(st.session_state.selected_articles):
            status_text.text(f"📖 Processing {i+1}/{len(st.session_state.selected_articles)}: {article['title']}")
            
            # Update metrics
            metrics = st.session_state.scraper.get_performance_metrics()
            metrics_text.text(f"📊 Success Rate: {metrics['success_rate']:.1f}% | Requests: {metrics['total_requests']}")
            
            article_data = st.session_state.scraper.scrape_complete_article(article['url'])
            
            if article_data and article_data['sections']:
                pdf_path = st.session_state.scraper.create_enhanced_pdf(article_data)
                if pdf_path:
                    st.session_state.generated_pdfs.append({
                        'title': article_data['title'],
                        'path': pdf_path,
                        'size': os.path.getsize(pdf_path),
                        'sections': len(article_data['sections']),
                        'content_blocks': article_data['total_content_blocks']
                    })
                else:
                    failed_articles.append(article['title'])
            else:
                failed_articles.append(article['title'])
            
            progress_bar.progress((i + 1) / len(st.session_state.selected_articles))
            
            # Add delay between requests
            if i < len(st.session_state.selected_articles) - 1:
                time.sleep(delay)
        
        status_text.text("✅ Completed!")
        metrics_text.empty()
        
        # Show failure summary
        if failed_articles:
            st.error(f"❌ Failed to generate PDFs for {len(failed_articles)} articles:")
            for failed in failed_articles:
                st.write(f"- {failed}")
        
        # Show success summary
        if st.session_state.generated_pdfs:
            st.success(f"🎉 Successfully generated {len(st.session_state.generated_pdfs)} PDFs!")
            display_batch_download_options()

def display_batch_download_options():
    """Display batch download options for generated PDFs"""
    if not st.session_state.get('generated_pdfs', []):
        return
    
    st.markdown("---")
    st.subheader("📄 Generated PDFs")
    
    total_size = sum(pdf['size'] for pdf in st.session_state.generated_pdfs) / (1024 * 1024)
    total_sections = sum(pdf['sections'] for pdf in st.session_state.generated_pdfs)
    total_blocks = sum(pdf['content_blocks'] for pdf in st.session_state.generated_pdfs)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total PDFs", len(st.session_state.generated_pdfs))
    with col2:
        st.metric("Total Sections", total_sections)
    with col3:
        st.metric("Total Size", f"{total_size:.2f} MB")
    
    # Bulk Download Options
    st.markdown("### 📦 Bulk Download Options")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📦 Download All as ZIP", use_container_width=True):
            with st.spinner("Creating ZIP file..."):
                pdf_paths = [pdf['path'] for pdf in st.session_state.generated_pdfs]
                zip_buffer = create_zip_file(pdf_paths)
                
                st.download_button(
                    label="⬇️ Download ZIP File",
                    data=zip_buffer.getvalue(),
                    file_name=f"medscape_articles_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                    mime="application/zip",
                    key="download_zip",
                    type="primary"
                )
    
    with col2:
        if st.button("📑 Download All as Single PDF", use_container_width=True):
            with st.spinner("Combining PDFs..."):
                pdf_paths = [pdf['path'] for pdf in st.session_state.generated_pdfs]
                combined_pdf_buffer = create_combined_pdf(pdf_paths)
                
                st.download_button(
                    label="⬇️ Download Combined PDF",
                    data=combined_pdf_buffer.getvalue(),
                    file_name=f"combined_articles_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    key="download_combined",
                    type="primary"
                )
    
    st.info("💡 **Bulk Download Tips:**\n"
           "- **ZIP File**: Best for keeping individual articles separate\n"
           "- **Combined PDF**: Best for reading all articles in sequence")
    
    # Individual PDF downloads
    st.markdown("### 📋 Individual PDF Downloads")
    for i, pdf in enumerate(st.session_state.generated_pdfs):
        with st.expander(f"📋 {pdf['title']}", expanded=False):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.write(f"**Title:** {pdf['title']}")
            with col2:
                st.write(f"**Size:** {pdf['size']/1024:.1f} KB")
            with col3:
                st.write(f"**Sections:** {pdf['sections']}")
            with col4:
                st.write(f"**Blocks:** {pdf['content_blocks']}")
            
            # Download button
            with open(pdf['path'], "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
            
            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name=os.path.basename(pdf['path']),
                mime="application/pdf",
                key=f"download_{i}",
                type="primary"
            )

def render_favorites_tab():
    """Render the favorites tab"""
    st.header("⭐ Favorite Articles")
    
    if not st.session_state.favorite_articles:
        st.info("🌟 No favorite articles yet. Add some from the Single Article tab!")
        return
    
    # Display favorites
    for i, fav in enumerate(st.session_state.favorite_articles):
        with st.expander(f"⭐ {fav['title']}", expanded=False):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.write(f"**URL:** {fav['url']}")
                st.write(f"**Added:** {fav['added_date'].strftime('%Y-%m-%d %H:%M')}")
            with col2:
                st.write(f"**Sections:** {fav.get('sections', 'N/A')}")
            with col3:
                st.write(f"**Blocks:** {fav.get('content_blocks', 'N/A')}")
            with col4:
                if st.button("🚀 Scrape", key=f"scrape_fav_{i}"):
                    st.session_state.single_article_url = fav['url']
                    st.rerun()
                
                if st.button("🗑️ Remove", key=f"remove_fav_{i}"):
                    st.session_state.favorite_articles.pop(i)
                    st.rerun()

def render_analytics_tab():
    """Render the analytics tab"""
    st.header("📈 Advanced Analytics")
    
    metrics = st.session_state.scraper.get_performance_metrics()
    
    # Overall metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Requests", metrics['total_requests'])
    with col2:
        st.metric("Success Rate", f"{metrics['success_rate']:.1f}%")
    with col3:
        st.metric("Failed Requests", metrics['failed_requests'])
    with col4:
        st.metric("User Agents", metrics['user_agents_count'])
    
    # Performance charts
    if st.session_state.scraper.request_history:
        # Success over time
        df = pd.DataFrame(st.session_state.scraper.request_history)
        df['success_numeric'] = df['success'].astype(int)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.line(df, x='timestamp', y='success_numeric', 
                          title='Request Success Over Time',
                          labels={'success_numeric': 'Success', 'timestamp': 'Time'})
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Status code distribution
            status_counts = df['status_code'].value_counts()
            fig2 = px.pie(values=status_counts.values, names=status_counts.index,
                         title='Status Code Distribution')
            st.plotly_chart(fig2, use_container_width=True)
    
    # Download history
    if st.session_state.download_history:
        st.subheader("📥 Download History")
        download_df = pd.DataFrame(st.session_state.download_history)
        st.dataframe(download_df[['title', 'file_size_kb', 'sections', 'content_blocks', 'timestamp']].tail(10))
    
    # Export analytics
    if st.button("📊 Export All Analytics Data"):
        analytics_data = {
            'performance_metrics': st.session_state.scraper.get_performance_metrics(),
            'download_history': st.session_state.download_history,
            'request_history': st.session_state.scraper.request_history[-100:],  # Last 100 requests
            'favorite_articles': st.session_state.favorite_articles,
            'export_timestamp': datetime.now().isoformat()
        }
        
        analytics_json = json.dumps(analytics_data, default=str, indent=2)
        st.download_button(
            label="📥 Download Analytics JSON",
            data=analytics_json,
            file_name=f"scraper_analytics_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )

def main():
    st.set_page_config(
        page_title="=Medscape Scraper",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏥 Medscape Scraper")
    st.markdown("---")
    
    # Initialize session state with enhanced features
    if 'scraper' not in st.session_state:
        st.session_state.scraper = AdvancedMedscapeScraper()
    if 'download_history' not in st.session_state:
        st.session_state.download_history = []
    if 'favorite_articles' not in st.session_state:
        st.session_state.favorite_articles = []
    if 'articles_found' not in st.session_state:
        st.session_state.articles_found = []
    if 'generated_pdfs' not in st.session_state:
        st.session_state.generated_pdfs = []
    if 'select_all' not in st.session_state:
        st.session_state.select_all = False
    if 'selected_articles' not in st.session_state:
        st.session_state.selected_articles = []
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    if 'single_article_mode' not in st.session_state:
        st.session_state.single_article_mode = False
    if 'scraping_presets' not in st.session_state:
        st.session_state.scraping_presets = {
            'Quick': {'delay': 1, 'retries': 3},
            'Balanced': {'delay': 3, 'retries': 5},
            'Thorough': {'delay': 5, 'retries': 8}
        }
    
    # Enhanced sidebar
    with st.sidebar:
        st.header("⚙️ Advanced Settings")
        
        # Scraping presets
        preset = st.selectbox(
            "Scraping Preset:",
            ["Custom", "Quick", "Balanced", "Thorough"],
            index=1
        )
        
        if preset != "Custom":
            settings = st.session_state.scraping_presets[preset]
            delay = st.slider("Delay (seconds)", 1, 10, settings['delay'])
            max_retries = st.slider("Max Retries", 1, 10, settings['retries'])
        else:
            delay = st.slider("Delay (seconds)", 1, 10, 3)
            max_retries = st.slider("Max Retries", 1, 10, 5)
        
        st.session_state.scraper.user_agent_rotation_frequency = st.slider(
            "User Agent Rotation:",
            min_value=1,
            max_value=10,
            value=3,
            help="Rotate user agent every N requests"
        )
        
        st.session_state.debug_mode = st.checkbox("Debug Mode", value=False)
        
        st.markdown("---")
        st.header("📊 Real-time Dashboard")
        create_dashboard_metrics(st.session_state.scraper)
        
        st.markdown("---")
        st.header("📈 Download History")
        if st.session_state.download_history:
            recent_downloads = st.session_state.download_history[-5:]  # Last 5 downloads
            for dl in reversed(recent_downloads):
                st.caption(f"📄 {dl['title'][:30]}... ({dl['file_size_kb']:.1f} KB)")
        
        st.markdown("---")
        st.header("🎯 Quick Actions")
        if st.button("🔄 Reset Scraper", use_container_width=True):
            st.session_state.scraper = AdvancedMedscapeScraper()
            st.rerun()
    
    # Main content area with tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 Single Article", "📚 Multiple Articles", "⭐ Favorites", "📈 Analytics"])
    
    with tab1:
        render_single_article_tab()
    
    with tab2:
        render_multiple_articles_tab(delay, max_retries)
    
    with tab3:
        render_favorites_tab()
    
    with tab4:
        render_analytics_tab()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
        <p>Medscape Scraper</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()


