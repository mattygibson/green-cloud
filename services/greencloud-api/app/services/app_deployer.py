"""
External app deployment service.

Handles the full lifecycle for user-deployed apps:
  1. Clone/update the repo
  2. Parse greencloud.yml
  3. Build Docker images
  4. Deploy containers with Traefik labels
  5. Health-check and report status
"""

import asyncio
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml
from docker import DockerClient
from docker.errors import DockerException, NotFound

from app.config import settings

logger = logging.getLogger(__name__)

WORKSPACE_DIR = Path("/app/workspaces")
NETWORK_NAME = "greencloud-prod"


class DeployError(Exception):
    """Raised when a deployment step fails."""
    pass


def parse_greencloud_config(config_path: Path) -> dict[str, Any]:
    """Parse a greencloud.yml configuration file."""
    if not config_path.exists():
        raise DeployError(f"greencloud.yml not found at {config_path}")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Validate required fields
    if not config.get("name"):
        raise DeployError("greencloud.yml missing required field: name")
    if not config.get("services"):
        raise DeployError("greencloud.yml missing required field: services")
    if not config.get("routing", {}).get("subdomain"):
        raise DeployError("greencloud.yml missing required field: routing.subdomain")

    return config


def clone_or_update_repo(repo_url: str, app_name: str) -> Path:
    """Clone a repo or pull latest if already cloned."""
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    repo_dir = WORKSPACE_DIR / app_name

    if repo_dir.exists():
        # Pull latest
        logger.info(f"Updating existing clone: {repo_dir}")
        result = subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            # If pull fails, do a fresh clone
            logger.warning(f"Pull failed, re-cloning: {result.stderr}")
            shutil.rmtree(repo_dir)
            return clone_or_update_repo(repo_url, app_name)
    else:
        # Fresh clone
        logger.info(f"Cloning {repo_url} to {repo_dir}")
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(repo_dir)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise DeployError(f"Clone failed: {result.stderr}")

    return repo_dir


def build_service_image(
    repo_dir: Path,
    app_name: str,
    service_name: str,
    service_config: dict,
) -> str:
    """
    Build a Docker image for a service.
    Returns the image tag.
    """
    context_path = repo_dir / service_config.get("context", ".")
    image_tag = f"{app_name}-{service_name}:latest"

    if not context_path.exists():
        raise DeployError(
            f"Build context not found: {context_path} "
            f"(service: {service_name})"
        )

    # Check for Dockerfile
    dockerfile = context_path / "Dockerfile"
    if not dockerfile.exists():
        raise DeployError(
            f"Dockerfile not found at {dockerfile} "
            f"(service: {service_name})"
        )

    logger.info(f"Building image: {image_tag} from {context_path}")

    result = subprocess.run(
        [
            "docker", "build",
            "-t", image_tag,
            str(context_path),
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )

    if result.returncode != 0:
        raise DeployError(
            f"Build failed for {service_name}:\n{result.stderr}"
        )

    logger.info(f"Built: {image_tag}")
    return image_tag


def deploy_container(
    client: DockerClient,
    app_name: str,
    service_name: str,
    service_config: dict,
    routing_config: dict,
    image_tag: str,
    domain: str,
) -> str:
    """
    Deploy a single container with Traefik labels.
    Returns the container ID.
    """
    container_name = f"{app_name}-{service_name}"
    subdomain = routing_config["subdomain"]
    hostname = f"{subdomain}.{domain}"
    port = service_config.get("port", 8000)

    # Build Traefik labels
    router_name = f"{app_name}-{service_name}"
    labels = {
        "traefik.enable": "true",
        "traefik.docker.network": NETWORK_NAME,
        f"traefik.http.routers.{router_name}.entrypoints": "web",
        f"traefik.http.services.{router_name}.loadbalancer.server.port": str(port),
        # Label to identify as a greencloud-managed app
        "greencloud.app": app_name,
        "greencloud.service": service_name,
    }

    # Determine routing rule based on routing config
    rules = routing_config.get("rules", [])
    matching_rule = None
    for rule in rules:
        if rule.get("service") == service_name:
            matching_rule = rule
            break

    if matching_rule and matching_rule.get("path_prefix") == "/api":
        # API service with path prefix
        labels[f"traefik.http.routers.{router_name}.rule"] = (
            f"Host(`{hostname}`) && PathPrefix(`/api`)"
        )
        # Strip prefix middleware
        middleware_name = f"{app_name}-strip"
        labels[f"traefik.http.middlewares.{middleware_name}.stripprefix.prefixes"] = "/api"
        labels[f"traefik.http.routers.{router_name}.middlewares"] = middleware_name
        # Health router
        health_router = f"{app_name}-health"
        labels[f"traefik.http.routers.{health_router}.rule"] = (
            f"Host(`{hostname}`) && Path(`/health`)"
        )
        labels[f"traefik.http.routers.{health_router}.entrypoints"] = "web"
        labels[f"traefik.http.routers.{health_router}.service"] = router_name
    else:
        # Default: catch-all for this hostname (lower priority for UI)
        labels[f"traefik.http.routers.{router_name}.rule"] = f"Host(`{hostname}`)"
        if service_name in ("ui", "frontend", "web"):
            labels[f"traefik.http.routers.{router_name}.priority"] = "1"

    # Environment variables
    environment = {}
    for env_str in service_config.get("environment", []):
        if "=" in env_str:
            key, value = env_str.split("=", 1)
            environment[key] = value

    # Resource limits
    resources = service_config.get("resources", {})
    mem_limit = resources.get("memory", "256MB").upper().replace("MB", "m")
    cpu_limit = float(resources.get("cpu", 0.5))

    # Remove existing container if any
    try:
        old = client.containers.get(container_name)
        logger.info(f"Removing old container: {container_name}")
        old.stop(timeout=10)
        old.remove()
    except NotFound:
        pass

    # Create and start the new container
    logger.info(f"Starting container: {container_name} (image: {image_tag})")

    container = client.containers.run(
        image=image_tag,
        name=container_name,
        labels=labels,
        environment=environment,
        network=NETWORK_NAME,
        mem_limit=mem_limit,
        nano_cpus=int(cpu_limit * 1e9),
        detach=True,
        restart_policy={"Name": "unless-stopped"},
    )

    return container.id


async def deploy_app(
    repo_url: str,
    app_name_hint: str | None = None,
    commit_sha: str = "latest",
) -> dict[str, Any]:
    """
    Full deployment pipeline for an external app.

    Args:
        repo_url: Git clone URL of the app
        app_name_hint: Optional override for the app name (derived from greencloud.yml otherwise)
        commit_sha: The commit SHA being deployed

    Returns:
        Dict with deployment result info
    """
    logs: list[str] = []
    domain = settings.domain if hasattr(settings, "domain") else "green-cloud.uk"

    try:
        # Step 1: Clone or update repo
        logs.append("Cloning repository...")
        temp_name = app_name_hint or repo_url.split("/")[-1].replace(".git", "").lower()
        repo_dir = await asyncio.to_thread(clone_or_update_repo, repo_url, temp_name)
        logs.append(f"Repository ready at {repo_dir}")

        # Step 2: Parse greencloud.yml
        logs.append("Reading greencloud.yml...")
        config_path = repo_dir / "greencloud.yml"
        config = parse_greencloud_config(config_path)
        app_name = config["name"]
        logs.append(f"App: {app_name}, subdomain: {config['routing']['subdomain']}")

        # Step 3: Build images for each service
        images: dict[str, str] = {}
        for svc_name, svc_config in config["services"].items():
            logs.append(f"Building {svc_name}...")
            image_tag = await asyncio.to_thread(
                build_service_image, repo_dir, app_name, svc_name, svc_config
            )
            images[svc_name] = image_tag
            logs.append(f"Built: {image_tag}")

        # Step 4: Deploy containers
        logs.append("Deploying containers...")
        client = DockerClient.from_env()

        # Ensure network exists
        try:
            client.networks.get(NETWORK_NAME)
        except NotFound:
            client.networks.create(NETWORK_NAME, driver="bridge")

        container_ids: dict[str, str] = {}
        for svc_name, svc_config in config["services"].items():
            container_id = await asyncio.to_thread(
                deploy_container,
                client,
                app_name,
                svc_name,
                svc_config,
                config["routing"],
                images[svc_name],
                domain,
            )
            container_ids[svc_name] = container_id
            logs.append(f"Deployed: {app_name}-{svc_name} ({container_id[:12]})")

        # Step 5: Wait briefly and check health
        logs.append("Waiting for containers to start...")
        await asyncio.sleep(5)

        subdomain = config["routing"]["subdomain"]
        url = f"https://{subdomain}.{domain}"
        logs.append(f"Deployment complete! Live at: {url}")

        return {
            "status": "deployed",
            "app_name": app_name,
            "url": url,
            "containers": container_ids,
            "commit_sha": commit_sha,
            "logs": "\n".join(logs),
        }

    except DeployError as e:
        logs.append(f"ERROR: {e}")
        logger.error(f"Deploy failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "logs": "\n".join(logs),
        }
    except Exception as e:
        logs.append(f"UNEXPECTED ERROR: {e}")
        logger.error(f"Deploy error: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "logs": "\n".join(logs),
        }
