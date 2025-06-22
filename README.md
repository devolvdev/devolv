# devolv

[![PyPI - Version](https://img.shields.io/pypi/v/devolv)](https://pypi.org/project/devolv/)
[![Tests](https://github.com/devolvdev/devolv/actions/workflows/test.yml/badge.svg)](https://github.com/devolvdev/devolv/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
![CI](https://github.com/YOUR_USERNAME/devolv/actions/workflows/test.yml/badge.svg)

**Devolv** is a modular DevOps CLI toolkit focused on AWS IAM security and cloud automation.

🔧 Install once — and unlock multiple tools to validate, transform, and secure your infrastructure.

📖 **Docs:** [devolvdev.github.io/devolv](https://devolvdev.github.io/devolv)

---

## 🧰 Available Tools

| Command                | Description                                |
|------------------------|--------------------------------------------|
| `devolv validate`      | Validate AWS IAM policies (✅ live)        |
| `devolv scan`          | 🔜 Scan AWS accounts (coming soon)         |
| `devolv generate`      | 🧠 Generate safe IAM policies (coming soon)|
| `devolv etl`           | ⚙️ CI/CD IAM transformation (planned)      |

---

## 📦 Installation

```bash
pip install devolv
```

## 🛠 Example

```bash
devolv validate file path/to/policy.json
```

> Outputs security warnings if wildcards or risks are found.

---

## 🧪 Run Tests

```bash
pytest
```

---

## 🧰 Full Documentation

📖 Visit: [https://devolvdev.github.io/devolv](https://devolvdev.github.io/devolv)

Built with love by the [Devolv Dev](https://github.com/devolvdev) team.
