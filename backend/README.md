# Unit Test Generator Backend

This backend uses the robust Gemini AI integration from `generateUnitTest.py` to generate comprehensive C/C++ unit tests through a FastAPI web service.

## Features

- **Robust Gemini AI Integration**: Uses the advanced prompting and parsing logic from `generateUnitTest.py`
- **Multiple Fallback Mechanisms**: Supports both Vertex AI and Google GenAI clients
- **Comprehensive Test Generation**: Creates Unity framework-based unit tests with full coverage
- **Smart Response Parsing**: Handles both JSON and markdown table formats from AI responses
- **RESTful API**: Clean FastAPI endpoints for frontend integration

## Setup Instructions

### 1. Install Dependencies

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r ../requirements.txt
```

### 2. Configure API Keys

Set your Google Gemini API key:

```bash
# Option 1: Environment variable
export GOOGLE_API_KEY="your_gemini_api_key"

# Option 2: For Vertex AI (optional)
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
```

Get your API key from [Google AI Studio](https://aistudio.google.com/)

### 3. Run the Backend

```bash
# Run the FastAPI server
python app.py

# Or with uvicorn directly (with auto-reload for development)
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **Main API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Endpoints

### POST `/upload_files`
Upload C/C++ source and header files.

**Request**: Multipart form data with files
**Response**:
```json
{
  "status": "success",
  "message": "Uploaded 2 files successfully",
  "files": [...]
}
```

### POST `/generate_tests`
Generate comprehensive unit tests using Gemini AI.

**Request Body**:
```json
{
  "files": [
    {
      "filename": "example.c",
      "content": "/* C source code */",
      "size": 1234
    }
  ]
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Test cases generated successfully",
  "data": {
    "test_cases": [
      {
        "id": "TC_001",
        "function_name": "test_example_function",
        "description": "Test normal operation",
        "input_data": "Valid inputs",
        "expected_output": "Expected result",
        "type": "Positive",
        "test_code": "/* Unity test code */"
      }
    ],
    "test_runner_script": "/* Complete test runner */",
    "makefile_content": "/* Build configuration */",
    "summary": {
      "total_tests": 5,
      "functions_tested": ["example_function"],
      "coverage_areas": []
    }
  }
}
```

### GET `/health`
Health check endpoint.

## Architecture

### File Structure
```
backend/
├── app.py                    # FastAPI application
├── generateUnitTest.py       # Core Gemini AI integration & parsing
├── uploads/                  # Temporary file uploads
├── temp_files/               # Temporary files for processing
└── README.md                 # This file
```

### Key Components

1. **TestGenerationService**: Main service class that:
   - Calls Gemini AI with structured prompts
   - Handles temporary file management
   - Parses AI responses with multiple fallback strategies

2. **Robust Parsing**: The system can handle:
   - JSON responses from Gemini
   - Markdown table formats
   - C code block extraction
   - Mixed response formats

3. **Structured Prompts**: Uses comprehensive prompts that ensure:
   - 100% code coverage requirements
   - Unity framework compliance
   - Both positive and negative test scenarios
   - Boundary value and error path testing

## Integration with Frontend

The backend expects the frontend to be running on:
- http://localhost:5173 (Vite dev server)
- http://localhost:3000 (Alternative dev port)

CORS is configured to allow these origins. Update the `allow_origins` list in `app.py` for production deployment.

## Error Handling

The API provides detailed error responses:

- **400**: Invalid file types or missing required data
- **500**: Gemini AI errors, parsing failures, or system errors

All errors include descriptive messages for debugging.

## Development

For development with auto-reload:
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The FastAPI automatic documentation is available at `/docs` for testing endpoints.