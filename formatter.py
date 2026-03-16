from openai import OpenAI
import json

def format_user_input(user_input, api_key):

    client = OpenAI(
        api_key = api_key
    )
    
    response = client.responses.create(
        model="gpt-4.1-mini",
        temperature=0,
        input=[
            {
                "role": "system",
                "content": """
            You are a strict data extraction engine.

            Follow these rules carefully.

            CLASS RULES
            SS2F -> name = SS2
            SS2F -> group = F

            TERM RULES
            First Term -> first
            Second Term -> second
            Third Term -> third

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

            Return ONLY valid JSON.
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
    return data