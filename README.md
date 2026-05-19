# Aura: A Transparent Local AI Memory System

Aura is a lightweight Python implementation of a long-term memory and retrieval system for local Large Language Models (LLMs). It uses a custom Retrieval-Augmented Generation (RAG) loop to allow local AI models to "remember" past interactions across different sessions.

---

## How It Works
Aura performs a "Memory Loop":
- **Retrieval**: It scans `memory.md` for keywords related to your current message.
- **Context Injection**: It pulls most relevant past "blocks" into the current prompt.
- **Summarization**: Every 20 exchanges, it uses the AI to condense the conversation into a permanent `summary.md` file to keep the memory efficient.

---

## Getting Started

### 1. Prerequisites
You must have **Ollama** installed and running on your local machine.

### 2. Choose Your Model
By default, this script uses `dolphin3:8b`, but you can use any model you have downloaded. 
* Open `soul.py` and change the `MODEL` variable at the top:

 
  ```python
  MODEL = "your-model-name-here"
  
IT IS VITAL YOU CHANGE THIS TO YOUR LOCAL AI

---

## The Story Behind Aura
This project was mainly just a passion project after seeing news headlines about sites like character ai or other ai chat websites, I thought it would be a good fun challegen to devleop my own personal version. I made sure to ensure that Aura was built to ensure that:
1. **The User is in Control**: All memories are stored in human-readable Markdown files.
2. **Privacy is Absolute**: No data ever leaves your machine.
3. **Consistency Matters**: The AI uses past context to remain stable and helpful over long periods.

---

## Authors Notes

Author: Created by RA-DevProjects
GitHub profile: https://github.com/RA-DevProjects
