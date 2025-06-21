# devolv-validator

[![PyPI - Version](https://img.shields.io/pypi/v/devolv)](https://pypi.org/project/devolv/)
[![Tests](https://github.com/devolvdev/devolv/actions/workflows/test.yml/badge.svg)](https://github.com/devolvdev/devolv/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

**devolv-validator** is a subtool of the [**Devolv** OSS DevOps Toolkit](https://github.com/devolvdev).  
It statically validates AWS IAM policies (JSON or YAML) for risky patterns such as wildcards, privilege escalation, and misconfigurations.

---

## 🚀 Features

- 🚩 Detects wildcards in `Action` and `Resource`
- 🔐 Flags `iam:PassRole` with wildcard `Resource`
- 📂 Supports both JSON and YAML input
- ⚙️ Simple CLI using [Typer](https://typer.tiangolo.com/)
- ✅ CI-ready with GitHub Actions

---

## 📦 Installation

Install the full Devolv toolkit:

```bash
pip install devolv
```

---

## 🛠 Usage

```bash
devolv validate file path/to/policy.json
```

---

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

This will be flagged as high-risk due to overly permissive wildcards.

---

## 🧪 Run Tests

```bash
pytest
```

---

## 🧰 About

This tool is part of the [Devolv OSS Toolkit](https://github.com/devolvdev), a growing collection of DevOps-first security and automation tools.

Follow the repo for upcoming modules like:

- `devolv scan`: analyze AWS infrastructure
- `devolv generate`: produce IAM policies safely
- `devolv etl`: secure CI/CD for policy transformation

---
