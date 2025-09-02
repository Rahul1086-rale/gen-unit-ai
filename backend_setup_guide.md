# UnitTestGen AI Backend Setup Guide

## Prerequisites

1. **Python 3.8+** installed on your system
2. **GCC compiler** and **MinGW** (for Windows)
3. **Unity testing framework** installed
4. **lcov** for coverage reports
5. **Gemini API Key** from Google AI Studio

## Installation Steps

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up Gemini API Key

1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Replace `"your-gemini-api-key-here"` in `backend_fastapi.py` with your actual API key

### 3. Install System Dependencies

#### On Windows (MinGW):
```bash
# Install MinGW-w64
# Install Unity framework
# Install lcov for Windows
```

#### On Linux/Mac:
```bash
sudo apt-get install gcc make lcov  # Ubuntu/Debian
# or
brew install gcc make lcov  # macOS
```

### 4. Directory Structure

The backend will create these directories automatically:
- `uploads/` - For uploaded source files
- `test_scripts/` - For generated test scripts
- `test_results/` - For test results and coverage reports

### 5. Run the Backend

```bash
python backend_fastapi.py
```

The server will start on `http://localhost:8000`

## API Endpoints

- `POST /upload_files` - Upload source and header files
- `POST /generate_test_cases` - Generate tests using Gemini AI
- `POST /get_excel` - Generate Excel report
- `POST /get_scripts` - Extract test scripts
- `POST /run_unit_test` - Run unit tests with make
- `GET /show_result` - Display results and coverage
- `GET /health` - Health check

## Configuration

### Gemini AI Settings
- Model: `gemini-1.5-flash` (can be changed in the code)
- Timeout: 300 seconds for test execution
- File size limits: Adjust as needed

### CORS Settings
- Currently allows all origins (`*`) - configure for production
- Modify in the `CORSMiddleware` section

## Usage Flow

1. Upload your C source files and headers
2. Generate test cases using AI
3. Extract scripts and Excel report
4. Run unit tests
5. View results and coverage reports

## Troubleshooting

- Ensure all system dependencies are properly installed
- Check that your Gemini API key is valid
- Verify file permissions for upload directories
- Check that MinGW/GCC is in your system PATH