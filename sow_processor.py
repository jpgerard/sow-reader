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
        self.categories = {
            'Technical': r'\b(?:technical|system|software|hardware|network|infrastructure|security)\b',
            'Process': r'\b(?:process|procedure|workflow|method|approach|implementation)\b',
            'Service': r'\b(?:service|support|maintenance|operation|performance)\b',
            'Documentation': r'\b(?:document|report|plan|deliverable|submission)\b',
            'Compliance': r'\b(?:comply|compliance|requirement|standard|regulation|policy)\b',
            'Training': r'\b(?:training|instruction|education|knowledge|skill)\b'
        }
        self.mandatory_keywords = ["shall", "must", "required to", "responsible for", "directed to"]
        self.informative_keywords = ["will", "plans to", "anticipated", "expected to"]

    def process_document(self, file_path: str) -> List[Dict]:
        text = self._load_document(file_path)
        return self.extract_requirements_from_text(text)

    def _load_document(self, file_path: str) -> str:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()
        if suffix == '.pdf':
            with pdfplumber.open(file_path) as pdf:
                with ThreadPoolExecutor() as executor:
                    chunks = list(executor.map(self._process_pdf_page, pdf.pages))
                return '\n'.join(chunk for chunk in chunks if chunk)
        else:
            raise ValueError("Unsupported file format. Only PDF files are supported.")

    def _process_pdf_page(self, page) -> str:
        try:
            text = page.extract_text(layout=True) or page.extract_text(layout=False)
        except Exception as e:
            print(f"Error extracting text from page: {e}")
            return ""

        lines = []
        buffer = ""
        for line in text.split('\n'):
            line = line.strip()
            if not line or re.search(r'(?:Source|Page|For Official Use Only|^\d+$)', line):
                continue
            if re.match(r'^[A-Z]\.(\d+)?', line) or buffer:
                if buffer:
                    buffer += " " + line
                    if not line.endswith('.'):
                        continue
                else:
                    buffer = line
            else:
                lines.append(buffer)
                buffer = line if line.endswith('.') else ""
        if buffer:
            lines.append(buffer)
        return '\n'.join(lines)

    def extract_requirements_from_text(self, text: str) -> List[Dict]:
        sections = self._parse_sections(text)
        all_requirements = []

        for section in sections:
            requirements = self._extract_requirements(section)
            all_requirements.extend(requirements)

        unique_requirements = self._deduplicate_requirements(all_requirements)
        categorized_requirements = self._categorize_requirements(unique_requirements)
        return self._sort_requirements(categorized_requirements)

    def _parse_sections(self, text: str) -> List[Dict]:
        text = re.sub(r'(?m)^.*?(?:Source|Page|For Official Use Only).*$\n?', '', text)
        text = re.sub(r'\.{3,}.*?(?:\d+|$)', '', text)
        text = re.sub(r'\(cid:\d*\)', '', text)

        sections = []
        section_patterns = [
            r'(?:(?<=\n)|^)([A-Z]\.(\d+)?).*?(?=\n[A-Z]\.(\d+)?|$)',
            r'(?:(?<=\n)|^)(\d+\.\d+\.\d+).*?(?=\n\d+\.\d+\.\d+|$)'
        ]

        for pattern in section_patterns:
            matches = re.finditer(pattern, text, re.DOTALL)
            for match in matches:
                section_id = match.group(1).strip()
                content = match.group(0)[len(section_id):].strip()
                if content:
                    sections.append({'id': section_id, 'content': self._clean_content(content)})

        return sections

    def _clean_content(self, content: str) -> str:
        content = re.sub(r'\.{3,}.*?(?:\d+|$)', '', content)
        content = re.sub(r'\(cid:\d*\)', '', content)
        content = re.sub(r'\s+', ' ', content)
        return content.strip()

    def _extract_requirements(self, section: Dict) -> List[Dict]:
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', section['content'])
        requirements = []

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence.split()) < 3 or re.match(r'^[A-Z](?:\.\d+)*\s+', sentence):
                continue

            result = self._analyze_requirement(sentence)
            if result['is_requirement']:
                requirements.append({
                    'section_id': section['id'],
                    'text': sentence,
                    'type': result['type'],
                    'confidence': result['confidence']
                })

        return requirements

    def _analyze_requirement(self, sentence: str) -> Dict:
        doc = nlp(sentence)
        if len(sentence.split()) < 5:
            return {"is_requirement": False, "type": None, "confidence": 0.0}

        is_mandatory = any(re.search(rf'\b{re.escape(kw)}\b', sentence.lower()) for kw in self.mandatory_keywords)
        is_informative = any(re.search(rf'\b{re.escape(kw)}\b', sentence.lower()) for kw in self.informative_keywords)

        confidence = 0.8 if is_mandatory else (0.6 if is_informative else 0.0)

        return {
            "is_requirement": is_mandatory or is_informative,
            "type": "Mandatory" if is_mandatory else ("Informative" if is_informative else None),
            "confidence": confidence
        }

    def _deduplicate_requirements(self, requirements: List[Dict]) -> List[Dict]:
        unique_requirements = {}
        for req in requirements:
            normalized_text = re.sub(r'\s+', ' ', req['text'].lower().strip())
            if normalized_text not in unique_requirements or req['confidence'] > unique_requirements[normalized_text]['confidence']:
                unique_requirements[normalized_text] = req

        return list(unique_requirements.values())

    def _categorize_requirements(self, requirements: List[Dict]) -> List[Dict]:
        categorized_requirements = []
        for req in requirements:
            category = self._categorize_requirement(req['text'])
            req['category'] = category
            categorized_requirements.append(req)
        return categorized_requirements

    def _categorize_requirement(self, text: str) -> str:
        for category, pattern in self.categories.items():
            if re.search(pattern, text, re.IGNORECASE):
                return category
        return 'General'

    def _sort_requirements(self, requirements: List[Dict]) -> List[Dict]:
        def sort_key(req):
            parts = []
            section_id = req['section_id']
            if not isinstance(section_id, str):
                return [str(section_id)]
            for part in section_id.split('.'):  
                parts.append(part)
            return parts
        return sorted(requirements, key=sort_key)

    def save_requirements_to_csv(self, requirements: List[Dict], filename: str = "extracted_requirements.csv"):
        df = pd.DataFrame(requirements)
        df.to_csv(filename, index=False)
