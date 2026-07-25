from typing import Optional
import re
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


def sanitize_input(text: str, max_length: int = 2000) -> str:
    """Sanitize user input."""
    if not text:
        return ""
    
    # Remove null bytes
    text = text.replace('\0', '')
    
    # Limit length
    text = text[:max_length]
    
    # Strip whitespace
    text = text.strip()
    
    return text


def validate_github_url(url: str) -> bool:
    """Validate GitHub repository URL."""
    pattern = r'^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(?:\.git)?/?$'
    return bool(re.match(pattern, url))


def extract_github_info(url: str) -> Optional[tuple]:
    """Extract owner and repo from GitHub URL."""
    match = re.match(r'^https://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?/?$', url)
    if match:
        return match.group(1), match.group(2)
    return None


def hash_api_key(api_key: str) -> str:
    """Hash API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_api_key_prefix(api_key: str) -> str:
    """Get prefix of API key for display."""
    return api_key[:8] + "..." if len(api_key) > 8 else "..."


def calculate_sha256(content: str) -> str:
    """Calculate SHA256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        
        if chunk.strip():
            chunks.append(chunk)
        
        start += chunk_size - overlap
    
    return chunks


def is_code_file(file_path: str, include_docs: bool = False) -> bool:
    """Check if file is a code file."""
    code_extensions = {
        '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cpp', '.c', '.h',
        '.cs', '.go', '.rb', '.php', '.swift', '.kt', '.scala', '.r',
        '.sql', '.sh', '.bash', '.json', '.xml', '.yaml', '.yml', '.toml',
        '.html', '.css', '.scss', '.less',
    }
    
    doc_extensions = {
        '.md', '.rst', '.txt', '.adoc',
    }
    
    ext = '.' + file_path.split('.')[-1].lower() if '.' in file_path else ''
    
    if include_docs:
        return ext in code_extensions or ext in doc_extensions
    
    return ext in code_extensions


def get_file_language(file_path: str) -> Optional[str]:
    """Detect programming language from file extension."""
    extension_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript JSX',
        '.jsx': 'JavaScript JSX',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.h': 'C Header',
        '.cs': 'C#',
        '.go': 'Go',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.r': 'R',
        '.sql': 'SQL',
        '.sh': 'Shell',
        '.bash': 'Bash',
        '.json': 'JSON',
        '.xml': 'XML',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.toml': 'TOML',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.less': 'LESS',
        '.md': 'Markdown',
        '.rst': 'ReStructuredText',
    }
    
    ext = '.' + file_path.split('.')[-1].lower() if '.' in file_path else ''
    return extension_map.get(ext)


def is_binary_file(file_path: str) -> bool:
    """Check if file is binary."""
    binary_extensions = {
        '.exe', '.bin', '.dll', '.so', '.dylib', '.o', '.a', '.lib',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg', '.webp',
        '.mp3', '.mp4', '.avi', '.mov', '.mkv',
        '.zip', '.tar', '.gz', '.rar', '.7z',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    }
    
    ext = '.' + file_path.split('.')[-1].lower() if '.' in file_path else ''
    return ext in binary_extensions


def is_test_file(file_path: str) -> bool:
    """Check if file is a test file."""
    test_patterns = [
        'test_', '_test.', '.test.', 'tests/',
        'spec_', '_spec.', '.spec.',
        '__tests__/',
    ]
    
    normalized_path = file_path.lower().replace('\\', '/')
    return any(pattern in normalized_path for pattern in test_patterns)


def is_documentation_file(file_path: str) -> bool:
    """Check if file is documentation."""
    doc_patterns = [
        'readme', 'changelog', 'license', 'contributing',
        'docs/', 'documentation/', 'guide/',
    ]
    
    normalized_path = file_path.lower().replace('\\', '/')
    return any(pattern in normalized_path for pattern in doc_patterns)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def extract_imports_from_code(code: str, language: str) -> list:
    """Extract import statements from code."""
    imports = []
    lines = code.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if language.lower() in ['python']:
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)
        
        elif language.lower() in ['javascript', 'typescript']:
            if line.startswith('import ') or line.startswith('require('):
                imports.append(line)
        
        elif language.lower() == 'java':
            if line.startswith('import '):
                imports.append(line)
        
        elif language.lower() in ['c', 'c++']:
            if line.startswith('#include '):
                imports.append(line)
    
    return imports


def extract_function_signature(code: str, language: str) -> Optional[str]:
    """Extract function signature from code block."""
    # This is a simplified version - in production, use AST parsing
    if language.lower() == 'python':
        for line in code.split('\n'):
            if line.strip().startswith('def '):
                return line.strip()
    
    elif language.lower() in ['javascript', 'typescript']:
        for line in code.split('\n'):
            if 'function' in line or '=>' in line:
                return line.strip()
    
    return None


def safe_json_dumps(obj: any) -> str:
    """Safely serialize object to JSON."""
    try:
        return json.dumps(obj, default=str)
    except Exception as e:
        logger.error(f"JSON serialization error: {str(e)}")
        return json.dumps({"error": "Serialization failed"})
