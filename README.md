# FarmBot documentation utilities

Checks to run during development and on pull requests (GitHub Actions workflows).

---

[FarmBot-Docs GitHub organization overview](https://github.com/FarmBot-Docs/farmbot-docs/blob/main/docs/overview.md)

## Running locally

```
git clone https://github.com/FarmBot-Docs/farmbot-genesis
git clone https://github.com/FarmBot-Docs/farmbot-express
git clone https://github.com/FarmBot-Docs/farmbot-software
git clone https://github.com/FarmBot-Docs/farmbot-developers
git clone https://github.com/FarmBot-Docs/farmbot-meta
git clone https://github.com/FarmBot-Docs/farmbot-oer
git clone https://github.com/FarmBot-Docs/utilities
python -m pip install -r utilities/requirements.txt
python utilities/run_all_checks.py
```
