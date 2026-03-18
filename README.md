# 🛠️ SK Manager — Comprehensive Deployment Guide

Welcome to the SK Manager! This guide provides a detailed, step-by-step walkthrough for deploying the entire AWS stack, from infrastructure to application code.

---

## 📋 Prerequisites
Before you begin, ensure you have the following installed and configured:
- **AWS CLI**: [Installed](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and configured (`aws configure`).
- **Terraform**: [Installed](https://developer.hashicorp.com/terraform/downloads) (version 1.5+ recommended).
- **Python**: Version 3.12 or higher.
- **SSH Client**: Standard OpenSSH (available by default on Windows 10/11, Mac, and Linux).

---

## 1. 🏗️ Infrastructure Provisioning (Terraform)
Terraform manages the VPC, RDS (PostgreSQL), DynamoDB, S3, API Gateway, and the EC2 Frontend server.

1. **Enter the Terraform directory**:
   ```powershell
   cd terraform
   ```
2. **Initialize the workspace**:
   ```bash
   terraform init
   ```
3. **Verify and Plan**:
   ```bash
   terraform validate
   terraform plan
   ```
4. **Deploy the resources**:
   ```bash
   terraform apply -auto-approve
   ```
   *Note: Creating the RDS database can take 5-7 minutes.*

5. **📋 Capture the Outputs**:
   After completion, copy these values from your terminal:
   - `api_url` — Your backend endpoint.
   - `frontend_public_ip` — `16.171.227.41` (The IP for the `awsa-rds` instance).
   - `photos_bucket_name` — Where gear photos are stored.
   - `rds_endpoint` — Your database connection string.

---

## 2. 🐍 Backend Deployment (AWS Lambda)
The backend is a Python API using a pure-Python PostgreSQL driver (`pg8000`) for easy packaging.

1. **Enter the backend directory**:
   ```bash
   cd ../backend
   ```
2. **Install the DB Driver** (Clean install into the local directory):
   ```bash
   pip install pg8000 -t .
   ```
3. **Package the Code**:
   - **Windows (PowerShell)**:
     ```powershell
     Compress-Archive -Path * -DestinationPath ..\api.zip -Force
     ```
   - **Mac/Linux (Bash)**:
     ```bash
     zip -r ../api.zip .
     ```
4. **Push to AWS**:
   ```bash
   aws lambda update-function-code `
     --function-name sk-manager-api-dev `
     --zip-file fileb://../api.zip `
     --region eu-north-1
   ```

---

## 3. 🌐 Frontend Deployment (EC2 + Nginx)
The frontend is built with Vanilla JS modules and runs on a pre-configured Nginx server.

1. **Configure the API URL**:
   Open `frontend/js/modules/api.js` and ensure the `API_BASE_URL` matches your `api_url` output:
   ```javascript
   const API_BASE_URL = 'https://pzy29y713k.execute-api.eu-north-1.amazonaws.com/v1';
   ```
2. **Transfer files to EC2**:
   Use `scp` to upload the `frontend/` contents to the Nginx web root:
   ```powershell
   cd ../frontend
   # Replace 'key.pem' with your actual private key file
   scp -i your-key.pem -r ./* ec2-user@16.171.227.41:/usr/share/nginx/html/
   ```
3. **Visit the Site**:
   Navigate to `http://16.171.227.41` in your browser. 🎉

---

## ⏰ 4. Automated Cost Management (Scheduler)
To minimize AWS costs, the **EventBridge Scheduler** is configured for the "Staging" environment:
- **Stop**: Workdays (Mon-Fri) at **7 PM UTC**.
- **Start**: Workdays (Mon-Fri) at **6 AM UTC**.
- **Target**: Any instance tagged with `Environment: staging` (The `awsa-rds` instance is tagged by default).

---

## 🛠️ Maintenance & Updates
- **Update Backend**: Modify the Python code, Re-run the `Compress-Archive` and `aws lambda update` commands.
- **Update Frontend**: Modify the JS/HTML, Re-run the `scp` command.
- **Database Migrations**: Connect to the `rds_endpoint` using any SQL client (like DBeaver or `psql`) to run manual schema updates if required.

---

## 🛑 Tear Down (Delete Everything)
To avoid ongoing charges:
1. **Empty the Photos S3 Bucket**:
   ```bash
   aws s3 rm s3://<your-photos-bucket-name> --recursive
   ```
2. **Destroy Infrastructure**:
   ```bash
   cd terraform
   terraform destroy -auto-approve
   ```
