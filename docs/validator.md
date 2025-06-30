
# `devolv validate`

This is the **first released module** of **Devolv** — the Modular DevOps CLI Toolkit.

---

## 🛡 Purpose

Statically validate AWS IAM policy files to detect:

- ✅ Wildcards in Action (`*`, `s3:*`)  
- 🔐 `iam:PassRole` with wildcard resources  
- 🚨 Common privilege escalation risks

---

## 📂 Supported Input Formats

- `.json`
- `.yaml` / `.yml`

---

## 🔧 Usage

### 🔹 Validate a Single File

```bash
devolv validate path/to/policy.json
```

### 🔹 Validate a Folder

```bash
devolv validate path/to/folder/
```

> Scans all `.json`, `.yaml`, and `.yml` files in the folder recursively.

---

## 📋 Example Output

```bash
🔹 Validating: path/to/policy.json
❌ High-risk findings detected:
  - HIGH: Policy uses overly permissive action 's3:*' with resource ['arn:aws:s3:::example-bucket/*']. Statement starts at line 6.
  - HIGH: iam:PassRole with wildcard Resource ('*') can lead to privilege escalation. Statement starts at line 11.

🔹 Validating: path/to/another-policy.json
✅ No high-risk findings — policy is safe.
```

---

## ✅ Exit Codes

| Code | Meaning                                   |
|------|-------------------------------------------|
| `0`  | All checks passed (no issues found)       |
| `1`  | Risk(s) found in policy                   |
| `2`  | File/folder not found or invalid format   |
