import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import time
import csv
import os
from datetime import datetime
import re
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json

class WebScraper:
    def __init__(self):
        self.visited_urls = set()
        self.scraped_data = []
        self.base_domain = None
        self.driver = None
        
    def setup_driver(self):
        """Setup Selenium WebDriver for JavaScript-heavy sites"""
        try:
            edge_options = Options()
            edge_options.add_argument("--headless=new")
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--disable-dev-shm-usage")
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--disable-extensions")
            
            service = Service(EdgeChromiumDriverManager().install())
            self.driver = webdriver.Edge(service=service, options=edge_options)
            return True
        except Exception as e:
            print(f"Failed to setup driver: {e}")
            return False
    
    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def is_same_domain(self, url):
        """Check if URL belongs to the same domain"""
        if not url or not self.base_domain:
            return False
        
        try:
            parsed_url = urlparse(url)
            if not parsed_url.netloc:
                return False
            return parsed_url.netloc == self.base_domain or parsed_url.netloc.endswith('.' + self.base_domain)
        except Exception:
            return False
    
    def clean_url(self, url):
        """Clean and normalize URL"""
        if not url:
            return None
        
        try:
            parsed = urlparse(url)
            # Remove fragment and some query parameters
            clean_parsed = parsed._replace(fragment='')
            cleaned = urlunparse(clean_parsed)
            return cleaned if cleaned and cleaned != 'None' else None
        except Exception:
            return None
    
    def extract_text_content(self, soup):
        """Extract meaningful text content from BeautifulSoup object"""
        if not soup:
            return ""
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "aside"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        if not text:
            return ""
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text if text else ""
    
    def is_valid_url_path(self, path):
        """Check if a path looks like a valid URL path"""
        if not path or not isinstance(path, str):
            return False
        
        # Remove common invalid patterns
        invalid_patterns = [
            # CSS classes and styling
            r'bg-gradient|from-|to-|border-|rounded-|hover:|md:|lg:|xl:',
            # CSS properties
            r'absolute|relative|inset-|overflow-|opacity-',
            # File extensions we don't want to crawl
            r'\.(css|js|json|xml|txt|pdf|doc|docx|jpg|jpeg|png|gif|svg|ico|woff|woff2|ttf|eot)$',
            # Fragment identifiers and anchors
            r'^#',
            # Data URLs
            r'^data:',
            # Protocol-relative URLs
            r'^//',
            # Query parameters only
            r'^\?',
            # JavaScript code patterns
            r'function\s*\(|var\s+|let\s+|const\s+|return\s+',
            # CSS selectors
            r'^\.|^@|^\s*\{|\}\s*$',
            # Numbers only
            r'^\d+$',
            # Too many spaces (likely CSS)
            r'\s{2,}',
            # Contains parentheses (likely function calls)
            r'\([^)]*\)',
            # Contains semicolons (likely code)
            r';',
            # Contains curly braces (likely CSS/JS)
            r'[{}]',
            # Starts with CSS properties
            r'^(width|height|margin|padding|color|background|font|text|display|position|top|left|right|bottom)',
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                return False
        
        # Must contain at least one valid URL character pattern
        if not re.search(r'^[a-zA-Z0-9][a-zA-Z0-9\-_/\.]*[a-zA-Z0-9]?$', path.strip('/')):
            return False
        
        # Path should not be too long (likely CSS or junk)
        if len(path) > 200:
            return False
        
        # Should not contain too many consecutive special characters
        if re.search(r'[/\-_\.]{3,}', path):
            return False
        
        return True

    def extract_links(self, soup, base_url):
        """Extract all links from the page"""
        if not soup or not base_url:
            return []
        
        links = []
        
        try:
            # Standard <a> tags (most reliable)
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and href.strip():
                    href = href.strip()
                    # Skip obvious non-page links
                    if href.startswith(('#', 'mailto:', 'tel:', 'javascript:', 'data:')):
                        continue
                    
                    try:
                        full_url = urljoin(base_url, href)
                        clean_url = self.clean_url(full_url)
                        
                        if clean_url and self.is_same_domain(clean_url) and clean_url not in self.visited_urls:
                            # Additional validation for the path part
                            parsed = urlparse(clean_url)
                            if self.is_valid_url_path(parsed.path):
                                links.append(clean_url)
                    except Exception:
                        continue
            
            # Look for common navigation patterns only
            nav_selectors = ['nav', '[role="navigation"]', '.nav', '.navigation', '.menu']
            for selector in nav_selectors:
                try:
                    nav_elements = soup.select(selector)
                    for nav in nav_elements:
                        for link in nav.find_all('a', href=True):
                            href = link.get('href')
                            if href and href.strip() and not href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                                try:
                                    full_url = urljoin(base_url, href.strip())
                                    clean_url = self.clean_url(full_url)
                                    
                                    if clean_url and self.is_same_domain(clean_url) and clean_url not in self.visited_urls:
                                        parsed = urlparse(clean_url)
                                        if self.is_valid_url_path(parsed.path):
                                            links.append(clean_url)
                                except Exception:
                                    continue
                except Exception:
                    continue
            
            # Only look for data-href attributes in specific contexts
            for element in soup.find_all(['button', 'div'], attrs={'data-href': True}):
                href = element.get('data-href')
                if href and href.strip() and not href.startswith('#'):
                    href = href.strip()
                    if self.is_valid_url_path(href):
                        try:
                            full_url = urljoin(base_url, href)
                            clean_url = self.clean_url(full_url)
                            
                            if clean_url and self.is_same_domain(clean_url) and clean_url not in self.visited_urls:
                                links.append(clean_url)
                        except Exception:
                            continue
        
        except Exception as e:
            print(f"DEBUG: Error in extract_links: {e}")
            return []
        
        # Remove duplicates and sort
        unique_links = list(set(links))
        
        print(f"DEBUG: Found {len(unique_links)} valid links from {base_url}")
        for i, link in enumerate(unique_links[:5]):  # Print first 5 links for debugging
            print(f"  {i+1}. {link}")
        
        return unique_links
    
    def scrape_page_with_requests(self, url):
        """Scrape a single page using requests"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract page data with null checks
            title = soup.find('title')
            title_text = title.get_text().strip() if title and title.get_text() else "No Title"
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = ""
            if meta_desc and meta_desc.get('content'):
                description = meta_desc.get('content', '').strip()
            
            # Extract headings
            headings = []
            for i in range(1, 7):  # h1 to h6
                for heading in soup.find_all(f'h{i}'):
                    heading_text = heading.get_text() if heading else ""
                    if heading_text:
                        headings.append({
                            'level': f'h{i}',
                            'text': heading_text.strip()
                        })
            
            # Extract main content
            content = self.extract_text_content(soup)
            content = content if content else ""
            
            # Extract links for further crawling
            links = self.extract_links(soup, url)
            
            page_data = {
                'url': url,
                'title': title_text,
                'meta_description': description,
                'headings': headings,
                'content': content[:5000],  # Limit content length
                'word_count': len(content.split()) if content else 0,
                'links_found': len(links) if links else 0,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return page_data, links
            
        except Exception as e:
            return {'url': url, 'error': str(e), 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, []
    
    def scrape_page_with_selenium(self, url):
        """Scrape a single page using Selenium for JavaScript-heavy sites"""
        try:
            if not self.driver:
                if not self.setup_driver():
                    return self.scrape_page_with_requests(url)
            
            self.driver.get(url)
            time.sleep(3)  # Wait for page to load
            
            # Get page source and create soup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract page data with null checks (same as requests method)
            title = soup.find('title')
            title_text = title.get_text().strip() if title and title.get_text() else "No Title"
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = ""
            if meta_desc and meta_desc.get('content'):
                description = meta_desc.get('content', '').strip()
            
            headings = []
            for i in range(1, 7):
                for heading in soup.find_all(f'h{i}'):
                    heading_text = heading.get_text() if heading else ""
                    if heading_text:
                        headings.append({
                            'level': f'h{i}',
                            'text': heading_text.strip()
                        })
            
            content = self.extract_text_content(soup)
            content = content if content else ""
            links = self.extract_links(soup, url)
            
            page_data = {
                'url': url,
                'title': title_text,
                'meta_description': description,
                'headings': headings,
                'content': content[:5000],
                'word_count': len(content.split()) if content else 0,
                'links_found': len(links) if links else 0,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return page_data, links
            
        except Exception as e:
            return {'url': url, 'error': str(e), 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, []
    
    def scrape_website(self, start_url, max_pages=50, use_selenium=False, update_callback=None):
        """Scrape entire website starting from a URL"""
        try:
            # Initialize
            parsed_start = urlparse(start_url)
            self.base_domain = parsed_start.netloc
            self.visited_urls = set()
            self.scraped_data = []
            
            # Queue for URLs to visit
            urls_to_visit = [self.clean_url(start_url)]
            pages_scraped = 0
            
            if update_callback:
                update_callback(f"🚀 Starting to scrape {self.base_domain}")
                update_callback(f"📄 Target: {max_pages} pages maximum")
            
            while urls_to_visit and pages_scraped < max_pages:
                current_url = urls_to_visit.pop(0)
                
                if current_url in self.visited_urls:
                    continue
                
                self.visited_urls.add(current_url)
                
                if update_callback:
                    update_callback(f"🔍 Scraping page {pages_scraped + 1}: {current_url}")
                
                # Choose scraping method
                if use_selenium:
                    page_data, new_links = self.scrape_page_with_selenium(current_url)
                else:
                    page_data, new_links = self.scrape_page_with_requests(current_url)
                
                self.scraped_data.append(page_data)
                pages_scraped += 1
                
                # Add new links to queue
                for link in new_links:
                    if link not in self.visited_urls and link not in urls_to_visit:
                        urls_to_visit.append(link)
                
                # Progress update
                if update_callback:
                    if 'error' in page_data:
                        update_callback(f"❌ Error on {current_url}: {page_data['error']}")
                    else:
                        update_callback(f"✅ Scraped: {page_data['title']} ({page_data['word_count']} words)")
                
                # Small delay to be respectful
                time.sleep(1)
            
            if update_callback:
                update_callback(f"🎉 Scraping completed! Total pages: {pages_scraped}")
            
            return self.scraped_data
            
        except Exception as e:
            if update_callback:
                update_callback(f"❌ Scraping failed: {str(e)}")
            return []
        finally:
            self.close_driver()
    
    def save_to_csv(self, filename=None):
        """Save scraped data to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            domain = self.base_domain.replace('.', '_') if self.base_domain else 'scraped'
            filename = f"results/web_scrape_{domain}_{timestamp}.csv"
        
        # Create results directory if it doesn't exist
        os.makedirs('results', exist_ok=True)
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                if self.scraped_data:
                    fieldnames = self.scraped_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for page_data in self.scraped_data:
                        # Convert complex fields to strings
                        row_data = page_data.copy()
                        if 'headings' in row_data and isinstance(row_data['headings'], list):
                            # Handle both old format (strings) and new format (dicts)
                            heading_strings = []
                            for heading in row_data['headings']:
                                if isinstance(heading, dict):
                                    heading_strings.append(f"{heading.get('level', 'h1').upper()}: {heading.get('text', '')}")
                                else:
                                    heading_strings.append(str(heading))
                            row_data['headings'] = ' | '.join(heading_strings)
                        writer.writerow(row_data)
                    
                    return filename
        except Exception as e:
            print(f"Error saving to CSV: {e}")
            return None
    
    def save_to_json(self, filename=None):
        """Save scraped data to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            domain = self.base_domain.replace('.', '_') if self.base_domain else 'scraped'
            filename = f"results/web_scrape_{domain}_{timestamp}.json"
        
        # Create results directory if it doesn't exist
        os.makedirs('results', exist_ok=True)
        
        try:
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(self.scraped_data, jsonfile, indent=2, ensure_ascii=False)
            return filename
        except Exception as e:
            print(f"Error saving to JSON: {e}")
            return None
    
    def analyze_scraped_data(self, scraped_data, gemini_api_key=None):
        """
        Analyze scraped data and generate useful insights
        """
        if not scraped_data or not gemini_api_key:
            return {"error": "No data to analyze or missing API key"}
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Prepare data for analysis
            successful_pages = [page for page in scraped_data if 'error' not in page]
            
            if not successful_pages:
                return {"error": "No successful pages to analyze"}
            
            # Aggregate content for analysis
            all_titles = [page.get('title', '') for page in successful_pages if page.get('title')]
            all_content = [page.get('content', '')[:1000] for page in successful_pages if page.get('content')]
            all_descriptions = [page.get('meta_description', '') for page in successful_pages if page.get('meta_description')]
            all_headings = []
            
            for page in successful_pages:
                if page.get('headings'):
                    all_headings.extend([h.get('text', '') for h in page['headings']])
            
            # Calculate basic statistics
            total_pages = len(successful_pages)
            total_words = sum([page.get('word_count', 0) for page in successful_pages])
            avg_words = total_words // total_pages if total_pages > 0 else 0
            total_links = sum([page.get('links_found', 0) for page in successful_pages])
            
            # Prepare analysis prompt
            analysis_prompt = f"""
            Analyze the following website data and provide comprehensive insights:
            
            WEBSITE STATISTICS:
            - Total pages analyzed: {total_pages}
            - Total words: {total_words:,}
            - Average words per page: {avg_words:,}
            - Total internal links: {total_links}
            
            PAGE TITLES (First 20):
            {chr(10).join(all_titles[:20])}
            
            META DESCRIPTIONS (First 10):
            {chr(10).join(all_descriptions[:10])}
            
            MAIN HEADINGS (First 30):
            {chr(10).join(all_headings[:30])}
            
            CONTENT SAMPLES (First 5 pages):
            {chr(10).join([f"Page {i+1}: {content[:500]}..." for i, content in enumerate(all_content[:5])])}
            
            Please provide a comprehensive analysis including:
            
            1. **WEBSITE OVERVIEW**
               - What type of website this appears to be
               - Main purpose and target audience
               - Overall content quality assessment
            
            2. **CONTENT THEMES & TOPICS**
               - Primary themes and topics covered
               - Content categories identified
               - Most frequently mentioned subjects
            
            3. **CONTENT STRUCTURE ANALYSIS**
               - Page organization patterns
               - Content depth and quality
               - Navigation and user experience insights
            
            4. **SEO & TECHNICAL INSIGHTS**
               - SEO optimization level
               - Meta description usage and quality
               - Heading structure effectiveness
               - Content length distribution
            
            5. **KEY FINDINGS**
               - Most interesting discoveries
               - Content gaps or opportunities
               - Recommendations for improvement
            
            6. **CONTENT CLASSIFICATION**
               - Categorize pages by type (e.g., product, blog, about, contact)
               - Identify the most common page types
            
            7. **ACTIONABLE INSIGHTS**
               - Business intelligence findings
               - Market positioning insights
               - Competitive analysis points
               - Content strategy recommendations
            
            Format the response in clear sections with bullet points for easy reading.
            Be specific and provide actionable insights based on the actual data.
            """
            
            # Generate AI analysis
            response = model.generate_content(analysis_prompt)
            
            # Structure the analysis response
            insights = {
                "summary_stats": {
                    "total_pages": total_pages,
                    "total_words": total_words,
                    "average_words_per_page": avg_words,
                    "total_internal_links": total_links,
                    "content_samples_analyzed": min(5, len(all_content)),
                    "titles_analyzed": len(all_titles),
                    "descriptions_analyzed": len(all_descriptions),
                    "headings_analyzed": len(all_headings)
                },
                "ai_analysis": response.text,
                "data_breakdown": {
                    "page_types": self._classify_pages(successful_pages),
                    "content_length_distribution": self._analyze_content_lengths(successful_pages),
                    "most_common_words": self._extract_common_words(all_content),
                    "heading_analysis": self._analyze_headings(successful_pages)
                }
            }
            
            return insights
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _classify_pages(self, pages):
        """Classify pages by type based on URL patterns and content"""
        classifications = {
            "homepage": 0,
            "product": 0,
            "blog": 0,
            "about": 0,
            "contact": 0,
            "category": 0,
            "other": 0
        }
        
        for page in pages:
            url = page.get('url', '').lower()
            title = page.get('title', '').lower()
            
            if any(word in url for word in ['product', 'item', 'buy']) or any(word in title for word in ['product', 'buy', 'price']):
                classifications["product"] += 1
            elif any(word in url for word in ['blog', 'news', 'article', 'post']) or any(word in title for word in ['blog', 'news']):
                classifications["blog"] += 1
            elif any(word in url for word in ['about', 'company', 'team']) or any(word in title for word in ['about', 'company']):
                classifications["about"] += 1
            elif any(word in url for word in ['contact', 'support', 'help']) or any(word in title for word in ['contact', 'support']):
                classifications["contact"] += 1
            elif any(word in url for word in ['category', 'section', 'department']) or len(url.split('/')) <= 4:
                classifications["category"] += 1
            elif url.endswith('/') and len(url.split('/')) == 4:
                classifications["homepage"] += 1
            else:
                classifications["other"] += 1
        
        return classifications
    
    def _analyze_content_lengths(self, pages):
        """Analyze distribution of content lengths"""
        lengths = [page.get('word_count', 0) for page in pages]
        if not lengths:
            return {}
        
        lengths.sort()
        return {
            "min_words": min(lengths),
            "max_words": max(lengths),
            "median_words": lengths[len(lengths)//2],
            "short_pages": len([l for l in lengths if l < 200]),
            "medium_pages": len([l for l in lengths if 200 <= l <= 1000]),
            "long_pages": len([l for l in lengths if l > 1000])
        }
    
    def _extract_common_words(self, contents):
        """Extract most common words from content"""
        try:
            from collections import Counter
            import re
            
            # Combine all content
            all_text = ' '.join(contents).lower()
            
            # Remove common stop words and extract meaningful words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 
                         'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
                         'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}
            
            # Extract words (alphanumeric, minimum 3 characters)
            words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text)
            meaningful_words = [word for word in words if word not in stop_words]
            
            # Count and return top 15
            word_counts = Counter(meaningful_words)
            return dict(word_counts.most_common(15))
            
        except Exception:
            return {}
    
    def _analyze_headings(self, pages):
        """Analyze heading structure and patterns"""
        heading_stats = {"h1": 0, "h2": 0, "h3": 0, "h4": 0, "h5": 0, "h6": 0}
        all_headings = []
        
        for page in pages:
            if page.get('headings'):
                for heading in page['headings']:
                    level = heading.get('level', 'h1')
                    heading_stats[level] = heading_stats.get(level, 0) + 1
                    if heading.get('text'):
                        all_headings.append(heading['text'])
        
        return {
            "heading_distribution": heading_stats,
            "total_headings": sum(heading_stats.values()),
            "common_heading_words": self._extract_common_words([' '.join(all_headings)]) if all_headings else {}
        }
    
    def discover_pages_from_sitemap(self, base_url):
        """Try to discover pages from sitemap.xml"""
        discovered_urls = []
        sitemap_urls = [
            urljoin(base_url, '/sitemap.xml'),
            urljoin(base_url, '/sitemap_index.xml'),
            urljoin(base_url, '/robots.txt')  # robots.txt often contains sitemap references
        ]
        
        for sitemap_url in sitemap_urls:
            try:
                response = requests.get(sitemap_url, timeout=10)
                if response.status_code == 200:
                    if 'sitemap.xml' in sitemap_url:
                        # Parse XML sitemap
                        soup = BeautifulSoup(response.content, 'xml')
                        for loc in soup.find_all('loc'):
                            url = loc.get_text().strip()
                            if self.is_same_domain(url):
                                discovered_urls.append(self.clean_url(url))
                    elif 'robots.txt' in sitemap_url:
                        # Look for sitemap references in robots.txt
                        for line in response.text.split('\n'):
                            if line.lower().startswith('sitemap:'):
                                sitemap_ref = line.split(':', 1)[1].strip()
                                # Recursively check referenced sitemaps
                                discovered_urls.extend(self.discover_pages_from_sitemap(sitemap_ref))
            except Exception:
                continue
        
        return list(set(discovered_urls))
    
    def discover_all_pages(self, start_url, use_selenium=False, update_callback=None):
        """Discover all pages on the website without scraping content"""
        try:
            # Initialize
            parsed_start = urlparse(start_url)
            self.base_domain = parsed_start.netloc
            discovered_pages = set()
            
            if update_callback:
                update_callback(f"🔍 Starting page discovery for {self.base_domain}")
            
            # Try sitemap first
            if update_callback:
                update_callback("📋 Checking sitemap.xml for page discovery...")
            
            sitemap_pages = self.discover_pages_from_sitemap(start_url)
            discovered_pages.update(sitemap_pages)
            
            if sitemap_pages:
                if update_callback:
                    update_callback(f"✅ Found {len(sitemap_pages)} pages from sitemap")
            
            # Try common page patterns
            if update_callback:
                update_callback("🎯 Checking common page patterns...")
            
            common_pages = self.discover_common_pages(start_url)
            discovered_pages.update(common_pages)
            
            if common_pages:
                if update_callback:
                    update_callback(f"✅ Found {len(common_pages)} common pages")
            
            # Crawl method for additional discovery (limited and smarter)
            if update_callback:
                update_callback("🕷️ Crawling website for additional pages...")
            
            urls_to_visit = [self.clean_url(start_url)]
            visited_for_discovery = set()
            max_pages_to_discover = 50  # Reasonable limit
            max_crawl_depth = 5  # Only crawl a few levels deep
            
            crawl_count = 0
            while urls_to_visit and len(discovered_pages) < max_pages_to_discover and crawl_count < max_crawl_depth:
                current_url = urls_to_visit.pop(0)
                
                if current_url in visited_for_discovery:
                    continue
                
                visited_for_discovery.add(current_url)
                discovered_pages.add(current_url)
                crawl_count += 1
                
                if update_callback:
                    update_callback(f"🔍 Discovering links from: {current_url}")
                
                try:
                    # Quick request to get links only
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    
                    response = requests.get(current_url, headers=headers, timeout=5)  # Shorter timeout
                    if response.status_code != 200:
                        continue
                        
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract links (now with better filtering)
                    new_links = self.extract_links(soup, current_url)
                    
                    # Filter out obviously bad links
                    valid_new_links = []
                    for link in new_links:
                        if link not in discovered_pages and link not in urls_to_visit:
                            # Additional validation
                            parsed = urlparse(link)
                            if (parsed.path and 
                                len(parsed.path) < 100 and  # Not too long
                                not parsed.path.count('/') > 5 and  # Not too deep
                                self.is_valid_url_path(parsed.path)):
                                valid_new_links.append(link)
                    
                    # Only add a limited number of new URLs to prevent explosion
                    for link in valid_new_links[:10]:  # Max 10 new links per page
                        urls_to_visit.append(link)
                        discovered_pages.add(link)
                    
                    if update_callback:
                        update_callback(f"📄 Found {len(valid_new_links)} valid links. Total discovered: {len(discovered_pages)}")
                    
                    time.sleep(0.3)  # Small delay
                    
                except Exception as e:
                    if update_callback:
                        update_callback(f"⚠️ Error discovering from {current_url}: {str(e)}")
                    continue
            
            # Final filtering to remove any remaining junk URLs
            final_pages = set()
            for page in discovered_pages:
                try:
                    parsed = urlparse(page)
                    if (parsed.scheme in ['http', 'https'] and 
                        parsed.netloc == self.base_domain and
                        self.is_valid_url_path(parsed.path) and
                        len(page) < 200):  # Reasonable URL length
                        final_pages.add(page)
                except Exception:
                    continue
            
            if update_callback:
                update_callback(f"🎉 Page discovery completed! Found {len(final_pages)} valid pages")
            
            # Debug output
            print(f"DEBUG: Final discovered pages count: {len(final_pages)}")
            sorted_pages = sorted(list(final_pages))
            for i, page in enumerate(sorted_pages[:10]):
                print(f"  {i+1}. {page}")
            
            return sorted_pages
            
        except Exception as e:
            if update_callback:
                update_callback(f"❌ Page discovery failed: {str(e)}")
            return []
        finally:
            self.close_driver()
    
    def scrape_single_page(self, url, use_selenium=False):
        """Scrape a single specific page"""
        try:
            # Ensure URL is valid and properly formatted
            if not url:
                raise ValueError("URL cannot be empty")
            
            # Add https:// if not present
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Initialize base domain for this single page scrape
            parsed_url = urlparse(url)
            if not parsed_url.netloc:
                raise ValueError(f"Invalid URL format: {url}")
            
            self.base_domain = parsed_url.netloc
            
            # Reset visited URLs for single page scrape
            self.visited_urls = set()
            
            if use_selenium:
                page_data, _ = self.scrape_page_with_selenium(url)
            else:
                page_data, _ = self.scrape_page_with_requests(url)
            
            return page_data
            
        except Exception as e:
            error_msg = str(e) if e else "Unknown error occurred"
            return {'url': url or 'Unknown URL', 'error': error_msg, 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    def discover_common_pages(self, base_url):
        """Try common page patterns for portfolio/business websites"""
        common_patterns = [
            # Portfolio specific
            '/about', '/about.html', '/about-me', '/about-us',
            '/contact', '/contact.html', '/contact-me',
            '/portfolio', '/projects', '/work', '/gallery',
            '/resume', '/cv', '/experience',
            '/blog', '/blog.html', '/news', '/articles',
            '/services', '/skills', '/expertise',
            '/testimonials', '/reviews',
            
            # Business specific
            '/home', '/index.html',
            '/products', '/solutions',
            '/team', '/staff', '/people',
            '/careers', '/jobs',
            '/privacy', '/terms', '/legal',
            '/sitemap', '/sitemap.html',
            
            # Social/External links (still same domain)
            '/social', '/links',
            
            # Technical pages
            '/404', '/404.html',
            '/search', '/site-search'
        ]
        
        discovered_urls = []
        
        for pattern in common_patterns:
            test_url = urljoin(base_url, pattern)
            clean_url = self.clean_url(test_url)
            
            if self.is_same_domain(clean_url):
                try:
                    # Quick HEAD request to check if page exists
                    response = requests.head(clean_url, timeout=5, allow_redirects=True)
                    if response.status_code == 200:
                        discovered_urls.append(clean_url)
                        print(f"DEBUG: Found common page: {clean_url}")
                except:
                    # If HEAD fails, try GET with short timeout
                    try:
                        response = requests.get(clean_url, timeout=3, allow_redirects=True)
                        if response.status_code == 200:
                            discovered_urls.append(clean_url)
                            print(f"DEBUG: Found common page (via GET): {clean_url}")
                    except:
                        continue
        
        return discovered_urls 