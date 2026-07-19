"""Dev environment commands."""

import typer
from rich.console import Console

from greencloud.api_client import api_get, api_post, _get_agent_url

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("start")
def start():
    """Start the dev environment."""
    console.print("[bold]Starting dev environment...[/bold]")
    result = api_post("/agent/dev/start", base=_get_agent_url())
    if result:
        console.print(f"[green]Dev environment started.[/green]")
    else:
        console.print("[red]Failed to start dev environment.[/red]")


@app.command("stop")
def stop():
    """Stop the dev environment."""
    console.print("[bold]Stopping dev environment...[/bold]")
    result = api_post("/agent/dev/stop", base=_get_agent_url())
    if result:
        console.print(f"[green]Dev environment stopped.[/green]")
    else:
        console.print("[red]Failed to stop dev environment.[/red]")


@app.command("status")
def dev_status():
    """Check dev environment status."""
    result = api_get("/agent/dev/status", base=_get_agent_url())
    if result:
        running = result.get("running", False)
        if running:
            console.print("[green]Dev environment is running.[/green]")
        else:
            console.print("[dim]Dev environment is stopped.[/dim]")
    else:
        console.print("[red]Could not check dev status.[/red]")
