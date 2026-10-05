# Local GitHub Repository Code Explainer

A college mini project that analyzes a public GitHub repository and explains its code in beginner-friendly language using a locally running Ollama `llama3.2` model.

## 1. Project Objective

The objective is to help a learner understand an unfamiliar code repository. The app collects a bounded set of relevant text files, summarizes repository details, and asks a local language model to describe the project structure and workflow.

## 2. Core Feature

Enter a public GitHub repository URL to clone it temporarily, detect supported source files, extract relevant text, and generate a structured explanation through local Ollama inference. The app also shows repository metrics, detected languages and technologies, short descriptions of included files, analysis notes, and Markdown and TXT download buttons.

## 3. Architecture

```text
GitHub Repository URL
        ↓
Repository Cloning
        ↓
Source Code Detection
        ↓
Code Extraction
        ↓
Local Ollama LLM
        ↓
Llama 3.2
        ↓
AI Explanation
        ↓
Streamlit Frontend
```

In the implementation, `app.py` handles the Streamlit interface, `repo_processor.py` validates and clones the repository and prepares bounded text context, and `llm.py` sends that context to Ollama's local HTTP API and returns the generated explanation.

## 4. Technology Stack

- **Local GenAI:** Python, Ollama, Llama 3.2, and local LLM inference
- **Repository processing:** GitPython and Python file handling
- **Frontend:** Streamlit
- **LLM communication:** Requests and the Ollama HTTP API (`http://localhost:11434/api/generate`)
- **System requirement:** Git must be installed and available on PATH for cloning

The Python package dependencies are listed in `requirements.txt`: Streamlit, GitPython, and Requests. Git and Ollama are installed separately. The application does not call an online AI API.

## 5. How the Application Works

1. The user enters a public GitHub repository URL in the Streamlit frontend.
2. `repo_processor.py` validates the URL and shallow-clones the repository into a temporary directory.
3. The processor skips generated and hidden directories, ignores `.env` and `.env.*` files, and identifies files with supported extensions.
4. It prioritizes files such as `README.md`, `app.py`, `main.py`, index files, and package manifests; reads selected files as text; redacts common secret patterns; and limits the text context sent for analysis.
5. The processor detects languages and selected technologies from filenames and text hints, and estimates the project type.
6. `llm.py` sends the context to the local Ollama HTTP API using the `llama3.2` model.
7. The Streamlit app displays the explanation, repository summary, important file descriptions, workflow, and analysis notes. Users can download the explanation as Markdown or TXT.
8. The temporary clone is deleted when repository processing finishes.

## 6. Installation

Install Python 3.10 or newer and Git. Open a terminal in the project folder and create a virtual environment:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, or use `.venv\Scripts\python.exe` explicitly.

Install the Python dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 7. Ollama Setup

Install Ollama for your operating system from [ollama.com/download](https://ollama.com/download). Start the Ollama service; the app expects its local API at `http://localhost:11434`.

Download the model:

```powershell
ollama pull llama3.2
ollama list
```

Keep the Ollama service running while using the app. If Ollama cannot connect or the model is missing, the app displays a user-facing error with setup guidance.

## 8. How to Run

From the project folder, with the virtual environment active:

```powershell
streamlit run app.py
```

Open the local URL printed in the terminal by Streamlit.

## 9. Example Input

Paste this public repository URL into the input field and select **Explain Repository**:

```text
https://github.com/saurabhsen848/FoodieHub
```

## 10. Expected Output

After the repository is cloned and Ollama generates an explanation, the page displays:

- Repository name and URL
- Source file count and number of files included in analysis
- Counts of detected languages and technologies, plus their names
- Estimated project type
- Expandable summaries of important included source files
- The **How It Works** workflow
- AI-generated sections for project overview, purpose, features, technologies, important files, how the project works, main workflow, code structure, and possible improvements
- Expandable security, performance, code organization, and potential improvement notes
- Buttons to download the explanation as Markdown or TXT

For repositories exceeding the file selection limit, the app displays a notice that analysis was limited to relevant files.

## 11. Security

- Repository code and setup scripts are never executed; dependencies from cloned projects are never installed.
- Files are read as text. `.env` and `.env.*` files are excluded from source extraction.
- Common secret assignment patterns, private key blocks, and GitHub token patterns are redacted before the text context is sent to Ollama.
- Clones are stored in temporary directories and removed after processing.
- Selected repository text is sent to the locally running Ollama service. The application does not use an online AI API.
- Repository contents are untrusted, and pattern-based secret redaction cannot detect every possible secret. Use public repositories without sensitive information.

## 12. Limitations

- Only public GitHub repositories are supported.
- Supported file extensions are configured in `repo_processor.py`; files outside that set are not extracted as source context.
- The analysis selects at most 15 files, limits each file to 8,000 characters, and limits the collected text content to 40,000 characters. The README excerpt is capped at 5,000 characters, and recognized package metadata is capped at 2,000 characters per file.
- Large repositories are represented by a prioritized subset, so the model does not analyze the full codebase.
- Language and technology detection uses file extensions, filenames, and text hints; detections and project type are estimates and can be incomplete or incorrect.
- Explanation quality and response time depend on the local `llama3.2` model and available hardware.
- Cloning requires Git, network access to GitHub, and a valid public repository URL.

## 13. Future Enhancements

- Add user-controlled source-file selection before analysis.
- Improve language and framework detection using more dependency manifests.
- Add more source formats while keeping strict file and text limits.
- Generate module relationship diagrams from source imports.
- Add optional local caching for repeated repository analyses.
