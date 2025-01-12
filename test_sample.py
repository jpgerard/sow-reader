import os
import json
from dotenv import load_dotenv
import anthropic

# Load environment variables
load_dotenv()

def analyze_proposal_match():
    # Initialize Anthropic client
    client = anthropic.Anthropic()
    
    # Sample SOW text
    sow_text = """
    A.2 This SOW will address requirements for transition from the existing NLRB services that are currently under the Circuit Switched Voice Service (CSVS) section of the GSA EIS contract.

    A.3 NLRB plans to replace this service on a like-for-like or equivalent basis where required and to utilize transformative services and or options to be incrementally implemented to support overarching agency objectives where possible.

    A.4 The Contractor shall provide POTS service, or equivalent, including installation and DMARC extension at all field, offices and headquarters.
    """

    # Sample proposal text
    proposal_text = """
    Our team understands NLRB's requirements for transitioning from the existing Circuit Switched Voice Service. We will implement a comprehensive transition plan that ensures continuity of service.

    We propose to provide POTS service with full installation support and DMARC extension capabilities across all NLRB field offices and headquarters locations. Our solution is designed to be equivalent to the existing service while offering enhanced features.

    The transition will be managed on a like-for-like basis, ensuring minimal disruption to NLRB operations. We will incrementally implement transformative services to support NLRB's objectives.
    """

    print("Analyzing proposal match...")
    
    try:
        response = client.messages.create(
            model="claude-2",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"""Analyze how well this proposal text matches the SOW requirements. Return a JSON object with this exact format:
                {{
                    "requirements": [
                        {{
                            "text": "The requirement text from SOW",
                            "matched_text": "The exact text from proposal that addresses this requirement",
                            "compliance": "Fully Compliant/Partially Compliant/Not Addressed",
                            "confidence": 0.0 to 1.0,
                            "suggestions": ["Improvement suggestions"]
                        }}
                    ]
                }}

                SOW Text:
                {sow_text}

                Proposal Text:
                {proposal_text}"""
            }]
        )
        
        # Extract and parse JSON response
        response_text = response.content[0].text
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            analysis = json.loads(json_str)
            
            # Print results
            print("\nAnalysis Results:")
            print("-" * 80)
            for req in analysis['requirements']:
                print(f"\nRequirement: {req['text']}")
                print(f"Compliance: {req['compliance']}")
                print(f"Confidence: {req['confidence']:.2f}")
                print(f"Matched Text: {req['matched_text']}")
                if req['suggestions']:
                    print("\nSuggestions:")
                    for suggestion in req['suggestions']:
                        print(f"- {suggestion}")
                print("-" * 80)
        else:
            print("Error: Could not parse JSON response")
            
    except Exception as e:
        print(f"Error analyzing proposal: {str(e)}")

if __name__ == "__main__":
    analyze_proposal_match()
