# System Patterns

## Architecture Overview
- Streamlit-based web application
- Modular design with clear separation of concerns
- Event-driven UI with session state management
- Pipeline-based document processing

## Key Components

### Document Processing
- PDF processing using pdfplumber
- DOCX processing using python-docx
- Layout-aware text extraction with fallback options
- Progress tracking and error handling

### Requirement Analysis
- SOWProcessor for requirement extraction
- Section ID pattern matching (X.X.X format)
- Type and category classification
- Confidence scoring system

### Search and Matching
- Hybrid approach combining:
  - Vector-based semantic search using sentence-transformers
  - Text-based matching using Jaccard similarity
  - Section ID structural matching
- Configurable scoring weights
- Detailed match explanations
- Improvement suggestions

### LLM Integration
- Claude-3-opus model for analysis
- JSON-structured responses
- Error handling for API responses
- Rate limit and token management

### Data Management
- Session state for data persistence
- Temporary file handling
- Cleanup procedures
- Export functionality (CSV/Excel)

## Design Patterns

### State Management
- Centralized session state
- Initialization checks
- Progress tracking
- Results caching

### Error Handling
- Graceful degradation
- User feedback
- Cleanup on failure
- Fallback mechanisms

### UI Components
- Two-column layout
- Progress indicators
- Interactive tables
- Metric displays
- Export controls

### File Processing
- Temporary file management
- Multi-format support
- Progress tracking
- Resource cleanup

### Search Implementation
- Modular search components
- Extensible scoring system
- Configurable weights
- Detailed explanations
- Suggestion generation

## Best Practices
- Environment variable management
- API key validation
- Resource cleanup
- User feedback
- Error recovery
- Data validation
