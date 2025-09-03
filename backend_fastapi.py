from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import google.generativeai as genai
import os
import shutil
import subprocess
import json
import pandas as pd
from typing import List, Dict, Any
import tempfile
import re
from pathlib import Path

app = FastAPI(title="UnitTestGen AI Backend")

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini AI
GEMINI_API_KEY = "your-gemini-api-key-here"  # Replace with your actual API key
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

# Directory paths
UPLOAD_DIR = "uploads"
SCRIPTS_DIR = "test_scripts"
RESULTS_DIR = "test_results"

# Create directories if they don't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SCRIPTS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

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

2. Create test runner script
3. Create makefile for compilation
4. Format the response as JSON with the following structure:

{{
    "test_cases": [
        {{
            "function_name": "test_function_name",
            "description": "Test description",
            "test_code": "Complete C test function code",
            "expected_result": "Expected outcome"
        }}
    ],
    "test_runner_script": "Complete test_runner.c content",
    "makefile_content": "Complete Makefile content",
    "test_summary": {{
        "total_tests": 0,
        "functions_tested": [],
        "coverage_areas": []
    }}
}}

Ensure all generated code is syntactically correct and follows Unity framework conventions.
"""

@app.post("/upload_files")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload source and header files"""
    try:
        uploaded_files = []
        
        for file in files:
            # Save uploaded file
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            uploaded_files.append({
                "filename": file.filename,
                "size": os.path.getsize(file_path),
                "path": file_path
            })
        
        return JSONResponse({
            "status": "success",
            "message": f"Uploaded {len(uploaded_files)} files successfully",
            "files": uploaded_files
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.post("/generate_test_cases")
async def generate_test_cases(file_data: Dict[str, Any]):
    """Generate unit test cases using Gemini AI"""
    try:
        source_files = file_data.get("source_files", [])
        header_files = file_data.get("header_files", [])
        
        # Read source code content
        source_content = ""
        for source_file in source_files:
            file_path = os.path.join(UPLOAD_DIR, source_file)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    source_content += f"// File: {source_file}\n{f.read()}\n\n"
        
        # Read header files
        header_contents = []
        for header_file in header_files:
            file_path = os.path.join(UPLOAD_DIR, header_file)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    header_contents.append(f"// Header: {header_file}\n{f.read()}")
        
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
                json_str = ai_response
            
            parsed_response = json.loads(json_str)
            
            return JSONResponse({
                "status": "success",
                "message": "Test cases generated successfully",
                "data": parsed_response
            })
            
        except json.JSONDecodeError:
            return JSONResponse({
                "status": "partial_success",
                "message": "Generated response but failed to parse JSON",
                "raw_response": ai_response
            })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")

@app.post("/get_excel")
async def get_excel(test_data: Dict[str, Any]):
    """Generate Excel report from test cases"""
    try:
        test_cases = test_data.get("test_cases", [])
        
        # Create DataFrame
        df_data = []
        for i, test_case in enumerate(test_cases):
            df_data.append({
                "Test ID": f"TC_{i+1:03d}",
                "Function Name": test_case.get("function_name", ""),
                "Description": test_case.get("description", ""),
                "Expected Result": test_case.get("expected_result", ""),
                "Status": "Pending"
            })
        
        df = pd.DataFrame(df_data)
        
        # Save to Excel
        excel_path = os.path.join(RESULTS_DIR, "test_cases.xlsx")
        df.to_excel(excel_path, index=False)
        
        return JSONResponse({
            "status": "success",
            "message": "Excel file generated successfully",
            "file_path": excel_path,
            "download_url": f"/download/excel/{os.path.basename(excel_path)}"
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel generation failed: {str(e)}")

@app.post("/get_scripts")
async def get_scripts(test_data: Dict[str, Any]):
    """Extract and save test scripts"""
    try:
        # Save test runner script
        test_runner_content = test_data.get("test_runner_script", "")
        test_runner_path = os.path.join(SCRIPTS_DIR, "test_runner.c")
        with open(test_runner_path, 'w') as f:
            f.write(test_runner_content)
        
        # Save makefile
        makefile_content = test_data.get("makefile_content", "")
        makefile_path = os.path.join(SCRIPTS_DIR, "Makefile")
        with open(makefile_path, 'w') as f:
            f.write(makefile_content)
        
        # Save individual test files
        test_files = []
        for i, test_case in enumerate(test_data.get("test_cases", [])):
            test_file_path = os.path.join(SCRIPTS_DIR, f"test_{i+1:03d}.c")
            with open(test_file_path, 'w') as f:
                f.write(test_case.get("test_code", ""))
            test_files.append(test_file_path)
        
        return JSONResponse({
            "status": "success",
            "message": "Scripts extracted and saved successfully",
            "files": {
                "test_runner": test_runner_path,
                "makefile": makefile_path,
                "test_files": test_files
            }
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script extraction failed: {str(e)}")

@app.post("/run_unit_test")
async def run_unit_test():
    """Run unit tests using make and display results"""
    try:
        # Change to scripts directory
        original_dir = os.getcwd()
        os.chdir(SCRIPTS_DIR)
        
        try:
            # Run make command
            result = subprocess.run(
                ["make", "test"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Check if tests passed or failed
            if result.returncode == 0:
                # Tests passed - generate coverage report
                coverage_result = subprocess.run(
                    ["lcov", "--capture", "--directory", ".", "--output-file", "coverage.info"],
                    capture_output=True,
                    text=True
                )
                
                html_result = subprocess.run(
                    ["genhtml", "coverage.info", "--output-directory", "../test_results/coverage_report"],
                    capture_output=True,
                    text=True
                )
                
                return JSONResponse({
                    "status": "success",
                    "message": "All tests passed successfully",
                    "test_output": result.stdout,
                    "coverage_generated": coverage_result.returncode == 0,
                    "coverage_report_path": "../test_results/coverage_report/index.html"
                })
            else:
                # Tests failed
                return JSONResponse({
                    "status": "failed",
                    "message": "Unit tests failed",
                    "test_output": result.stdout,
                    "error_output": result.stderr,
                    "return_code": result.returncode
                })
        
        finally:
            # Always return to original directory
            os.chdir(original_dir)
    
    except subprocess.TimeoutExpired:
        os.chdir(original_dir)
        raise HTTPException(status_code=408, detail="Test execution timed out")
    
    except Exception as e:
        os.chdir(original_dir)
        raise HTTPException(status_code=500, detail=f"Test execution failed: {str(e)}")

@app.get("/show_result")
async def show_result():
    """Display test results and coverage report"""
    try:
        results = {
            "test_results": {},
            "coverage_report": None,
            "files_generated": []
        }
        
        # Check for test output files
        test_output_file = os.path.join(SCRIPTS_DIR, "test_output.txt")
        if os.path.exists(test_output_file):
            with open(test_output_file, 'r') as f:
                results["test_results"]["output"] = f.read()
        
        # Check for coverage report
        coverage_index = os.path.join(RESULTS_DIR, "coverage_report", "index.html")
        if os.path.exists(coverage_index):
            results["coverage_report"] = f"/download/coverage/{os.path.basename(coverage_index)}"
        
        # List generated files
        for dir_path in [SCRIPTS_DIR, RESULTS_DIR]:
            if os.path.exists(dir_path):
                for file in os.listdir(dir_path):
                    results["files_generated"].append({
                        "name": file,
                        "path": os.path.join(dir_path, file),
                        "size": os.path.getsize(os.path.join(dir_path, file))
                    })
        
        return JSONResponse({
            "status": "success",
            "message": "Results retrieved successfully",
            "data": results
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve results: {str(e)}")

@app.get("/download/excel/{filename}")
async def download_excel(filename: str):
    """Download Excel file"""
    file_path = os.path.join(RESULTS_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/download/coverage/{filename}")
async def download_coverage(filename: str):
    """Download coverage report file"""
    file_path = os.path.join(RESULTS_DIR, "coverage_report", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "UnitTestGen AI Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)