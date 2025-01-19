import os

# Create .streamlit directory if it doesn't exist
os.makedirs('.streamlit', exist_ok=True)

# Write secrets.toml with explicit encoding and newlines
with open('.streamlit/secrets.toml', 'w', encoding='ascii', newline='\n') as f:
    f.write('[general]\n')
    f.write('ANTHROPIC_API_KEY = "your-api-key-here"\n')
