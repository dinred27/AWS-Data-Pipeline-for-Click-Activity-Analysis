# AWS-Data-Pipeline-for-Click-Activity-Analysis

This project is designed to track and analyze click activity on certification links embedded in my resume. By collecting and transforming raw click data, I gain insights into the reach and engagement of my resume, helping me assess the visibility of my profile in job market.

---

## Project Workflow

### 1. S3 Buckets Setup
- **Certificate Bucket:**  
  - Contains all my certifications with **public access enabled**.
  - Public URLs of these certifications are embedded in my resume as access points.

- **Access Log Bucket:**  
  - Stores **access logs** for all clicks on the certification links.  
  - Access logs are automatically generated whenever someone clicks on a certification link.

### 2. Scheduled Lambda Invocation
- A **EventBridge rule** triggers a **Lambda function** every week to process new access logs.
- Since Lambda is stateless, **DynamoDB** is used to maintain the state of processed logs and track:
  - Old data already processed.
  - New data that needs processing.

### 3. Data Processing
- The **Lambda function** processes the new logs by:
  1. **Concatenates new data** from the access log bucket.
  2. Extracting useful fields such as:
     - **IP Address**
     - **Timestamp**
     - **Certificate Accessed**
     - **Request Type**
     - **Request Code**
  3. Saving the processed data to a temporary **S3 file**.

### 4. Data Mapping and Storage
- **AWS Glue Job**:
  - Triggered by the Lambda function after processing is complete.
  - Reads the temporary S3 file and maps the new data to an **RDS MySQL instance** table.

### 5. Data Storage and Analysis
- The transformed data stored in **RDS MySQL** provides insights into:
  - Most clicked certifications.
  - Engagement patterns over time.
  - Additional request-level details for in-depth analysis.

---

## Technology Stack
- **AWS S3:** For certificate storage and access log collection.
- **AWS Lambda:** For serverless processing of access logs.
- **AWS DynamoDB:** For maintaining state between old and new data.
- **AWS Glue:** For ETL and mapping data to the RDS table.
- **AWS RDS (MySQL):** For structured data storage and querying.
- **Python:** For Lambda function and Glue scripting.
- **SQL:** For querying and analyzing the transformed data.

---


