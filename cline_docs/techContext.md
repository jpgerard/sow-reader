# Technical Context

## Technologies Used

### Frontend
- Streamlit for UI
  - Interactive web interface
  - Built-in file upload widgets
  - Data visualization components
  - Session state management
  - Automatic responsive layout

### Backend Components
- Python-based document processing
- LLM integration for analysis
- Hybrid search system:
  - Vector-based semantic search
  - Text-based matching
  - Section ID matching
- Export capabilities

### Core Libraries
- sentence-transformers for embeddings
- faiss-cpu for vector search
- pdfplumber for PDF processing
- python-docx for DOCX processing
- numpy for numerical operations
- pandas for data handling

### Development Setup
- Python environment
  - Streamlit for web interface
  - Document processing libraries
  - LLM integration
  - Data analysis tools
- Environment variables management
- Virtual environment for dependency isolation

### Project Structure
- /src
  - Core processing:
    - Entity processing in /entity_processing
    - Search functionality in /search
      - vector_search.py for semantic search
      - hybrid_search.py for combined search
      - proposal_matcher.py for matching logic
    - System monitoring in /monitoring
  - Streamlit interface:
    - Main app in app.py
    - Component modules
    - Utility functions
- /tests for test files
- Configuration:
  - requirements.txt for Python dependencies
  - .env for environment variables
  - .gitignore for version control

### Deployment Guide

#### Prerequisites
1. GitHub Account
2. Streamlit Cloud Account (https://share.streamlit.app)
3. Required Files:
   - app.py
   - requirements.txt
   - .env (for local development)
   - All supporting Python modules

#### Step-by-Step Deployment Instructions

1. Prepare Repository
   ```bash
   # Initialize git repository (if not already done)
   git init
   
   # Create .gitignore
   echo ".env" >> .gitignore
   echo "__pycache__" >> .gitignore
   echo "*.pyc" >> .gitignore
   
   # Add files
   git add .
   git commit -m "Initial commit"
   ```

2. Create GitHub Repository
   - Go to github.com
   - Click "New repository"
   - Name it "sow-reader"
   - Make it Public
   - Don't initialize with README
   - Push your code:
     ```bash
     git remote add origin [your-repo-url]
     git branch -M main
     git push -u origin main
     ```

3. Set Up Streamlit Cloud
   - Go to share.streamlit.app
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Select main branch
   - Set main file path to app.py

4. Configure Secrets
   - In Streamlit Cloud:
     - Go to App Settings
     - Under "Secrets", add:
     ```toml
     [secrets]
     ANTHROPIC_API_KEY = "your-api-key"
     ```

5. Deploy
   - Click "Deploy!"
   - Wait for build process
   - App will be available at https://[your-app-name].streamlit.app

#### Environment Variables
Required secrets for deployment:
- ANTHROPIC_API_KEY: Your Claude API key

#### Maintenance
- Monitor app performance
- Check error logs in Streamlit Cloud
- Update dependencies as needed
- Keep API keys current

### Technical Constraints
1. Document Processing
   - Memory limitations for large documents
   - PDF/Word parsing accuracy
   - Text extraction fidelity
   - Document structure preservation

2. LLM Integration
   - API rate limits
   - Response time considerations
   - Token usage optimization
   - Cost management

3. System Performance
   - Server memory management
   - Large file handling
   - Concurrent processing limits
   - Streamlit session state limitations

4. Security Considerations
   - File upload validation
   - Document content security
   - API authentication
   - Data privacy compliance

### Streamlit-Specific Considerations
1. State Management
   - Session state for user data
   - Cache management for computations
   - Component rerun behavior

2. UI Components
   - File uploaders for documents
   - Progress indicators
   - Interactive data tables
   - Download buttons for exports

3. Performance Optimization
   - Caching strategies
   - Efficient data handling
   - Background processing
   - Memory management
