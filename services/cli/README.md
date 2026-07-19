# GreenCloud CLI

Command-line tool for managing your GreenCloud PaaS.

## Install

```bash
cd services/cli
pip install -e .
# or
pipx install .
```

## Configure

```bash
# Point to your API (defaults to localhost)
greencloud config set api_url https://api.green-cloud.uk
greencloud config set carbon_url https://carbon.green-cloud.uk
greencloud config set agent_url http://localhost:8001

# Set API key for authentication
greencloud config set api_key your-secret-key

# View config
greencloud config show
```

## Commands

```bash
# Status
greencloud status              # Overview of all services
greencloud status health       # Detailed health + system resources

# Deployments
greencloud deploy trigger      # Trigger deployment
greencloud deploy list         # Recent deployments
greencloud deploy status <id>  # Check specific deployment
greencloud deploy logs <id>    # View build logs

# Dev environment
greencloud dev start           # Start dev stack
greencloud dev stop            # Stop dev stack
greencloud dev status          # Check if dev is running

# Carbon
greencloud carbon              # Current grid intensity + status
greencloud carbon emissions    # Cumulative emissions data
greencloud carbon power        # Current power draw

# Config
greencloud config set <key> <value>
greencloud config show
```

## Config Location

Stored at `~/.greencloud/config.yml`
