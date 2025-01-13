import unittest
from pathlib import Path
import tempfile
from io import BytesIO
import pdfplumber

class TestSOWProcessor(unittest.TestCase):
    def setUp(self):
        from sow_processor import SOWProcessor
        self.processor = SOWProcessor()
        
        # Create a sample PDF for testing
        self.pdf_content = """
        A.1 Technical Requirements
        The system shall provide secure access. The network will be monitored.
        
        A.2 Process Requirements
        The contractor must document all procedures. Teams are expected to follow guidelines.
        """
        
    def test_analyze_requirement(self):
        # Test mandatory requirements
        mandatory_tests = [
            "The contractor shall provide support",
            "The team must complete documentation",
            "The vendor is required to maintain logs",
            "The staff is responsible for updates",
            "Teams are directed to follow procedures"
        ]
        
        for test in mandatory_tests:
            result = self.processor._analyze_requirement(test)
            self.assertTrue(result["is_requirement"], f"Failed to identify mandatory requirement: {test}")
            self.assertEqual(result["type"], "Mandatory")
            self.assertEqual(result["confidence"], 0.8)
        
        # Test informative requirements
        informative_tests = [
            "The system will be updated",
            "The team plans to implement changes",
            "Updates are anticipated weekly",
            "Staff is expected to attend training"
        ]
        
        for test in informative_tests:
            result = self.processor._analyze_requirement(test)
            self.assertTrue(result["is_requirement"], f"Failed to identify informative requirement: {test}")
            self.assertEqual(result["type"], "Informative")
            self.assertEqual(result["confidence"], 0.6)
        
        # Test non-requirements
        non_req_tests = [
            "This is a description",
            "Welcome to the document",
            "Page 1 of 10",
            "Table of Contents"
        ]
        
        for test in non_req_tests:
            result = self.processor._analyze_requirement(test)
            self.assertFalse(result["is_requirement"], f"Incorrectly identified as requirement: {test}")
            
    def test_categorize_requirement(self):
        # Test each category
        test_cases = {
            'Technical': [
                "The system shall be secure",
                "Update network infrastructure",
                "Implement software changes"
            ],
            'Process': [
                "Document the workflow",
                "Follow the procedure",
                "Implement new methods"
            ],
            'Service': [
                "Provide support services",
                "Maintain operation status",
                "Monitor performance metrics"
            ],
            'Documentation': [
                "Submit required reports",
                "Create plan documents",
                "Prepare deliverables"
            ],
            'Compliance': [
                "Meet compliance standards",
                "Follow regulations",
                "Adhere to policies"
            ],
            'Training': [
                "Complete required training",
                "Provide education materials",
                "Develop skill assessments"
            ]
        }
        
        for category, tests in test_cases.items():
            for test in tests:
                result = self.processor._categorize_requirement(test)
                self.assertEqual(result, category, f"Failed to categorize '{test}' as {category}")
                
        # Test general category
        general_tests = [
            "Complete all tasks",
            "Attend meetings regularly",
            "Submit weekly updates"
        ]
        
        for test in general_tests:
            result = self.processor._categorize_requirement(test)
            self.assertEqual(result, "General", f"Failed to categorize '{test}' as General")
            
    def test_parse_sections(self):
        test_text = """
        A.1 Technical Requirements
        The system shall be secure. Network monitoring will be implemented.
        
        A.2 Process Requirements
        Document all procedures. Teams shall follow guidelines.
        
        1.1.1 Additional Requirements
        Regular updates must be performed.
        """
        
        sections = self.processor._parse_sections(test_text)
        
        # Verify sections were extracted
        self.assertGreater(len(sections), 0, "No sections were extracted")
        
        # Verify section IDs
        section_ids = [section['id'] for section in sections]
        self.assertTrue(any('A.1' in id for id in section_ids), "Missing section A.1")
        self.assertTrue(any('A.2' in id for id in section_ids), "Missing section A.2")
        self.assertTrue(any('1.1.1' in id for id in section_ids), "Missing section 1.1.1")
        
    def test_extract_requirements_from_text(self):
        test_text = """
        A.1 Technical Requirements
        The system shall provide secure access. The network will be monitored daily.
        Regular maintenance must be performed.
        
        A.2 Process Requirements
        Teams shall document procedures. Updates are expected weekly.
        """
        
        requirements = self.processor.extract_requirements_from_text(test_text)
        
        # Verify requirements were extracted
        self.assertGreater(len(requirements), 0, "No requirements were extracted")
        
        # Check for both mandatory and informative requirements
        req_types = [req['type'] for req in requirements]
        self.assertTrue('Mandatory' in req_types, "No mandatory requirements found")
        self.assertTrue('Informative' in req_types, "No informative requirements found")
        
        # Check for proper categorization
        categories = [req['category'] for req in requirements]
        self.assertTrue('Technical' in categories, "No technical requirements found")
        self.assertTrue('Process' in categories, "No process requirements found")
        
        # Verify confidence scores
        confidences = [req['confidence'] for req in requirements]
        self.assertTrue(all(c in [0.8, 0.6] for c in confidences), "Invalid confidence scores found")

if __name__ == '__main__':
    unittest.main(verbosity=2)
