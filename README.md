
# Devolv

[![PyPI - Version](https://img.shields.io/pypi/v/devolv)](https://pypi.org/project/devolv/)
[![Tests](https://github.com/devolvdev/devolv/actions/workflows/test.yml/badge.svg)](https://github.com/devolvdev/devolv/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)](https://github.com/devolvdev/devolv/actions/workflows/test.yml)

**Devolv** is a modular DevOps CLI toolkit focused on AWS IAM security and cloud automation.

🔧 Install once — and unlock multiple tools to validate, detect drift, and secure your infrastructure.

📖 **Docs:** [https://devolvdev.github.io/devolv](https://devolvdev.github.io/devolv)

---

## 🧰 Available Tools

| Command                | Description                                 |
|------------------------|---------------------------------------------|
| `devolv validate`      | Validate AWS IAM policies (✅ live)         |
| `devolv drift`         | Detect IAM policy drift (✅ live)           |
| `devolv scan`          | 🔜 Scan AWS accounts (coming soon)          |
| `devolv generate`      | 🧠 Generate safe IAM policies (coming soon) |
| `devolv etl`           | ⚙️ CI/CD IAM transformation (planned)       |

---

## 📦 Installation

```bash
pip install devolv
```

---

## 🛠 Example Usage

### Validate IAM Policy
```bash
devolv validate path/to/policy.json
```
> Outputs security warnings if wildcards or risks are found.

### Detect IAM Drift
```bash
devolv drift --policy-name my-policy --file ./policy.json
```
> Shows differences between your local policy file and the deployed AWS policy.

---

## 🧪 Run Tests

```bash
pytest --cov=devolv --cov-report=term-missing
```

---

## 📖 Full Documentation

Visit: [https://devolvdev.github.io/devolv](https://devolvdev.github.io/devolv)

---

Built with ❤️ by the [Devolv Dev](https://github.com/devolvdev) team.
