# Architecture Diagram — How to Create

## Tool: https://app.diagrams.net (draw.io) — free, browser-based

## Steps:
1. Go to app.diagrams.net
2. Click "Create New Diagram" → Blank Diagram
3. On the left panel, search for "AWS" icons (they have a built-in AWS icon library)
4. Enable: File → Shapes → AWS 2024 (or AWS Architecture Icons)

---

## What to draw (left to right flow):

```
[Loan Officer]  →  [Streamlit UI]  →  [AWS Lambda]  →  [LightGBM Model]
     (user)         (EC2/Local)      (predict-default-    (loaded from S3)
                                       risk)
                                         ↑
                                    [Amazon S3]
                                    - lgbm_booster.txt
                                    - preprocessor.pkl

                    [Streamlit UI]  →  [SHAP TreeExplainer]
                                       (local computation)
                                         ↑
                                    [LightGBM Model]
                                    (local copy)
```

---

## Exact components to place on diagram:

### Left side (User):
- **User icon** → label: "Loan Officer"

### Middle (Application):
- **Streamlit logo or EC2 icon** → label: "Streamlit UI (Frontend)"
- Arrow → pointing right

### AWS Cloud boundary box:
Draw a large rectangle labeled "AWS Cloud" and "us-east-1" containing:

1. **Lambda icon** → label: "predict-default-risk (1024 MB)"
2. **S3 bucket icon** → label: "loan-copilot-quadra"
   - Sub-labels: lgbm_booster.txt, preprocessor.pkl
3. **ECR icon** → label: "predict-default-risk (container image)"
4. **CloudWatch icon** → label: "Logs & Monitoring"
5. **IAM icon** → label: "IAM Roles"

### Arrows:
- Loan Officer → Streamlit UI (labeled: "Enters applicant details")
- Streamlit UI → Lambda (labeled: "boto3 invoke (29 features)")
- Lambda → S3 (labeled: "Load model on cold start")
- ECR → Lambda (labeled: "Container image")
- Lambda → Streamlit UI (labeled: "risk_score, category, action")
- Streamlit UI → SHAP box (labeled: "Local SHAP computation")

### Bottom/side:
- **SHAP box** → label: "SHAP TreeExplainer (local)"
- Arrow back to Streamlit UI (labeled: "Top 5 feature explanations")

---

## Color coding (like the reference):
- AWS services: Use official orange/dark blue AWS icon colors
- User: Gray person icon
- Streamlit: Purple/red (Streamlit brand color)
- Arrows: Black with labels

---

## The finished diagram should look like:

```
┌─────────────────────────────────────────────────────────────┐
│  AWS Cloud (us-east-1)                                       │
│                                                              │
│   ┌──────────┐     ┌──────────────┐     ┌────────────┐     │
│   │   ECR    │────→│    Lambda    │←───→│     S3     │     │
│   │Container │     │predict-risk  │     │  Model +   │     │
│   │  Image   │     │  1024 MB     │     │Preprocessor│     │
│   └──────────┘     └──────┬───────┘     └────────────┘     │
│                           │                                  │
│   ┌──────────┐            │         ┌──────────┐           │
│   │   IAM    │            │         │CloudWatch│           │
│   │  Roles   │            │         │  Logs    │           │
│   └──────────┘            │         └──────────┘           │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
                            │ boto3 invoke
                            │
┌───────────────────────────┼──────────────────────────────────┐
│  Client (Local/EC2)       │                                  │
│                           ▼                                  │
│  ┌─────────┐     ┌──────────────┐     ┌──────────────┐     │
│  │  Loan   │────→│  Streamlit   │────→│    SHAP      │     │
│  │ Officer │     │     UI       │←────│TreeExplainer │     │
│  └─────────┘     └──────────────┘     └──────────────┘     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Alternative: Use AWS Architecture Tool
- https://aws.amazon.com/architecture/icons/
- Download the icon set and use in PowerPoint or draw.io
