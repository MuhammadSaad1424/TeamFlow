import os
from pathlib import Path
from typing import List, Optional

from app.utils.validators import (
    extract_imports_from_code,
    get_file_language,
    is_binary_file,
    is_code_file,
    is_documentation_file,
    is_test_file,
)


class CodeParser:
    """Parse repository files and extract structured metadata."""

    SKIP_DIRS = {
        ".git", "node_modules", "__pycache__", ".venv", "venv",
        "dist", "build", ".next", "coverage", ".pytest_cache",
        "vendor", "target", ".idea", ".vscode",
    }

    def scan_repository(self, repo_path: str) -> List[dict]:
        files = []
        repo_root = Path(repo_path)

        for path in repo_root.rglob("*"):
            if not path.is_file():
                continue

            rel_path = str(path.relative_to(repo_root)).replace("\\", "/")
            parts = rel_path.split("/")
            if any(part in self.SKIP_DIRS for part in parts):
                continue

            if is_binary_file(rel_path) or not is_code_file(rel_path, include_docs=True):
                continue

            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            if len(content) > 500_000:
                continue

            language = get_file_language(rel_path)
            lines = content.splitlines()
            imports = extract_imports_from_code(content, language or "Python")

            files.append({
                "file_path": rel_path,
                "file_name": path.name,
                "file_extension": path.suffix,
                "file_size_bytes": path.stat().st_size,
                "language": language,
                "content": content,
                "line_count": len(lines),
                "import_count": len(imports),
                "imports": imports,
                "is_binary": False,
                "is_test_file": is_test_file(rel_path),
                "is_documentation": is_documentation_file(rel_path),
                "function_count": self._count_functions(content, language),
                "class_count": self._count_classes(content, language),
            })

        return files

    @staticmethod
    def _count_functions(content: str, language: Optional[str]) -> int:
        if not language:
            return 0
        lang = language.lower()
        count = 0
        for line in content.splitlines():
            stripped = line.strip()
            if lang == "python" and stripped.startswith("def "):
                count += 1
            elif lang in ("javascript", "typescript", "typescript jsx", "javascript jsx"):
                if "function " in stripped or "=> {" in stripped:
                    count += 1
        return count

    @staticmethod
    def _count_classes(content: str, language: Optional[str]) -> int:
        if not language:
            return 0
        lang = language.lower()
        count = 0
        for line in content.splitlines():
            stripped = line.strip()
            if lang == "python" and stripped.startswith("class "):
                count += 1
            elif lang in ("javascript", "typescript") and stripped.startswith("class "):
                count += 1
        return count

    def detect_languages(self, files: List[dict]) -> dict:
        lang_counts: dict = {}
        for f in files:
            lang = f.get("language")
            if lang:
                lang_counts[lang] = lang_counts.get(lang, 0) + f.get("line_count", 0)

        primary = max(lang_counts, key=lang_counts.get) if lang_counts else None
        return {
            "language_primary": primary,
            "languages_detected": list(lang_counts.keys()),
            "language_stats": lang_counts,
        }
