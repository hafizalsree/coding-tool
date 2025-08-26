import json                    # Import the JSON library to handle JSON data
import os                      # Import the operating system library to work with files/folders
from typing import Dict, Any   # Import type hints (Dict = dictionary, Any = anything)
from tools_definition import ToolDefinition  # Import our custom ToolDefinition class


class EditFileInput:           # Create a new class called EditFileInput
    """Input schema for the edit_file tool"""  # Documentation explaining what this class is for
    
    def __init__(self, path: str, old_str: str, new_str: str):  # Constructor method that runs when creating object
        self.path = path       # Store the file path value in the object
        self.old_str = old_str # Store the old string to search for
        self.new_str = new_str # Store the new string to replace with
    
    def to_dict(self) -> Dict[str, Any]:  # Method to convert object to dictionary
        return {"path": self.path, "old_str": self.old_str, "new_str": self.new_str}  # Return a dictionary with all fields


def generate_schema(input_class) -> Dict[str, Any]:  # Function to create JSON schema
    """Generate schema for a given input class"""  # Documentation
    
    # For simplicity, we'll create a basic schema
    # In a real implementation, you might use a library like pydantic
    if input_class == EditFileInput:  # If this is the EditFileInput class
        return {                       # Return the schema
            "type": "object",          # This is an object type
            "properties": {            # What properties it has
                "path": {              # The "path" property
                    "type": "string",  # It's a string
                    "description": "The path to the file"  # What it does
                },
                "old_str": {           # The "old_str" property
                    "type": "string",  # It's a string
                    "description": "Text to search for - must match exactly and must only have one match exactly"  # What it does
                },
                "new_str": {           # The "new_str" property
                    "type": "string",  # It's a string
                    "description": "Text to replace old_str with"  # What it does
                }
            },
            "required": ["path", "old_str", "new_str"]  # All properties are required
        }
    return {}                         # Return empty dict for other classes


def create_new_file(file_path: str, content: str) -> str:
    """Helper function to create a new file with content"""
    try:
        # Get the directory part of the file path
        dir_path = os.path.dirname(file_path)
        
        # If directory is not current directory, create it
        if dir_path != "" and dir_path != ".":
            os.makedirs(dir_path, exist_ok=True)  # Create directory if it doesn't exist
        
        # Write the content to the new file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        return f"Successfully created file {file_path}"
        
    except Exception as e:
        return f"Failed to create file: {str(e)}"


def edit_file(input_data: Any) -> tuple[str, Exception | None]:  # Main function to edit files
    """Edit file function that matches the Go implementation"""  # Documentation
    
    try:                    # Try to do the work (error handling)
        # Parse the input - handle JSON input properly
        if isinstance(input_data, str):  # If input is a string
            # If it's a string, parse it as JSON
            input_dict = json.loads(input_data)  # Convert string to dictionary
        elif isinstance(input_data, dict):  # If input is already a dictionary
            # If it's already a dictionary, use it directly
            input_dict = input_data  # Use it as is
        elif isinstance(input_data, bytes):  # If input is bytes
            # If it's bytes, decode to string first, then parse JSON
            input_data = input_data.decode('utf-8')  # Convert bytes to string
            input_dict = json.loads(input_data)  # Convert string to dictionary
        else:  # If input is something else
            # Unknown format
            return "", Exception(f"Unknown input format: {type(input_data)}")  # Return error
        
        # Get the required fields from the input
        file_path = input_dict.get("path", "")  # Get the file path
        old_str = input_dict.get("old_str", "")  # Get the old string to search for
        new_str = input_dict.get("new_str", "")  # Get the new string to replace with
        
        # Check if input parameters are valid
        if file_path == "" or old_str == new_str:  # If path is empty or old/new strings are the same
            return "", Exception("Invalid input parameters")  # Return error
        
        # Check if file exists
        if not os.path.exists(file_path):  # If the file doesn't exist
            if old_str == "":  # If old_str is empty, we can create a new file
                result = create_new_file(file_path, new_str)  # Create the new file
                return result, None  # Return success message
            else:  # If old_str is not empty, we can't create file
                return "", Exception(f"File not found: {file_path}")  # Return error
        
        # Read the existing file
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                old_content = file.read()  # Read the current file content
        except Exception as e:
            return "", Exception(f"Failed to read file: {str(e)}")  # Return error
        
        # Replace the old string with the new string
        new_content = old_content.replace(old_str, new_str)  # Do the replacement
        
        # Check if the replacement actually changed anything
        if old_content == new_content and old_str != "":  # If content didn't change and old_str wasn't empty
            return "", Exception("old_str not found in file")  # Return error
        
        # Write the new content back to the file
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(new_content)  # Write the updated content
        except Exception as e:
            return "", Exception(f"Failed to write file: {str(e)}")  # Return error
        
        return "OK", None  # Return success message
        
    except json.JSONDecodeError as e:  # If JSON parsing failed
        # Specific error for JSON parsing issues
        return "", Exception(f"Invalid JSON input: {e}")  # Return JSON error
    except Exception as e:  # If any other error happened
        return "", e  # Return the error


# Create the tool definition
EditFileInputSchema = generate_schema(EditFileInput)  # Create the schema for this tool

EditFileDefinition = ToolDefinition(  # Create the tool definition object
    name="edit_file",  # Name of the tool
    description="Make edits to a text file. Replaces 'old_str' with 'new_str' in the given file. 'old_str' and 'new_str' MUST be different from each other. If the file specified with path doesn't exist, it will be created.",  # What it does
    input_schema=EditFileInputSchema,  # What input it expects
    function=edit_file  # Which function to run
)

