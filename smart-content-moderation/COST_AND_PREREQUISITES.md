# Cost Analysis & Prerequisites

## 1. Estimated AWS Costs
This project is generally **Low Cost** as it utilizes "Serverless" AI APIs which have generous free tiers.

| Service | Pricing Model | Student/Demo Estimate |
| :--- | :--- | :--- |
| **Amazon S3** | Storage | **$0.00** (Free Tier) |
| **AWS Lambda** | Compute | **$0.00** (Free Tier) |
| **Amazon Rekognition** | Image Analysis | **$0.00** (Free Tier: 5,000 images/month). $1.00 per 1k images after that. |
| **Amazon Comprehend** | Text Analysis | **$0.00** (Free Tier: 50k units/mo). $0.0001 per unit after that. |
| **API Gateway** | API Calls | **$0.00** (Free Tier: 1M calls/mo) |

### 💰 Total Estimated Cost: $0.00 - $1.00 USD
*   *Assumption:* You process < 1,000 social media posts during development and demo.
*   *Safety:* Even if you demo heavily, the cost per 1,000 images is very low ($1).

## 2. Prerequisites & Requirements

### Technical Skills
*   **Web Development:** Strong React.js / Next.js skills (this project is heavy on the UI).
*   **Backend:** Node.js logic for the Lambda functions.
*   **Asynchronous Flows:** Understanding how to handle image uploads and wait for processing results.

### Tools & Accounts
1.  **AWS Account:** Active.
2.  **Node.js environment:** Installed.
3.  **Frontend Framework:** React or Next.js setup.
4.  **Mock Data:** You might need a set of test images (safe vs unsafe) to demonstrate the checking capability.
