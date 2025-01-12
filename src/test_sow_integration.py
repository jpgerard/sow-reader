"""
Test script to demonstrate SOW processing integration.
"""

from entity_processing.entity_extractor import EntityExtractor
import json
from pathlib import Path

def main():
    # Initialize entity extractor
    extractor = EntityExtractor()
    
    # Process SOW document
    sow_path = r"C:\Users\jpg02\SOW_reader\A17 J1 SOW NLRB-POTS.pdf"  # Using the test document
    print(f"\nProcessing SOW document: {sow_path}")
    
    try:
        # Process the document
        result = extractor.process_sow(sow_path)
        
        # Print summary
        print("\nProcessing Summary:")
        print(f"Total requirements found: {result['metadata']['entity_counts']['total']}")
        print(f"Mandatory requirements: {result['metadata']['entity_counts']['mandatory']}")
        print(f"Informative requirements: {result['metadata']['entity_counts']['informative']}")
        
        # Print requirements by category
        print("\nRequirements by Category:")
        for key, value in result['metadata']['entity_counts'].items():
            if key.startswith('category_'):
                print(f"{key[9:]}: {value}")
        
        # Save results to file
        output_file = "sow_analysis_results.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nFull results saved to: {output_file}")
        
        # Print sample requirements
        print("\nSample Requirements:")
        for req in result['requirements'][:5]:  # First 5 requirements
            print(f"\nSection {req['section_id']} ({req['type']}, {req['category']}):")
            print(f"Confidence: {req['confidence']:.2f}")
            print(f"Text: {req['text'][:200]}...")
            
    except Exception as e:
        print(f"Error processing document: {str(e)}")

if __name__ == "__main__":
    main()
