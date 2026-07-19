"""GreenCloud CLI — main entry point."""

import typer

from greencloud.commands import carbon, config, deploy, dev, status

app = typer.Typer(
    name="greencloud",
    help="GreenCloud CLI — manage your carbon-aware PaaS from the terminal.",
    no_args_is_help=True,
)

app.add_typer(deploy.app, name="deploy", help="Deployment management")
app.add_typer(dev.app, name="dev", help="Dev environment control")
app.add_typer(status.app, name="status", help="Service status and health")
app.add_typer(carbon.app, name="carbon", help="Carbon intensity and emissions")
app.add_typer(config.app, name="config", help="CLI configuration")


if __name__ == "__main__":
    app()
