from pydantic import BaseModel


class GitHubPushEvent(BaseModel):
    """Relevant fields from a GitHub push webhook payload."""
    ref: str  # e.g., "refs/heads/main"
    after: str  # commit SHA
    repository: dict  # contains clone_url, full_name, etc.
    pusher: dict  # who pushed

    @property
    def branch(self) -> str:
        """Extract branch name from ref (e.g., 'refs/heads/main' → 'main')."""
        return self.ref.removeprefix("refs/heads/")

    @property
    def commit_sha(self) -> str:
        return self.after

    @property
    def repo_url(self) -> str:
        return self.repository.get("clone_url", "")

    @property
    def repo_name(self) -> str:
        return self.repository.get("full_name", "")
