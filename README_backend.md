# Unit Test Generator Backend

## Setup Instructions

### 1. Install Dependencies

First, create a virtual environment and install the required packages:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set up Gemini API Key

You need a Google Gemini API key to generate unit tests. 

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create an API key
3. Set the environment variable:

```bash
# On Windows:
set GOOGLE_API_KEY=your_api_key_here

# On macOS/Linux:
export GOOGLE_API_KEY=your_api_key_here
```

Or update the `GEMINI_API_KEY` variable in `app.py` directly.

### 3. Run the FastAPI Backend

```bash
# Run with uvicorn
python app.py

# Or use uvicorn directly
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- Main API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 4. Run the Frontend

Make sure the frontend is configured to connect to the backend at `http://localhost:8000`.

```bash
npm install
npm run dev
```

## API Endpoints

### POST /upload_files
Upload C/C++ source and header files.

### POST /generate_tests  
Generate unit tests using Gemini AI.

**Request Body:**
```json
{
  "files": [
    {
      "filename": "example.c",
      "content": "source code content",
      "size": 1234
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Test cases generated successfully",
  "data": {
    "test_cases": [...],
    "test_runner_script": "...",
    "makefile_content": "...",
    "summary": {...}
  }
}
```

### GET /health
Health check endpoint.

## Project Structure

```
├── app.py                 # Main FastAPI application
├── backend/
│   └── generateUnitTest.py # Original test generation logic
├── uploads/               # Uploaded files directory
├── requirements.txt       # Python dependencies
└── README_backend.md     # This file
```

## Troubleshooting

1. **CORS Issues**: Make sure the frontend URL is added to the `allow_origins` list in `app.py`

2. **API Key Issues**: Verify your Gemini API key is valid and has sufficient quota

3. **File Upload Issues**: Ensure uploaded files are valid C/C++ source files

4. **Import Errors**: Make sure all dependencies are installed with `pip install -r requirements.txt`