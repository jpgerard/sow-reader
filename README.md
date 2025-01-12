# SOW Analyzer

A powerful tool for analyzing Statement of Work (SOW) requirements against proposals using Claude's LLM technology.

## Background

The SOW Analyzer automates the process of analyzing Statement of Work requirements against proposals. It helps ensure comprehensive coverage and compliance by:

- Extracting and classifying requirements from SOW documents
- Mapping requirements to proposal sections
- Assessing compliance and confidence levels
- Generating improvement suggestions
- Providing structured output in Excel format

## Features

- **Document Support**: Process PDF and Word documents
- **Smart Analysis**: LLM-powered requirement identification and mapping
- **Compliance Checking**: Automated assessment of proposal coverage
- **Export Capability**: Structured Excel output with detailed analysis

## Setup

1. **Environment Setup**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Environment Variables**
   Create a `.env` file with:
   ```
   ANTHROPIC_API_KEY=your_claude_api_key
   ```

## Usage

1. **Launch Application**
   ```bash
   streamlit run app.py
   ```

2. **Upload Documents**
   - Use the SOW Document uploader for your Statement of Work (PDF/DOCX)
   - Use the Proposal Document uploader for your proposal document (PDF/DOCX)

3. **View Analysis**
   Navigate through:
   - Analysis Results: Overview of requirement mapping
   - Document Sections: Detailed document structure
   - Requirements: Extracted requirements list

4. **Export Results**
   - Use the Export button to download analysis in Excel format
   - Results include:
     * SOW Section
     * Requirement details
     * Classification
     * Proposal mapping
     * Compliance status
     * Confidence level
     * Improvement suggestions

## Technical Details

### Document Processing
- PDFPlumber for PDF parsing
- python-docx for Word documents
- Structured text extraction with format preservation

### Analysis Engine
- Claude API integration
- Semantic matching
- Requirement classification
- Compliance assessment

### User Interface
- Streamlit-based interface
- Intuitive file upload
- Interactive results display
- Excel export using openpyxl

## Development

### Testing
```bash
# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=src tests/
```

### Project Structure
```
src/
├── core/               # Core processing logic
├── entity_processing/  # Entity extraction
├── graph_construction/ # Relationship building
├── llm/               # Claude integration
├── monitoring/        # System monitoring
└── search/           # Search functionality
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[License details to be added]
