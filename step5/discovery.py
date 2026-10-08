import os
import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

class DocumentDiscoverer:
    def __init__(self, target_url: str, save_dir: str):
        self.target_url = target_url
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.doc_patterns = {
            'Privacy_Policy': r'(?i)privacy\s*(policy|notice)',
            'Cookie_Policy': r'(?i)cookie\s*(policy|notice)',
            'DPA': r'(?i)data\s*processing\s*(addendum|agreement)|dpa',
            'Subprocessors': r'(?i)sub(-?)processor'
        }

    def discover_and_download(self) -> dict:
        """Crawls the target URL for policy links and downloads them."""
        print(f"Discovering documents at {self.target_url}...")
        try:
            resp = self.session.get(self.target_url, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"Failed to fetch {self.target_url}: {e}")
            return {}

        soup = BeautifulSoup(resp.text, 'html.parser')
        links = soup.find_all('a', href=True)
        
        found_docs = {}
        for link in links:
            text = link.get_text(strip=True)
            href = link['href']
            
            for doc_type, pattern in self.doc_patterns.items():
                if doc_type not in found_docs and re.search(pattern, text):
                    abs_url = urljoin(self.target_url, href)
                    # Don't download external links unless they look like docs (pdf)
                    if urlparse(abs_url).netloc != urlparse(self.target_url).netloc and not abs_url.endswith('.pdf'):
                        continue
                        
                    print(f"Found {doc_type} link: {abs_url}")
                    found_docs[doc_type] = abs_url

        downloaded_files = {}
        for doc_type, doc_url in found_docs.items():
            try:
                doc_resp = self.session.get(doc_url, timeout=10)
                doc_resp.raise_for_status()
                
                # Determine extension
                ext = ".pdf" if doc_url.endswith('.pdf') or 'application/pdf' in doc_resp.headers.get('Content-Type', '') else ".html"
                filename = f"{doc_type}{ext}"
                filepath = os.path.join(self.save_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(doc_resp.content)
                    
                downloaded_files[doc_type] = filepath
                print(f"Downloaded {filename}")
            except Exception as e:
                print(f"Failed to download {doc_url}: {e}")
                
        return downloaded_files
