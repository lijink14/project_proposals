# Cost Analysis & Prerequisites

## 1. Estimated AWS Costs
⚠️ **Medium Cost Risk:** This project uses **Streaming** and **Machine Learning** services which bill by the hour. You must shut down resources immediately after the demo to avoid unwanted charges.

| Service | Pricing Model | Student/Demo Estimate |
| :--- | :--- | :--- |
| **Kinesis Data Firehose** | Data ingestion volume | **$0.00** (Low volume is nearly free, but watch out for provisioning) |
| **Kinesis Data Streams** | Per Shard Hour | **~$11.00/month** (approx $0.015/hour). **DELETE immediately after use.** |
| **Amazon S3** | Storage | **$0.00** (Free Tier) |
| **SageMaker Training** | Per hour of training | **<$1.00** (If using `ml.m5.large` for ~1 hour of training) |
| **SageMaker Endpoint** | Per hour of hosting | **IMPORTANT:** `ml.t2.medium` costs ~$0.05/hour. If stuck on 24/7 = **$36/month**. |
| **AWS Lambda** | Per invocation | **$0.00** (Free Tier) |

### 💰 Total Estimated Cost: $2.00 - $5.00 USD
*   *Assumption:* You create resources, run the demo for 2-3 hours, and then **DELETE** the Kinesis Streams and SageMaker Endpoints.
*   *Warning:* Leaving a SageMaker Endpoint running is the #1 cause of unexpected student bills.

## 2. Prerequisites & Requirements

### Technical Skills
*   **Python:** Strong Python skills needed for data simulation and Streamlit.
*   **Data Science:** Basic understanding of "Anomaly Detection" (Random Cut Forest).
*   **Cloud:** Understanding of data streams vs database storage.

### Tools & Accounts
1.  **AWS Account:** Active account with billing enabled.
2.  **Python 3.9+:** Installed locally.
3.  **Boto3 Library:** For interacting with AWS services from Python.
4.  **Streamlit:** For building the dashboard (`pip install streamlit`).
