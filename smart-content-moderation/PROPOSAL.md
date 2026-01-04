# Smart Content Moderation Pipeline

## 1. Project Overview
This project builds a real-time content moderation system for a social media platform. It automatically detects and filters out toxic text (hate speech) and inappropriate images (explicit content) using AI, ensuring a safe user environment without human intervention.

## 2. Industrial Application
**Sector:** Social Media, Gaming, E-commerce, EdTech
*   **Problem:** User-generated content platforms struggle to moderate millions of posts daily. Human moderation is slow, expensive, and psychologically damaging to workers.
*   **Solution:** An AI-driven pipeline that instantly flags or blocks harmful content, scaling infinitely with traffic.
*   **Real-World Example:** Facebook/Meta automatically removing violent videos, or Twitch filtering chat in real-time.

## 3. Architecture & Workflow
The system uses a highly scalable, event-driven pattern:

1.  **Frontend (Social Feed App):**
    *   A simple React app ("SocialFeed") where users can post text status updates or upload images.
    *   Images are uploaded directly to **Amazon S3**.
    *   Text posts are sent via **API Gateway**.

2.  **Analysis Logic (AWS Lambda & Step Functions):**
    *   **Text Path:** Lambda sends the text to **Amazon Comprehend** to detect Sentiment (Positive/Negative) and PII (Personal Info). Custom logic checks for specific "banned words."
    *   **Image Path:** S3 upload triggers a Lambda that sends the image to **Amazon Rekognition** to detect labels like "Explicit," "Violence," or "Weapons."

3.  **Decision Engine:**
    *   If `Toxic Score > 80%` OR `Image Label = Unsafe`:
        *   Mark item as "FLAGGED" in the database.
        *   Optionally blur the image or hide the post.
    *   If `Safe`:
        *   Mark item as "PUBLISHED."

4.  **Database (Amazon DynamoDB):**
    *   Stores the Post ID, User ID, Content URL, and Moderation Status (Published/Flagged).

5.  **Analytics Dashboard (Amazon QuickSight):**
    *   Visualizes metrics: "Percentage of Toxic Posts per Day," "Most Common Violation Types."

## 4. Technology Stack
*   **Cloud Provider:** AWS
*   **Frontend:** React.js / Next.js
*   **Backend:** AWS Lambda (Node.js/Python), Amazon API Gateway
*   **Storage:** Amazon S3
*   **Database:** Amazon DynamoDB
*   **AI Services:**
    *   Amazon Rekognition (Image Analysis)
    *   Amazon Comprehend (Text Analysis)
*   **Orchestration:** AWS Step Functions (Optional, for complex flows)
