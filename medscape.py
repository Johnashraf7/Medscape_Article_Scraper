import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import json
from urllib.parse import urljoin
import re
import os
from datetime import datetime
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

class ComprehensiveMedscapeScraper:
    def __init__(self):
        self.session = requests.Session()
        self.user_agents = [
            # Chrome - Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            
            # Chrome - Mac
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # Chrome - Linux
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            
            # Firefox - Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0',
            
            # Firefox - Mac
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
            
            # Firefox - Linux
            'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
            
            # Edge - Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/118.0.0.0 Safari/537.36',
            
            # Safari - Mac
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            
            # Mobile - iOS
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            
            # Mobile - Android
            'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.210 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.210 Mobile Safari/537.36',
            
            # Additional browsers
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Whale/3.23.214.10 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0',
        ]
        self.setup_session()
        self.base_url = "https://emedicine.medscape.com"
        self.setup_pdf_styles()
        self.content_hash_tracker = set()
        self.request_count = 0
        self.user_agent_rotation_frequency = 3  # Rotate every 3 requests
    
    def setup_session(self):
        """Setup session with proper headers to avoid blocking"""
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
    
    def rotate_user_agent(self):
        """Rotate user agent to avoid detection"""
        self.request_count += 1
        
        # Rotate user agent based on frequency
        if self.request_count % self.user_agent_rotation_frequency == 0:
            new_agent = random.choice(self.user_agents)
            self.session.headers.update({
                'User-Agent': new_agent
            })
            if st.session_state.get('debug_mode', False):
                st.write(f"🔄 Rotated User Agent: {new_agent[:50]}...")
    
    def get_random_delay(self, base_delay=3):
        """Get random delay with jitter"""
        return base_delay + random.uniform(0.5, 2.0)
    
    def make_request(self, url, max_retries=10, delay=3):
        """Make request with retry logic and proper delays"""
        for attempt in range(max_retries):
            try:
                self.rotate_user_agent()
                current_delay = self.get_random_delay(delay)
                time.sleep(current_delay)
                
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 403:
                    st.warning(f"🔒 Got 403, retrying... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(8)  # Longer wait for 403
                    continue
                elif response.status_code == 429:
                    st.warning(f"⏳ Rate limited, waiting... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(15)  # Longer wait for rate limiting
                    continue
                elif response.status_code == 503:
                    st.warning(f"🔧 Service unavailable, retrying... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(10)
                    continue
                elif response.status_code != 200:
                    st.warning(f"⚠️ Got status {response.status_code}, retrying... (attempt {attempt + 1}/{max_retries})")
                    continue
                
                response.raise_for_status()
                
                # Check for blocking patterns in content
                if self.is_blocked(response.text):
                    st.warning(f"🚫 Blocking detected, rotating... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(10)
                    continue
                    
                return response
                
            except requests.exceptions.Timeout:
                st.warning(f"⏰ Timeout, retrying... (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))
            except requests.exceptions.RequestException as e:
                st.warning(f"❌ Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))
        
        st.error(f"💥 Failed to fetch {url} after {max_retries} attempts")
        return None

    def is_blocked(self, html_content):
        """Check if response indicates blocking"""
        blocked_indicators = [
            "access denied", "cloudflare", "captcha", "bot protection",
            "security check", "distil", "incapsula", "blocked"
        ]
        
        content_lower = html_content.lower()
        return any(indicator in content_lower for indicator in blocked_indicators)

    def setup_pdf_styles(self):
        """Setup PDF styles"""
        self.styles = getSampleStyleSheet()
        
        self.article_title_style = ParagraphStyle(
            name='ArticleTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        self.section_title_style = ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=6,
            textColor=colors.darkblue
        )
        
        self.subsection_style = ParagraphStyle(
            name='Subsection',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=6,
            textColor=colors.darkblue
        )
        
        self.normal_style = ParagraphStyle(
            name='NormalText',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            leading=14
        )
        
        self.metadata_style = ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.gray,
            spaceAfter=3
        )

    def extract_article_links(self, html_content):
        """Extract all article URLs"""
        soup = BeautifulSoup(html_content, 'html.parser')
        article_links = []
        
        st.info("🔍 Extracting articles from categorized sections...")
        
        # Extract from topic sections only
        topic_sections = soup.find_all('div', class_='topic-section')
        
        for section in topic_sections:
            category = section.find('div', class_='topic-head')
            category_name = category.get_text(strip=True) if category else 'Unknown'
            
            links = section.find_all('a', href=True)
            for link in links:
                href = link['href']
                if re.search(r'/article/\d+-overview', href):
                    full_url = urljoin(self.base_url, href)
                    article_links.append({
                        'url': full_url,
                        'title': link.get_text(strip=True),
                        'category': category_name
                    })
        
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
        """Get URLs for all sections of an article"""
        response = self.make_request(overview_url)
        if not response:
            return {'Overview': overview_url}
            
        soup = BeautifulSoup(response.content, 'html.parser')
        sections = {}
        
        # Standard medical section order
        standard_order = [
            'Overview', 'Background', 'Pathophysiology', 'Etiology', 'Epidemiology', 'Prognosis',
            'Presentation', 'History', 'Physical Examination', 
            'DDx', 'Differential Diagnoses',
            'Workup', 'Approach Considerations', 'Laboratory Studies', 'Imaging Studies', 
            'Treatment', 'Medical Care', 'Surgical Care', 'Prevention',
            'Medication', 'Medication Summary',
            'Guidelines', 'Guidelines Summary'
        ]
        
        # Find navigation
        nav_selectors = ['div.sections-nav', 'div#dd_nav', 'div.sections-nav ul']
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
                if any(keyword in section_name for keyword in ['Show All', 'Media Gallery', 'References', 'Share', 'Print', 'Feedback']):
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
        
        # Order sections
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
        """Scrape content from a specific section"""
        response = self.make_request(section_url)
        if not response:
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        content = []
        
        # Find content area
        content_selectors = [
            'div.drugdbsectioncontent',
            'div.article-content',
            'div.refsection_content',
            'div.drugdbmain'
        ]
        
        content_area = None
        for selector in content_selectors:
            content_area = soup.select_one(selector)
            if content_area:
                break
        
        if not content_area:
            return content
        
        # Extract content
        elements = content_area.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'p', 'ul', 'ol'])
        
        current_section = {'heading': section_name, 'content': []}
        seen_hashes = set()
        
        for element in elements:
            # Skip navigation elements
            if element.get('class'):
                class_names = ' '.join(element.get('class', []))
                if any(nav_class in class_names for nav_class in ['action-items', 'back_next_btn', 'emed-logo']):
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
                if text and len(text) > 20:
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
                    if item_text and len(item_text) > 5:
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
        
        if current_section['content']:
            content.append(current_section)
        
        return content

    def scrape_complete_article(self, article_url):
        """Scrape complete article content from all sections"""
        st.info(f"📖 Scraping complete article: {article_url}")
        
        try:
            sections = self.get_all_article_sections(article_url)
            st.info(f"📑 Found {len(sections)} sections")
            
            complete_content = {}
            successful_sections = 0
            
            # Create progress bar for single article mode
            if st.session_state.get('single_article_mode', False):
                progress_bar = st.progress(0)
                status_text = st.empty()
                total_sections = len(sections)
            
            for i, (section_name, section_url) in enumerate(sections.items()):
                if st.session_state.get('single_article_mode', False):
                    status_text.text(f"🔍 Scraping section {i+1}/{total_sections}: {section_name}")
                    progress_bar.progress((i + 1) / total_sections)
                else:
                    st.info(f"🔍 Scraping section: {section_name}")
                
                section_content = self.scrape_section_content(section_url, section_name)
                
                if section_content:
                    complete_content[section_name] = section_content
                    successful_sections += 1
                    if st.session_state.get('single_article_mode', False):
                        st.success(f"✅ {section_name}: {len(section_content)} content blocks")
                else:
                    st.warning(f"⚠️ {section_name}: No content extracted")
                
                time.sleep(self.get_random_delay(1))
            
            # Clear progress indicators
            if st.session_state.get('single_article_mode', False):
                status_text.empty()
                progress_bar.empty()
            
            # Get article info
            response = self.make_request(article_url)
            if not response:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title = self._extract_title(soup)
            authors = self._extract_authors(soup)
            updated_date = self._extract_updated_date(soup)
            
            total_content_blocks = sum(len(content) for content in complete_content.values())
            
            return {
                'url': article_url,
                'title': title,
                'authors': authors,
                'last_updated': updated_date,
                'sections': complete_content,
                'total_sections': len(complete_content),
                'total_content_blocks': total_content_blocks,
                'successful_sections': successful_sections
            }
            
        except Exception as e:
            st.error(f"💥 Error scraping complete article: {e}")
            return None

    def _extract_title(self, soup):
        title = soup.find('h1')
        return title.get_text(strip=True) if title else "Title not found"

    def _extract_authors(self, soup):
        authors = []
        author_section = soup.find('div', class_='condition-title-info')
        if author_section:
            author_li = author_section.find('li')
            if author_li:
                author_text = author_li.get_text(strip=True)
                if 'Author:' in author_text:
                    author_part = author_text.split('Author:')[-1].split('more...')[0]
                    authors = [auth.strip() for auth in author_part.split(';') if auth.strip()]
        return authors if authors else ["Authors information not available"]

    def _extract_updated_date(self, soup):
        updated_div = soup.find('div', class_='clinref_updated')
        if updated_div:
            date_text = updated_div.get_text(strip=True)
            return date_text.replace('Updated:', '').strip()
        return "Date not available"

    def create_comprehensive_pdf(self, article_data, output_dir="comprehensive_pdfs"):
        """Create PDF with content from all sections"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        safe_title = "".join(c for c in article_data['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title[:50]}.pdf"
        filepath = os.path.join(output_dir, filename)
        
        try:
            doc = SimpleDocTemplate(
                filepath,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            story = []
            
            # Title and metadata
            story.append(Paragraph(article_data['title'], self.article_title_style))
            story.append(Spacer(1, 12))
            
            story.append(Paragraph(f"<b>Source:</b> {article_data['url']}", self.metadata_style))
            story.append(Paragraph(f"<b>Authors:</b> {', '.join(article_data['authors'])}", self.metadata_style))
            story.append(Paragraph(f"<b>Last Updated:</b> {article_data['last_updated']}", self.metadata_style))
            story.append(Paragraph(f"<b>Sections:</b> {article_data['successful_sections']}/{article_data['total_sections']}", self.metadata_style))
            story.append(Paragraph(f"<b>Content Blocks:</b> {article_data['total_content_blocks']}", self.metadata_style))
            story.append(Spacer(1, 20))
            
            # Table of Contents
            if article_data['sections']:
                story.append(Paragraph("Table of Contents", self.section_title_style))
                story.append(Spacer(1, 10))
                
                for section_name in article_data['sections'].keys():
                    content_blocks = len(article_data['sections'][section_name])
                    story.append(Paragraph(f"• {section_name} ({content_blocks} blocks)", self.normal_style))
                    story.append(Spacer(1, 3))
            
            story.append(Spacer(1, 20))
            story.append(PageBreak())
            
            # Content
            for section_name, section_content in article_data['sections'].items():
                if section_content:
                    story.append(Paragraph(section_name, self.section_title_style))
                    story.append(Spacer(1, 15))
                    
                    for content_block in section_content:
                        if content_block['heading'] and content_block['heading'] != section_name:
                            story.append(Paragraph(content_block['heading'], self.subsection_style))
                            story.append(Spacer(1, 10))
                        
                        for item in content_block['content']:
                            if item['type'] == 'paragraph':
                                paragraphs = self._split_paragraph(item['text'])
                                for para in paragraphs:
                                    story.append(Paragraph(para, self.normal_style))
                                    story.append(Spacer(1, 6))
                            
                            elif item['type'] == 'list':
                                for list_item in item['items']:
                                    story.append(Paragraph(f"• {list_item}", self.normal_style))
                                    story.append(Spacer(1, 3))
                                story.append(Spacer(1, 6))
                    
                    story.append(Spacer(1, 20))
                    
                    if section_name in ['Overview', 'Presentation', 'Treatment', 'Medication']:
                        story.append(PageBreak())
            
            doc.build(story)
            file_size = os.path.getsize(filepath)
            st.success(f"📄 PDF created: {os.path.basename(filepath)} ({file_size/1024:.1f} KB)")
            return filepath
            
        except Exception as e:
            st.error(f"💥 PDF creation failed: {e}")
            return None

    def _split_paragraph(self, text, max_chars=500):
        """Split long paragraphs"""
        if len(text) <= max_chars:
            return [text]
        
        sentences = text.split('. ')
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
        
        return paragraphs

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
            # Add a blank page with the article title as a separator
            # (This is a simplified approach - for better results you might want to create proper cover pages)
            merger.append(pdf_path)
        except Exception as e:
            st.warning(f"⚠️ Could not merge {os.path.basename(pdf_path)}: {e}")
    
    # Save to bytes buffer
    combined_buffer = BytesIO()
    merger.write(combined_buffer)
    merger.close()
    combined_buffer.seek(0)
    
    return combined_buffer

def main():
    st.set_page_config(
        page_title="Medscape Article Scraper",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 Medscape Article Scraper")
    st.markdown("---")
    
    # Initialize session state
    if 'scraper' not in st.session_state:
        st.session_state.scraper = ComprehensiveMedscapeScraper()
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
    
    # Settings sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        st.session_state.debug_mode = st.checkbox("Debug Mode", value=False)
        
        # Single Article Mode specific settings
        st.markdown("---")
        st.markdown("### 🔧 Single Article Settings")
        single_article_delay = st.slider(
            "Delay between section requests (seconds):",
            min_value=1,
            max_value=10,
            value=3,
            key="single_article_delay"
        )
        
        st.session_state.scraper.user_agent_rotation_frequency = st.slider(
            "User Agent Rotation Frequency:",
            min_value=1,
            max_value=10,
            value=3,
            help="Rotate user agent every N requests"
        )
        
        st.markdown("---")
        st.markdown("### 📊 Statistics")
        if st.session_state.scraper:
            st.write(f"Requests made: {st.session_state.scraper.request_count}")
            st.write(f"User agents: {len(st.session_state.scraper.user_agents)}")
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.info(
            "This tool helps scrape medical articles from Medscape. "
            "Please use responsibly and respect rate limits."
        )
    
    # Mode selection
    mode = st.radio(
        "Select Mode:",
        ["Single Article", "Multiple Articles from Base URL"],
        horizontal=True
    )
    
    if mode == "Single Article":
        st.session_state.single_article_mode = True
        st.header("Single Article Mode")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            article_url = st.text_input(
                "Enter Article URL:",
                placeholder="https://emedicine.medscape.com/article/..."
            )
        
        with col2:
            st.markdown("###")
            generate_btn = st.button("🚀 Generate PDF", key="single_article", type="primary", use_container_width=True)
        
        if generate_btn:
            if article_url:
                # Validate URL format
                if not re.match(r'https?://emedicine\.medscape\.com/article/\d+', article_url):
                    st.warning("⚠️ Please enter a valid Medscape article URL")
                    st.info("💡 Example: https://emedicine.medscape.com/article/1234567-overview")
                else:
                    with st.spinner("🔄 Initializing scraper with enhanced user agent rotation..."):
                        # Reset request count for new session
                        st.session_state.scraper.request_count = 0
                        
                        # Create progress container
                        progress_container = st.container()
                        
                        with progress_container:
                            st.info("🔍 Starting article scraping with enhanced user agent rotation...")
                            
                            # Show user agent info
                            if st.session_state.debug_mode:
                                current_agent = st.session_state.scraper.session.headers['User-Agent']
                                st.write(f"🎭 Initial User Agent: {current_agent[:60]}...")
                            
                            article_data = st.session_state.scraper.scrape_complete_article(article_url)
                        
                        if article_data and article_data['sections']:
                            st.success(f"✅ Successfully scraped article: {article_data['title']}")
                            
                            # Display comprehensive article info
                            st.markdown("### 📊 Article Statistics")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Sections Scraped", f"{article_data['successful_sections']}/{article_data['total_sections']}")
                            with col2:
                                st.metric("Content Blocks", article_data['total_content_blocks'])
                            with col3:
                                st.metric("Authors", len(article_data['authors']))
                            with col4:
                                st.metric("Requests Made", st.session_state.scraper.request_count)
                            
                            # Show sections overview
                            with st.expander("📋 Sections Overview", expanded=True):
                                for section_name, section_content in article_data['sections'].items():
                                    blocks_count = len(section_content)
                                    st.write(f"• **{section_name}**: {blocks_count} content blocks")
                            
                            # Generate PDF
                            with st.spinner("📄 Generating PDF document..."):
                                pdf_path = st.session_state.scraper.create_comprehensive_pdf(article_data)
                                
                                if pdf_path:
                                    st.success("✅ PDF generated successfully!")
                                    
                                    # File info
                                    file_size = os.path.getsize(pdf_path) / 1024  # KB
                                    st.info(f"📁 File: `{os.path.basename(pdf_path)}` ({file_size:.1f} KB)")
                                    
                                    # Download button
                                    with open(pdf_path, "rb") as pdf_file:
                                        pdf_bytes = pdf_file.read()
                                    
                                    col1, col2, col3 = st.columns([2, 1, 1])
                                    with col1:
                                        st.download_button(
                                            label="📥 Download PDF",
                                            data=pdf_bytes,
                                            file_name=os.path.basename(pdf_path),
                                            mime="application/pdf",
                                            type="primary",
                                            use_container_width=True
                                        )
                                    
                                    with col2:
                                        # Add to batch option
                                        if st.button("➕ Add to Batch", use_container_width=True):
                                            if pdf_path not in [pdf['path'] for pdf in st.session_state.generated_pdfs]:
                                                st.session_state.generated_pdfs.append({
                                                    'title': article_data['title'],
                                                    'path': pdf_path,
                                                    'size': os.path.getsize(pdf_path),
                                                    'sections': len(article_data['sections']),
                                                    'content_blocks': article_data['total_content_blocks']
                                                })
                                                st.success("✅ Added to batch download list!")
                                            else:
                                                st.info("ℹ️ Article already in batch list")
                                    
                                    with col3:
                                        if st.button("🔄 Scrape Another", use_container_width=True):
                                            st.rerun()
                                    
                                    # Debug info
                                    if st.session_state.debug_mode:
                                        with st.expander("🔍 Debug Information"):
                                            st.write(f"Total requests made: {st.session_state.scraper.request_count}")
                                            st.write(f"User agents used: {st.session_state.scraper.request_count // st.session_state.scraper.user_agent_rotation_frequency}")
                                            st.write(f"Current user agent: {st.session_state.scraper.session.headers['User-Agent']}")
                        else:
                            st.error("❌ Failed to scrape article content. Please check the URL and try again.")
                            st.info("💡 Tips:")
                            st.write("- Ensure the URL is correct and accessible")
                            st.write("- Try again later if the server is busy")
                            st.write("- Check if the article requires login")
                            
                            if st.session_state.debug_mode:
                                st.write(f"Debug: Request count: {st.session_state.scraper.request_count}")
            else:
                st.warning("⚠️ Please enter an article URL.")
    
    else:  # Multiple Articles mode
        st.session_state.single_article_mode = False
        st.header("Multiple Articles Mode")
        
        col1, col2 = st.columns(2)
        
        with col1:
            base_url = st.text_input(
                "Enter Base URL:",
                value="https://emedicine.medscape.com/pulmonology",
                placeholder="https://emedicine.medscape.com/specialty"
            )
            
            delay = st.slider(
                "Delay between requests (seconds):",
                min_value=1,
                max_value=10,
                value=3,
                key="multi_article_delay"
            )
        
        with col2:
            if st.button("🔍 Discover Articles", key="discover", use_container_width=True):
                if base_url:
                    with st.spinner("Discovering articles..."):
                        response = st.session_state.scraper.make_request(base_url)
                        if response:
                            st.session_state.articles_found = st.session_state.scraper.extract_article_links(response.text)
                            # Reset selection states when new articles are discovered
                            st.session_state.select_all = False
                            st.session_state.selected_articles = []
                        else:
                            st.error("❌ Failed to fetch the base URL.")
                else:
                    st.warning("⚠️ Please enter a base URL.")
        
        # Display discovered articles
        if st.session_state.articles_found:
            st.subheader(f"📋 Discovered Articles ({len(st.session_state.articles_found)})")
            
            # Show warning if many articles are found
            if len(st.session_state.articles_found) > 10:
                st.warning(f"⚠️ Found {len(st.session_state.articles_found)} articles. Generating PDFs for all of them may take a long time. Consider selecting specific articles.")
            
            # Select all checkbox
            col1, col2 = st.columns([1, 4])
            with col1:
                select_all = st.checkbox("Select All Articles", 
                                       value=st.session_state.select_all,
                                       key="select_all_checkbox")
            
            # Update session state when select all changes
            if select_all != st.session_state.select_all:
                st.session_state.select_all = select_all
                # Force rerun to update individual checkboxes
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
                    # Use the select_all state to determine checkbox state
                    article_selected = st.checkbox(
                        "Select",
                        value=st.session_state.select_all,
                        key=f"article_{i}_{st.session_state.select_all}"  # Include select_all in key to force update
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
                    estimated_time = len(st.session_state.selected_articles) * (delay + 5)  # 5 seconds per article for processing
                    minutes = estimated_time // 60
                    seconds = estimated_time % 60
                    time_msg = f"{minutes} minutes and {seconds} seconds" if minutes > 0 else f"{seconds} seconds"
                    st.warning(f"⏰ Generating {len(st.session_state.selected_articles)} PDFs may take approximately {time_msg}")
                
                # Generate PDFs button - ALWAYS show when there are selected articles
                if st.button("🚀 Generate Selected PDFs", 
                           key="generate_multiple", 
                           type="primary",
                           use_container_width=True):
                    
                    # Double-check we have selected articles
                    if not st.session_state.selected_articles:
                        st.error("❌ No articles selected. Please select articles to generate PDFs.")
                        return
                    
                    st.info(f"🚀 Generating PDFs for {len(st.session_state.selected_articles)} selected articles...")
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    st.session_state.generated_pdfs = []
                    failed_articles = []
                    
                    for i, article in enumerate(st.session_state.selected_articles):
                        status_text.text(f"📖 Processing {i+1}/{len(st.session_state.selected_articles)}: {article['title']}")
                        
                        article_data = st.session_state.scraper.scrape_complete_article(article['url'])
                        
                        if article_data and article_data['sections']:
                            pdf_path = st.session_state.scraper.create_comprehensive_pdf(article_data)
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
                    
                    # Show failure summary
                    if failed_articles:
                        st.error(f"❌ Failed to generate PDFs for {len(failed_articles)} articles:")
                        for failed in failed_articles:
                            st.write(f"- {failed}")
            else:
                st.info("🔘 No articles selected. Please select articles to generate PDFs.")
        
        # Display generated PDFs and bulk download options
        if st.session_state.generated_pdfs:
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
                # Download as ZIP
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
                # Download as Combined PDF
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
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
        <p>Medscape Article Scraper | Enhanced User Agent Rotation | Use Responsibly</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
