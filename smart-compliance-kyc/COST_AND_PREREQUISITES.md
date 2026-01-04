# Cost Analysis & Prerequisites

## 1. Estimated AWS Costs
This project is very **Cost-Efficient** and can likely be run entirely within the **AWS Free Tier** for a student demonstration.

| Service | Pricing Model | Student/Demo Estimate |
| :--- | :--- | :--- |
| **Amazon S3** | Storage & Requests | **$0.00** (Free Tier: 5GB storage, 20k GETs) |
| **AWS Lambda** | Per invocation | **$0.00** (Free Tier: 1M requests/month) |
| **Amazon Textract** | Per page processed | **$0.00** (Free Tier: 1,000 pages/month for 3 months) |
| **Amazon Rekognition** | Per image analyzed | **$0.00** (Free Tier: 5,000 images/month for 12 months) |
| **Amazon Comprehend** | Per unit of text | **$0.00** (Free Tier: 50k units/month for 12 months) |
| **DynamoDB** | Read/Write capacity | **$0.00** (Free Tier: 25GB storage) |

### 💰 Total Estimated Cost: $0.00 - $1.00 USD
*   *Assumption:* You verify < 100 documents for the demo.
*   *Warning:* If you exceed Free Tier limits, Textract costs ~$1.50 per 1,000 pages.

## 2. Prerequisites & Requirements

### Technical Skills
*   **Frontend:** React.js (or basic HTML/JS) to build the upload form.
*   **Backend:** Basic Python or Node.js for AWS Lambda functions.
*   **Concepts:** Understanding of JSON and REST APIs.

### Tools & Accounts
1.  **AWS Account:** A credit card is required to sign up, even for Free Tier.
2.  **AWS CLI:** Installed and configured on your laptop.
3.  **Node.js / Python:** Installed.
4.  **Postman:** Useful for testing your API endpoints before building the frontend.
