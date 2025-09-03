from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import json
import tempfile
from typing import List, Dict, Any, Optional

# Import functions from generateUnitTest module
from generateUnitTest import (
    call_gemini,
    try_extract_json_block,
    parse_markdown_table,
    extract_c_code_blocks,
    USER_PROMPT_JSON,
    JSON_MIRROR_INSTRUCTION
)

app = FastAPI(title="UnitTestGen AI Backend")

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory paths
UPLOAD_DIR = "uploads"
TEMP_DIR = "temp_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

class TestGenerationService:
    @staticmethod
    def call_gemini_with_content(source_code: str, headers: List[str], model_name: str = "gemini-1.5-flash") -> str:
        """Call Gemini AI with file contents instead of file paths"""
        # Create temporary files for the call_gemini function
        temp_files = []
        
        try:
            # Create temp file for source code
            if source_code.strip():
                with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False, dir=TEMP_DIR) as f:
                    f.write(source_code)
                    temp_files.append(f.name)
            
            # Create temp files for headers
            for i, header_content in enumerate(headers):
                if header_content.strip():
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.h', delete=False, dir=TEMP_DIR) as f:
                        f.write(header_content)
                        temp_files.append(f.name)
            
            # Call the original call_gemini function
            response = call_gemini(temp_files, model_name)
            return response
            
        finally:
            # Clean up temp files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
    
    @staticmethod
    def parse_gemini_response(response_text: str) -> Dict[str, Any]:
        """Parse Gemini response using the existing parsing logic"""
        # First try to extract JSON block
        json_obj = try_extract_json_block(response_text)
        
        if json_obj and "table_rows" in json_obj:
            # Convert table_rows to test_cases format
            test_cases = []
            for row in json_obj.get("table_rows", []):
                test_case = {
                    "id": row.get("Test Case ID", ""),
                    "function_name": row.get("Unit Test Function Name", ""),
                    "description": row.get("Description", ""),
                    "input_data": row.get("Input Data", ""),
                    "expected_output": row.get("Expected Output / Behavior", ""),
                    "type": row.get("Type (Positive / Negative)", ""),
                    "test_code": ""  # Will be filled from test_script_c
                }
                test_cases.append(test_case)
            
            return {
                "test_cases": test_cases,
                "test_runner_script": json_obj.get("test_runner_c", ""),
                "makefile_content": json_obj.get("makefile_content", ""),
                "summary": {
                    "total_tests": len(test_cases),
                    "functions_tested": [tc["function_name"] for tc in test_cases],
                    "coverage_areas": []
                },
                "raw_response": response_text
            }
        
        # Fallback: parse markdown table and code blocks
        table_rows = parse_markdown_table(response_text)
        c_code_blocks = extract_c_code_blocks(response_text)
        
        test_cases = []
        for i, row in enumerate(table_rows):
            test_case = {
                "id": row.get("Test Case ID", f"TC_{i+1:03d}"),
                "function_name": row.get("Unit Test Function Name", ""),
                "description": row.get("Description", ""),
                "input_data": row.get("Input Data", ""),
                "expected_output": row.get("Expected Output / Behavior", ""),
                "type": row.get("Type (Positive / Negative)", ""),
                "test_code": c_code_blocks[0] if c_code_blocks else ""
            }
            test_cases.append(test_case)
        
        return {
            "test_cases": test_cases,
            "test_runner_script": c_code_blocks[1] if len(c_code_blocks) > 1 else "",
            "makefile_content": "",
            "summary": {
                "total_tests": len(test_cases),
                "functions_tested": [tc["function_name"] for tc in test_cases],
                "coverage_areas": []
            },
            "raw_response": response_text
        }

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
    """Generate unit test cases using Gemini AI with robust parsing"""
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
        
        # Use the robust Gemini calling function from generateUnitTest.py
        ai_response = TestGenerationService.call_gemini_with_content(
            source_content, 
            header_contents, 
            "gemini-1.5-flash"
        )
        
        if not ai_response:
            raise HTTPException(status_code=500, detail="No response from Gemini AI")
        
        # Parse the response using the robust parsing logic
        parsed_data = TestGenerationService.parse_gemini_response(ai_response)
        
        return JSONResponse({
            "status": "success",
            "message": "Test cases generated successfully",
            "data": parsed_data
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