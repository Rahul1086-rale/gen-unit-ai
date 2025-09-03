#!/usr/bin/env python3
"""
gemini_ut_generator.py

Upload C sources/headers + a structured prompt to Gemini (Google GenAI),
retrieve response, parse table + code, and save artifacts.

Outputs:
  - test_cases.csv
  - test_script.c
  - test_runner.c

Requirements:
  pip install google-cloud-aiplatform
  pip install google-genai   # optional fallback

Environment:
  export GOOGLE_API_KEY="YOUR_KEY"
  or ensure ADC (Application Default Credentials) is configured for Vertex AI.
"""

import os
import sys
import json
import re
import argparse
from typing import List, Dict, Any, Tuple, Optional

# -----------------------------------------------------------------------------
# Structured Prompt
# -----------------------------------------------------------------------------
USER_PROMPT_JSON = {
    "role": "You are an expert C developer and software tester with deep knowledge of unit testing, code coverage methodologies, and C testing frameworks.",
    "rules": [
        "Analyze the uploaded C code including header files thoroughly before generating test cases.",
        "Ensure 100% coverage across: Statement Coverage, Branch Coverage, Condition Coverage, Boundary Value Coverage, Error Path Coverage, Data Flow Coverage.",
        "Ensure that all loops are fully covered, including zero-iteration, single-iteration, and multiple-iteration cases.",
        "Include both positive and negative test scenarios.",
        "Every line of code must be covered by at least one test case.",
        "Keep explanations clear, concise, and structured.",
        "Each unit test must be explicitly mapped from the test case table to the generated C test function."
    ],
    "task": [
        "Identify all functions, input parameters, return values, and expected behavior of the uploaded C code.",
        "identify all the definations present in header files. use that functions instead of writing mock/stubs",
        "Use unity framework for test",
        "Generate comprehensive unit test cases that fully cover the code according to the rules above.",
        "Provide meaningful descriptions for each test case so they can be implemented in a unit testing framework.",
        "Write a test script in C that implements the generated test cases.",
        "Write a test_runner script which can run this test script."
    ],
    "output_format": {
        "parts": [
            {
                "type": "table",
                "columns": [
                    "Test Case ID",
                    "Description",
                    "Input Data",
                    "Expected Output / Behavior",
                    "Type (Positive / Negative)",
                    "Unit Test Function Name"
                ]
            },
            {
                "type": "code",
                "language": "c",
                "description": "Provide a C test script implementing the generated test cases. Wrap the code inside triple backticks with 'c' for easy parsing. Each function in the script must match the 'Unit Test Function Name' from the table.",
                "format": "c\n// C test script here\n"
            }
        ]
    },
    "note": "Ensure that the unit tests cover each line of code and achieve full coverage across all statements, branches, conditions, and loops."
}

JSON_MIRROR_INSTRUCTION = """
Additionally, provide a JSON mirror of your answer with this exact schema:

{
  "table_rows": [
    {
      "Test Case ID": "...",
      "Description": "...",
      "Input Data": "...",
      "Expected Output / Behavior": "...",
      "Type (Positive / Negative)": "...",
      "Unit Test Function Name": "..."
    }
  ],
  "test_script_c": "/* full C test script here (Unity-based) */",
  "test_runner_c": "/* full C test runner here that compiles and executes the test script */"
}

Keep your normal (human-friendly) output too (markdown table + ```c code blocks),
but always include the JSON block as the last section so tools can parse it.
"""

# -----------------------------------------------------------------------------
# Parsing Helpers
# -----------------------------------------------------------------------------
def try_extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    last_brace = text.rfind('{')
    if last_brace == -1:
        return None
    candidate = text[last_brace:]
    candidate = candidate.strip().rstrip('`').strip()
    try:
        return json.loads(candidate)
    except Exception:
        fenced = re.findall(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
        for block in reversed(fenced):
            try:
                return json.loads(block)
            except Exception:
                continue
    return None

def parse_markdown_table(md: str) -> List[Dict[str, str]]:
    lines = md.splitlines()
    table_lines = []
    for i, line in enumerate(lines):
        if '|' in line and re.search(r'\|\s*-+\s*\|', line):
            if i > 0 and '|' in lines[i-1]:
                table_lines = [lines[i-1], line]
                for j in range(i+1, len(lines)):
                    if '|' in lines[j]:
                        table_lines.append(lines[j])
                    else:
                        break
                break
    if not table_lines:
        return []

    def split_row(row: str) -> List[str]:
        return [c.strip() for c in row.strip().strip('|').split('|')]

    header = split_row(table_lines[0])
    rows = []
    for r in table_lines[2:]:
        cells = split_row(r)
        if len(cells) < len(header):
            cells += [''] * (len(header) - len(cells))
        rows.append({header[i]: cells[i] for i in range(len(header))})
    return rows

def extract_c_code_blocks(text: str) -> List[str]:
    return re.findall(r"```c\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)

# -----------------------------------------------------------------------------
# I/O Helpers
# -----------------------------------------------------------------------------
def write_csv(rows: List[Dict[str, str]], path: str) -> None:
    if not rows:
        open(path, 'w').close()
        return
    cols = list(rows[0].keys())
    with open(path, 'w', encoding='utf-8') as f:
        f.write(','.join([json.dumps(c) for c in cols]) + '\n')
        for r in rows:
            f.write(','.join([json.dumps(str(r.get(c, ""))) for c in cols]) + '\n')

def save_text(path: str, content: str) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# -----------------------------------------------------------------------------
# Gemini Call (Vertex AI first, fallback to google-genai)
# -----------------------------------------------------------------------------
def call_gemini(files: List[str], model: str) -> str:
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel

        vertexai.init(project=os.getenv("rock-range-464908-g5"), location="global")
        model_obj = GenerativeModel(model)

        # Upload not yet directly supported in vertexai; we just read content
        # and pass as text + filenames inline.
        file_contents = []
        for f in files:
            with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
                code = fh.read()
            file_contents.append(f"\n===== FILE: {os.path.basename(f)} =====\n{code}\n")

        system_preamble = (
            "System: You are a meticulous senior C developer and testing expert. "
            "Follow the user's rules and tasks exactly. "
            "Return both human-friendly output (table + code fences) AND the JSON mirror."
        )
        payload = system_preamble + "\n\nUSER_PROMPT:\n" + json.dumps(USER_PROMPT_JSON, indent=2) \
                  + "\n\n" + JSON_MIRROR_INSTRUCTION + "\n\nFILES:\n" + "\n".join(file_contents)

        resp = model_obj.generate_content([payload])
        return resp.text if hasattr(resp, "text") else ""
    except Exception as e_vertex:
        try:
            from google import genai
            client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            uploaded = [client.files.upload(file=f) for f in files]

            payload = json.dumps(USER_PROMPT_JSON, indent=2) + "\n\n" + JSON_MIRROR_INSTRUCTION
            resp = client.responses.create(
                model=model,
                contents=[*uploaded, payload],
            )
            return resp.text if hasattr(resp, "text") else ""
        except Exception as e_genai:
            raise RuntimeError(f"Gemini call failed.\nVertex error: {e_vertex}\nGenAI error: {e_genai}")

# -----------------------------------------------------------------------------
# Main Parsing + Saving
# -----------------------------------------------------------------------------
def parse_and_save(response_text: str, out_dir: str) -> Tuple[str, str, str]:
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, "test_cases.csv")
    test_c_path = os.path.join(out_dir, "test_script.c")
    runner_c_path = os.path.join(out_dir, "test_runner.c")

    json_obj = try_extract_json_block(response_text)
    if json_obj:
        rows = json_obj.get("table_rows", [])
        if rows:
            write_csv(rows, csv_path)
        test_code = json_obj.get("test_script_c", "")
        runner_code = json_obj.get("test_runner_c", "")
        if test_code:
            save_text(test_c_path, test_code)
        if runner_code:
            save_text(runner_c_path, runner_code)

    if not os.path.exists(test_c_path) or os.path.getsize(test_c_path) == 0:
        blocks = extract_c_code_blocks(response_text)
        if blocks:
            save_text(test_c_path, blocks[0])
            if len(blocks) > 1:
                save_text(runner_c_path, blocks[1])

    if os.path.getsize(csv_path) == 0:
        rows = parse_markdown_table(response_text)
        if rows:
            write_csv(rows, csv_path)

    return csv_path, test_c_path, runner_c_path

# -----------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Generate C unit tests with Gemini.")
    parser.add_argument("--files", nargs="+", required=True, help="C source/header files")
    parser.add_argument("--model", default="gemini-2.5-pro", help="Gemini model name")
    parser.add_argument("--out-dir", default="gemini_ut_output", help="Output directory")
    args = parser.parse_args()

    print("Calling Gemini...")
    raw_text = call_gemini(args.files, args.model)
    if not raw_text:
        print("No text returned from Gemini", file=sys.stderr)
        sys.exit(1)

    print("Parsing + saving outputs...")
    csv_path, test_c_path, runner_c_path = parse_and_save(raw_text, args.out_dir)

    print(f"\nGenerated artifacts in {args.out_dir}:")
    print(f"- {csv_path}")
    print(f"- {test_c_path}")
    print(f"- {runner_c_path}")

if __name__ == "__main__":
    main()
