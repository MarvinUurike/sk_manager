# SK Manager — Deployment Guide

This guide covers how to deploy the SK Manager AWS serverless infrastructure, backend code, and frontend UI, as well as how to tear it all down when you're done.

## Prerequisites
1. **AWS CLI** installed and configured (`aws configure`)
2. **Terraform** installed (`terraform -v`)
3. **Python 3.12+** installed 

---

## 1. Deploy the AWS Infrastructure (Terraform)

Terraform will create the RDS database, DynamoDB tables, VPC, S3 (Photos), Lambda functions, API Gateway, and the **EC2 instance (`awsa-rds`)** for frontend hosting.

1. Navigate to the Terraform directory:
   ```bash
   cd terraform
   ```
2. Initialize Terraform (downloads AWS provider):
   ```bash
   terraform init
   ```
3. Preview the changes:
   ```bash
   terraform plan
   ```
4. Deploy the infrastructure:
   ```bash
   terraform apply
   ```
   *(Type `yes` when prompted)*
5. **Important:** Note the outputs printed at the end. You will need:
   - `api_url`
   - `photos_bucket_name`
   - `frontend_public_ip` (The IP of the `awsa-rds` instance)

---

## 2. Deploy the Backend Code (Python Lambda)

The initial Terraform run deploys a dummy "Hello World" Lambda. Next, package and upload the actual Python backend code.

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install the **pg8000** driver. Since pg8000 is a pure-Python driver, it is much easier to package than psycopg2 and does not require a specialized AWS Lambda layer.
   ```bash
   pip install pg8000 -t .
   ```
3. Zip the backend code:
   ```bash
   # On Windows (PowerShell):
   Compress-Archive -Path * -DestinationPath ..\api.zip -Force
   ```
4. Update the Lambda function with the ZIP:
   ```bash
   aws lambda update-function-code --function-name sk-manager-api-dev --zip-file fileb://../api.zip
   ```

---

## 3. Deploy the Frontend (EC2)

1. Navigate to the frontend code:
   ```bash
   cd frontend
   ```
2. Open `js/modules/api.js` in a text editor and update the `API_BASE_URL` if it differs from the default localhost/production logic.
3. **Transfer files to EC2**: You can use `scp` or simply copy-paste the files to the `/usr/share/nginx/html/` directory on the `awsa-rds` instance.
   ```bash
   # Example using SCP (if you have the SSH key):
   scp -r ./* ec2-user@<frontend_public_ip>:/usr/share/nginx/html/
   ```
4. Open the `frontend_public_ip` in your browser. You're live! 🎉

---

## 4. Instance Scheduler (Cost Management)

The application includes an automated scheduler to save costs:
- **Stops** all instances tagged `Environment: staging` at **7 PM UTC** (Mon-Fri).
- **Starts** them at **6 AM UTC** (Mon-Fri).
- The `awsa-rds` instance is tagged as `staging` by default for this purpose.

---

## Maintenance: Updating Code

- **Backend updates**: Re-zip the `backend/` folder and run `aws lambda update-function-code` again.
- **Frontend updates**: Run the `aws s3 sync` command again to push new HTML/CSS/JS.

---

## 🛑 How to Delete Everything (Tear Down)

If you want to stop paying for AWS resources (especially the RDS database), you can tear down the entire stack using Terraform.

1. Navigate to the Terraform directory:
   ```bash
   cd terraform
   ```
2. **Empty the S3 bucket first!** Terraform cannot delete the photos bucket if it contains objects:
   ```bash
   aws s3 rm s3://<your-photos-bucket-name> --recursive
   ```
3. Run the destroy command:
   ```bash
   terraform destroy
   ```
   *(Type `yes` when prompted. This will permanently delete the databases, VPC, API, and all other AWS resources.)*
