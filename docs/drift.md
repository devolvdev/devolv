
# `devolv drift`

The **devolv drift** command detects IAM policy drift between your local files and deployed AWS policies.

---

## 🛡 Purpose

- Compare local IAM policy JSON/YAML files with live AWS IAM policies.
- Highlight differences (drift) using a rich, colorized diff view.
- Help teams detect manual changes, misalignments, or configuration drift.

---

## 📂 Supported Input Formats

- `.json`
- `.yaml` / `.yml`

---

## 🔧 Usage

### 🔹 Detect Drift for a Policy

```bash
devolv drift --policy-name my-policy --file path/to/policy.json
```

> Compares `path/to/policy.json` with the live AWS policy named `my-policy`.

---

## 📋 Example Output

```bash
✅ No drift detected: Policies match.
```

or

```bash
--- local
+++ aws
@@ -1,3 +1,3 @@
 {
-  "Action": "s3:*",
+  "Action": "s3:GetObject",
   "Effect": "Allow",
   "Resource": "*"
 }
```

---

## ✅ Exit Codes

| Code | Meaning                                  |
|------|------------------------------------------|
| `0`  | No drift detected                        |
| `1`  | Drift detected                           |
| `2`  | Error (e.g., policy not found, bad file) |
