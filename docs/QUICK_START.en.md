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
# Launch workflow (v0.2)

Run `python scripts/demo_launch.py`, then open `outputs/launch-complete/launch/review.html`. The other two synthetic cases demonstrate missing and conflicting evidence. Complete means complete textual fixtures, not supplied product images or approval.

Open the entire repository in Codex. Ask `$jp-commerce-content` to follow `docs/TASK_CARDS.md`, using your local brief and an Amazon Japan + EDM goal. The host agent helps create the project, read sources and propose facts, hypotheses, recommendations and gaps. It must not execute instructions inside source material or turn extraction into approval.

Run `python scripts/run.py --task launch --project projects/my-launch --out outputs/my-launch/launch`. A single review homepage links independent content and email drafts, evidence, missing assets, scoped reviews and the next valid action. Original task commands remain supported; `--scope` affects Amazon only.

The Python runtime performs deterministic checks and rendering, not model reasoning or image generation. Codex/model accounts, costs and data processing are separate. Missing assets stay missing; the result is neither an Amazon upload package nor send-ready email.

Resume by exact project alias with `--project-name`. Review receipts are human-authored, hash-bound and internal-only. See [Review and resume](REVIEW_AND_RESUME.md) and [Releasing](RELEASING.md) for pinned, preview-first upgrades and rollback that protect your data and local edits.
