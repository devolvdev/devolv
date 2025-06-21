# `devolv validate file`

This is the first released module of Devolv.

---

## 🛡 Purpose

Statically validate AWS IAM policy files for:

- ✅ Wildcards in Action or Resource
- 🔐 `iam:PassRole` misuse
- 🚨 Common escalation risks

---

## 📂 Supported Input

- `.json`
- `.yaml` / `.yml`

---

## 🔧 Usage

```bash
devolv validate file path/to/policy.json
```

---

## 📋 Example

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

Output:

```
❌ HIGH: Policy uses wildcard in Action, which is overly permissive.
```

---

## ✅ Exit Codes

- `0`: All checks passed
- `1`: Risk found in policy
- `2`: File or format error

