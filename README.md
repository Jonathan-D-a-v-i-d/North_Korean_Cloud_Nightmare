# 🇰🇵 North Korean Cloud Nightmare

<img src="./logo.png" alt="North Korean Cloud Nightmare" width="400"/>


**Advanced Persistent Threat Simulation Platform**

A comprehensive simulation of North Korean APT-style attack scenarios for security demonstrations, training, and sales engineering purposes.

## 🚀 Run Locally (Free)

If you don’t want to use GitHub Codespaces (which consumes billing),  
you can run this repo locally with **VS Code Dev Containers**:

1. Install:
   - [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - [VS Code](https://code.visualstudio.com/)
   - [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

2. Clone the repo:
   ```bash
   git clone https://github.com/Jonathan-D-a-v-i-d/North_Korean_Cloud_Nightmare.git
   cd North_Korean_Cloud_Nightmare
   code .
   ```

3. When prompted, click **"Reopen in Container"** to build the dev environment.

## ⚙️ Configuration Setup

Before running any scenarios, you need to configure your environment:

### 1. AWS Configuration
Set up your AWS credentials and region:

```bash
# Configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### 2. Pulumi Configuration

**Option A: Environment Variable (Recommended for CI/CD)**
```bash
# Get your token from https://app.pulumi.com/account/tokens
export PULUMI_ACCESS_TOKEN=your_pulumi_token_here
```

**Option B: Interactive Login (Recommended for Development)**
```bash
# Login from the Infra directory
cd Infra
pulumi login
cd ..
```

**Option C: Use Environment Setup Script (Recommended for Sales Engineers)**
```bash
# Interactive script that prompts for credentials and sets them up
source setup-env.sh
```

**Option D: Use Built-in Setup Command (For validation)**
```bash
# This will guide you through the setup process
python North_Korean_Cloud_Nightmare.py setup
```

## ⚡ Quick Start for Sales Engineers

1. **Set up credentials** (one-time setup):
   ```bash
   source setup-env.sh
   ```

2. **Validate environment**:
   ```bash
   python North_Korean_Cloud_Nightmare.py setup
   ```

3. **Run a full demo**:
   ```bash
   python North_Korean_Cloud_Nightmare.py execute_full_scenario
   ```

4. **Clean up when done**:
   ```bash
   python North_Korean_Cloud_Nightmare.py clean_up
   ```

## 🎯 Usage Instructions

The North Korean Cloud Nightmare platform provides four main commands for sales engineers to demonstrate advanced persistent threat scenarios:

### Command Overview

```bash
python North_Korean_Cloud_Nightmare.py <command>
```

Available commands:
- `setup` - Check and validate environment configuration (run this first!)
- `deploy_infrastructure` - Deploy AWS infrastructure only
- `launch_attack` - Execute attack simulation (requires infrastructure)
- `execute_full_scenario` - Deploy infrastructure and launch attack in sequence
- `clean_up` - Remove all deployed infrastructure and artifacts

### 0. Setup Environment (Run This First!)

Before running any scenarios, validate your environment:

```bash
python North_Korean_Cloud_Nightmare.py setup
```

This command will:
- ✅ Check AWS credentials and connectivity
- ✅ Verify Pulumi login status
- ✅ Create and configure Pulumi stack
- ✅ Install required Pulumi plugins automatically
- ✅ Provide clear instructions if any setup is needed

**If setup fails**, the command will give you specific instructions to fix the issues.

### 1. Deploy Infrastructure Only

For demonstrations where you want to show the infrastructure first:

```bash
python North_Korean_Cloud_Nightmare.py deploy_infrastructure
```

This command:
- ✅ Deploys AWS infrastructure (IAM users, S3 buckets, DynamoDB tables, etc.)
- ✅ Validates deployment success
- ✅ Populates sample data
- ⏱️ **Duration**: ~5-10 minutes

### 2. Launch Attack Simulation

For executing just the attack portion (requires infrastructure to be deployed):

```bash
python North_Korean_Cloud_Nightmare.py launch_attack
```

This command:
- 🔐 Sets up MFA for DevOps user
- 🔍 Enumerates AWS resources
- 👤 Creates malicious user with elevated permissions
- 🛡️ Disables security controls (GuardDuty, CloudTrail)
- 💾 Exfiltrates and destroys S3 data
- 🗃️ Exfiltrates and destroys DynamoDB data
- 💀 Places ransomware notes
- ⏱️ **Duration**: ~15-20 minutes

### 3. Execute Full Scenario

For complete end-to-end demonstrations:

```bash
python North_Korean_Cloud_Nightmare.py execute_full_scenario
```

This command:
- 🚀 Deploys infrastructure
- ⚔️ Launches complete attack simulation
- ⏱️ **Duration**: ~20-30 minutes

### 4. Clean Up

To remove all infrastructure and artifacts after demonstrations:

```bash
python North_Korean_Cloud_Nightmare.py clean_up
```

This command:
- 🧹 Removes all AWS resources
- 🗑️ Deletes local artifacts
- 💰 Prevents ongoing AWS charges
- ⏱️ **Duration**: ~5-10 minutes

## 📊 Demo Artifacts

After running attacks, check these directories for demonstration artifacts:

- `./AWS_Enumeration/` - AWS resource enumeration results
- `./Infra/s3_Exfiltration/` - Exfiltrated S3 data
- `./Infra/DynamoDB_Exfiltration/` - Exfiltrated DynamoDB data

## 🎪 Sales Engineer Tips

### For Customer Demos:

1. **Start with `deploy_infrastructure`** to show the target environment
2. **Use `launch_attack`** to demonstrate the attack in real-time
3. **Always finish with `clean_up`** to remove resources

### For Proof of Concepts:

1. **Use `execute_full_scenario`** for complete automated demonstrations
2. **Monitor AWS CloudWatch** for real-time attack detection
3. **Show GuardDuty findings** after infrastructure deployment

### For Training Sessions:

1. **Run each command separately** to explain each phase
2. **Examine artifacts** between phases to show attack progression
3. **Use `--verbose` flag** for detailed output during training

## ⚠️ Important Notes

- 🔒 This is for **authorized security demonstrations only**
- 💰 Always run `clean_up` to avoid ongoing AWS charges
- 🎯 Designed for **sandbox/demo AWS accounts only**
- 📋 Requires appropriate AWS permissions for IAM, S3, DynamoDB, etc.

## 🆘 Troubleshooting

### Common Issues:

**Environment setup issues:**
```bash
# Run setup first to diagnose issues
python North_Korean_Cloud_Nightmare.py setup
```

**"Infrastructure not found" error:**
```bash
# Ensure infrastructure is deployed first
python North_Korean_Cloud_Nightmare.py deploy_infrastructure
```

**AWS permission errors:**
- Run `aws sts get-caller-identity` to verify credentials
- Ensure your AWS user has admin permissions
- Check that your AWS account has sufficient limits

**Pulumi errors:**
- Run the setup command for guided troubleshooting
- For manual setup: ensure you're in the Infra directory when running `pulumi login`
- Alternative: Set `PULUMI_ACCESS_TOKEN` environment variable

For additional support, check the `/docs` directory or contact your platform administrator.
