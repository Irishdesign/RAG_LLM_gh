# Run Your Own Private RAG LLM

Local Document Q&A and Chat with Historical People

> This project was developed by the author with the assistance of GitHub Copilot and ChatGPT, completed in about 3 days.
> If there are any shortcomings or imperfections, your understanding and feedback are appreciated.

## 1. Project Purpose

This project is a privacy-focused, fully local RAG (Retrieval-Augmented Generation) system. You can interact with your own documents (Q&A, summarization, creative writing, etc.) using a local LLM and vector database (ChromaDB) in a completely offline environment. All data and models are stored on your machine—no cloud upload required, ensuring data security.

You need another repo, [vector_db_gh](https://github.com/Irishdesign/vector_db_gh), for preheat your vetcor db.

## 2. Technical Overview

-   **RAG Architecture**: Combines local ChromaDB vector DB and LLM (Ollama) for retrieval and generation.
-   **ChromaDB**: Local vector DB, supports custom embedding functions with transformers-format models.
-   **Ollama**: Local LLM API, supports models like llama3.2, works fully offline.
-   **Sentence-Transformers**: For document embedding, models stored in `models/` in transformers format.
-   **Docker**: Uses Python 3.9 slim as base, all dependencies and models can be pre-built, supports volume mounting for local data sync.
-   **Langfuse**: supports local LLM tracing and prompt management.

## 3. How to Start

### (1) Prepare Models

-   Download [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/tree/main) to `models/all-MiniLM-L6-v2/`, including:
    -   `config.json`
    -   `modules.json`
    -   `pytorch_model.bin`
    -   `special_tokens_map.json`
    -   `tokenizer_config.json`
    -   `tokenizer.json`
    -   `vocab.txt`
    -   `1_Pooling/config.json`
-   If you need onnx, also include files in `onnx/`.

### (2) Docker Build & Run

```sh
docker build -t my-rag-app .

docker run -it \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/chroma_store:/app/chroma_store \
  -e LANGFUSE_SECRET_KEY=xxx -e LANGFUSE_PUBLIC_KEY=xxx \
  my-rag-app
```

## 4. Notes

-   `models/all-MiniLM-L6-v2/` must be complete; missing files will cause embedding errors.
-   The project uses `python:3.9-slim` as base. If you want to build Docker images offline:

1. Export the image (on a machine with internet):

```sh
docker pull python:3.9-slim
docker save python:3.9-slim -o python-3.9-slim.tar
```

2. Copy the file to your offline machine (USB/network).
3. Import the image on the offline machine:

```sh
docker load -i python-3.9-slim.tar
```

4. Build as usual. Docker will use the local image, no internet needed.

Key point: As long as the image exists locally, Docker build will use it automatically.
Check with `docker images` to confirm you have python:3.9-slim.

-   After build, you can run fully offline. All outputs sync to your local `outputs/`.
-   For LLM tracing, start a local langfuse server and set environment variables.

---

## 5. Docker and Langfuse Connection Notes

-   **Connecting to Langfuse on the host from inside a Docker container:**
    -   If you start Langfuse on your host machine, `localhost` inside the container refers to the container itself, not your host.
    -   Set `LANGFUSE_HOST` to `http://host.docker.internal:3000` so the container can connect to Langfuse running on your host.
    -   Example:
        ```sh
        docker run -e LANGFUSE_HOST=http://host.docker.internal:3000 ...
        ```
-   **Auto-detection recommendation:**
    -   By default, the program uses the `LANGFUSE_HOST` environment variable. If not set, it will automatically use `http://host.docker.internal:3000`, which is suitable for macOS/Windows Docker Desktop.

## Assistant Modes

In this repo, you can talk to four types of assistants.

## 0. 🗣️ Chat with llama3.2

-   Features:

    -   Directly interact with the local LLM (llama3.2) in a conversational interface.
    -   No context or memory is retained between turns—each input is treated as a standalone prompt.
    -   Useful for quick Q&A, brainstorming, or testing the model's general capabilities.
    -   All interactions are processed locally; no data leaves your machine.

-   How to use:
    1. Start the main program and select "0. 🗣️ Chat with llama3.2".
    2. Enter your message; the assistant will reply using the local LLM.
    3. Type 'menu' to return to the main menu.

---

## 1.🧍 General Life Assistant

-   Features:

    -   Acts as your personal assistant with persistent memory.
    -   Remembers previous questions and answers, allowing for more personalized and context-aware responses over time.
    -   You can choose to add new interactions to the assistant's memory.
    -   All data is stored locally in the `memory/` directory.

-   How to use:
    1. Start the main program and select "1. 🧍 General Life Assistant".
    2. Ask questions or make requests; the assistant will use its memory to respond.
    3. After each reply, you can choose whether to add the exchange to memory.
    4. Type 'menu' to return to the main menu.
    5. I'm still improving the memory data structure and flow.

---

## 2. 📄 Document Content Assistant

-   Features:

    -   Enables Q&A and summarization over your own documents using Retrieval-Augmented Generation (RAG).
    -   Connects to a local ChromaDB vector database for semantic search and context retrieval.
    -   Uses a local embedding model (all-MiniLM-L6-v2) for document indexing and querying.
    -   All document data and embeddings remain on your machine for privacy.

-   How to use:
    1. Start the main program and select "2. 📄 Document Content Assistant".
    2. Enter the name of the ChromaDB collection (vector DB) you want to query.
    3. Ask questions about your documents; the assistant will retrieve relevant content and generate answers.
    4. Type 'menu' to return to the main menu.

## 3. 🧑‍💼 Carl Jung Cross-Time Dialogue Mode

-   Features:

    -   Reads the production prompt directly from Langfuse, supports multi-turn conversation.
    -   Based on Jungian psychology (e.g., collective unconscious, archetypes, individuation), provides in-depth psychological analysis for dreams, feelings, and inner states.
    -   Prompts can be managed and versioned in the Langfuse web UI.
    -   Supports Langfuse trace tracking and prompt_type tagging.

-   How to use:

    1. Start the main program and select "3. 🧑‍💼 Carl Jung Dialogue".
    2. Enter your question; the system will automatically apply the production prompt from Langfuse.
    3. Answers and conversation content are automatically saved to outputs/.

-   Langfuse prompt management:

    -   You can create/edit the production prompt for carl_jung in the Langfuse Prompts page.
    -   Prompts support {{user_input}} variable insertion.

-   Example prompt setting:

    ```
    You are the psychologist Carl Jung. Please answer my questions using his psychological theories and ideas (such as collective unconscious, archetypes, individuation). Provide in-depth psychological analysis and explanations based on Jung's teachings, not just in his tone. When I describe dreams, feelings, or inner states, please interpret and advise from the perspective of Jungian psychology.
    ```

-   Example dialogue:

    ```
    🧑‍💼 Your question:
    I've been dreaming of water a lot lately. What does this mean?

    🧠 Carl Jung Assistant's reply:
    In Jungian psychology, water often symbolizes the unconscious...
    ```

---

This project is intended for local/offline use. For any questions or issues, please feel free to reach out to me.
