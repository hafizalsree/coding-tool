import json
import os
from typing import Dict, Any
from tools_definition import ToolDefinition


class ReadFileInput:
    """Input schema for the read_file tool"""
    def __init__(self, path: str):
        self.path = path
    
    def to_dict(self) -> Dict[str, Any]:
        return {"path": self.path}


def generate_schema(input_class) -> Dict[str, Any]:
    """Generate schema for a given input class"""
    # For simplicity, we'll create a basic schema
    # In a real implementation, you might use a library like pydantic
    if input_class == ReadFileInput:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The relative path of a file in the working directory."
                }
            },
            "required": ["path"]
        }
    return {}


def read_file(input_data: Any) -> tuple[str, Exception | None]:
    """Read file function that matches the Go implementation"""
    try:
        # Parse the input - handle JSON input properly
        if isinstance(input_data, str):
            # If it's a string, parse it as JSON
            input_dict = json.loads(input_data)
        elif isinstance(input_data, dict):
            # If it's already a dictionary, use it directly
            input_dict = input_data
        elif isinstance(input_data, bytes):
            # If it's bytes, decode to string first, then parse JSON
            input_data = input_data.decode('utf-8')
            input_dict = json.loads(input_data)
        else:
            # Unknown format
            return "", Exception(f"Unknown input format: {type(input_data)}")
        
        # Get the path from the input
        if "path" not in input_dict:
            return "", Exception("No 'path' field in input")
        
        file_path = input_dict["path"]
        
        # Check if file exists
        if not os.path.exists(file_path):
            return "", Exception(f"File not found: {file_path}")
        
        # Read the file - works with any file type (.txt, .py, .json, etc.)
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        return content, None
    except json.JSONDecodeError as e:
        # Specific error for JSON parsing issues
        return "", Exception(f"Invalid JSON input: {e}")
    except Exception as e:
        return "", e


# Create the tool definition
ReadFileInputSchema = generate_schema(ReadFileInput)

ReadFileDefinition = ToolDefinition(
    name="read_file",
    description="Read the contents of a given relative file path. Use this when you want to see what's inside a file. Do not use this with directory names.",
    input_schema=ReadFileInputSchema,
    function=read_file
)
