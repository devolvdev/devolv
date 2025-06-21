# devolv-validator

**devolv-validator** is a Python CLI tool that statically validates AWS IAM policies (JSON or YAML) for risky patterns such as wildcards, privilege escalation risks, and bad practices.

## 🚀 Features

- 🚩 Detects wildcards in `Action` and `Resource`
- 🔐 Flags `iam:PassRole` on wildcard `Resource`
- 📂 Supports both JSON and YAML formats
- ⚙️ Clean CLI built with Typer
- ✅ Ready for CI with GitHub Actions

## 📦 Installation

```bash
pip install devolv-validator
```

## 🛠 Usage

```bash
devolv-validator validate path/to/policy.json
```

## 📁 Example

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

This policy will be flagged with high-severity warnings.

## 🧪 Run Tests

```bash
pytest
```

## 🧰 About

This is part of the [devolv](https://github.com/devolvdev) OSS DevOps toolkit.
