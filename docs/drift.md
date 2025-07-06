
# Devolv Drift — CI/CD-First IAM Policy Drift Detection

`devolv drift` is a **CI/CD-first tool** that automatically detects IAM policy drift between your local files and deployed AWS IAM policies. It is designed primarily for automated pipelines, with local CLI use as a secondary option.

---

## 🚀 Why Devolv Drift in CI/CD?

✅ Automate IAM drift detection on every PR, push, or merge  
✅ Auto-create PRs or issues to resolve drift  
✅ No manual AWS console checks  
✅ Secure OIDC-based AWS access — no long-term credentials  

👉 **CI/CD is the primary use case** — local CLI use is optional for manual checks.

---

## 📦 How to Get Started

### 1️⃣ **Install Devolv (for local CLI use)**

```bash
pip install devolv
```
✅ Required if you want to run `devolv drift` manually outside CI/CD.

⚠ **Note:** In CI/CD, installation is typically handled by your workflow or container image — you don't need to install it manually.

---

### 2️⃣ **Set Up AWS OIDC Role for GitHub Actions**

Download our onboarding script:  
https://github.com/devolvdev/devolv-actions/blob/main/devolv_oidc_onboard.py  

Download via terminal:
```bash
curl -O https://raw.githubusercontent.com/devolvdev/devolv-actions/main/devolv_oidc_onboard.py
```
Run in **AWS CloudShell** or any AWS CLI-authenticated machine:
```bash
python devolv_oidc_onboard.py --github-org YourOrgName
```
✅ This will:
- Set up the OIDC provider (if missing)
- Create an IAM role trusted for your GitHub org
- Attach IAM policy permissions needed by Devolv Drift
- Output the role ARN + a GitHub Actions block

---

### 3️⃣ **Add GitHub Actions Workflow**

Create a file at:
```
.github/workflows/devolv-drift.yml
```
Example contents:
```yaml
permissions:
  id-token: write
  contents: write
  pull-requests: write
  issues: write

jobs:
  drift-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::<account_id>:role/YourOrg-DevolvRole
          aws-region: us-east-1

      - name: Run Devolv Drift
        uses: devolvdev/devolv-actions@v2
        with:
          tool: drift
          policy-name: DevolvTestPolicy
          path: ./test-devolv-policy.json
          approvers: ""                  # Empty by default; pass comma-separated list if needed
          github-token: ${{ secrets.GITHUB_TOKEN }}
          approval-anyway: false        # false by default; 

```

✅ **⚠ Mandatory repository setting:**  
In your GitHub repository settings under **Actions → General → actions**, ensure you enable:
```
☑ Allow GitHub Actions to create and approve pull requests
```
This is required for Devolv Drift to auto-create PRs.

---

## 📝 What Devolv Drift Does in CI/CD

✅ Checks your local IAM policy files against live AWS policies  
✅ Shows a rich, colorized diff of detected drift in workflow logs  
✅ Automatically opens PRs to sync your code or propose AWS updates  
✅ Optionally opens issues to track drift findings  

---

## ⚡ Final Checklist for Success

✅ Devolv installed (`pip install devolv`) for local CLI use  
✅ OIDC AWS role set up using `devolv_oidc_onboard.py`  
✅ Workflow file includes correct `permissions:` block  
✅ Repository setting enabled to allow Actions to create/approve PRs  
✅ Role trust and policy match your GitHub org + IAM needs  
✅ Devolv Drift runs on every PR / push in your workflow  

---

## 🌟 Summary

**Devolv Drift is built for CI/CD.** Automate IAM drift detection, protect your AWS environment, and ensure policy alignment — with zero manual effort.

➡ [Get the onboarding script](https://github.com/devolvdev/devolv-actions/blob/main/devolv_oidc_onboard.py)  
➡ [Install the CLI (for local use)](https://pypi.org/project/devolv/)  
➡ Add the workflow file, enable PR permissions, and go!
