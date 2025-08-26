import json
from typing import Callable, Dict, Any


class ToolDefinition:
    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        function: Callable[[Any], tuple[str, Exception | None]]
    ):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.function = function
