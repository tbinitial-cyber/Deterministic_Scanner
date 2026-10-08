import fitz  # PyMuPDF
from bs4 import BeautifulSoup
import re
from .schemas import ExtractedFact

class DeterministicExtractor:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = filepath.split('/')[-1].split('\\')[-1]
        self.text_blocks = self._extract_blocks()

    def _extract_blocks(self) -> list[tuple[str, str]]:
        """Extracts blocks maintaining structural integrity for HTML (grabs full lists)."""
        blocks = []
        try:
            if self.filepath.endswith('.pdf'):
                doc = fitz.open(self.filepath)
                for page in doc:
                    text = page.get_text("blocks")
                    for b in text:
                        if b[4].strip():
                            tag = "h" if len(b[4].strip()) < 100 and '\n' not in b[4].strip() else "p"
                            blocks.append((tag, b[4].strip()))
            else:
                with open(self.filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    for header in headers:
                        header_text = header.get_text(strip=True)
                        if not header_text: continue
                        
                        content_blocks = []
                        sib = header.find_next_sibling()
                        while sib and sib.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                            if sib.name in ['p', 'ul', 'ol', 'div']:
                                if sib.name in ['ul', 'ol']:
                                    items = [f"- {li.get_text(strip=True)}" for li in sib.find_all('li')]
                                    if items:
                                        content_blocks.append("\n".join(items))
                                else:
                                    text = sib.get_text(separator=' ', strip=True)
                                    if text: content_blocks.append(text)
                            sib = sib.find_next_sibling()
                            
                        if content_blocks:
                            blocks.append(("h", header_text))
                            blocks.append(("content", "\n\n".join(content_blocks)))
                            
        except Exception as e:
            print(f"Extraction error on {self.filepath}: {e}")
        return blocks

    def extract_fact(self, pattern: str, fact_name: str) -> ExtractedFact:
        """Matches a header pattern and returns its paired content block."""
        for i, (tag, text) in enumerate(self.text_blocks):
            if tag == "h" and re.search(pattern, text):
                if i + 1 < len(self.text_blocks) and self.text_blocks[i+1][0] == "content":
                    snippet = self.text_blocks[i+1][1]
                    # Cap at 3000 chars but preserve structure
                    if len(snippet) > 3000: snippet = snippet[:3000] + "... [truncated]"
                    
                    return ExtractedFact(
                        value="Found explicitly listed details",
                        source_document=self.filename,
                        section_hint=text,
                        snippet=snippet,
                        status="extracted",
                        confidence="high"
                    )
                    
        return ExtractedFact(
            value="Not explicitly found",
            source_document=self.filename,
            section_hint=pattern,
            snippet="",
            status="not_found",
            confidence="high"
        )
