from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import json
import tempfile
import csv
import io
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

app = FastAPI(
    title="UnitTestGen AI Backend",
    description="AI-powered unit test generation for C/C++ code using Gemini AI",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8081", "http://127.0.0.1:5173", "http://127.0.0.1:3000", "http://127.0.0.1:8081", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory paths
UPLOAD_DIR = "uploads"
TEMP_DIR = "temp_files"
OUTPUT_DIR = "generated_tests"

# Ensure directories exist
for directory in [UPLOAD_DIR, TEMP_DIR, OUTPUT_DIR]:
    os.makedirs(directory, exist_ok=True)

class TestGenerationService:
    @staticmethod
    def call_gemini_with_content(source_code: str, headers: List[str], model_name: str = "gemini-2.5-pro") -> str:
        """Call Gemini AI with file contents instead of file paths"""
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
            
            if not temp_files:
                raise ValueError("No valid source code or header files provided")
            
            # Call the original call_gemini function
            response = call_gemini(temp_files, model_name)
            return response
            
        finally:
            # Clean up temp files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass
    
    @staticmethod
    def parse_gemini_response(response_text: str) -> Dict[str, Any]:
        """Parse Gemini response using the existing parsing logic"""
        if not response_text.strip():
            return {
                "test_cases": [],
                "test_runner_script": "",
                "makefile_content": "",
                "summary": {
                    "total_tests": 0,
                    "functions_tested": [],
                    "coverage_areas": []
                },
                "raw_response": response_text
            }
        
        # First try to extract JSON block
        json_obj = try_extract_json_block(response_text)
        
        if json_obj and "table_rows" in json_obj:
            # Convert table_rows to test_cases format
            test_cases = []
            for i, row in enumerate(json_obj.get("table_rows", [])):
                test_case = {
                    "id": row.get("Test Case ID", f"TC_{i+1:03d}"),
                    "function_name": row.get("Unit Test Function Name", ""),
                    "description": row.get("Description", ""),
                    "input_data": row.get("Input Data", ""),
                    "expected_output": row.get("Expected Output / Behavior", ""),
                    "type": row.get("Type (Positive / Negative)", ""),
                    "test_code": json_obj.get("test_script_c", "")
                }
                test_cases.append(test_case)
            
            return {
                "test_cases": test_cases,
                "test_runner_script": json_obj.get("test_runner_c", ""),
                "test_script": json_obj.get("test_script_c", ""),
                "makefile_content": json_obj.get("makefile_content", ""),
                "summary": {
                    "total_tests": len(test_cases),
                    "functions_tested": list(set(tc["function_name"] for tc in test_cases if tc["function_name"])),
                    "coverage_areas": ["Statement", "Branch", "Condition", "Boundary", "Error Path"]
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
            "test_script": c_code_blocks[0] if c_code_blocks else "",
            "makefile_content": "",
            "summary": {
                "total_tests": len(test_cases),
                "functions_tested": list(set(tc["function_name"] for tc in test_cases if tc["function_name"])),
                "coverage_areas": ["Statement", "Branch", "Condition", "Boundary", "Error Path"]
            },
            "raw_response": response_text
        }

    @staticmethod
    def generate_csv_content(test_cases: List[Dict[str, Any]]) -> str:
        """Generate CSV content from test cases"""
        if not test_cases:
            return ""
        
        output = io.StringIO()
        fieldnames = ["Test Case ID", "Description", "Input Data", "Expected Output / Behavior", "Type (Positive / Negative)", "Unit Test Function Name"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        for test_case in test_cases:
            writer.writerow({
                "Test Case ID": test_case.get("id", ""),
                "Description": test_case.get("description", ""),
                "Input Data": test_case.get("input_data", ""),
                "Expected Output / Behavior": test_case.get("expected_output", ""),
                "Type (Positive / Negative)": test_case.get("type", ""),
                "Unit Test Function Name": test_case.get("function_name", "")
            })
        
        return output.getvalue()
    
    @staticmethod
    def analyze_c_code_blocks(c_code_blocks: List[str]) -> Dict[str, Any]:
        """Analyze C code blocks and provide detailed information"""
        analysis = {
            "total_blocks": len(c_code_blocks),
            "blocks": [],
            "functions_found": [],
            "includes_found": [],
            "assertions_count": 0,
            "unity_framework_detected": False
        }
        
        for i, block in enumerate(c_code_blocks):
            block_analysis = {
                "index": i,
                "lines": len(block.split('\n')),
                "size": len(block),
                "type": "unknown",
                "functions": [],
                "includes": [],
                "assertions": 0,
                "has_main": False
            }
            
            # Find function definitions
            function_pattern = r'(?:void|int|char\*?|float|double)\s+(\w+)\s*\([^)]*\)\s*\{'
            functions = re.findall(function_pattern, block)
            block_analysis["functions"] = functions
            analysis["functions_found"].extend(functions)
            
            # Find includes
            include_pattern = r'#include\s*[<"]([^>"]+)[>"]'
            includes = re.findall(include_pattern, block)
            block_analysis["includes"] = includes
            analysis["includes_found"].extend(includes)
            
            # Count assertions
            assertions = len(re.findall(r'TEST_ASSERT|assert\(', block))
            block_analysis["assertions"] = assertions
            analysis["assertions_count"] += assertions
            
            # Check for main function
            block_analysis["has_main"] = 'main(' in block
            
            # Check for Unity framework
            if any(unity_keyword in block for unity_keyword in ['UNITY_BEGIN', 'UNITY_END', 'RUN_TEST', 'TEST_ASSERT']):
                analysis["unity_framework_detected"] = True
            
            # Determine block type
            if "TEST_ASSERT" in block or "void test_" in block:
                block_analysis["type"] = "test_script"
            elif "main(" in block and ("RUN_TEST" in block or "UNITY_BEGIN" in block):
                block_analysis["type"] = "test_runner"
            elif "CC=" in block or "CFLAGS=" in block or "all:" in block:
                block_analysis["type"] = "makefile"
            elif "#include" in block and len(functions) > 0:
                block_analysis["type"] = "source_code"
            
            analysis["blocks"].append(block_analysis)
        
        # Remove duplicates and sort
        analysis["functions_found"] = sorted(list(set(analysis["functions_found"])))
        analysis["includes_found"] = sorted(list(set(analysis["includes_found"])))
        
        return analysis

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "UnitTestGen AI Backend",
        "version": "1.0.0",
        "description": "AI-powered unit test generation for C/C++ code",
        "endpoints": {
            "upload_files": "POST /upload_files - Upload source and header files",
            "generate_tests": "POST /generate_tests - Generate unit tests from uploaded files",
            "health": "GET /health - Health check endpoint",
            "docs": "GET /docs - API documentation"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check if required environment variables are set
    api_key = os.getenv("GOOGLE_API_KEY")
    vertex_project = os.getenv("GOOGLE_CLOUD_PROJECT")
    
    status = {
        "status": "healthy",
        "service": "UnitTestGen AI Backend",
        "version": "1.0.0",
        "gemini_configured": bool(api_key or vertex_project),
        "directories": {
            "uploads": os.path.exists(UPLOAD_DIR),
            "temp": os.path.exists(TEMP_DIR),
            "output": os.path.exists(OUTPUT_DIR)
        }
    }
    
    if not (api_key or vertex_project):
        status["warning"] = "GOOGLE_API_KEY or Vertex AI credentials not configured"
    
    return status

@app.post("/upload_files")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload source and header files"""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        uploaded_files = []
        supported_extensions = {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hh', '.hxx'}
        
        for file in files:
            if not file.filename:
                continue
            
            # Get file extension
            file_ext = os.path.splitext(file.filename.lower())[1]
            
            # Validate file type
            if file_ext not in supported_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file type: {file.filename}. Supported types: {', '.join(supported_extensions)}"
                )
            
            # Read file content
            try:
                content_bytes = await file.read()
                content = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content = content_bytes.decode('latin-1')
                except UnicodeDecodeError:
                    raise HTTPException(status_code=400, detail=f"Could not decode file: {file.filename}")
            
            uploaded_files.append({
                "filename": file.filename,
                "content": content,
                "size": len(content_bytes),
                "type": "source" if file_ext in {'.c', '.cpp', '.cc', '.cxx'} else "header"
            })
        
        if not uploaded_files:
            raise HTTPException(status_code=400, detail="No valid files uploaded")
        
        return JSONResponse({
            "status": "success",
            "message": f"Uploaded {len(uploaded_files)} files successfully",
            "files": uploaded_files,
            "summary": {
                "total_files": len(uploaded_files),
                "source_files": len([f for f in uploaded_files if f["type"] == "source"]),
                "header_files": len([f for f in uploaded_files if f["type"] == "header"])
            }
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.post("/generate_tests")
async def generate_tests(request_data: Dict[str, Any]):
    """Generate unit test cases using Gemini AI with robust parsing"""
    try:
        # Validate request data
        files = request_data.get("files", [])
        model = request_data.get("model", "gemini-2.5-pro")
        
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Separate source files and headers
        source_content = ""
        header_contents = []
        
        for file_info in files:
            filename = file_info.get("filename", "")
            content = file_info.get("content", "")
            
            if not content.strip():
                continue
            
            if filename.lower().endswith(('.c', '.cpp', '.cc', '.cxx')):
                source_content += f"// File: {filename}\n{content}\n\n"
            elif filename.lower().endswith(('.h', '.hpp', '.hh', '.hxx')):
                header_contents.append(f"// Header: {filename}\n{content}")
        
        if not source_content.strip():
            raise HTTPException(status_code=400, detail="No valid source code found in uploaded files")
        
        # Call Gemini AI
        try:
            ai_response = TestGenerationService.call_gemini_with_content(
                source_content, 
                header_contents, 
                model
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gemini AI call failed: {str(e)}")
        
        if not ai_response or not ai_response.strip():
            raise HTTPException(status_code=500, detail="Empty response from Gemini AI")
        
        # Parse the response using the robust parsing logic
        try:
            parsed_data = TestGenerationService.parse_gemini_response(ai_response)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse Gemini response: {str(e)}")
        
        # Generate CSV content
        csv_content = TestGenerationService.generate_csv_content(parsed_data["test_cases"])
        parsed_data["csv_content"] = csv_content
        
        return JSONResponse({
            "status": "success",
            "message": "Test cases generated successfully",
            "data": parsed_data,
            "metadata": {
                "model_used": model,
                "files_processed": len(files),
                "response_length": len(ai_response)
            }
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Unit Test Generator Backend...")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🏥 Health Check: http://localhost:8000/health")
    print("⚡ Server URL: http://localhost:8000")
    print("🔧 Using Vertex AI with project: rock-range-464908-g5")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)