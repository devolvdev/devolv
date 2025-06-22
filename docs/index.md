# Welcome to Devolv 👋

**Devolv** is a growing CLI toolkit designed for cloud engineers who want secure-by-default infrastructure.

---

## 🚀 Why Devolv?

- Prevent security risks in IAM policies  
- Automate least-privilege generation  
- Enable continuous IAM validation in CI/CD  
- All via one CLI interface: `devolv`

---

## 📦 Installation

```bash
pip install devolv
```

---

## 🔍 What Can It Do?

| Command                  | Status   | Description                                        |
|--------------------------|----------|----------------------------------------------------|
| `devolv validate file`   | ✅ Ready | Validate a single AWS IAM JSON/YAML policy file    |
| `devolv validate folder` | ✅ Ready | Validate all policies inside a folder              |
| `devolv scan`            | 🔜 WIP   | Scan AWS accounts for live misconfigurations       |
| `devolv generate`        | 🔜 WIP   | AI/Rule-based IAM policy generation                |
| `devolv etl`             | 🔜 WIP   | Transform/clean policies for IAM pipelines         |

---

## 📖 Docs Navigation

- [Validator CLI](./validator.md)
- [Roadmap](./roadmap.md)
- [GitHub Repo](https://github.com/devolvdev/devolv)
