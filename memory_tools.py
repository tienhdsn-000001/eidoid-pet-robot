# memory_tools.py
# Tool declarations for memory management within Gemini Live sessions

memory_query_tool_decl = {
    "function_declarations": [
        {
            "name": "query_memories",
            "description": "Search through long-term memories to find relevant information about past conversations, user preferences, or shared experiences.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find relevant memories"
                    },
                    "memory_type": {
                        "type": "string",
                        "enum": ["fact", "preference", "experience", "emotion", "skill", "personality", "all"],
                        "description": "Type of memory to search for (default: all)"
                    },
                    "max_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "description": "Maximum number of memories to return (default: 5)"
                    }
                },
                "required": ["query"]
            }
        }
    ]
}

memory_store_tool_decl = {
    "function_declarations": [
        {
            "name": "store_important_memory",
            "description": "Explicitly store an important fact, preference, or experience in long-term memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The memory content to store"
                    },
                    "memory_type": {
                        "type": "string",
                        "enum": ["fact", "preference", "experience", "emotion", "skill", "personality"],
                        "description": "Type of memory"
                    },
                    "importance": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Importance level of the memory"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional tags for categorizing the memory"
                    }
                },
                "required": ["content", "memory_type", "importance"]
            }
        }
    ]
}

personality_analysis_tool_decl = {
    "function_declarations": [
        {
            "name": "analyze_personality_development",
            "description": "Get current personality trait analysis and evolution over time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_history": {
                        "type": "boolean",
                        "description": "Include historical personality changes (default: false)"
                    }
                }
            }
        }
    ]
}