"""
SOW Document Processor
Handles extraction and processing of requirements from Statement of Work (SOW) documents.

Features:
- PDF document processing with parallel page extraction
- Section identification and parsing
- Requirement extraction and classification
- Content cleaning and normalization
- Requirement categorization
- Deduplication of requirements
"""

import re
import pandas as pd
import spacy
import pdfplumber
from pathlib import Path
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess
    subprocess.check_call(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")


class SOWProcessor:
    """Processes Statement of Work documents to extract requirements."""

    def __init__(self):
        """Initialize the SOW processor."""
        self.categories = {
            'Technical': r'\b(?:technical|system|software|hardware|network|infrastructure|security)\b',
            'Process': r'\b(?:process|procedure|workflow|method|approach|implementation)\b',
            'Service': r'\b(?:service|support|maintenance|operation|performance)\b',
            'Documentation': r'\b(?:document|report|plan|deliverable|submission)\b',
            'Compliance': r'\b(?:comply|compliance|requirement|standard|regulation|policy)\b',
            'Training': r'\b(?:training|instruction|education|knowledge|skill)\b'
        }
        self.mandatory_keywords = [
            "shall", "must", "required to", "responsible for", "directed to",
            "shall provide", "shall develop", "shall support", "shall describe",
            "shall coordinate", "shall ensure", "shall comply", "shall implement",
            "required", "mandatory", "essential", "critical", "shall be",
            "is required", "are required", "must be", "must have"
        ]
        self.informative_keywords = [
            "will", "plans to", "anticipates", "intends to",
            "to be implemented", "to support", "to utilize", "to replace",
            "like-for-like", "equivalent basis", "will address", "will include",
            "should", "expected to", "recommended", "proposed",
            "will be", "should be", "may be", "can be"
        ]
        self.action_verbs = [
            "provide", "implement", "support", "maintain", "develop",
            "establish", "ensure", "perform", "deliver", "create",
            "replace", "transition", "utilize", "coordinate",
            "design", "install", "configure", "manage", "operate",
            "test", "verify", "document", "report", "monitor"
        ]

    def process_document(self, file_path: str) -> List[Dict]:
        """Process a document and extract requirements.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of extracted requirements with metadata
        """
        text = self._load_document(file_path)
        return self.extract_requirements_from_text(text)

    def _load_document(self, file_path: str) -> str:
        """Load and clean text from a document."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_path.suffix.lower() == '.pdf':
            with pdfplumber.open(file_path) as pdf:
                with ThreadPoolExecutor() as executor:
                    chunks = list(executor.map(self._process_pdf_page, pdf.pages))
                return '\n'.join(chunk for chunk in chunks if chunk)
        else:
            raise ValueError("Unsupported file format. Only PDFs are supported.")

    def _process_pdf_page(self, page) -> str:
        """Process a single PDF page."""
        text = page.extract_text(layout=True)
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line and not line.isspace():
                # Skip headers, footers, and page numbers
                if re.search(r'(?:Source|Page|For Official Use Only|^\d+$)', line):
                    continue
                # Skip lines with just dots (table of contents)
                if re.match(r'^\.+\s*\d*$', line):
                    continue
                lines.append(line)
        return '\n'.join(lines) if lines else ''

    def extract_requirements_from_text(self, text: str) -> List[Dict]:
        """Extract requirements from text content."""
        sections = self._parse_sections(text)
        all_requirements = []
        
        for section in sections:
            requirements = self._extract_requirements(section)
            all_requirements.extend(requirements)
        
        # Deduplicate and categorize requirements
        unique_requirements = self._deduplicate_requirements(all_requirements)
        categorized_requirements = self._categorize_requirements(unique_requirements)
        
        return self._sort_requirements(categorized_requirements)

    def _clean_content(self, content: str) -> str:
        """Clean and normalize text content."""
        # Remove headers/footers and common control characters
        content = re.sub(r'(?:Source-Selection-Sensitive|For Official Use Only|Page \d+|oSuerc\s*-\s*leStcoien\s*-\s*Snestivie)', '', content)
        content = re.sub(r'(?:ioFrf|For)\s*Ofiacs\s*l\s*UOneyl', '', content)
        
        # Remove artifacts and formatting markers
        content = re.sub(r'\.{3,}.*?(?:\d+|$)', '', content)  # Remove excessive dots
        content = re.sub(r'\(cid:[^\)]*\)', '', content)  # Remove CID markers
        content = re.sub(r'(?:Paeg|Page)\s*\d+\s*(?:of|fo)\s*\d+', '', content)  # Remove page numbers
        content = re.sub(r'(?:−|[−-])\s*', '', content)  # Fix various types of hyphens
        content = re.sub(r'\s*\([^)]*\)\s*$', '', content)  # Remove trailing parentheticals
        
        # Remove Table of Contents and section markers
        content = re.sub(r'Table of Contents.*?(?=A\.\d+)', '', content, flags=re.DOTALL)
        
        # Clean up line breaks and hyphenation
        content = re.sub(r'(?<=[a-zA-Z])-\s*\n\s*(?=[a-zA-Z])', '', content)
        content = re.sub(r'(?<=[a-zA-Z])\s*\n\s*(?=[a-zA-Z])', ' ', content)
        
        # Clean up bullet points and lists
        content = re.sub(r'[•⚫●○]\s*', '- ', content)  # Various bullet points
        content = re.sub(r'\(\s*[a-z]\s*\)', '', content)  # Remove lettered list markers
        content = re.sub(r'\s*\(\s*\d+\s*\)', '', content)  # Remove numbered list markers
        content = re.sub(r'^\s*[a-z]\.\s+', '', content, flags=re.MULTILINE)  # Remove list prefixes
        
        # Normalize whitespace and punctuation
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\s*[,;]\s*', ', ', content)  # Normalize commas and semicolons
        content = re.sub(r'\s*\.\s*', '. ', content)  # Normalize periods
        content = re.sub(r'\s*[.]\s*([a-z])', r'. \1', content)  # Fix sentence spacing
        
        return content.strip()

    def _parse_sections(self, text: str) -> List[Dict]:
        """Extract sections using regex with flexible patterns."""
        # Clean up text before parsing sections
        text = re.sub(r'(?m)^\s*Table of Contents.*?(?=A\.\d+)', '', text, flags=re.DOTALL)
        text = re.sub(r'(?m)^.*?(?:Source|Page|For Official Use Only).*$\n?', '', text)
        text = re.sub(r'(?m)^\s*\d+\s*$\n?', '', text)
        text = re.sub(r'\.{3,}.*?(?:\d+|$)', '', text)
        text = re.sub(r'oSuerc\s*-\s*leStcoien\s*-\s*Snestivie', '', text)
        text = re.sub(r'\(cid:\d*\)', '', text)
        
        # Find all section headers with improved pattern
        section_patterns = [
            r'(?:^|\n)\s*(?:Section\s+)?([A-Z](?:\.\d+)+)\s+([^\n]+)',  # A.1, B.2, etc.
            r'(?:^|\n)\s*([A-Z])\s+([^\n]+?)(?=\s*\n|$)',  # A, B, C, etc.
            r'(?:^|\n)\s*([A-Z])\.\s+([^\n]+?)(?=\s*\n|$)'  # E. Contract Administration
        ]
        
        matches = []
        for pattern in section_patterns:
            matches.extend(list(re.finditer(pattern, text, re.DOTALL)))
        
        # Sort matches by their position in the text
        matches.sort(key=lambda x: x.start())
        
        sections = []
        for i, match in enumerate(matches):
            section_id = match.group(1)
            title = match.group(2)
            
            # Get content until next section or end
            start = match.end()
            end = matches[i+1].start() if i < len(matches)-1 else len(text)
            content = text[start:end].strip()
            
            # Combine title and content
            full_content = f"{title}\n{content}" if content else title
            
            # Only include sections with substantial content
            if len(full_content.split()) > 10:
                cleaned_content = self._clean_content(full_content)
                if cleaned_content:
                    sections.append({
                        'id': section_id,
                        'content': cleaned_content
                    })
        
        return sections

    def _analyze_requirement(self, sentence: str) -> Dict:
        """Analyze if a sentence is a requirement."""
        # Skip sentences with common non-requirement indicators
        if any(indicator in sentence.lower() for indicator in [
            "table of contents",
            "section",
            "page",
            "for official use only",
            "source selection sensitive"
        ]):
            return {
                "is_requirement": False,
                "type": None,
                "confidence": 0.0
            }

        doc = nlp(sentence)

        # Skip sentences that are too short or lack substance
        if len(sentence.split()) < 5:
            return {
                "is_requirement": False,
                "type": None,
                "confidence": 0.0
            }

        # Check for keywords with word boundaries
        is_mandatory = any(re.search(rf'\b{re.escape(kw)}\b', sentence.lower()) 
                        for kw in self.mandatory_keywords)
        is_informative = any(re.search(rf'\b{re.escape(kw)}\b', sentence.lower())
                          for kw in self.informative_keywords)

        # Enhanced verb and subject analysis
        verbs = [token for token in doc if token.pos_ == "VERB"]
        has_action = any(str(verb.lemma_).lower() in self.action_verbs for verb in verbs)
        has_subject = any(token.dep_ == "nsubj" for token in doc)

        # Look for implicit requirements with enhanced patterns
        if not (is_mandatory or is_informative):
            implicit_patterns = [
                (r'This SOW\b.*?\b(?:address|describe|define|specify|outline)', 0.6),
                (r'NLRB\b.*?\b(?:plans|will|intends|needs|requires)', 0.7),
                (r'\b(?:like-for-like|equivalent)\b.*?\b(?:basis|service|replacement|solution)', 0.7),
                (r'\b(?:transition|replace|support|utilize)\b.*?\b(?:service|requirement|system|solution)s?\b', 0.7),
                (r'\b(?:contractor|vendor|provider)\b.*?\b(?:responsible|accountable)', 0.8),
                (r'\b(?:service|system|solution)\b.*?\b(?:must|should|shall|will)\b', 0.8)
            ]
            
            for pattern, conf in implicit_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    is_informative = True
                    base_confidence = conf
                    break
            else:
                base_confidence = 0.8 if is_mandatory else (0.6 if is_informative else 0.0)
        else:
            base_confidence = 0.8 if is_mandatory else (0.6 if is_informative else 0.0)

        # Enhanced confidence calculation
        confidence = base_confidence
        if has_action:
            confidence += 0.15
        if has_subject:
            confidence += 0.15
        if len(verbs) > 0:
            confidence += 0.1

        return {
            "is_requirement": is_mandatory or is_informative,
            "type": "Mandatory" if is_mandatory else ("Informative" if is_informative else None),
            "confidence": min(confidence, 1.0)
        }

    def _extract_requirements(self, section: Dict) -> List[Dict]:
        """Extract requirements from a section."""
        # Split into sentences more accurately
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', section['content'])
        
        requirements = []
        for sentence in sentences:
            sentence = sentence.strip()
            # Skip short sentences and section headers
            if len(sentence.split()) < 3 or re.match(r'^[A-Z](?:\.\d+)*\s+', sentence):
                continue

            result = self._analyze_requirement(sentence)
            if result['is_requirement'] and result['confidence'] >= 0.7:
                requirements.append({
                    'section_id': section['id'],
                    'text': sentence,
                    'type': result['type'],
                    'confidence': result['confidence']
                })

        return requirements

    def _deduplicate_requirements(self, requirements: List[Dict]) -> List[Dict]:
        """Remove duplicate requirements while keeping highest confidence versions."""
        unique_requirements = {}
        for req in requirements:
            # Create a normalized version of the text for comparison
            normalized_text = re.sub(r'\s+', ' ', req['text'].lower().strip())
            # Only keep the highest confidence version of duplicate requirements
            if normalized_text not in unique_requirements or req['confidence'] > unique_requirements[normalized_text]['confidence']:
                unique_requirements[normalized_text] = req
        
        return list(unique_requirements.values())

    def _categorize_requirements(self, requirements: List[Dict]) -> List[Dict]:
        """Categorize requirements and split long informative ones."""
        categorized_requirements = []
        for req in requirements:
            # Add category based on content
            category = self._categorize_requirement(req['text'])
            req['category'] = category
            
            # Split long informative requirements
            if req['type'] == 'Informative' and len(req['text'].split()) > 30:
                split_reqs = self._split_informative_requirement(req)
                categorized_requirements.extend(split_reqs)
            else:
                categorized_requirements.append(req)
        
        return categorized_requirements

    def _categorize_requirement(self, text: str) -> str:
        """Categorize requirement based on content."""
        for category, pattern in self.categories.items():
            if re.search(pattern, text, re.IGNORECASE):
                return category
        return 'General'

    def _split_informative_requirement(self, req: Dict) -> List[Dict]:
        """Split long informative requirements into smaller, focused requirements."""
        # Split on common conjunctions while preserving context
        splits = re.split(r'\s+(?:and|or|as well as|additionally|furthermore|moreover)\s+', req['text'])
        
        # Only split if we get meaningful chunks
        if len(splits) > 1 and all(len(s.split()) > 10 for s in splits):
            return [{
                'section_id': req['section_id'],
                'text': split.strip(),
                'type': req['type'],
                'confidence': req['confidence'],
                'category': req['category']
            } for split in splits]
        
        return [req]

    def _sort_requirements(self, requirements: List[Dict]) -> List[Dict]:
        """Sort requirements by section ID."""
        def sort_key(req):
            # Split ID into parts and convert numbers
            parts = []
            for part in req['section_id'].split('.'):
                try:
                    parts.append(int(part))
                except ValueError:
                    parts.append(part)
            return parts
        
        return sorted(requirements, key=sort_key)

    def save_requirements_to_csv(self, requirements: List[Dict], filename: str = "extracted_requirements.csv"):
        """Save requirements to a CSV file."""
        df = pd.DataFrame(requirements)
        df.to_csv(filename, index=False)
