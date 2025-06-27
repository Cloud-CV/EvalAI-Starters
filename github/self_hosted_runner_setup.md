# Self-Hosted Runner Setup Guide

This guide will help you set up a GitHub Actions self-hosted runner for local EvalAI challenge development.

## Overview

When developing EvalAI challenges locally, GitHub's hosted runners cannot access your localhost server. Self-hosted runners solve this by running the GitHub Actions workflow directly on your local machine, giving the workflow access to your local EvalAI server.

## Prerequisites

- Local EvalAI server running and accessible
- GitHub repository with appropriate permissions
- Local machine with internet connectivity

## Step 1: Download and Configure the Runner

### 1.1 Navigate to Runner Settings
1. Go to your GitHub repository
2. Click on **Settings** tab
3. Click on **Actions** in the left sidebar
4. Click on **Runners**
5. Click **New self-hosted runner**

### 1.2 Download the Runner
Follow the download instructions for your operating system:

**Linux/macOS:**
```bash
# Create a folder
mkdir actions-runner && cd actions-runner

# Download the latest runner package
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract the installer
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz
```

**Windows:**
```powershell
# Create a folder under the drive root
mkdir \actions-runner ; cd \actions-runner

# Download the latest runner package
Invoke-WebRequest -Uri https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-win-x64-2.311.0.zip -OutFile actions-runner-win-x64-2.311.0.zip

# Extract the installer
Add-Type -AssemblyName System.IO.Compression.FileSystem ; [System.IO.Compression.ZipFile]::ExtractToDirectory("$PWD\actions-runner-win-x64-2.311.0.zip", "$PWD")
```

### 1.3 Configure the Runner
```bash
# Configure the runner (follow the prompts)
./config.sh --url https://github.com/YOUR_USERNAME/YOUR_REPO --token YOUR_TOKEN

# When prompted for runner group, press Enter for default
# When prompted for runner name, you can use: localhost-runner
# When prompted for labels, add: self-hosted,localhost-dev
# When prompted for work folder, press Enter for default
```

## Step 2: Start the Runner

### 2.1 Run the Runner
```bash
# Start the runner
./run.sh
```

The runner will now listen for jobs from GitHub Actions.

### 2.2 Run as a Service (Optional)
For persistent operation, you can install the runner as a service:

**Linux/macOS:**
```bash
sudo ./svc.sh install
sudo ./svc.sh start
```

**Windows (run as Administrator):**
```powershell
.\svc.sh install
.\svc.sh start
```

## Step 3: Configure Your EvalAI Server

### 3.1 Update host_config.json
Make sure your `github/host_config.json` is configured for localhost:

```json
{
    "token": "your_evalai_auth_token",
    "team_pk": "your_team_primary_key", 
    "evalai_host_url": "http://localhost:8888"
}
```

### 3.2 Start Your EvalAI Server
Ensure your local EvalAI server is running and accessible:

```bash
# If using Django development server
python manage.py runserver 0.0.0.0:8888

# If using Docker
docker-compose up -d

# Verify server is running
curl http://localhost:8888/api/
```

**Important:** Make sure your server binds to `0.0.0.0` (all interfaces) rather than `127.0.0.1` (localhost only), especially if your runner is on a different machine or container.

## Step 4: Test the Setup

### 4.1 Trigger a Workflow
1. Push to the `challenge` branch or create a pull request
2. Go to the **Actions** tab in your repository
3. You should see the workflow running on your self-hosted runner

### 4.2 Monitor the Workflow
The workflow will:
1. Detect localhost configuration
2. Use your self-hosted runner
3. Perform health checks on your local server
4. Process the challenge configuration

## Troubleshooting

### Runner Not Appearing
- Check if the runner process is still running
- Verify the registration token hasn't expired
- Check network connectivity to GitHub

### Server Connection Issues
```bash
# Test server connectivity manually
curl -v http://localhost:8888/
curl -v http://localhost:8888/api/

# Check if server is listening on correct interface
netstat -tlnp | grep 8888
ss -tlnp | grep 8888
```

### Workflow Still Using GitHub-Hosted Runner
- Verify your `host_config.json` contains a localhost URL
- Check that the runner has the correct labels
- Ensure the runner is online and available

### Permission Issues
- Make sure the runner has appropriate file system permissions
- On Linux/macOS, avoid running as root if possible
- Check that the runner can access network resources

## Security Considerations

### Local Development Only
- Only use self-hosted runners for development/testing
- Don't use self-hosted runners for production workloads
- Be cautious about what code you run on your local machine

### Network Security
- Ensure your local EvalAI server is not exposed to the internet
- Use firewall rules to restrict access if needed
- Monitor runner logs for unexpected activity

### Token Management
- Keep your GitHub and EvalAI tokens secure
- Rotate tokens regularly
- Don't commit tokens to version control

## Advanced Configuration

### Multiple Runners
You can set up multiple runners for load balancing:
```bash
# Configure additional runners with different names
./config.sh --url https://github.com/YOUR_USERNAME/YOUR_REPO --token YOUR_TOKEN --name localhost-runner-2
```

### Custom Labels
Add custom labels to target specific runners:
```bash
# During configuration, add custom labels
# Example: self-hosted,localhost-dev,linux,x64,gpu
```

Then target them in your workflow:
```yaml
runs-on: [self-hosted, localhost-dev, gpu]
```

### Environment Variables
Set environment variables for the runner:
```bash
# Create .env file in runner directory
echo "EVALAI_DEBUG=true" >> .env
echo "CUSTOM_CONFIG_PATH=/path/to/config" >> .env
```

## Best Practices

1. **Keep Runners Updated**: Regularly update your self-hosted runners
2. **Monitor Resources**: Keep an eye on CPU, memory, and disk usage
3. **Clean Workspace**: Periodically clean the runner's work directory
4. **Log Management**: Monitor and rotate runner logs
5. **Backup Configuration**: Keep a backup of your runner configuration

## Getting Help

If you encounter issues:

1. Check the runner logs in the `_diag` folder
2. Review the GitHub Actions workflow logs
3. Test EvalAI server connectivity manually
4. Check GitHub's self-hosted runner documentation
5. Open an issue in your repository with detailed error information

## Example Complete Setup Script

```bash
#!/bin/bash
# complete-setup.sh - Automated setup script

set -e

echo "🚀 Setting up self-hosted runner for EvalAI local development"

# Download and extract runner
mkdir -p actions-runner && cd actions-runner
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

echo "📝 Please run the following command to configure your runner:"
echo "./config.sh --url https://github.com/YOUR_USERNAME/YOUR_REPO --token YOUR_TOKEN --name localhost-runner --labels self-hosted,localhost-dev"
echo ""
echo "Then start the runner with:"
echo "./run.sh"
```

This setup enables seamless local EvalAI challenge development with GitHub Actions! 