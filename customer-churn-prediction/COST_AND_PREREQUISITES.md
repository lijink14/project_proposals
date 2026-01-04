# Cost Analysis & Prerequisites

## 1. Estimated AWS Costs
⚠️ **Medium Cost Risk:** Machine Learning training and hosting are the main costs here. Using **SageMaker Serverless Inference** can drastically reduce hosting costs compared to real-time endpoints.

| Service | Pricing Model | Student/Demo Estimate |
| :--- | :--- | :--- |
| **Amazon S3** | Storage | **$0.00** (Free Tier) |
| **AWS Glue** | DPU-Hour (ETL) | **$0.44/DPU-Hour**. A simple job runs in minutes. Est: **$0.50** per run. |
| **SageMaker Training** | Compute time | **$0.00** (SageMaker Free Tier offers 50 hours of `ml.m5.xlarge` for first 2 months) |
| **SageMaker Endpoint** | Hosting time | **$30-$70/month** if left running. **DELETE after demo.** |
| **API Gateway** | REST Calls | **$0.00** (Free Tier) |

### 💰 Total Estimated Cost: $1.00 - $5.00 USD
*   *Assumption:* You perform ETL once, Train once, and run the Endpoint only during the presentation.
*   *Tip:* Use **SageMaker Canvas** (No-code) for a faster, albeit potentially slightly pricier (session-based), alternative if coding models is too hard.

## 2. Prerequisites & Requirements

### Technical Skills
*   **Data Science:** Understanding of Classification models, Accuracy, Precision/Recall.
*   **Python:** Pandas, NumPy, Scikit-Learn (basic).
*   **Jupyter Notebooks:** Comfortable working in a notebook environment.

### Tools & Accounts
1.  **AWS Account:** Active.
2.  **Dataset:** You need a CSV dataset (e.g., Telco Customer Churn from Kaggle).
3.  **Jupyter/Anaconda:** Installed locally or usage of SageMaker Studio Lab (free).
