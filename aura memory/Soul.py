import os
import re
import ollama
from ollama import Client
import datetime
from collections import Counter

# --- CONFIGURATION ---
MODEL = "dolphin3:8b"
MEMORY_FILE = "memory.md"
SUMMARY_FILE = "summary.md"
SUMMARY_STATE_FILE = "summary_state.txt"

SUMMARY_EVERY_N_EXCHANGES = 20
MAX_MEMORY_BLOCKS_TO_KEEP = 20
MAX_RELEVANT_BLOCKS = 5
MAX_RECENT_BLOCKS_IN_PROMPT = 4

# Generic Personality
SYSTEM_PROMPT = """
You are Aura, a helpful and concise AI assistant. 
You use the provided context and conversation history to stay consistent.
Keep responses natural and engaging.
"""

STOPWORDS = {
    "the", "and", "but", "for", "are", "was", "were", "with", "that", "this",
    "from", "have", "has", "had", "you", "your", "yours", "about", "into",
    "what", "when", "where", "why", "how", "who", "which", "want", "like",
    "know", "think", "just", "very", "really", "also", "too", "can", "could",
    "would", "should", "there", "their", "them", "they", "his", "her", "our",
    "out", "hey", "ok", "okay", "yeah", "true", "whatever", "sure"
}

def ensure_files():
    for f in [MEMORY_FILE, SUMMARY_FILE]:
        if not os.path.exists(f):
            open(f, "w", encoding="utf-8").close()

def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def tokenize(text: str):
    words = normalize_text(text).split()
    return [w for w in words if len(w) > 2 and w not in STOPWORDS]

def split_blocks(raw_text: str):
    return [p.strip() for p in raw_text.split("---") if p.strip()]

def load_blocks(path: str):
    if not os.path.exists(path): return []
    with open(path, "r", encoding="utf-8") as f:
        return split_blocks(f.read())

def save_blocks(path: str, blocks):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n---\n\n".join(blocks).strip() + ("\n" if blocks else ""))

def load_summary():
    if not os.path.exists(SUMMARY_FILE): return ""
    with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()

def save_memory_exchange(user, reply):
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"user: {user}\nassistant: {reply}\n---\n")

def count_exchanges():
    if not os.path.exists(MEMORY_FILE): return 0
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return f.read().count("---")

def get_last_summary_exchange():
    if not os.path.exists(SUMMARY_STATE_FILE): return 0
    try:
        with open(SUMMARY_STATE_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except: return 0

def set_last_summary_exchange(value: int):
    with open(SUMMARY_STATE_FILE, "w", encoding="utf-8") as f:
        f.write(str(value))

def score_block(block: str, query_tokens):
    if not query_tokens: return 0
    block_tokens = tokenize(block)
    if not block_tokens: return 0
    block_counter = Counter(block_tokens)
    query_counter = Counter(query_tokens)
    overlap = sum(min(block_counter[t], query_counter[t]) for t in query_counter)
    normalized_block = normalize_text(block)
    bonus = sum(1 for token in query_tokens if token in normalized_block)
    return overlap + bonus * 0.25

def retrieve_relevant_blocks(blocks, user_input, summary_text):
    query_tokens = tokenize(user_input + " " + summary_text)
    if not query_tokens or not blocks: return []
    scored = []
    for idx, block in enumerate(blocks):
        score = score_block(block, query_tokens)
        score += (idx + 1) / max(len(blocks), 1) * 0.2
        if score > 0: scored.append((score, block))
    scored.sort(key=lambda x: x[0], reverse=True)
    selected, seen = [], set()
    for _, block in scored:
        norm = normalize_text(block)
        if norm not in seen:
            seen.add(norm)
            selected.append(block)
        if len(selected) >= MAX_RELEVANT_BLOCKS: break
    return selected

def update_summary():
    if not os.path.exists(MEMORY_FILE): return
    old_summary = load_summary()
    blocks = load_blocks(MEMORY_FILE)
    if not blocks: return
    recent_memory = "\n---\n\n".join(blocks[-MAX_MEMORY_BLOCKS_TO_KEEP:])
    print("\n[Updating memory summary...]")
    prompt = f"Update this summary with new facts. One fact per line.\n\nOld Summary:\n{old_summary}\n\nNew Conversation:\n{recent_memory}\n\nUpdated Summary:"
    response = ollama.generate(model=MODEL, prompt=prompt, options={"temperature": 0.3})
    summary = response.get("response", "").strip()
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write(summary + "\n")
    save_blocks(MEMORY_FILE, blocks[-MAX_MEMORY_BLOCKS_TO_KEEP:])

def build_prompt(summary, relevant_memory, recent_memory, user_input):
    now = datetime.datetime.now().strftime("%A, %I:%M %p")
    return f"""{SYSTEM_PROMPT}
[Current Time: {now}]
### CONTEXT SUMMARY:
{summary}
### RELEVANT PAST DETAILS:
{relevant_memory}
### RECENT CHAT HISTORY:
{recent_memory}
user: {user_input}
assistant:"""

def run():
    host_address = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    client = Client(host=host_address)
    ensure_files()
    print("\n--- [ Aura Memory System v1.0 ] ---\n")
    while True:
        try:
            user_in = input("You: ").strip()
            if not user_in: continue
            if user_in.lower() in ["exit", "quit"]: break

            summary = load_summary()
            blocks = load_blocks(MEMORY_FILE)
            recent_memory = "\n---\n\n".join(blocks[-MAX_RECENT_BLOCKS_IN_PROMPT:])
            relevant_memory = "\n---\n\n".join(retrieve_relevant_blocks(blocks, user_in, summary))

            prompt = build_prompt(summary, relevant_memory, recent_memory, user_in)
            print("\nAura: ", end="", flush=True)

            reply = ""
            stream = ollama.generate(model=MODEL, prompt=prompt, stream=True, options={"temperature": 0.7, "num_ctx": 8192})

            for chunk in stream:
                content = chunk.get("response", "")
                print(content, end="", flush=True)
                reply += content

            print("\n")
            save_memory_exchange(user_in, reply)
            if count_exchanges() - get_last_summary_exchange() >= SUMMARY_EVERY_N_EXCHANGES:
                update_summary()
                set_last_summary_exchange(count_exchanges())

        except Exception as e:
            print(f"\n[ERROR]: {e}\n")

if __name__ == "__main__":
    run()