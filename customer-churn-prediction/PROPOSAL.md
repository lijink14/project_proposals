# Intelligent Customer Churn Prediction

## 1. Project Overview
This project builds a Data Science pipeline to predict which customers are likely to cancel their subscription (churn). It involves a complete workflow from analyzing raw data to training a Machine Learning model and deploying it as an API for a "Customer Retention Portal" used by support agents.

## 2. Industrial Application
**Sector:** SaaS, Telecom, E-commerce
*   **Problem:** Acquiring a new customer is 5x more expensive than retaining an existing one. Companies lose revenue when users leave silently.
*   **Solution:** Accurately identifying "at-risk" customers allows the company to proactively offer discounts or support, reducing churn.
*   **Real-World Example:** Netflix or Spotify predicting if you will cancel, or a Telecom provider offering a better data plan before you switch.

## 3. Architecture & Workflow
The system demonstrates the full ML Lifecycle (MLOps):

1.  **Data Ingestion & Cleaning (AWS Glue):**
    *   Raw customer data (demographics, usage history, billing) is stored in **Amazon S3**.
    *   **AWS Glue** (ETL) cleans the data, handles missing values, and transforms it for training.

2.  **Model Building (Amazon SageMaker):**
    *   Use **SageMaker Autopilot** or **XGBoost** in a Jupyter Notebook instance.
    *   Train a binary classification model (Churn: Yes/No).
    *   Evaluate model accuracy and deploy the best model to a **SageMaker Endpoint**.

3.  **API Layer (API Gateway & Lambda):**
    *   **Amazon API Gateway** exposes a REST API endpoint (e.g., `POST /predict-churn`).
    *   **AWS Lambda** receives the request (Customer ID), fetches the user's latest usage features, and queries the SageMaker Endpoint.

4.  **User Interface (Retention Portal):**
    *   A simple web app (HTML/JS or Streamlit) for Support Agents.
    *   Agent enters a Customer ID.
    *   System displays: "Churn Risk: 85% (High)" and "Recommended Action: Offer 20% Discount."

## 4. Technology Stack
*   **Cloud Provider:** AWS
*   **ETL/Data Prep:** AWS Glue or SageMaker Data Wrangler
*   **Machine Learning:** Amazon SageMaker (XGBoost/AutoPilot)
*   **Storage:** Amazon S3
*   **API:** Amazon API Gateway + AWS Lambda
*   **Frontend:** Simple Web Interface (Streamlit/React)
