from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import google.generativeai as genai
import os
import json
import re
from typing import List, Dict, Any

app = FastAPI(title="UnitTestGen AI Backend")

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini AI
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "your-api-key-here")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Directory paths
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class TestGenerationService:
    @staticmethod
    def get_unit_test_prompt(source_code: str, headers: List[str]) -> str:
        """Generate specialized prompt for unit test generation"""
        return f"""
Generate comprehensive unit tests for the following C source code using Unity testing framework.

Source Code:
{source_code}

Header Files:
{chr(10).join(headers)}

Requirements:
1. Generate complete unit test cases covering:
   - Normal functionality
   - Edge cases  
   - Error conditions
   - Boundary value testing

2. Format the response as JSON with the following structure:

{{
    "test_cases": [
        {{
            "id": "TC_001",
            "function_name": "test_function_name",
            "description": "Test description",
            "input_data": "Input parameters",
            "expected_output": "Expected outcome",
            "type": "Positive/Negative",
            "test_code": "Complete C test function code"
        }}
    ],
    "test_runner_script": "Complete test_runner.c content",
    "makefile_content": "Complete Makefile content", 
    "summary": {{
        "total_tests": 0,
        "functions_tested": [],
        "coverage_areas": []
    }}
}}

Ensure all generated code follows Unity framework conventions.
"""

@app.post("/upload_files")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload source and header files"""
    try:
        uploaded_files = []
        
        for file in files:
            # Validate file type
            if not file.filename.endswith(('.c', '.h', '.cpp', '.hpp')):
                raise HTTPException(status_code=400, detail=f"Invalid file type: {file.filename}")
            
            # Read file content
            content = await file.read()
            
            uploaded_files.append({
                "filename": file.filename,
                "content": content.decode('utf-8'),
                "size": len(content)
            })
        
        return JSONResponse({
            "status": "success",
            "message": f"Uploaded {len(uploaded_files)} files successfully",
            "files": uploaded_files
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.post("/generate_tests")
async def generate_tests(request_data: Dict[str, Any]):
    """Generate unit test cases using Gemini AI"""
    try:
        files = request_data.get("files", [])
        
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Separate source files and headers
        source_content = ""
        header_contents = []
        
        for file_info in files:
            filename = file_info.get("filename", "")
            content = file_info.get("content", "")
            
            if filename.endswith(('.c', '.cpp')):
                source_content += f"// File: {filename}\n{content}\n\n"
            elif filename.endswith(('.h', '.hpp')):
                header_contents.append(f"// Header: {filename}\n{content}")
        
        # Generate prompt and send to Gemini
        prompt = TestGenerationService.get_unit_test_prompt(source_content, header_contents)
        
        response = model.generate_content(prompt)
        ai_response = response.text
        
        # Parse JSON response from Gemini
        try:
            # Extract JSON from response (handle markdown formatting)
            json_match = re.search(r'```json\n(.*?)\n```', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON in the response
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    json_str = ai_response[json_start:json_end]
                else:
                    json_str = ai_response
            
            parsed_response = json.loads(json_str)
            
            return JSONResponse({
                "status": "success",
                "message": "Test cases generated successfully",
                "data": parsed_response
            })
            
        except json.JSONDecodeError as e:
            return JSONResponse({
                "status": "partial_success", 
                "message": "Generated response but failed to parse JSON",
                "raw_response": ai_response,
                "error": str(e)
            })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "UnitTestGen AI Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)