# memory_intelligence.py
# Intelligent memory processing that analyzes conversations to extract
# facts, emotions, topics, and personality development cues.

import re
from typing import Dict, List, Tuple, Optional


class MemoryIntelligence:
    """
    Analyzes conversation turns to extract meaningful information
    for long-term memory storage and personality development.
    """
    
    # Patterns for detecting user facts
    FACT_PATTERNS = [
        (r"(?:my name is|i'm|i am|call me)\s+(\w+)", "name"),
        (r"i (?:live|am) (?:in|at|from)\s+([^.,!?]+)", "location"),
        (r"i (?:work|am working) (?:as|at)\s+([^.,!?]+)", "occupation"),
        (r"i (?:like|love|enjoy|prefer)\s+([^.,!?]+)", "likes"),
        (r"i (?:don't like|dislike|hate)\s+([^.,!?]+)", "dislikes"),
        (r"my (?:favorite|favourite)\s+(\w+)\s+is\s+([^.,!?]+)", "favorite"),
        (r"i have (?:a|an)\s+([^.,!?]+)", "possession"),
        (r"i'm (?:learning|studying)\s+([^.,!?]+)", "learning"),
        (r"i (?:want|would like) to\s+([^.,!?]+)", "goal"),
    ]
    
    # Emotional indicators
    POSITIVE_EMOTIONS = [
        "happy", "excited", "great", "wonderful", "amazing", "love", "fantastic",
        "awesome", "excellent", "perfect", "thank you", "thanks", "appreciate",
        "helpful", "nice", "good", "glad"
    ]
    
    NEGATIVE_EMOTIONS = [
        "sad", "frustrated", "angry", "annoying", "bad", "terrible", "awful",
        "hate", "dislike", "upset", "disappointed", "confused", "worried"
    ]
    
    # Common conversation topics
    TOPIC_KEYWORDS = {
        "technology": ["computer", "software", "code", "programming", "tech", "ai", "robot"],
        "weather": ["weather", "temperature", "rain", "snow", "sunny", "cloudy", "forecast"],
        "entertainment": ["movie", "music", "game", "show", "series", "watch", "play"],
        "work": ["work", "job", "office", "project", "meeting", "colleague", "boss"],
        "personal": ["family", "friend", "relationship", "home", "life", "personal"],
        "health": ["health", "exercise", "fitness", "sick", "doctor", "medical"],
        "food": ["food", "eat", "cook", "restaurant", "dinner", "lunch", "breakfast"],
        "travel": ["travel", "trip", "vacation", "visit", "country", "city"],
        "learning": ["learn", "study", "education", "school", "course", "teach"],
        "hobbies": ["hobby", "interest", "passion", "collect", "craft", "art"],
    }
    
    @staticmethod
    def extract_user_facts(user_text: str) -> List[Tuple[str, str]]:
        """
        Extract factual information about the user from their message.
        
        Args:
            user_text: The user's message
            
        Returns:
            List of (fact, category) tuples
        """
        facts = []
        text_lower = user_text.lower().strip()
        
        for pattern, category in MemoryIntelligence.FACT_PATTERNS:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 1:
                    fact_value = match.group(1).strip()
                    if fact_value and len(fact_value) > 1:
                        if category == "name":
                            facts.append((f"User's name is {fact_value.title()}", "name"))
                        elif category == "location":
                            facts.append((f"User lives in {fact_value}", "location"))
                        elif category == "occupation":
                            facts.append((f"User works as/at {fact_value}", "occupation"))
                        elif category == "likes":
                            facts.append((f"User likes {fact_value}", "preference"))
                        elif category == "dislikes":
                            facts.append((f"User dislikes {fact_value}", "preference"))
                        elif category == "learning":
                            facts.append((f"User is learning {fact_value}", "interest"))
                        elif category == "goal":
                            facts.append((f"User wants to {fact_value}", "goal"))
                elif len(match.groups()) == 2:
                    # For patterns like "my favorite X is Y"
                    category_val = match.group(1).strip()
                    item_val = match.group(2).strip()
                    facts.append((f"User's favorite {category_val} is {item_val}", "favorite"))
        
        return facts
    
    @staticmethod
    def detect_emotion(text: str) -> Optional[Tuple[str, float]]:
        """
        Detect emotional tone in a message.
        
        Args:
            text: The message to analyze
            
        Returns:
            Tuple of (emotion_type, intensity) or None
            emotion_type is "positive" or "negative"
            intensity is 0.0-1.0
        """
        text_lower = text.lower()
        words = text_lower.split()
        
        positive_count = sum(1 for word in words if any(pos in word for pos in MemoryIntelligence.POSITIVE_EMOTIONS))
        negative_count = sum(1 for word in words if any(neg in word for neg in MemoryIntelligence.NEGATIVE_EMOTIONS))
        
        # Check for punctuation intensity
        exclamation_count = text.count('!')
        
        if positive_count > negative_count:
            intensity = min(1.0, (positive_count / max(len(words), 1)) * 10)
            intensity = min(1.0, intensity + (exclamation_count * 0.1))
            return ("positive", intensity)
        elif negative_count > positive_count:
            intensity = min(1.0, (negative_count / max(len(words), 1)) * 10)
            return ("negative", intensity)
        
        return None
    
    @staticmethod
    def identify_topics(text: str) -> List[str]:
        """
        Identify conversation topics from a message.
        
        Args:
            text: The message to analyze
            
        Returns:
            List of identified topics
        """
        text_lower = text.lower()
        identified_topics = []
        
        for topic, keywords in MemoryIntelligence.TOPIC_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                identified_topics.append(topic)
        
        return identified_topics
    
    @staticmethod
    def analyze_interaction_quality(user_text: str, assistant_text: str) -> Dict[str, any]:
        """
        Analyze the quality of an interaction to guide personality development.
        
        Args:
            user_text: The user's message
            assistant_text: The assistant's response
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "user_engagement": "low",  # low, medium, high
            "requires_detailed_response": False,
            "is_question": False,
            "topic_switch": False,
            "emotional_tone": None
        }
        
        # Check user engagement (length and complexity)
        word_count = len(user_text.split())
        if word_count > 20:
            analysis["user_engagement"] = "high"
        elif word_count > 5:
            analysis["user_engagement"] = "medium"
        
        # Check if user is asking for details
        detail_keywords = ["explain", "tell me more", "how", "why", "what", "details", 
                          "elaborate", "describe", "go deep"]
        if any(keyword in user_text.lower() for keyword in detail_keywords):
            analysis["requires_detailed_response"] = True
        
        # Check if it's a question
        analysis["is_question"] = "?" in user_text or user_text.lower().startswith(("what", "how", "why", "when", "where", "who", "can", "could", "would", "should"))
        
        # Detect emotional tone
        emotion = MemoryIntelligence.detect_emotion(user_text)
        if emotion:
            analysis["emotional_tone"] = emotion
        
        return analysis
    
    @staticmethod
    def suggest_personality_adjustments(interaction_history: List[Dict], current_traits: Dict[str, float]) -> Dict[str, float]:
        """
        Suggest personality trait adjustments based on interaction history.
        
        Args:
            interaction_history: Recent interactions with analysis
            current_traits: Current personality trait values
            
        Returns:
            Dictionary of suggested trait adjustments
        """
        suggestions = {}
        
        if not interaction_history:
            return suggestions
        
        # Analyze patterns in recent interactions
        avg_user_engagement = sum(
            1 if i.get("user_engagement") == "high" else 0.5 if i.get("user_engagement") == "medium" else 0
            for i in interaction_history
        ) / len(interaction_history)
        
        detail_requests = sum(1 for i in interaction_history if i.get("requires_detailed_response", False))
        positive_emotions = sum(1 for i in interaction_history 
                               if i.get("emotional_tone") and i["emotional_tone"][0] == "positive")
        
        # Suggest trait adjustments
        # If user is highly engaged, increase enthusiasm
        if avg_user_engagement > 0.6:
            suggestions["enthusiasm"] = min(1.0, current_traits.get("enthusiasm", 0.5) + 0.05)
        
        # If user asks for details often, increase detail_orientation
        if detail_requests / len(interaction_history) > 0.3:
            suggestions["detail_orientation"] = min(1.0, current_traits.get("detail_orientation", 0.5) + 0.05)
        
        # If user is consistently positive, increase warmth
        if positive_emotions / len(interaction_history) > 0.5:
            suggestions["warmth"] = min(1.0, current_traits.get("warmth", 0.5) + 0.05)
        
        return suggestions


# Global instance
memory_intelligence = MemoryIntelligence()
