from openai import OpenAI
import json
import openai

SYSTEM_PROMPT = """
You are a strict data extraction engine.

First, validate if the input follows the expected format. If it doesn't, respond with exactly:
{"error": "Invalid input provided"}

The input may contain data for **multiple classes**, each separated by blank lines or newlines.
You MUST output a **JSON array** where each element is a class report object (following the schema below).
If only one class is present, output an array with one element.

--------------------------------------------------
CLASS PARSING RULES (per class)
--------------------------------------------------
- class.name: extract the class level only (SS1, SS2, SS3, JSS1, JSS2, JSS3). Remove the final letter.
  Example: "SS2F" -> "SS2"
- class.group: the final letter (A, B, C, etc.). Example: "SS2F" -> "F"
- class.term: normalise to lowercase: "first", "second", "third".

--------------------------------------------------
SUBJECT MAPPING RULES (per class)
--------------------------------------------------
The number before the subject name (1., 2., 3., etc) is NOT the subject_id.
Ignore those numbers.

You MUST use the following exact subject mapping table.
Match the subject name from the input to the "name" field (case‑insensitive) or the "potential_abbreviation".
If a subject has multiple winners (e.g., "Student A, Student B & Student C"), create a separate entry for each student with the same subject_id.

SUBJECT DATABASE (id, name, potential_abbreviation):
1, English, Eng
2, Mathematics, Maths
3, Christian Religious Knowledge, CRS
4, Co-Curricular Activities, CCA
5, Basic Science, Basic Sci
6, Basic Technology, Basic Tech
7, Catering And Craft Practices, CCP
8, Creative Arts, CCA
9, Civic Education, Civic Edu
10, Financial Accounting, Fin Acc
11, Government, Govt
12, Agriculture, Agric
13, Chemistry, Chem
14, Biology, Bio
15, Physics, Phy
16, Geography, Geo
17, Economics, Econs
18, Marketing, Mktng
19, Data Processing, Data Proc
20, Moral Instruction, Moral Instruct
21, Literature In English, Lit In Eng
22, Pre-Vocational Studies, Pre-Voc
23, National Values, Nat-Val
24, Igbo, igbo
25, Pre-vocational study, pvs

IMPORTANT EXAMPLES:
- Input "Igbo" → subject_id 24, name "Igbo"
- Input "Moral" → subject_id 20, name "Moral Instruction"
- Input "CRS" → subject_id 3, name "Christian Religious Knowledge"
- Input "PVS" → subject_id 25, name "Pre-vocational study"

Never invent subject_ids. Always use the ids from the table above.

--------------------------------------------------
TOP STUDENTS
--------------------------------------------------
Extract first, second, third positions with name and average.
If average is not explicitly given, set average = 0.

--------------------------------------------------
MOST IMPROVED
--------------------------------------------------
If present, keep the improvement text exactly as written.
If not present, return an empty list.

--------------------------------------------------
OUTPUT FORMAT
--------------------------------------------------
Return a JSON object with a single key "reports" whose value is an array of class report objects.
Each class report object follows this schema:

{
  "class": {"name": "...", "group": "...", "term": "..."},
  "top_students": {
    "first": {"name": "...", "average": number},
    "second": {"name": "...", "average": number},
    "third": {"name": "...", "average": number}
  },
  "top_students_in_subjects": [
    {"subject_id": number, "name": "...", "score": number}
  ],
  "most_improved_students": [
    {"name": "...", "improvement": "..."}
  ]
}

No extra fields.
"""

def validate_extracted_data(data):
    # If the model returned an "error", raise immediately
    if isinstance(data, dict) and "error" in data:
        raise ValueError(data["error"])

    # Now data must be a list
    if not isinstance(data, list):
        raise ValueError("Invalid input provided")

    for idx, item in enumerate(data):
        # Check top-level keys
        required_fields = ["class", "top_students", "top_students_in_subjects", "most_improved_students"]
        if not all(field in item for field in required_fields):
            raise ValueError(f"Invalid input provided at class index {idx}")

        # Validate "class" structure
        cls = item.get("class", {})
        if cls.get("name") not in ["SS1","SS2","SS3","JSS1","JSS2","JSS3"]:
            raise ValueError(f"Invalid class name at index {idx}")
        if not cls.get("group") or not cls["group"].isalpha() or len(cls["group"]) != 1:
            raise ValueError(f"Invalid class group at index {idx}")
        if cls.get("term") not in ["first", "second", "third"]:
            raise ValueError(f"Invalid term at index {idx}")

        # Validate top_students averages
        top_students = item.get("top_students", {})
        for pos in ["first", "second", "third"]:
            student = top_students.get(pos, {})
            if "name" not in student or not isinstance(student.get("average"), (int, float)):
                raise ValueError(f"Invalid top_students at index {idx}")

        # Validate top_students_in_subjects
        subjects = item.get("top_students_in_subjects", [])
        if not isinstance(subjects, list) or any("subject_id" not in s or "name" not in s or "score" not in s for s in subjects):
            raise ValueError(f"Invalid top_students_in_subjects at index {idx}")

        # Validate most_improved_students
        improved = item.get("most_improved_students", [])
        if not isinstance(improved, list) or any("name" not in s or "improvement" not in s for s in improved):
            raise ValueError(f"Invalid most_improved_students at index {idx}")

    return True

def is_valid_raw_input(user_input):
    required_keywords = [
        "Report",
        "position",
        "BEST IN SUBJECTS",
        # "MOST IMPROVED"
    ]
    # If any keyword is missing, input is invalid
    return all(keyword in user_input for keyword in required_keywords)

def format_user_input(user_input, api_key):
    # print(user_input)

    if not is_valid_raw_input(user_input):
        return {
            "error": "Invalid input provided",
            "error_type": "validation"
        }
    
    try:
        client = OpenAI(api_key=api_key)
        
        response = client.responses.create(
            model="gpt-4.1-mini",
            temperature=0,
            input=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ],
            tools=[
                {
                    "type": "file_search",
                    "vector_store_ids": ["vs_69b71909d7688191b0b61a7e41035bb9"],
                    "max_num_results": 10
                }
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "class_report_array",
                    "schema": {
                        "type": "object",
                         "additionalProperties": False,
                        "properties": {
                            "reports": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                "class": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                    "name": {"type": "string"},
                                    "group": {"type": "string", "pattern": "^[A-Z]$"},
                                    "term": {"type": "string", "enum": ["first", "second", "third"]}
                                    },
                                    "required": ["name", "group", "term"]
                                },
                                "top_students": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                    "first": {"$ref": "#/$defs/student"},
                                    "second": {"$ref": "#/$defs/student"},
                                    "third": {"$ref": "#/$defs/student"}
                                    },
                                    "required": ["first", "second", "third"]
                                },
                                "top_students_in_subjects": {
                                    "type": "array",
                                    "items": {"$ref": "#/$defs/subject_student"}
                                },
                                "most_improved_students": {
                                    "type": "array",
                                    "items": {"$ref": "#/$defs/improved_student"}
                                }
                                },
                                "required": [
                                "class",
                                "top_students",
                                "top_students_in_subjects",
                                "most_improved_students"
                                ]
                            }
                            }
                        },
                        "required": ["reports"],
                        "$defs": {
                            "student": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "name": {"type": "string"},
                                "average": {"type": "number"}
                            },
                            "required": ["name", "average"]
                            },
                            "subject_student": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "subject_id": {"type": "integer"},
                                "name": {"type": "string"},
                                "score": {"type": "number"}
                            },
                            "required": ["subject_id", "name", "score"]
                            },
                            "improved_student": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "name": {"type": "string"},
                                "improvement": {"type": "string"}
                            },
                            "required": ["name", "improvement"]
                            }
                        }
                    }
                }
            }
        )

        data = json.loads(response.output_text)

        # try:
        #     validate_extracted_data(data)
        # except ValueError:
        #     # If validation fails, force the error object
        #     return {
        #         "error": "Invalid input provided",
        #         "error_type": "validation"
        #     }

        print(json.dumps(data, indent=4))
        # time.sleep(1000)
        return {"data": data}
        
    except openai.APIConnectionError as e:
        # Network error - can't connect to OpenAI
        print(f"Network error: {e}")
        return {
            "error": "Network error: Could not connect to OpenAI. Please check your internet connection.",
            "error_type": "network"
        }
    
    except openai.RateLimitError as e:
        # Rate limit exceeded
        print(f"Rate limit error: {e}")
        return {
            "error": "Rate limit exceeded. Please wait a moment and try again.",
            "error_type": "rate_limit"
        }
    
    except openai.APIStatusError as e:
        # API returned an error status (4xx or 5xx)
        print(f"API status error: {e}")
        status_code = e.status_code
        if status_code == 401:
            return {
                "error": "Authentication error: Invalid API key. Please check your OpenAI API key in config.json.",
                "error_type": "auth"
            }
        elif status_code == 429:
            return {
                "error": "Quota exceeded: You have exceeded your OpenAI API quota. Please check your billing details.",
                "error_type": "quota"
            }
        elif status_code == 500:
            return {
                "error": "OpenAI server error. Please try again later.",
                "error_type": "server"
            }
        else:
            return {
                "error": f"OpenAI API error (HTTP {status_code}): {str(e)}",
                "error_type": "api_error"
            }
    
    except openai.APITimeoutError as e:
        # Request timed out
        print(f"Timeout error: {e}")
        return {
            "error": "Request timed out. Please try again.",
            "error_type": "timeout"
        }
    
    except Exception as e:
        # Any other unexpected error
        print(f"Unexpected error: {e}")
        return {
            "error": f"An unexpected error occurred: {str(e)}",
            "error_type": "general"
        }