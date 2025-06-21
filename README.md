# devolv

[![PyPI - Version](https://img.shields.io/pypi/v/devolv)](https://pypi.org/project/devolv/)
[![Tests](https://github.com/devolvdev/devolv/actions/workflows/test.yml/badge.svg)](https://github.com/devolvdev/devolv/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

**Devolv** is a modular DevOps toolkit built for secure-by-default cloud infrastructure.  
Install once — and unlock a growing set of powerful CLI tools designed to improve cloud security, automation, and IAM hygiene.

---

## 🧰 Available Tools

| Command                | Description                                  |
|------------------------|----------------------------------------------|
| `devolv validate file` | Validate AWS IAM policies statically         |


> All tools are accessible through the single CLI entrypoint: `devolv`

---

## 🔐 IAM Validator (Live Now)

`devolv validate file` statically analyzes AWS IAM policies for:

- 🚩 Wildcards in `Action` and `Resource`
- 🔐 `iam:PassRole` without restriction
- ⚠️ Common privilege escalation patterns

Supports both `.json` and `.yaml` input formats.

---

## 📦 Installation

```bash
pip install devolv
```

---

## 🛠 Usage

```bash
devolv validate file path/to/policy.json
```

Example output:

```
❌ HIGH: Policy uses wildcard in Action, which is overly permissive.
```

---

## 📁 Example Policy

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

---

## 🧪 Run Tests

```bash
pytest
```

---

## 👀 Follow the Journey

Devolv is built in public — one CLI tool at a time.  
More tools, community features, and integrations are coming soon.

- 🐍 PyPI: [devolv](https://pypi.org/project/devolv)
- 🔗 GitHub: [github.com/devolvdev](https://github.com/devolvdev)
- 🐦 Twitter/X: [@Devolv__](https://x.com/Devolv__)

---

> Built for cloud engineers. Backed by open-source. Shipped with love.
