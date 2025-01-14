# SOW Analyzer

A Streamlit application for analyzing Statement of Work (SOW) documents and comparing them against proposal documents. The app extracts requirements from SOWs and uses Claude-3 AI to analyze proposal compliance.

## Latest Working Version

The current working version uses:
- Claude-3 Opus (model: claude-3-opus-20240229)
- Anthropic API v0.42.0
- Streamlit for the web interface

Key requirements for proper functionality:
1. Valid Anthropic API key configured in Streamlit secrets
2. Correct API initialization and message format
3. Python 3.8+ environment

## Features

- Extract requirements from SOW documents (PDF/DOCX)
- Categorize requirements by type (Mandatory/Informative)
- Analyze proposal documents against SOW requirements
- Generate compliance reports with section matching
- Export results to CSV and Excel formats

## Deployment

### Streamlit Cloud

1. Fork this repository
2. Sign up for [Streamlit Cloud](https://streamlit.io/cloud)
3. Create a new app and connect it to your forked repository
4. Add your Anthropic API key in Streamlit Cloud:
   - Go to your app settings
   - Click on "Secrets"
   - Add your secrets in the following format:
     ```toml
     [general]
     ANTHROPIC_API_KEY = "your-api-key-here"
     ```

### Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create `.streamlit/secrets.toml` with your Anthropic API key:
   ```toml
   [general]
   ANTHROPIC_API_KEY = "your-api-key-here"
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Usage

1. Upload a SOW document (PDF/DOCX)
2. (Optional) Upload a proposal document to analyze compliance
3. View extracted requirements and analysis results
4. Export results using the provided buttons

## Requirements

- Python 3.8+
- See requirements.txt for full list of dependencies

## Notes

- The app uses spaCy for NLP processing
- Claude-3 AI (via Anthropic API) is used for proposal analysis with the following configuration:
  - Model: claude-3-opus-20240229
  - System message set at top level
  - Messages formatted according to Claude-3 requirements
- Temporary files are automatically cleaned up after processing
- API calls are properly authenticated using the configured API key
