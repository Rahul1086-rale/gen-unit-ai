# Unit Test Generator Backend

## Setup Instructions

### 1. Install Dependencies

First, navigate to the backend directory and install dependencies:

```bash
cd backend
pip install -r ../requirements.txt
```

### 2. Set up Gemini API Key

You need a Google Gemini API key to generate unit tests. 

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create an API key
3. Set the environment variable:

```bash
export GOOGLE_API_KEY="your_api_key_here"
```

### 3. Run the Backend

```bash
# Option 1: Using the run script (recommended)
python run_server.py

# Option 2: Direct uvicorn command
python app.py

# Option 3: With uvicorn and auto-reload
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- Main API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 4. Run the Frontend

In a separate terminal, run the frontend:

```bash
# From project root
npm install
npm run dev
```

## Features

- **Robust Gemini AI Integration**: Uses advanced prompting and parsing from `generateUnitTest.py`
- **Comprehensive Coverage**: Generates tests for statement, branch, condition, boundary value, and error path coverage
- **Unity Framework**: All generated tests follow Unity testing framework conventions
- **Smart Parsing**: Handles multiple response formats from AI with fallback mechanisms

## API Endpoints

### POST /upload_files
Upload C/C++ source and header files.

### POST /generate_tests  
Generate unit tests using Gemini AI with robust parsing.

### GET /health
Health check endpoint.

## File Structure

```
backend/
├── app.py                 # FastAPI application with integrated parsing
├── generateUnitTest.py    # Core Gemini AI functions and parsing logic  
├── run_server.py          # Convenient server runner script
├── uploads/               # Temporary uploaded files
├── temp_files/            # Temporary processing files
└── README.md             # Backend documentation
```

## Integration Notes

The backend now uses the robust functions from `generateUnitTest.py`:
- `call_gemini()` for AI integration with fallback support
- `try_extract_json_block()` for JSON parsing  
- `parse_markdown_table()` for table extraction
- Structured prompts for comprehensive test generation