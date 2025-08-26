import json                    # Import the JSON library to handle JSON data
import os                      # Import the operating system library to work with files/folders
from typing import Dict, Any   # Import type hints (Dict = dictionary, Any = anything)
from tools_definition import ToolDefinition  # Import our custom ToolDefinition class


class ListFilesInput:          # Create a new class called ListFilesInput
    """Input schema for the list_files tool"""  # Documentation explaining what this class is for
    
    def __init__(self, path: str = ""):  # Constructor method that runs when creating object
        self.path = path       # Store the path value in the object
    
    def to_dict(self) -> Dict[str, Any]:  # Method to convert object to dictionary
        return {"path": self.path}  # Return a dictionary with the path


def generate_schema(input_class) -> Dict[str, Any]:  # Function to create JSON schema
    """Generate schema for a given input class"""  # Documentation
    
    # For simplicity, we'll create a basic schema
    # In a real implementation, you might use a library like pydantic
    if input_class == ListFilesInput:  # If this is the ListFilesInput class
        return {                       # Return the schema
            "type": "object",          # This is an object type
            "properties": {            # What properties it has
                "path": {              # The "path" property
                    "type": "string",  # It's a string
                    "description": "Optional relative path to list files from. Defaults to current directory if not provided."  # What it does
                }
            },
            "required": []             # No properties are required (all optional)
        }
    return {}                         # Return empty dict for other classes


def list_files(input_data: Any) -> tuple[str, Exception | None]:  # Main function to list files
    """List files function that matches the Go implementation"""  # Documentation
    
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
        
        # Get the path from the input (optional)
        dir_path = input_dict.get("path", ".")  # Get path from dict, default to "." (current directory)
        
        # Check if directory exists
        if not os.path.exists(dir_path):  # If the path doesn't exist
            return "", Exception(f"Directory not found: {dir_path}")  # Return error
        
        if not os.path.isdir(dir_path):  # If the path exists but isn't a directory
            return "", Exception(f"Path is not a directory: {dir_path}")  # Return error
        
        # List files and directories
        files = []  # Create empty list to store file names
        try:  # Try to list files
            for item in os.listdir(dir_path):  # Loop through each item in directory
                item_path = os.path.join(dir_path, item)  # Create full path to item
                if os.path.isdir(item_path):  # If item is a directory
                    files.append(item + "/")  # Add slash to show it's a directory
                else:  # If item is a file
                    files.append(item)  # Add file name as is
        except PermissionError:  # If we don't have permission to read directory
            return "", Exception(f"Permission denied accessing directory: {dir_path}")  # Return error
        
        # Sort the list for better readability
        files.sort()  # Put files in alphabetical order
        
        # Return the result in JSON format
        result_json = json.dumps({  # Convert result to JSON string
            "files": files,         # List of files and directories
            "directory": dir_path,  # Which directory we listed
            "count": len(files)     # How many items we found
        })
        
        return result_json, None  # Return the JSON result and no error
        
    except json.JSONDecodeError as e:  # If JSON parsing failed
        # Specific error for JSON parsing issues
        return "", Exception(f"Invalid JSON input: {e}")  # Return JSON error
    except Exception as e:  # If any other error happened
        return "", e  # Return the error


# Create the tool definition
ListFilesInputSchema = generate_schema(ListFilesInput)  # Create the schema for this tool

ListFilesDefinition = ToolDefinition(  # Create the tool definition object
    name="list_files",  # Name of the tool
    description="List files and directories at a given path. If no path is provided, lists files in the current directory.",  # What it does
    input_schema=ListFilesInputSchema,  # What input it expects
    function=list_files  # Which function to run
)
