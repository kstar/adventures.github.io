# Zero-Cost Serverless Analytics for Adventures in Deep Space

This directory contains a privacy-focused and cookie-less analytics tracking system. It runs entirely on **AWS Lambda (via Function URLs)** and **Amazon DynamoDB**, ensuring that your operating costs are **permanently $0.00** for low-to-moderate traffic.

---

## Architecture Overview

```
[ Visitor Browser ] 
        │
        ├── (POST /event) ──► [ AWS Lambda Function URL ] 
        │                            │
        │                       (Writes to)
        │                            ▼
        │                    [ Amazon DynamoDB ]
        │
        └── (GET /) ────────► [ Beautiful HTML Dashboard ]
```

1. **Tracker (`docs/assets/analytics.js`):** Injected automatically on every page of your site via `common.js`. Tracks pageviews, referrers, constellation anchor clicks, and CSV exports. It does not set cookies or use localStorage.
2. **Lambda Ingestion (`analytics/lambda_function.py`):** Runs on AWS Lambda. It extracts geographic country codes from CloudFront network headers for free, classifies traffic into human vs. bot categories using the User-Agent, hashes IP addresses using a daily-rotated cryptographic salt for privacy-preserving anonymity, and stores data.
3. **Database (Amazon DynamoDB):** Stores pageviews and event records. It has no open ports, is secured via IAM, and fits entirely in the perpetual AWS Free Tier.
4. **Dashboard:** Served directly from your Lambda URL when accessed in a browser. It presents human-only metrics, geographical breakdowns, top pages, referrer sources, constellation click counts, and bot traffic breakdowns in a sleek glassmorphic UI.

---

## Deployment Steps

Follow these steps to deploy your serverless analytics backend in 10 minutes:

### Step 1: Create the DynamoDB Table
1. Open the [Amazon DynamoDB Console](https://console.aws.amazon.com/dynamodb/).
2. Click **Create table**.
3. Configure the table settings:
   * **Table name:** `ads_analytics`
   * **Partition key:** `PK` (Type: `String`)
   * **Sort key:** `SK` (Type: `String`)
4. Under **Table settings**, select **Customize settings**:
   * **Read/write capacity settings:** Choose **Provisioned**.
   * Set **Read capacity units (RCU)** to `5`.
   * Set **Write capacity units (WCU)** to `5`.
   * Turn **Auto-scaling** **OFF** (this keeps you inside the perpetual Free Tier and caps any cost at exactly $0, since DynamoDB will throttle excess requests if spammed).
5. Click **Create table**.

---

### Step 2: Create the AWS Lambda Function
1. Open the [AWS Lambda Console](https://console.aws.amazon.com/lambda/).
2. Click **Create function**.
3. Select **Author from scratch**:
   * **Function name:** `ads-analytics-tracker`
   * **Runtime:** `Python 3.12` (or current Python 3.x version)
   * **Architecture:** `x86_64`
4. Click **Create function**.
5. Once created, in the **Code** tab, replace the boilerplate code in `lambda_function.py` with the complete contents of the [lambda_function.py](file:///home/akarsh/devel/adventures.github.io/analytics/lambda_function.py) file in this directory.
6. Click **Deploy** at the top of the code editor.

---

### Step 3: Enable the Function URL (Perpetually Free Endpoint)
1. In the Lambda function page, go to the **Configuration** tab.
2. Select **Function URL** in the left sidebar and click **Create Function URL**.
3. Configure the Function URL:
   * **Auth type:** `NONE` (so public web browsers can send events).
   * **CORS:** Leave *disabled* or set to defaults (since our Python code handles CORS headers dynamically inside the Lambda handler to restrict access to `adventuresindeepspace.com` and `localhost`).
4. Click **Save**.
5. Copy the newly generated **Function URL** from the top right of the page (it will look like `https://xxxxxxxxx.lambda-url.us-east-1.on.aws/`).

---

### Step 4: Configure IAM Database Permissions
By default, the Lambda function does not have permission to write to your DynamoDB database. Let's authorize it:
1. In the Lambda function page, go to the **Configuration** tab.
2. Select **Permissions** in the left sidebar.
3. Under **Execution role**, click on the blue link representing your Role name (e.g., `ads-analytics-tracker-role-xxxx`). This opens the IAM Console.
4. In the IAM Role page, click **Add permissions** -> **Create inline policy**.
5. Go to the **JSON** tab and paste the following policy:
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Sid": "DynamoDBReadWriteAccess",
               "Effect": "Allow",
               "Action": [
                   "dynamodb:PutItem",
                   "dynamodb:Query"
               ],
               "Resource": "arn:aws:dynamodb:*:*:table/ads_analytics"
           }
       ]
   }
   ```
6. Click **Review policy**.
7. Name the policy `DynamoDBAnalyticsAccess` and click **Create policy**.
8. Close the IAM console tab.

---

### Step 5: Configure Environment Variables
1. Back in the Lambda function page, go to the **Configuration** tab.
2. Select **Environment variables** in the left sidebar and click **Edit**.
3. Add the following variables:
   * **Key:** `DYNAMODB_TABLE` | **Value:** `ads_analytics`
   * **Key:** `ANALYTICS_SECRET` | **Value:** (Type a random 32-character string. This key is used as a cryptographic salt for hashing IP addresses. *Keep this private!*)
4. Click **Save**.
5. Increase the function timeout slightly by going to **General configuration** -> **Edit** -> Change **Timeout** to `5 seconds` -> Click **Save**.

---

### Step 6: Update the Client Tracker Endpoint
1. Open the file [analytics.js](file:///home/akarsh/devel/adventures.github.io/docs/assets/analytics.js) in your text editor.
2. Replace the placeholder endpoint at line 8:
   ```javascript
   const DEFAULT_ENDPOINT = 'https://analytics.your-personal-server.com/api/event';
   ```
   with your actual AWS Lambda Function URL:
   ```javascript
   const DEFAULT_ENDPOINT = 'https://xxxxxxxxx.lambda-url.us-east-1.on.aws/';
   ```

---

### Step 7: Activate the Tracker on Your Site
1. Open the file [common.js](file:///home/akarsh/devel/adventures.github.io/docs/assets/common.js) in your editor.
2. Find the commented-out dynamic import at the end of the script inclusions block:
   ```javascript
   // To enable analytics tracking once your AWS backend is deployed, uncomment the line below:
   // import('./analytics.js').catch(err => console.warn('Analytics failed to load:', err));
   ```
3. Uncomment the import line:
   ```javascript
   // To enable analytics tracking once your AWS backend is deployed, uncomment the line below:
   import('./analytics.js').catch(err => console.warn('Analytics failed to load:', err));
   ```
4. Commit and push the changes to GitHub. Your website will now dynamically load the tracker and start recording analytics!

---

## Accessing Your Dashboard

Your HTML analytics dashboard is served directly from the Lambda function URL:
1. Open your web browser.
2. Navigate to your Lambda Function URL: `https://xxxxxxxxx.lambda-url.us-east-1.on.aws/`
3. You will immediately see your live traffic, top pages, referrers, country origins, constellation click-throughs, and AI crawler statistics!
