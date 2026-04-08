from extractor import extract_modules

sample_text = """
I'm working on a project to build a modular context system for AI.
The goal is to allow context transfer between sessions.

So far, I've decided to split context into modules like objective, decisions, and constraints.

One constraint is token limits. Another is privacy — I don't want personal info shared.

Also, I prefer concise explanations.
"""

result = extract_modules(sample_text)

print("\n=== EXTRACTED MODULES ===\n")
print(result)