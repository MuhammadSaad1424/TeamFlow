import re
from typing import List, Optional

from app.core.config import settings
from app.utils.validators import calculate_sha256, chunk_text


class CodeChunker:
    """Split source files into semantic chunks for embedding."""

    def chunk_file(self, file_data: dict) -> List[dict]:
        content = file_data["content"]
        language = file_data.get("language", "Unknown")
        file_path = file_data["file_path"]

        semantic_chunks = self._extract_semantic_blocks(content, language)
        if semantic_chunks:
            return [
                self._build_chunk(file_data, block, idx)
                for idx, block in enumerate(semantic_chunks)
            ]

        raw_chunks = chunk_text(
            content,
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP,
        )
        return [
            self._build_chunk(
                file_data,
                {"content": c, "entity_name": None, "entity_type": "block",
                 "start_line": 1, "end_line": len(c.splitlines())},
                idx,
            )
            for idx, c in enumerate(raw_chunks)
        ]

    def _build_chunk(self, file_data: dict, block: dict, index: int) -> dict:
        content = block["content"]
        return {
            "chunk_index": index,
            "chunk_type": block.get("entity_type", "block"),
            "raw_content": content,
            "cleaned_content": content.strip(),
            "content_hash": calculate_sha256(content),
            "language": file_data.get("language"),
            "start_line_number": block.get("start_line", 1),
            "end_line_number": block.get("end_line", 1),
            "entity_name": block.get("entity_name"),
            "entity_type": block.get("entity_type"),
            "file_path": file_data["file_path"],
            "metadata": {
                "file_path": file_data["file_path"],
                "entity_name": block.get("entity_name"),
                "entity_type": block.get("entity_type"),
                "language": file_data.get("language"),
            },
        }

    def _extract_semantic_blocks(self, content: str, language: str) -> List[dict]:
        lang = (language or "").lower()
        if lang == "python":
            return self._chunk_python(content)
        if lang in ("javascript", "typescript", "typescript jsx", "javascript jsx"):
            return self._chunk_js(content)
        return []

    def _chunk_python(self, content: str) -> List[dict]:
        blocks = []
        lines = content.splitlines()
        current: List[str] = []
        current_name: Optional[str] = None
        current_type: Optional[str] = None
        start_line = 1

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("class ") or stripped.startswith("def ") or stripped.startswith("async def "):
                if current:
                    blocks.append({
                        "content": "\n".join(current),
                        "entity_name": current_name,
                        "entity_type": current_type,
                        "start_line": start_line,
                        "end_line": i - 1,
                    })
                current = [line]
                start_line = i
                if stripped.startswith("class "):
                    current_type = "class"
                    current_name = stripped.split("(")[0].replace("class ", "").strip(":")
                else:
                    current_type = "function"
                    current_name = re.sub(r"^(async )?def ", "", stripped).split("(")[0]
            elif current:
                current.append(line)

        if current:
            blocks.append({
                "content": "\n".join(current),
                "entity_name": current_name,
                "entity_type": current_type,
                "start_line": start_line,
                "end_line": len(lines),
            })

        return blocks

    def _chunk_js(self, content: str) -> List[dict]:
        blocks = []
        lines = content.splitlines()
        current: List[str] = []
        current_name: Optional[str] = None
        start_line = 1

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("class ") or stripped.startswith("function ") or "export " in stripped:
                if current:
                    blocks.append({
                        "content": "\n".join(current),
                        "entity_name": current_name,
                        "entity_type": "function",
                        "start_line": start_line,
                        "end_line": i - 1,
                    })
                current = [line]
                start_line = i
                if "function" in stripped:
                    current_name = stripped.split("(")[0].split()[-1]
                elif stripped.startswith("class "):
                    current_name = stripped.split("{")[0].replace("class ", "").strip()
            elif current:
                current.append(line)

        if current:
            blocks.append({
                "content": "\n".join(current),
                "entity_name": current_name,
                "entity_type": "function",
                "start_line": start_line,
                "end_line": len(lines),
            })

        return blocks
