# Modular Context Abstraction & Transfer Engine

## Overview
This project extracts, structures, and assembles AI context into modular components.

It converts unstructured transcripts into:
- structured modules (objective, decisions, constraints, etc.)
- configurable context packets
- transfer prompts under constraints (token, privacy, relevance)

---

## How to Run

### 1. Install dependencies
pip install -r requirements.txt

### 2. Add API key
Create a `.env` file:

OPENAI_API_KEY=your_api_key_here

### 3. Run the app
streamlit run app.py

### 4. Use the app
- Upload or paste a transcript
- Click "Extract Modules"
- View structured modules and generated prompts

---

## Notes
- Requires OpenAI API key
- Prototype for modular context management

## Testing
Run:
python test_extraction.py