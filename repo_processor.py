"""Safely clone public GitHub repositories and extract bounded text context."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from git import GitCommandError, Repo

SOURCE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".html", ".css", ".json", ".md", ".go", ".rs", ".c", ".cpp", ".h", ".cs", ".php", ".rb", ".sql", ".sh"}
IGNORED_DIRS = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build", "target", "vendor"}
IGNORED_FILES = {".env"}
MAX_FILES = 15
MAX_FILE_CHARS = 8_000
MAX_TOTAL_CHARS = 40_000


class RepositoryError(ValueError):
    """A user-facing repository validation or inspection error."""


def validate_github_url(url: str) -> str:
    """Return a normalized HTTPS clone URL for a GitHub owner/repository URL."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"https", "http"} or parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        raise RepositoryError("Enter a GitHub URL such as https://github.com/owner/repository.")
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) != 2:
        raise RepositoryError("Use a repository URL in the form https://github.com/owner/repository.")
    owner, repo = parts
    repo = repo.removesuffix(".git")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner) or not re.fullmatch(r"[A-Za-z0-9_.-]+", repo) or repo in {"", ".", ".."}:
        raise RepositoryError("The owner or repository name contains unsupported characters.")
    return f"https://github.com/{owner}/{repo}.git"


def _safe_text(path: Path) -> str:
    """Read text only and redact common credential patterns before model use."""
    try:
        data = path.read_bytes()
        if b"\0" in data:
            return ""
        content = data.decode("utf-8", errors="replace")
    except OSError:
        return ""
    content = re.sub(r"(?im)^\s*(?:[A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD)[A-Z0-9_]*)\s*[:=]\s*[^\r\n]+", "[REDACTED_SECRET_ASSIGNMENT]", content)
    content = re.sub(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----", "[REDACTED_PRIVATE_KEY]", content)
    return re.sub(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b", "[REDACTED_GITHUB_TOKEN]", content)


def _priority(path: Path) -> tuple[int, str]:
    preferred = {"readme.md": 0, "app.py": 1, "main.py": 2, "index.js": 3, "index.ts": 3, "index.jsx": 3,
                 "index.tsx": 3, "index.html": 3, "package.json": 4, "requirements.txt": 4, "pyproject.toml": 4,
                 "vite.config.js": 5, "vite.config.ts": 5}
    return preferred.get(path.name.lower(), 10), str(path).lower()


def _detect_metadata(files: list[Path], root: Path, readme: str) -> tuple[list[str], list[str], str]:
    suffix_languages = {".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript", ".java": "Java", ".html": "HTML", ".css": "CSS", ".go": "Go", ".rs": "Rust", ".c": "C", ".cpp": "C++", ".cs": "C#", ".php": "PHP", ".rb": "Ruby", ".sql": "SQL", ".sh": "Shell"}
    languages = sorted({suffix_languages[p.suffix.lower()] for p in files if p.suffix.lower() in suffix_languages})
    names = {p.name.lower() for p in files}
    probe = (readme + " " + " ".join(_safe_text(root / p)[:4000] for p in files[:MAX_FILES])).lower()
    tech_rules = [("Python", lambda: ".py" in {p.suffix.lower() for p in files}), ("JavaScript", lambda: bool({".js", ".jsx"} & {p.suffix.lower() for p in files})),
        ("React", lambda: bool(re.search(r"\breact\b|from ['\"]react['\"]", probe))), ("Node.js", lambda: "package.json" in names or "node.js" in probe),
        ("Express", lambda: bool(re.search(r"\bexpress\b", probe))), ("MongoDB", lambda: bool(re.search(r"\bmongodb\b|mongoose", probe))),
        ("HTML", lambda: ".html" in {p.suffix.lower() for p in files}), ("CSS", lambda: ".css" in {p.suffix.lower() for p in files}),
        ("Java", lambda: ".java" in {p.suffix.lower() for p in files}), ("Streamlit", lambda: "streamlit" in probe), ("Vite", lambda: any(n.startswith("vite.config.") for n in names) or '"vite"' in probe)]
    technologies = [name for name, detect in tech_rules if detect()]
    description = " ".join(readme.split())[:600].lower()
    if "streamlit" in probe: project_type = "Streamlit application"
    elif "react" in probe: project_type = "React web application"
    elif "express" in probe: project_type = "Node.js web service"
    elif "package.json" in names: project_type = "JavaScript application"
    elif any(p.suffix.lower() == ".py" for p in files): project_type = "Python application"
    elif any(p.suffix.lower() in {".html", ".css"} for p in files): project_type = "Web project"
    else: project_type = "Software project"
    if description and any(word in description for word in ("library", "framework", " cli ")): project_type = "Project type inferred from repository files"
    return languages, technologies, project_type


def _explain_file(path: str) -> str:
    name = Path(path).name.lower()
    descriptions = {"readme.md": "Introduces the project, its purpose, setup, and usage.", "app.py": "Likely the main application entry point.", "main.py": "Likely starts the Python application or its main workflow.", "package.json": "Lists JavaScript project metadata, scripts, and dependencies.", "requirements.txt": "Lists Python dependencies used by the project.", "index.html": "Provides the main HTML page structure.", "index.js": "Likely the JavaScript application entry point.", "index.ts": "Likely the TypeScript application entry point."}
    return descriptions.get(name, f"Contains {Path(path).suffix.lstrip('.').upper() or 'project'} source code used by the application.")


def analyze_repository(url: str) -> dict:
    """Clone into a temporary directory, extract bounded source context, then clean up."""
    clone_url = validate_github_url(url)
    try:
        with tempfile.TemporaryDirectory(prefix="repo-explainer-") as temporary_dir:
            root = Path(temporary_dir) / "repository"
            Repo.clone_from(clone_url, root, depth=1, multi_options=["--no-tags"])
            all_files: list[Path] = []
            for current, dirs, names in os.walk(root):
                dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS and not d.startswith("."))
                for name in names:
                    path = Path(current) / name
                    relative = path.relative_to(root)
                    if name.lower() in IGNORED_FILES or name.lower().startswith(".env."):
                        continue
                    if path.suffix.lower() in SOURCE_EXTENSIONS:
                        all_files.append(relative)
            all_files.sort(key=_priority)
            readme_path = next((p for p in (root / "README.md", root / "README.MD", root / "readme.md") if p.is_file()), None)
            readme = _safe_text(readme_path) if readme_path else ""
            if not all_files:
                raise RepositoryError("This repository is empty or contains no supported source files.")
            selected = all_files[:MAX_FILES]
            languages, technologies, project_type = _detect_metadata(all_files, root, readme)
            warnings = []
            if len(all_files) > MAX_FILES:
                warnings.append("Large repository detected. The analysis was limited to the most relevant source files.")
            sections: list[str] = []
            total = 0
            if readme:
                readme = readme[:5_000]
                sections.append(f"### README.md\n{readme}")
                total += len(readme)
            for metadata_name in ("package.json", "requirements.txt", "pyproject.toml", "pom.xml"):
                metadata_path = root / metadata_name
                if metadata_path.is_file():
                    metadata = _safe_text(metadata_path)[:2_000]
                    if metadata and total + len(metadata) <= MAX_TOTAL_CHARS:
                        sections.append(f"### {metadata_name}\n```text\n{metadata}\n```")
                        total += len(metadata)
            included = []
            for relative in selected:
                content = _safe_text(root / relative)
                if not content.strip():
                    continue
                if len(content) > MAX_FILE_CHARS:
                    content = content[:MAX_FILE_CHARS] + "\n[File truncated for size.]"
                remaining = MAX_TOTAL_CHARS - total
                if remaining <= 0:
                    warnings.append("The total context limit was reached; remaining files were omitted.")
                    break
                content = content[:remaining]
                total += len(content)
                included.append(relative.as_posix())
                sections.append(f"### {relative.as_posix()}\n```{relative.suffix.lstrip('.') or 'text'}\n{content}\n```")
            if not included:
                raise RepositoryError("No readable supported source files were found in this repository.")
            repo_name = clone_url.removesuffix(".git").rsplit("/", 1)[-1]
            return {"url": clone_url.removesuffix(".git"), "repository_name": repo_name,
                "summary": f"Inspected {repo_name} and extracted {len(included)} source file(s) for a bounded explanation.",
                "source_file_count": len(all_files), "included_file_count": len(included), "important_files": included,
                "file_explanations": [{"name": f, "explanation": _explain_file(f)} for f in included],
                "languages": languages, "technologies": technologies, "project_type": project_type,
                "warnings": warnings, "context": "\n\n".join(sections)}
    except GitCommandError as exc:
        detail = str(exc.stderr or exc).strip().splitlines()
        message = detail[-1] if detail else "Git could not clone this repository."
        if "not found" in message.lower() or "repository does not exist" in message.lower():
            raise RepositoryError("Repository not found. Check the owner and repository name and confirm it is public.") from exc
        if "not recognized" in message.lower() or "cannot find" in message.lower() or "git is not" in message.lower():
            raise RepositoryError("Git is unavailable. Install Git and ensure it is on your PATH, then restart the app.") from exc
        raise RepositoryError(f"Could not clone the repository. Check that it is public and the URL is correct. ({message})") from exc
    except OSError as exc:
        raise RepositoryError(f"Repository inspection failed: {exc}") from exc
