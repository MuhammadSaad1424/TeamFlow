import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import httpx

from app.utils.validators import extract_github_info


class GitHubCloner:
    """Clone or download GitHub repositories for indexing."""

    @staticmethod
    async def clone_repository(
        repo_url: str,
        access_token: Optional[str] = None,
        target_dir: Optional[str] = None,
    ) -> Tuple[str, dict]:
        info = extract_github_info(repo_url.rstrip("/"))
        if not info:
            raise ValueError("Invalid GitHub URL")

        owner, repo_name = info
        clone_url = repo_url.rstrip("/")
        if access_token and access_token != "dev-token":
            clone_url = f"https://{access_token}@github.com/{owner}/{repo_name}.git"

        work_dir = target_dir or tempfile.mkdtemp(prefix="teamflow_")
        repo_path = os.path.join(work_dir, repo_name)

        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, repo_path],
                check=True,
                capture_output=True,
                text=True,
                timeout=300,
            )
        except subprocess.CalledProcessError:
            await GitHubCloner._download_zip(owner, repo_name, repo_path, access_token)

        metadata = await GitHubCloner._fetch_github_metadata(owner, repo_name, access_token)
        return repo_path, metadata

    @staticmethod
    async def _download_zip(
        owner: str,
        repo_name: str,
        repo_path: str,
        access_token: Optional[str] = None,
    ) -> None:
        import zipfile

        url = f"https://github.com/{owner}/{repo_name}/archive/refs/heads/main.zip"
        headers = {}
        if access_token and access_token != "dev-token":
            headers["Authorization"] = f"token {access_token}"

        async with httpx.AsyncClient(follow_redirects=True, timeout=120) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 404:
                url = f"https://github.com/{owner}/{repo_name}/archive/refs/heads/master.zip"
                resp = await client.get(url, headers=headers)
            resp.raise_for_status()

        zip_path = repo_path + ".zip"
        os.makedirs(os.path.dirname(repo_path), exist_ok=True)
        with open(zip_path, "wb") as f:
            f.write(resp.content)

        extract_dir = os.path.dirname(repo_path)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        os.remove(zip_path)
        extracted = next(Path(extract_dir).glob(f"{repo_name}-*"))
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
        shutil.move(str(extracted), repo_path)

    @staticmethod
    async def _fetch_github_metadata(
        owner: str,
        repo_name: str,
        access_token: Optional[str] = None,
    ) -> dict:
        headers = {"Accept": "application/vnd.github+json"}
        if access_token and access_token != "dev-token":
            headers["Authorization"] = f"Bearer {access_token}"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"https://api.github.com/repos/{owner}/{repo_name}",
                    headers=headers,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "github_repo_id": data.get("id"),
                        "description": data.get("description"),
                        "language_primary": data.get("language"),
                        "github_stars": data.get("stargazers_count", 0),
                        "github_forks": data.get("forks_count", 0),
                        "is_fork": data.get("fork", False),
                        "is_private": data.get("private", False),
                        "repository_size_kb": data.get("size", 0),
                    }
        except Exception:
            pass

        return {
            "github_repo_id": None,
            "description": None,
            "language_primary": None,
            "github_stars": 0,
            "github_forks": 0,
            "is_fork": False,
            "is_private": False,
            "repository_size_kb": 0,
        }

    @staticmethod
    def cleanup(repo_path: str) -> None:
        parent = os.path.dirname(repo_path)
        if parent and "teamflow_" in parent:
            shutil.rmtree(parent, ignore_errors=True)
        elif os.path.exists(repo_path):
            shutil.rmtree(repo_path, ignore_errors=True)
