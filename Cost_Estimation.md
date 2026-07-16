# Cost Estimation — Loan Underwriting Copilot

## Assumptions

- Region: US East (N. Virginia) — us-east-1
- Usage: 1,000 predictions per day (moderate bank branch usage)
- 30 days/month = 30,000 invocations/month
- Lambda memory: 1024 MB
- Average execution time: 100ms (warm), 10s (cold start, ~5% of invocations)
- Model artifacts on S3: ~2 MB total
- ECR image: ~500 MB

---

## Cost Estimation Summary

| Service | Description | Monthly Cost (USD) |
|---------|-------------|-------------------|
| AWS Lambda | 30,000 invocations × 1024 MB × 100ms avg | $0.63 |
| Amazon S3 | 2 MB storage + 30,000 GET requests | $0.02 |
| Amazon ECR | 500 MB container image storage | $0.05 |
| CloudWatch Logs | 1 GB logs/month | $0.50 |
| Data Transfer | Minimal (< 1 GB outbound) | $0.00 |
| **TOTAL** | | **$1.20/month** |

---

## Detailed Breakdown

### AWS Lambda
- Requests: 30,000/month × $0.20 per 1M requests = $0.006
- Compute: 30,000 × 1024 MB × 0.1 sec = 3,072,000 MB-seconds
  - Free tier: 400,000 GB-seconds = 409,600,000 MB-seconds (covers everything)
  - After free tier: 3,072,000 MB-sec × $0.0000166667/GB-sec = $0.05
- Cold starts (5%): 1,500 × 1024 MB × 10 sec = 15,360,000 MB-sec = $0.26
- **Lambda total: ~$0.63/month**

### Amazon S3
- Storage: 2 MB × $0.023/GB = $0.00005
- GET requests: 30,000 × $0.0004/1000 = $0.012
- **S3 total: ~$0.02/month**

### Amazon ECR
- Storage: 0.5 GB × $0.10/GB = $0.05
- **ECR total: $0.05/month**

### CloudWatch
- Log ingestion: 1 GB × $0.50/GB = $0.50
- **CloudWatch total: $0.50/month**

---

## Scaling Scenarios

| Usage Level | Invocations/Month | Estimated Monthly Cost |
|-------------|-------------------|----------------------|
| Low (demo/dev) | 100 | $0.50 (mostly free tier) |
| Medium (branch) | 30,000 | $1.20 |
| High (production) | 500,000 | $15-20 |
| Enterprise | 5,000,000 | $150-200 |

---

## Cost Comparison vs Traditional

| Approach | Monthly Cost | Notes |
|----------|-------------|-------|
| **Our approach (Lambda)** | $1.20 | Serverless, scales to zero |
| SageMaker Endpoint (ml.m5.large) | $115 | Always-on, fixed cost |
| EC2 (t3.medium) 24/7 | $30 | Always-on, manual scaling |
| On-premises server | $500+ | Hardware, maintenance, electricity |

---

## Notes

- Free tier covers most usage for first 12 months (1M Lambda requests, 400K GB-seconds free)
- Cost at rest = $0 (Lambda + S3 only charge on usage)
- No NAT Gateway, VPC, or data transfer costs in this architecture
- Streamlit runs locally (no hosting cost) — for production, add EC2/App Runner (~$15-30/month)

---

## AWS Pricing Calculator Link

Configure at: https://calculator.aws/#/estimate

Services to add:
1. Lambda — 30,000 requests, 1024 MB, 100ms duration
2. S3 — 0.002 GB storage, 30,000 GET requests
3. ECR — 0.5 GB storage
