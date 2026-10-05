# Generative AI

A Python application that analyzes a public GitHub repository and explains its code in beginner-friendly language with a locally running Ollama model.

This repository collects the existing Generative AI project files in this folder. It currently contains one complete application; no separate assignment folders or Jupyter notebooks were present when the repository was inspected.

## Project files

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit user interface for submitting a repository and viewing its explanation. |
| `repo_processor.py` | Validates and clones a public repository, selects source files, and prepares bounded text for analysis. |
| `llm.py` | Sends the prepared context to the local Ollama API and returns the model response. |
| `requirements.txt` | Python package dependencies. |
| `README.md` | Project overview and setup instructions. |
| `.gitignore` | Excludes local environments, secrets, caches, and generated files from Git. |

## Purpose

The application helps learners understand unfamiliar codebases. It summarizes repository structure, selected files, detected languages and technologies, and the project workflow. Repository content is analyzed as text and is not executed by the application.

## Technologies

- Python
- Streamlit
- Ollama with the `llama3.2` model
- GitPython
- Requests
- Git (required to clone repositories)

Python dependencies are listed in `requirements.txt`. Ollama and Git must be installed separately.

## Setup and run

Install Python 3.10 or newer, Git, and Ollama. In a terminal opened at the project root, create and activate a virtual environment, then install the dependencies:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Download the model and start the application:

```powershell
ollama pull llama3.2
streamlit run app.py
```

Keep Ollama running while using the app. Streamlit prints the local address to open in a browser.

## Jupyter notebooks

There are no Jupyter notebooks in the current project folder. If notebooks are added later, install Jupyter with `python -m pip install notebook` and launch it from the project root with `jupyter notebook`.

## Security notes

The app expects public repository URLs. It reads selected repository files as text, limits the amount of source context, and sends that context to the locally running Ollama service. Do not include credentials in project files. Pattern-based secret detection is not comprehensive, so review files before publishing.
