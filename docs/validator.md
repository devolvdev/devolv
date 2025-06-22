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
devolv validate file path/to/policy.json
```

### 🔹 Validate a Folder

```bash
devolv validate folder path/to/folder/
```

> Scans all `.json`, `.yaml`, and `.yml` files in the folder recursively.

---

## 📋 Example

### Input File: `policy.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "*",
      "Resource": "*"
    }
  ]
}
```

### Output

```
❌ HIGH: Policy uses wildcard in Action, which is overly permissive.
❌ HIGH: iam:PassRole with wildcard resource can lead to privilege escalation.
```

---

## ✅ Exit Codes

| Code | Meaning                     |
|------|-----------------------------|
| `0`  | All checks passed           |
| `1`  | Risk found in policy        |
| `2`  | File/folder not found or invalid format |
