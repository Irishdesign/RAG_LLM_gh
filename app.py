import os
import datetime
import requests
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from langfuse import Langfuse
import time

langfuse = Langfuse(
  secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
  public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
  host=os.environ.get("LANGFUSE_HOST", "http://host.docker.internal:3000")
)

langfuse.flush()

LLM_MODEL = "llama3.2"

# ✅ General Functions: Call Local Model (Ollama)
def ask_ollama(prompt: str, tags: list[str] = []):
    trace = langfuse.trace(name="ollama_request", input=prompt)
    start_time = time.time()
    try:
        response = requests.post(
            "http://host.docker.internal:11434/api/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False}
        )
        latency = time.time() - start_time
        data = response.json()
        if "response" in data:
            res = data["response"]
            trace.update(output=res, tags=tags, metadata={"latency": latency})
            return res
        elif "error" in data:
            trace.update(output=data["error"], level="ERROR", metadata={"latency": latency})
            print(f"[Ollama API Error] {data['error']}")
            return f"[Ollama API Error] {data['error']}"
        else:
            trace.update(output=str(data), level="ERROR", metadata={"latency": latency})
            print(f"[Ollama API Unexpected Response] {data}")
            return f"[Ollama API Unexpected Response] {data}"
    except Exception as e:
        latency = time.time() - start_time
        trace.update(output=str(e), level="ERROR", metadata={"latency": latency})
        raise

def save_output(user_prompt, response, output_type):
    """Save prompt and response to outputs/ directory, filename auto-appended with category and timestamp."""
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"{output_type}_{timestamp}.md")
    with open(filename, "w", encoding="utf-8", errors="replace") as f:
        f.write("=== 📝 PROMPT ===\n")
        f.write(user_prompt + "\n\n")
        f.write("=== 🧠 RESPONSE ===\n")
        f.write(response)
    print(f"✅ Saved as {filename}")

# ✅ Assistant 0: Directly chat with llama3.2 and send Langfuse trace
def direct_assistant():
    while True:
        user_input = input("\n🗣️ Chat with llama3.2 (type 'menu' to return to main menu):\n> ")
        if user_input.lower() in ["exit", "quit", "menu"]:
            break
        response = ask_ollama(user_input, tags=['llama3.2'])
        print(f"\n🤖 Assistant Reply:\n{response}")


# ✅ Assistant 1: General Life Assistant with Memory
def general_assistant():
    memory_file = "memory/general.txt"
    os.makedirs("memory", exist_ok=True)
    if not os.path.exists(memory_file):
        open(memory_file, "w").close()

    while True:
        with open(memory_file, "r") as f:
            memory = f.read()

        user_input = input("\n🧍 You say:\n> ")
        if user_input.lower() in ["exit", "quit", "menu"]:
            break

        prompt = f"""You are my personal assistant. Here is your current memory：
{memory}

My question is：{user_input}

Please respond to me based on your memory.
"""
        response = ask_ollama(prompt, tags=['personal'])
        print(f"\n🤖 Assistant：\n{response}")

        update = input("⚙️ Add to memory? (y/n): ").strip().lower()
        if update == "y":
            with open(memory_file, "a") as f:
                f.write(f"\n[Question] {user_input}\n[Response] {response}\n")
            print("✅ Added to memory")

# ✅ Assistant 2: Document Content Assistant
def document_assistant():
    chromadb_db_name = input("\n📄 Please enter the vector DB Name to use:\n> ") 
    # Specify local transformers format embedding function
    embedding_function = SentenceTransformerEmbeddingFunction(
        model_name="./models/all-MiniLM-L6-v2"
    )
    client = chromadb.PersistentClient(path="./chroma_store")
    collection = client.get_collection(
        name=chromadb_db_name,
        embedding_function=embedding_function
    )
    while True:
        user_input = input("\n📄 Question (or type 'menu' to return to main menu):\n> ")
        if user_input.lower() in ["exit", "quit", "menu"]:
            break
        # Query ChromaDB
        results = collection.query(query_texts=[user_input], n_results=3)
        # Get query result content
        documents = results.get("documents", [[]])
        flat_docs = [doc for sublist in documents for doc in sublist]
        # Use flat_docs directly, no per-character merge
        rag_context = "\n---\n".join(flat_docs)
        prompt = f"""You are a professional assistant. Here is the document content：

【RAG Search Result】
{rag_context}

Based on the above, answer the question：{user_input}
"""
        response = ask_ollama(prompt,tags=['doc_search'])
        print(f"\n🧠 Document Assistant Reply：\n{response}")
        save_output(user_input, response, "askdoc")

# ✅ Assistant 3: Consult with Carl Jung
def messages_to_prompt(messages):
    """Convert multi-turn message list to Ollama single prompt string."""
    prompt = ""
    for msg in messages:
        if msg['role'] == 'system':
            prompt += f"[System]\n{msg['content']}\n"
        elif msg['role'] == 'user':
            prompt += f"[User]\n{msg['content']}\n"
    return prompt

def carl_jung_assistant():
    # Get production prompt from langfuse
    prompt_obj = langfuse.get_prompt("carl_jung", label="production")
    if not prompt_obj:
        print("❌ Unable to get Carl Jung prompt, please check langfuse settings.")
        return

    print("\n🧠 You can now ask Jung questions (type 'menu' to return to main menu):")

    while True:
        user_input = input("\n🧑‍💼 Your question:\n> ")
        if user_input.lower() in ["exit", "quit", "menu"]:
            break
        prompt = prompt_obj.compile(user_input=user_input)
        full_prompt = messages_to_prompt(prompt)
        print(full_prompt)
        response = ask_ollama(full_prompt, tags=["carl_jung"])
        print(f"{response}")


# ✅ Main Menu
def main():
    while True:
        print("\n🧭 Please select assistant mode：")
        print("0. 🗣️ Chat with llama3.2")
        print("1. 🧍 General Life Assistant")
        print("2. 📄 Document Content Assistant")
        print("3. 🧑‍💼 Chat with Carl Jung")
        print("Type 'exit' to quit")

        choice = input("> ").strip().lower()

        if choice in ["exit", "quit"]:
            print("👋 Goodbye!")
            break
        elif choice == "0":
            direct_assistant()
        elif choice == "1":
            general_assistant()
        elif choice == "2":
            document_assistant()
        elif choice == "3":
            carl_jung_assistant()
        else:
            print("❌ Invalid option, please enter 0/1/2/3 or exit")

if __name__ == "__main__":
    main()
