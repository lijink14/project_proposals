# AWS Cloud Deployment Guide

This folder contains the CloudFormation / SAM template to deploy the Weather Prediction Model to AWS.

## Contents
- `template.yaml`: The Infrastructure-as-Code (IaC) template defining the Lambda Logic and API Gateway.
- `src/app.py`: The Python source code for the Lambda function.
  - Contains **EnergyModel** (Internal Simulation)
  - Contains **Open-Meteo Integration** (Real Data)

## Application Logic
The API exposes a generic endpoint `/weather` that supports two modes:

1. **Simulated Mode (Default)**:
   - Uses the internal mathematical model to predict Solar/Wind/Carbon for a specific hour.
   - Example: `GET /weather?mode=simulated&hour=14`

2. **Real Mode**:
   - Fetches live/historical data from Open-Meteo for coordinates.
   - Example: `GET /weather?mode=real&lat=39.04&lon=-77.48`

## How to Deploy

### Option 1: Using AWS SAM CLI (Recommended)
1. Install [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html).
2. Open a terminal in this folder (`aws_deployment`).
3. Run:
   ```bash
   sam build
   sam deploy --guided
   ```
4. Follow the prompts. It will output your **API Gateway URL** at the end.

### Option 2: Using AWS Console (CloudFormation)
1. Zip the `src/` folder content into `source.zip`.
2. Upload `source.zip` to an S3 bucket (or edit the template to inline code if preferred, though text limit applies).
3. Go to **AWS CloudFormation** -> **Create Stack**.
4. Upload `template.yaml`.
5. *Note: For Console deployment without SAM, you might need to manually package the code to S3 first.* 

**Recommendation:** stick to SAM CLI or uploading the `src/app.py` content directly to the Lambda Console editor after creating the function via template if you want to modify it live.
