#!/usr/bin/env python3
# test_memory_system.py
# Test suite for the memory system

import os
import sys
import json
from pathlib import Path
import shutil

# Test imports
try:
    from memory_manager import memory_manager, PersonaMemory
    from memory_intelligence import memory_intelligence
    print("[✓] All imports successful")
except Exception as e:
    print(f"[✗] Import failed: {e}")
    sys.exit(1)


def cleanup_test_memory():
    """Clean up test memory directory."""
    test_dir = Path(".memory_test")
    if test_dir.exists():
        shutil.rmtree(test_dir)


def test_persona_memory():
    """Test PersonaMemory class."""
    print("\n=== Testing PersonaMemory ===")
    
    # Create test memory
    mem = PersonaMemory("test_persona", ".memory_test")
    
    # Test recording interaction
    mem.record_interaction()
    assert mem.interaction_count == 1, "Interaction count should be 1"
    assert mem.user_relationship['familiarity_level'] == 1, "Familiarity should be 1"
    print("[✓] Record interaction")
    
    # Test learning facts
    mem.learn_user_fact("User's name is Alice", confidence=0.9)
    assert len(mem.user_facts) == 1, "Should have 1 fact"
    assert mem.user_facts[0]['fact'] == "User's name is Alice"
    assert mem.user_facts[0]['confidence'] == 0.9
    print("[✓] Learn user fact")
    
    # Test reinforcing facts
    mem.learn_user_fact("User's name is Alice", confidence=0.95)
    assert len(mem.user_facts) == 1, "Should still have 1 fact (reinforced)"
    assert mem.user_facts[0]['reinforcement_count'] == 2
    print("[✓] Fact reinforcement")
    
    # Test preferences
    mem.update_preference("music", "jazz")
    mem.update_preference("music", "classical")
    assert "music" in mem.preferences
    assert len(mem.preferences["music"]) == 2
    print("[✓] Update preferences")
    
    # Test conversation topics
    mem.track_conversation_topic("technology")
    mem.track_conversation_topic("technology")
    mem.track_conversation_topic("weather")
    assert mem.conversation_topics["technology"] == 2
    assert mem.conversation_topics["weather"] == 1
    print("[✓] Track conversation topics")
    
    # Test personality traits
    mem.develop_personality_trait("enthusiasm", 0.7)
    assert mem.personality_traits["enthusiasm"] == 0.7
    mem.develop_personality_trait("enthusiasm", 0.9)
    # Should be weighted average: 0.7 * 0.7 + 0.9 * 0.3 = 0.76
    assert 0.75 <= mem.personality_traits["enthusiasm"] <= 0.77
    print("[✓] Develop personality traits")
    
    # Test important memories
    mem.add_important_memory("First conversation", emotional_weight=0.8)
    assert len(mem.important_memories) == 1
    assert mem.important_memories[0]['emotional_weight'] == 0.8
    print("[✓] Add important memories")
    
    # Test rapport indicators
    mem.add_rapport_indicator("User thanked me", positive=True)
    assert len(mem.user_relationship['rapport_indicators']) == 1
    assert mem.user_relationship['rapport_indicators'][0]['positive'] == True
    print("[✓] Add rapport indicators")
    
    # Test conversation turns
    mem.add_conversation_turn("user", "Hello!")
    mem.add_conversation_turn("assistant", "Hi there!")
    assert len(mem.conversation_buffer) == 2
    print("[✓] Add conversation turns")
    
    # Test context rendering
    short_context = mem.get_short_term_context()
    assert "User: Hello!" in short_context
    assert "Assistant: Hi there!" in short_context
    print("[✓] Get short-term context")
    
    long_context = mem.get_long_term_context()
    assert "Interaction count: 1" in long_context
    assert "Alice" in long_context
    print("[✓] Get long-term context")
    
    # Test save and load
    mem.save_memory()
    mem_file = Path(".memory_test/test_persona_memory.json")
    assert mem_file.exists(), "Memory file should exist"
    print("[✓] Save memory")
    
    # Create new instance and verify it loads
    mem2 = PersonaMemory("test_persona", ".memory_test")
    assert mem2.interaction_count == 1
    assert len(mem2.user_facts) == 1
    assert mem2.user_facts[0]['fact'] == "User's name is Alice"
    print("[✓] Load memory")
    
    # Test export
    export_data = mem2.export_memory()
    assert export_data['persona_key'] == "test_persona"
    assert export_data['interaction_count'] == 1
    print("[✓] Export memory")
    
    # Test clear short-term
    mem2.clear_short_term()
    assert len(mem2.conversation_buffer) == 0
    assert len(mem2.user_facts) == 1  # Long-term should remain
    print("[✓] Clear short-term memory")
    
    print("\n[✓] All PersonaMemory tests passed!")


def test_memory_intelligence():
    """Test MemoryIntelligence class."""
    print("\n=== Testing MemoryIntelligence ===")
    
    # Test fact extraction
    facts = memory_intelligence.extract_user_facts("My name is Bob and I live in Seattle")
    assert len(facts) >= 1, "Should extract at least 1 fact"
    fact_texts = [f[0] for f in facts]
    assert any("Bob" in f for f in fact_texts), "Should extract name"
    print(f"[✓] Fact extraction: {facts}")
    
    facts2 = memory_intelligence.extract_user_facts("I like pizza and I work as a teacher")
    assert len(facts2) >= 1, "Should extract facts"
    print(f"[✓] Multiple fact extraction: {facts2}")
    
    # Test emotion detection
    emotion = memory_intelligence.detect_emotion("I'm so happy! This is amazing!")
    assert emotion is not None, "Should detect emotion"
    assert emotion[0] == "positive", "Should be positive"
    assert emotion[1] > 0, "Should have positive intensity"
    print(f"[✓] Positive emotion detection: {emotion}")
    
    emotion2 = memory_intelligence.detect_emotion("I'm frustrated and upset")
    assert emotion2 is not None
    assert emotion2[0] == "negative", "Should be negative"
    print(f"[✓] Negative emotion detection: {emotion2}")
    
    # Test topic identification
    topics = memory_intelligence.identify_topics("Let's talk about programming and software development")
    assert "technology" in topics, "Should identify technology topic"
    print(f"[✓] Topic identification: {topics}")
    
    topics2 = memory_intelligence.identify_topics("What's the weather forecast for tomorrow?")
    assert "weather" in topics2
    print(f"[✓] Weather topic: {topics2}")
    
    # Test interaction analysis
    analysis = memory_intelligence.analyze_interaction_quality(
        "Can you explain how machine learning works? I'd like to understand it better.",
        "Machine learning is..."
    )
    assert analysis['requires_detailed_response'] == True
    assert analysis['is_question'] == True
    assert analysis['user_engagement'] in ["low", "medium", "high"]
    print(f"[✓] Interaction analysis: {analysis}")
    
    # Test personality adjustments
    mock_history = [
        {'user_engagement': 'high', 'requires_detailed_response': True, 'emotional_tone': ('positive', 0.8)},
        {'user_engagement': 'high', 'requires_detailed_response': True, 'emotional_tone': ('positive', 0.7)},
        {'user_engagement': 'medium', 'requires_detailed_response': False, 'emotional_tone': None},
    ]
    current_traits = {'enthusiasm': 0.5, 'warmth': 0.5}
    suggestions = memory_intelligence.suggest_personality_adjustments(mock_history, current_traits)
    print(f"[✓] Personality adjustments: {suggestions}")
    
    print("\n[✓] All MemoryIntelligence tests passed!")


def test_memory_manager():
    """Test MemoryManager class."""
    print("\n=== Testing MemoryManager ===")
    
    from memory_manager import MemoryManager
    mgr = MemoryManager(".memory_test")
    
    # Test getting persona memory
    mem1 = mgr.get_persona_memory("persona1")
    assert mem1 is not None
    assert mem1.persona_key == "persona1"
    print("[✓] Get persona memory")
    
    # Test that same persona returns same instance
    mem1_again = mgr.get_persona_memory("persona1")
    assert mem1 is mem1_again, "Should return same instance"
    print("[✓] Singleton behavior")
    
    # Test multiple personas
    mem2 = mgr.get_persona_memory("persona2")
    assert mem2 is not mem1
    assert mem2.persona_key == "persona2"
    print("[✓] Multiple personas")
    
    # Add some data
    mem1.record_interaction()
    mem2.record_interaction()
    mem2.record_interaction()
    
    # Test save all
    mgr.save_all_memories()
    file1 = Path(".memory_test/persona1_memory.json")
    file2 = Path(".memory_test/persona2_memory.json")
    assert file1.exists()
    assert file2.exists()
    print("[✓] Save all memories")
    
    # Test clear persona memory
    mgr.clear_persona_memory("persona1", keep_long_term=True)
    assert len(mem1.conversation_buffer) == 0
    print("[✓] Clear persona memory")
    
    print("\n[✓] All MemoryManager tests passed!")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("  Memory System Test Suite")
    print("=" * 60)
    
    try:
        # Clean up before tests
        cleanup_test_memory()
        
        # Run tests
        test_persona_memory()
        test_memory_intelligence()
        test_memory_manager()
        
        print("\n" + "=" * 60)
        print("  ✓ ALL TESTS PASSED")
        print("=" * 60)
        
        return True
        
    except AssertionError as e:
        print(f"\n[✗] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    except Exception as e:
        print(f"\n[✗] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up after tests
        cleanup_test_memory()
        print("\n[✓] Test cleanup complete")


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
