import os
import sys
import requests
from dotenv import load_dotenv
import logging

try:
    # Configure logging to output to both file and console
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('validator.log')
        ]
    )
    logger = logging.getLogger(__name__)

    print("Script started...")  # Debug print

    class OpenAIKeyValidator:
        def __init__(self):
            print("Initializing validator...")  # Debug print
            # Load environment variables
            load_dotenv()
            
            # Retrieve API key
            self.api_key = os.getenv("OPENAI_API_KEY")
            print(f"API key loaded: {'Yes' if self.api_key else 'No'}")  # Debug print
            
            # OpenAI API base URL
            self.base_url = "https://api.openai.com/v1"

        def validate_api_key(self):
            """
            Comprehensive API key validation method
            """
            print("Starting validation...")  # Debug print
            
            if not self.api_key:
                print("No API key found in environment variables")
                return False

            print(f"Key type: {'Project-specific' if self.api_key.startswith('sk-proj-') else 'Standard'}")  # Debug print

            # Test the API key by listing models
            try:
                print("Making API request...")  # Debug print
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                response = requests.get(
                    f"{self.base_url}/models", 
                    headers=headers,
                    timeout=10
                )
                
                print(f"Response received: {response.status_code}")  # Debug print
                print(f"Response content: {response.text}")  # Debug print
                
                if response.status_code == 200:
                    print("API key is valid!")
                    return True
                else:
                    print(f"API key validation failed. Status: {response.status_code}")
                    print(f"Error: {response.text}")
                    return False
                
            except Exception as e:
                print(f"Error during validation: {str(e)}")
                return False

        def suggest_fixes(self):
            """
            Provide suggestions for common API key issues
            """
            suggestions = [
                "1. Ensure you're using the correct API key type",
                "2. Verify the key is copied correctly",
                "3. Check if the key has the necessary permissions",
                "4. Verify your account is in good standing",
                "5. Check your billing and payment method",
                "6. Ensure you have sufficient credits",
                "7. Verify network connectivity"
            ]
            return "\n".join(suggestions)

    if __name__ == "__main__":
        print("Main execution started...")  # Debug print
        validator = OpenAIKeyValidator()
        is_valid = validator.validate_api_key()
        
        if not is_valid:
            print("\nAPI Key Validation Failed. Suggested Fixes:")
            print(validator.suggest_fixes())

except Exception as e:
    print(f"Critical error in script: {str(e)}")
    if hasattr(e, '__traceback__'):
        import traceback
        print("Full traceback:")
        traceback.print_tb(e.__traceback__)
