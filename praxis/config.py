# praxis/config.py
import os

# Database configuration
DB_PATH = "./praxis_data.db"

# Supported programming languages
PROGRAMMING_LANGUAGES = [
    "Python", "JavaScript", "Java", "C++", "C#", "Go", 
    "Ruby", "PHP", "TypeScript", "Rust", "Swift", "Kotlin"
]

# Skill categories
SKILL_CATEGORIES = [
    "data_structure", "algorithm", "paradigm", 
    "concept", "language_specific", "auto_detected", "code_review"
]

# Default programming skills
DEFAULT_SKILLS = [
    # Data structures
    ("Arrays/Lists", "data_structure"),
    ("Linked Lists", "data_structure"),
    ("Stacks", "data_structure"),
    ("Queues", "data_structure"),
    ("Hash Tables", "data_structure"),
    ("Trees", "data_structure"),
    ("Graphs", "data_structure"),
    ("Heaps", "data_structure"),
    
    # Algorithms
    ("Sorting", "algorithm"),
    ("Searching", "algorithm"),
    ("Recursion", "algorithm"),
    ("Dynamic Programming", "algorithm"),
    ("Greedy Algorithms", "algorithm"),
    ("Divide and Conquer", "algorithm"),
    ("Backtracking", "algorithm"),
    
    # Paradigms
    ("Object-Oriented Programming", "paradigm"),
    ("Functional Programming", "paradigm"),
    ("Procedural Programming", "paradigm"),
    
    # General concepts
    ("Time Complexity", "concept"),
    ("Space Complexity", "concept"),
    ("Error Handling", "concept"),
    ("Debugging", "concept"),
    ("Testing", "concept"),
    ("String Manipulation", "concept"),
    ("File I/O", "concept"),
    ("API Integration", "concept"),
    ("Database Operations", "concept"),
    ("Concurrency", "concept"),
    ("Memory Management", "concept"),
    ("Regular Expressions", "concept"),
    
    # Language-specific
    ("Python Collections", "language_specific"),
    ("JavaScript Async", "language_specific"),
    ("Java Multithreading", "language_specific"),
    ("C++ STL", "language_specific")
]

# Groq API configuration
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_DEFAULT_MODEL = "llama3-70b-8192"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Application modes
APP_MODES = ["Learning Path", "Code Review", "Analytics"]