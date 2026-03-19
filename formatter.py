from openai import OpenAI
import json
import openai

def validate_extracted_data(data):
    # If the model returned an "error", raise immediately
    if isinstance(data, dict) and "error" in data:
        raise ValueError(data["error"])

    # Check top-level keys
    required_fields = ["class", "top_students", "top_students_in_subjects", "most_improved_students"]
    if not all(field in data for field in required_fields):
        raise ValueError("Invalid input provided")

    # Validate "class" structure
    cls = data.get("class", {})
    if cls.get("name") not in ["SS1","SS2","SS3","JSS1","JSS2","JSS3"]:
        raise ValueError("Invalid input provided")
    if not cls.get("group") or not cls["group"].isalpha() or len(cls["group"]) != 1:
        raise ValueError("Invalid input provided")
    if cls.get("term") not in ["first", "second", "third"]:
        raise ValueError("Invalid input provided")

    # Validate top_students averages
    top_students = data.get("top_students", {})
    for pos in ["first", "second", "third"]:
        student = top_students.get(pos, {})
        if "name" not in student or not isinstance(student["average"], (int, float)):
            raise ValueError("Invalid input provided")

    # Validate top_students_in_subjects
    subjects = data.get("top_students_in_subjects", [])
    if not isinstance(subjects, list) or any("subject_id" not in s or "name" not in s or "score" not in s for s in subjects):
        raise ValueError("Invalid input provided")

    # Validate most_improved_students
    improved = data.get("most_improved_students", [])
    if not isinstance(improved, list) or any("name" not in s or "improvement" not in s for s in improved):
        raise ValueError("Invalid input provided")

    return True

def is_valid_raw_input(user_input):
    required_keywords = [
        "Report",
        "position",
        "BEST IN SUBJECTS",
        "MOST IMPROVED"
    ]
    # If any keyword is missing, input is invalid
    return all(keyword in user_input for keyword in required_keywords)

def format_user_input(user_input, api_key):
    print(user_input)

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
                    "content": """
You are a strict data extraction engine.

First, validate if the input follows the expected format. If it doesn't, respond with exactly:
{"error": "Invalid input provided"}

Otherwise, extract the data according to the schema.

CLASS RULES
SS2F -> name = SS2, group = F

TERM RULES
First Term -> first, Second Term -> second, Third Term -> third

SUBJECT RULES
The number before the subject name (1., 2., 3., etc) is NOT the subject_id.
Those numbers only represent ranking in the text and must be ignored.

You MUST determine the correct subject_id by matching the subject name
to the SUBJECT DATABASE provided in the context files.

Examples:
English language -> subject_id 1
Mathematics -> subject_id 2
Civic Education -> subject_id 9
Economics -> subject_id 17
Data Processing -> subject_id 19
Marketing -> subject_id 18
C.C.P -> subject_id 7
Moral -> subject_id 20

Never generate sequential IDs.
Never copy the numbering from the input.

Return ONLY valid JSON following the schema.
"""
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
                    "name": "class_report",
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "class": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "name": {"type": "string"},
                                    "group": {
                                        "type": "string",
                                        "pattern": "^[A-Z]$"
                                    },
                                    "term": {
                                        "type": "string",
                                        "enum": ["first", "second", "third"]
                                    }
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
                        "required": ["class", "top_students", "top_students_in_subjects", "most_improved_students"],
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

        try:
            validate_extracted_data(data)
        except ValueError:
            # If validation fails, force the error object
            return {
                "error": "Invalid input provided",
                "error_type": "validation"
            }

        print(json.dumps(data, indent=4))
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