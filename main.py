import anthropic                    # Import the Anthropic library to talk to Claude
import sys                          # Import system functions (for exiting, etc.)
from typing import Callable, Optional, Tuple, List, Dict, Any  # Import type hints
import contextlib                   # Import context management (not used in this code)
from dotenv import load_dotenv      # Import function to load environment variables from .env file
import os                          # Import operating system functions (like getting environment variables)
from tools_definition import ToolDefinition  # Import our custom ToolDefinition class
from read_file_tool import ReadFileDefinition  # Import our read_file tool
from list_files_tool import ListFilesDefinition  # Import our list_files tool
from edit_file_tool import EditFileDefinition  # Import our edit_file tool

# Load environment variables from .env file
load_dotenv()                      # Read the .env file to get your API key

def main():
    # Get your API key from environment variables
    api_key = os.getenv("ANTHROPIC_API_KEY")
    # Check if API key is set
    if not api_key:                # If no API key was found
        print("Error: ANTHROPIC_API_KEY not found. Please create a .env file with your API key.")  # Show error message
        return                      # Exit the function (program stops)
    
    # Create a client to talk to Claude
    client = anthropic.Anthropic(api_key=api_key)
    
    # Test different models to see which ones work
    test_models = [                # List of Claude models to try
        "claude-3-5-sonnet-20250106",      
        "claude-3-5-sonnet-20241022",     
        "claude-3-5-haiku-20241022",       
        "claude-3-haiku-20240307",        
        "claude-3-opus-20240229",         
        "claude-3-5-sonnet-latest"         
    ]
    
    working_model = None           # Variable to store which model works
    print("Testing available models...")   # Tell user we're testing models
    
    # Loop through each model in the list
    for model in test_models:
        try:                        # Try to use this model
            # Send a test message to Claude
            response = client.messages.create(
                model=model,        # Use this specific model
                max_tokens=5,       # Only ask for 5 tokens (very short response)
                messages=[{"role": "user", "content": "test"}]  # Send "test" as user message
            )
            print(f"✓ {model} - WORKS")  # If successful, show "✓ model - WORKS"
            working_model = model   # Remember which model worked
            break                   # Stop testing, we found a working one
        except Exception as e:      # If this model failed
            print(f"✗ {model} - {e}")  # Show "✗ model - error message"
    
    if not working_model:          # If no models worked
        print("No working model found!")  # Show error message
        return                      # Exit the function (program stops)
    
    # Define function to get user input
    def get_user_message() -> Tuple[str, bool]:
        try:                        # Try to get input
            user_input = input()    # Wait for user to type something and press Enter
            return user_input, True # Return what they typed and True (success)
        except EOFError:            # If user pressed Ctrl+D (end of file)
            return "", False        # Return empty string and False (failure)
    
    # Create our AI agent with the read_file tool
    agent = Agent(client, get_user_message, [ReadFileDefinition, ListFilesDefinition, EditFileDefinition], working_model)
    try:                           # Try to run the agent
        agent.run()                # Start the agent (this starts the chat)
    except KeyboardInterrupt:      # If user pressed Ctrl+C
        print("\nGoodbye!")        # Say goodbye
    except Exception as e:         # If any other error happened
        print(f"Error: {e}")      # Show the error message

# Function to create new agents
def new_agent(client: anthropic.Anthropic, get_user_message: Callable[[], Tuple[str, bool]], tools: List['ToolDefinition']) -> 'Agent':
    return Agent(client, get_user_message, tools)  # Return a new Agent object

# Define the Agent class (our AI chat system)
class Agent:
    # Constructor function - runs when we create a new Agent
    def __init__(self, client: anthropic.Anthropic, get_user_message: Callable[[], Tuple[str, bool]], tools: List['ToolDefinition'], model: str):
        self.client = client       # Store the Claude client
        self.get_user_message = get_user_message  # Store the function to get user input
        self.tools = tools         # Store the list of available tools
        self.conversation: List[Dict[str, Any]] = []  # Create empty list to store chat history
        self.model = model         # Store which Claude model to use
    
    # Main function that runs the chat
    def run(self):
        # Main agent loop
        print("Chat with Claude (use 'ctrl-c' to quit)")  # Show welcome message
        
        conversation = []           # Create empty list for this chat session
        waiting_for_user_input = True  # Start by waiting for user to type
        
        # Loop forever until user quits
        while True:
            if waiting_for_user_input:  # If it's user's turn to type
                print("\033[94mYou\033[0m: ", end="", flush=True)  # Show "You:" in blue, don't add newline
                message, success = self.get_user_message()  # Get what user typed
                if not success:     # If getting input failed
                    break           # Exit the loop
                
                # Add user message to conversation history
                user_message = {"role": "user", "content": message}  # Create user message object
                conversation.append(user_message)  # Add it to chat history
            
            # Process the message with the Anthropic client
            try:                    # Try to talk to Claude
                response = self.run_inference(conversation)  # Send chat to Claude, get response
                conversation.append({"role": "assistant", "content": response.content})  # Remember Claude's response
                
                tool_results = []   # List to store what tools did
                # Look at each part of Claude's response
                for content in response.content:
                    if hasattr(content, 'type'):  # Does this part have a type field?
                        if content.type == "text":  # If it's just text
                            print(f"\033[93mClaude\033[0m: {content.text}")  # Show Claude's words in yellow
                        elif content.type == "tool_use":  # If Claude wants to use a tool
                            result = self.execute_tool(content.id, content.name, content.input)  # Run the tool
                            tool_results.append(result)  # Remember what the tool did
                    else:           # Fallback for old-style responses
                        print(f"\033[93mClaude\033[0m: {content.text}")  # Show Claude's words
                
                if len(tool_results) == 0:  # If no tools were used
                    waiting_for_user_input = True  # Ask user for next message
                    continue        # Go back to start of loop
                
                waiting_for_user_input = False  # Tools were used, let Claude respond to results
                conversation.append({"role": "user", "content": tool_results})  # Tell Claude what tools did
                
            except Exception as e:  # If talking to Claude failed
                print(f"\033[91mError calling Claude API: {e}\033[0m")  # Show error in red
                waiting_for_user_input = True  # Ask user for input again
    
    # Function to talk to Claude
    def run_inference(self, conversation: List[Dict[str, Any]]):
        """Send conversation to Claude and return response"""
        
        # Convert our custom tools to Anthropic's format
        anthropic_tools = []       # List to store tools in Claude's format
        # Loop through each of our tools
        for tool in self.tools:
            # Add tool to the list
            anthropic_tools.append({
                "name": tool.name,    # Tool name (like "read_file")
                "description": tool.description,  # What the tool does
                "input_schema": tool.input_schema  # What input the tool expects
            })
        
        # Send message to Claude
        return self.client.messages.create(
            model=self.model,       # Use our working model
            max_tokens=1024,        # Allow Claude to write up to 1024 tokens
            messages=conversation,  # Send our chat history
            tools=anthropic_tools   # Tell Claude what tools are available
        )
    
    # Function to run tools
    def execute_tool(self, tool_id: str, tool_name: str, tool_input: Any) -> Dict[str, Any]:
        """Execute a tool and return the result"""
        # Find the tool definition
        tool_def = None            # Variable to store the tool we find
        # Look through all our available tools
        for tool in self.tools:
            if tool.name == tool_name:  # If this tool has the right name
                tool_def = tool    # Remember this tool
                break               # Stop looking, we found it
        
        if tool_def is None:       # If we couldn't find the tool
            # Return an error message
            return {
                "type": "tool_result",  # This is a tool result
                "tool_use_id": tool_id,  # ID to link with Claude's request
                "content": "tool not found",  # Error message
                "is_error": True   # Mark this as an error
            }
        
        # Show "tool: read_file(path)" in green
        print(f"\033[92mtool\033[0m: {tool_name}({tool_input})")
        
        # Debug: Show what type of input we received
        print(f"\033[95mDEBUG\033[0m: Input type: {type(tool_input)}, Input value: {tool_input}")
        
        try:                        # Try to run the tool
            response, error = tool_def.function(tool_input)  # Call the tool function
            
            # Debug: Show what the tool returned
            # print(f"\033[95mDEBUG\033[0m: Tool response: {response}, Error: {error}")
            
            if error:               # If the tool returned an error
                # Return error result
                return {
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": str(error),  # The error message
                    "is_error": True
                }
            # Tool worked! Return the result
            return {
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": response,  # What the tool returned
                "is_error": False
            }
        except Exception as e:      # If the tool crashed completely
            # Debug: Show the exception
            print(f"\033[95mDEBUG\033[0m: Exception: {e}")
            # Return crash error
            return {
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": str(e),  # What went wrong
                "is_error": True
            }

# If this file is run directly (not imported)
if __name__ == "__main__":
    main()                         # Run the main function
