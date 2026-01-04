# Smart Compliance & KYC Automation System

## 1. Project Overview
This project involves building an automated **Know Your Customer (KYC)** system that replaces manual identity verification. Users upload their ID documents (Passport/Driver's License) and a bank statement. The system uses AWS Artificial Intelligence services to extract text, verify the ID against a selfie (face match), and analyze financial documents for risk.

## 2. Industrial Application
**Sector:** FinTech, Banking, Insurance
*   **Problem:** Banks spend millions of dollars and days of processing time manually checking user documents for account opening.
*   **Solution:** This system reduces verification time from days to seconds, reduces human error, and improves fraud detection using AI.
*   **Real-World Example:** Digital banks like Monzo, Revolut, or Chime using automated onboarding.

## 3. Architecture & Workflow
The system follows a Serverless Event-Driven Architecture:

1.  **Frontend (React/Next.js):**
    *   User fills a form and uploads an ID image and a PDF bank statement.
    *   Apps connects to **AWS S3** via signed URLs to upload files securely.

2.  **Storage (Amazon S3):**
    *   Stores the raw images and documents.
    *   Triggers an event notification upon new object creation.

3.  **Processing (AWS Lambda):**
    *   A Lambda function is triggered by the S3 upload.
    *   It calls **Amazon Textract** to read data (Name, ID Number, Address) from the ID card.
    *   It calls **Amazon Rekognition** to compare the ID photo with a user-uploaded selfie (Facial Comparison).
    *   It calls **Amazon Comprehend** to look for specific keywords or entities in the bank statement.

4.  **Database (Amazon DynamoDB):**
    *   Stores the extracted user data, verification confidence scores, and status (Verified/Rejected).

5.  **Notification (Amazon SNS/SES):**
    *   Sends an email to the user with the result of the verification.

## 4. Technology Stack
*   **Cloud Provider:** AWS
*   **Frontend:** React.js, Tailwind CSS
*   **Backend:** AWS Lambda (Python/Node.js), API Gateway
*   **Storage:** Amazon S3
*   **Database:** Amazon DynamoDB
*   **AI Services:**
    *   Amazon Textract (OCR)
    *   Amazon Rekognition (Computer Vision)
    *   Amazon Comprehend (NLP)
