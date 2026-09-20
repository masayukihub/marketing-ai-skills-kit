# Quickstart

Requires Python 3.10+. The local runtime has no third-party Python dependencies and makes no network calls.

```bash
python scripts/install.py
python scripts/doctor.py
python scripts/demo.py
```

Open `outputs/demo-project/content/review.html` and `outputs/demo-project/edm/email.html`.
All fixture brands, products, reviews, creator accounts and metrics are synthetic. Missing images are labelled placeholders. No image model is bundled.

For agent-driven strategy and writing, open the whole repository in Codex after installing repo-local skills. Start a new thread and mention one of the five skills in README. The skills share runtime files, so downloading a single Skill folder is not supported.

Create a real project:

```bash
python scripts/new_project.py --id my-product
```

Complete the generated `projects/my-product/project.json` and local source files. Register evidence, preserve unknowns, and provide only rights-cleared images. User projects and output are ignored by Git.

The local scripts prepare deterministic evidence summaries and review drafts. They do not call an LLM, scrape marketplaces, connect corporate cloud storage, send email or publish products. These capabilities require separately configured host tools and explicit user authorization.

Licensing and private-repository creation instructions: `RELEASING.md`.
