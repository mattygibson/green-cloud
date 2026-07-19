"""Deployment commands."""

import typer
from rich.console import Console
from rich.table import Table

from greencloud.api_client import api_get, api_post

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("trigger")
def trigger(
    env: str = typer.Option("prod", "--env", "-e", help="Target environment (prod/dev)"),
):
    """Trigger a new deployment."""
    console.print(f"[bold]Triggering deployment to {env}...[/bold]")
    result = api_post("/deployments/trigger", {"environment": env})
    if result:
        console.print(f"[green]Deployment started:[/green] ID={result.get('id', 'unknown')}")
        console.print(f"  Status: {result.get('status', 'pending')}")
    else:
        console.print("[red]Failed to trigger deployment[/red]")


@app.command("list")
def list_deployments(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of deployments to show"),
):
    """List recent deployments."""
    deployments = api_get("/deployments")
    if not deployments:
        console.print("No deployments found.")
        return

    table = Table(title="Recent Deployments")
    table.add_column("ID", style="dim")
    table.add_column("Status")
    table.add_column("Environment")
    table.add_column("Created")

    for d in deployments[:limit]:
        status_color = {
            "deployed": "green",
            "building": "yellow",
            "failed": "red",
            "pending": "dim",
        }.get(d.get("status", ""), "white")

        table.add_row(
            str(d.get("id", "")),
            f"[{status_color}]{d.get('status', 'unknown')}[/{status_color}]",
            d.get("environment", "--"),
            d.get("created_at", "--"),
        )

    console.print(table)


@app.command("logs")
def show_logs(
    deployment_id: int = typer.Argument(..., help="Deployment ID"),
):
    """Show logs for a deployment."""
    result = api_get(f"/deployments/{deployment_id}/logs")
    if result and result.get("logs"):
        console.print(f"[bold]Logs for deployment {deployment_id}:[/bold]")
        console.print(result["logs"])
    else:
        console.print(f"No logs found for deployment {deployment_id}")


@app.command("status")
def deployment_status(
    deployment_id: int = typer.Argument(..., help="Deployment ID"),
):
    """Check status of a specific deployment."""
    result = api_get(f"/deployments/{deployment_id}")
    if result:
        console.print(f"[bold]Deployment {deployment_id}[/bold]")
        console.print(f"  Status: {result.get('status', 'unknown')}")
        console.print(f"  Environment: {result.get('environment', '--')}")
        console.print(f"  Created: {result.get('created_at', '--')}")
    else:
        console.print(f"[red]Deployment {deployment_id} not found[/red]")
