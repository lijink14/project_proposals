# Predictive Maintenance for Industrial IoT

## 1. Project Overview
This project simulates an Industrial IoT environment where factory machines send sensor data (vibration, temperature, pressure). The system ingests this streaming data, stores it, and uses a Machine Learning model to detect anomalies (potential failures) in real-time, preventing costly downtime.

## 2. Industrial Application
**Sector:** Manufacturing, Logistics, Energy
*   **Problem:** Factory machines break down unexpectedly, causing production halts that cost thousands of dollars per hour.
*   **Solution:** Predictive maintenance uses ML to predict failure *before* it happens, allowing for scheduled maintenance.
*   **Real-World Example:** Car manufacturing plants monitoring robot arms, or wind farms monitoring turbine health.

## 3. Architecture & Workflow
The system utilizes Real-Time Data Streaming and Anomaly Detection:

1.  **Data Generator (Python Simulation):**
    *   A script acts as a "Virtual Sensor," generating JSON data (DeviceID, Temp, RPM, Vibration) with occasional "anomaly" spikes.
    *   Streams data to **AWS Kinesis Data Firehose**.

2.  **Ingestion & Storage (AWS Kinesis & S3):**
    *   **Kinesis Data Firehose** buffers the stream and saves it to **Amazon S3** (Data Lake) for historical training.

3.  **Machine Learning (Amazon SageMaker):**
    *   **Training:** Use SageMaker to train a **Random Cut Forest (RCF)** model on historical "normal" data stored in S3.
    *   **Inference:** Deploy the trained model as a SageMaker Endpoint for real-time predictions.

4.  **Real-Time Processing (AWS Lambda):**
    *   A Lambda function consumes records from the Kinesis stream or is triggered periodically.
    *   It sends the live data point to the SageMaker Endpoint to get an "Anomaly Score."

5.  **Visualization & Alerting:**
    *   If the score is high (anomaly), publish a message to **Amazon SNS** (SMS alert to Engineer).
    *   A **Streamlit** (Python) dashboard reads the processed data and visualizes the "Health Score" of the machines in real-time.

## 4. Technology Stack
*   **Cloud Provider:** AWS
*   **Data Generator:** Python script
*   **Streaming:** AWS Kinesis Data Firehose
*   **Storage:** Amazon S3
*   **Machine Learning:** Amazon SageMaker (Random Cut Forest algorithm)
*   **Compute:** AWS Lambda
*   **Dashboard:** Streamlit or Amazon QuickSight
