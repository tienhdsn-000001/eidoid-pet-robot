#!/usr/bin/env python3
# memory_viewer.py
# Utility to view and manage persona memories

import sys
import json
from pathlib import Path
from memory_manager import memory_manager, PersonaMemory


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def view_persona_memory(persona_key: str):
    """View detailed memory for a specific persona."""
    mem = memory_manager.get_persona_memory(persona_key)
    
    print_section(f"Memory for: {persona_key.upper()}")
    
    # Basic stats
    print(f"\nInteraction Count: {mem.interaction_count}")
    if mem.last_interaction:
        print(f"Last Interaction: {mem.last_interaction}")
    
    familiarity = mem.user_relationship.get('familiarity_level', 0)
    print(f"Familiarity Level: {familiarity}/100")
    
    # User facts
    if mem.user_facts:
        print_section("Learned Facts About User")
        for i, fact_entry in enumerate(mem.user_facts[-10:], 1):
            confidence = fact_entry.get('confidence', 1.0)
            reinforcements = fact_entry.get('reinforcement_count', 1)
            print(f"{i}. {fact_entry['fact']}")
            print(f"   Confidence: {confidence:.1%}, Reinforcements: {reinforcements}")
    
    # Preferences
    if mem.preferences:
        print_section("User Preferences")
        for category, prefs in mem.preferences.items():
            print(f"\n{category.title()}:")
            for pref in prefs:
                print(f"  - {pref}")
    
    # Conversation topics
    if mem.conversation_topics:
        print_section("Conversation Topics")
        sorted_topics = sorted(
            mem.conversation_topics.items(),
            key=lambda x: x[1],
            reverse=True
        )
        for topic, count in sorted_topics[:10]:
            print(f"  {topic}: {count} times")
    
    # Important memories
    if mem.important_memories:
        print_section("Important Memories")
        for i, memory in enumerate(mem.important_memories[-5:], 1):
            weight = memory.get('emotional_weight', 0)
            print(f"{i}. {memory['memory']}")
            print(f"   Emotional weight: {weight:.1%}, Time: {memory.get('timestamp', 'N/A')}")
    
    # Personality traits
    if mem.personality_traits:
        print_section("Developed Personality Traits")
        sorted_traits = sorted(
            mem.personality_traits.items(),
            key=lambda x: x[1],
            reverse=True
        )
        for trait, value in sorted_traits:
            bar_length = int(value * 20)
            bar = '█' * bar_length + '░' * (20 - bar_length)
            print(f"  {trait:20s} [{bar}] {value:.2f}")
    
    # Rapport indicators
    if mem.user_relationship.get('rapport_indicators'):
        print_section("Recent Rapport Indicators")
        recent = mem.user_relationship['rapport_indicators'][-5:]
        for indicator in recent:
            emoji = "✓" if indicator['positive'] else "✗"
            print(f"  {emoji} {indicator['indicator']}")
    
    print("\n")


def list_all_personas():
    """List all personas with saved memories."""
    memory_dir = Path(".memory")
    if not memory_dir.exists():
        print("No memory directory found.")
        return []
    
    memory_files = list(memory_dir.glob("*_memory.json"))
    
    if not memory_files:
        print("No persona memories found.")
        return []
    
    print_section("Available Persona Memories")
    
    personas = []
    for memory_file in memory_files:
        persona_key = memory_file.stem.replace("_memory", "")
        personas.append(persona_key)
        
        try:
            with open(memory_file, 'r') as f:
                data = json.load(f)
            
            interaction_count = data.get('interaction_count', 0)
            last_interaction = data.get('last_interaction', 'Never')
            fact_count = len(data.get('user_facts', []))
            
            print(f"\n  {persona_key}:")
            print(f"    Interactions: {interaction_count}")
            print(f"    Facts learned: {fact_count}")
            print(f"    Last active: {last_interaction}")
        except Exception as e:
            print(f"\n  {persona_key}: Error reading memory ({e})")
    
    print("\n")
    return personas


def export_memory(persona_key: str, output_file: str):
    """Export persona memory to a JSON file."""
    mem = memory_manager.get_persona_memory(persona_key)
    data = mem.export_memory()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Memory exported to {output_file}")


def clear_persona_memory(persona_key: str, keep_long_term: bool = True):
    """Clear memory for a persona."""
    confirm = input(f"Are you sure you want to clear memory for '{persona_key}'? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return
    
    memory_manager.clear_persona_memory(persona_key, keep_long_term=keep_long_term)
    print(f"Memory cleared for {persona_key}")
    
    if not keep_long_term:
        # Delete the file
        memory_file = Path(".memory") / f"{persona_key}_memory.json"
        if memory_file.exists():
            memory_file.unlink()
            print(f"Memory file deleted: {memory_file}")


def main():
    """Main entry point for the memory viewer."""
    if len(sys.argv) < 2:
        print("Memory Viewer - View and manage persona memories")
        print("\nUsage:")
        print("  python memory_viewer.py list              - List all personas with memories")
        print("  python memory_viewer.py view <persona>    - View detailed memory for a persona")
        print("  python memory_viewer.py export <persona> <file> - Export memory to JSON")
        print("  python memory_viewer.py clear <persona>   - Clear short-term memory only")
        print("  python memory_viewer.py reset <persona>   - Reset all memory (DESTRUCTIVE)")
        print("\nExamples:")
        print("  python memory_viewer.py list")
        print("  python memory_viewer.py view jarvis")
        print("  python memory_viewer.py view alexa")
        print("  python memory_viewer.py export jarvis jarvis_backup.json")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_all_personas()
    
    elif command == "view":
        if len(sys.argv) < 3:
            print("Error: Please specify a persona key")
            print("Usage: python memory_viewer.py view <persona>")
            sys.exit(1)
        
        persona_key = sys.argv[2]
        view_persona_memory(persona_key)
    
    elif command == "export":
        if len(sys.argv) < 4:
            print("Error: Please specify persona key and output file")
            print("Usage: python memory_viewer.py export <persona> <output_file>")
            sys.exit(1)
        
        persona_key = sys.argv[2]
        output_file = sys.argv[3]
        export_memory(persona_key, output_file)
    
    elif command == "clear":
        if len(sys.argv) < 3:
            print("Error: Please specify a persona key")
            print("Usage: python memory_viewer.py clear <persona>")
            sys.exit(1)
        
        persona_key = sys.argv[2]
        clear_persona_memory(persona_key, keep_long_term=True)
    
    elif command == "reset":
        if len(sys.argv) < 3:
            print("Error: Please specify a persona key")
            print("Usage: python memory_viewer.py reset <persona>")
            sys.exit(1)
        
        persona_key = sys.argv[2]
        print("WARNING: This will delete ALL memory for this persona!")
        clear_persona_memory(persona_key, keep_long_term=False)
    
    else:
        print(f"Unknown command: {command}")
        print("Use 'python memory_viewer.py' to see usage instructions")
        sys.exit(1)


if __name__ == "__main__":
    main()
