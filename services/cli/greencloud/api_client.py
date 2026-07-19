"""API client for GreenCloud services."""

import httpx

from greencloud.config_store import get_config


def _get_headers() -> dict[str, str]:
    """Get request headers including auth if configured."""
    config = get_config()
    headers = {"Accept": "application/json"}
    if config.get("api_key"):
        headers["Authorization"] = f"Bearer {config['api_key']}"
    return headers


def _get_base_url() -> str:
    """Get the API base URL from config."""
    config = get_config()
    return config.get("api_url", "http://localhost:8000")


def _get_carbon_url() -> str:
    """Get the Carbon Engine base URL from config."""
    config = get_config()
    return config.get("carbon_url", "http://localhost:8002")


def _get_agent_url() -> str:
    """Get the Agent base URL from config."""
    config = get_config()
    return config.get("agent_url", "http://localhost:8001")


def api_get(path: str, base: str | None = None) -> dict | list | None:
    """Make a GET request to the GreenCloud API."""
    url = (base or _get_base_url()) + path
    try:
        resp = httpx.get(url, headers=_get_headers(), timeout=10.0)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            from rich.console import Console
            Console().print("[red]Authentication failed.[/red] Run: greencloud config set api-key <key>")
            raise SystemExit(1)
        if e.response.status_code == 403:
            from rich.console import Console
            Console().print("[red]Permission denied.[/red] Your API key lacks the required role.")
            raise SystemExit(1)
        raise
    except httpx.ConnectError:
        from rich.console import Console
        Console().print(f"[red]Cannot connect to {url}[/red]")
        raise SystemExit(1)


def api_post(path: str, data: dict | None = None, base: str | None = None) -> dict | None:
    """Make a POST request to the GreenCloud API."""
    url = (base or _get_base_url()) + path
    try:
        resp = httpx.post(url, json=data, headers=_get_headers(), timeout=30.0)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            from rich.console import Console
            Console().print("[red]Authentication failed.[/red]")
            raise SystemExit(1)
        raise
    except httpx.ConnectError:
        from rich.console import Console
        Console().print(f"[red]Cannot connect to {url}[/red]")
        raise SystemExit(1)


def api_delete(path: str, base: str | None = None) -> bool:
    """Make a DELETE request to the GreenCloud API."""
    url = (base or _get_base_url()) + path
    try:
        resp = httpx.delete(url, headers=_get_headers(), timeout=10.0)
        resp.raise_for_status()
        return True
    except httpx.ConnectError:
        return False
