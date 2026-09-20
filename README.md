# AI Product Ops — 100-App API & MCP Research

> An evidence-first research and verification pipeline for evaluating API access, authentication, developer surfaces, MCP support, and buildability across 100 applications.

[![Apps Researched](https://img.shields.io/badge/Apps%20Researched-100-blue)](https://github.com/souravjha127/composio-ai-product-ops)
[![Categories](https://img.shields.io/badge/Categories-10-purple)](https://github.com/souravjha127/composio-ai-product-ops)
[![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Complete-success)](https://github.com/souravjha127/composio-ai-product-ops)

## 🔗 Live Research Report

### [View the interactive research report →](https://souravjha127.github.io/composio-ai-product-ops/)

The report provides an interactive view of the 100-app research dataset, verification results, patterns, and buildability findings.

---

## 🎯 Project Overview

This project investigates how practical it is to build integrations and agent workflows around **100 real-world applications**.

For each application, the research pipeline evaluates:

* Authentication methods
* Credential/API access requirements
* API surface and protocols
* API breadth
* MCP availability
* Buildability
* Main integration blocker
* Evidence and source URLs
* Confidence and verification status

The project uses an **evidence-first approach**: conclusions are based on information collected from official documentation, developer pages, API references, pricing/access pages, and other relevant first-party sources where available.

---

## 🧩 What This Project Solves

When evaluating many applications for agent or automation integrations, manually answering questions such as:

> "Does this app have an API?"

is not enough.

A useful integration assessment also needs to understand:

**Can we authenticate? → Can we obtain credentials? → What developer surface exists? → How broad is the API? → Is MCP available? → Can an integration actually be built?**

This project turns those questions into a repeatable research pipeline.

---

## 🏗️ Research Pipeline

```text
                 ┌─────────────────────┐
                 │    100 App Dataset  │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Evidence Collector  │
                 │ researcher.py       │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ First-Pass Research │
                 │ raw_research.json   │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Verification Layer  │
                 │ verifier.py         │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Verified Dataset     │
                 │ verified_results.json│
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Pattern Analysis    │
                 │ analyzer.py         │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Interactive Report  │
                 │ app/index.html      │
                 └─────────────────────┘
```

---

## 📊 Current Research Snapshot

The verified dataset contains **100 applications across 10 categories**.

| Buildability | Records |
| ------------ | ------: |
| Ready        |       9 |
| Conditional  |      30 |
| Blocked      |      38 |
| Unknown      |      23 |
| **Total**    | **100** |

The second-pass verification layer recorded:

* **82 records with at least one field-level change**
* **209 field-level changes**
* **20-record human verification sample**
* **5 records currently marked as checked**
* **15 records pending user confirmation**

> The 82 changed records and 209 field changes describe differences between the first-pass and verification outputs. They are **not an accuracy percentage**.

Because the human verification sample is incomplete, the project does **not** report a final independent human-accuracy percentage.

---

## 🔐 Authentication Patterns

The research tracks common authentication approaches including:

* OAuth 2.0
* API keys
* Bearer/token authentication
* Basic authentication
* Multiple authentication methods

The dataset intentionally preserves `unknown` where available evidence was insufficient rather than treating missing evidence as a negative finding.

---

## 🔌 API Surface

The pipeline identifies developer surfaces such as:

* REST APIs
* GraphQL
* SDKs
* REST + SDK combinations
* REST + GraphQL + SDK combinations

The research also estimates API breadth as:

* Broad
* Moderate
* Narrow
* Unknown

---

## 🤖 MCP Detection

MCP findings use a conservative evidence rule.

An application is marked as having MCP support only when the available evidence explicitly indicates MCP support.

A third-party MCP integration or generic mention is not automatically treated as first-party MCP support.

Where evidence is insufficient, the result remains:

`unknown`

---

## 🧪 Verification Method

The project uses two research stages.

### Stage 1 — Evidence Collection

`agent/researcher.py`

The collector:

1. Reads the 100-app dataset.
2. Searches relevant application/developer pages.
3. Extracts page titles and metadata.
4. Detects authentication indicators.
5. Detects API/developer surfaces.
6. Searches for explicit MCP references.
7. Records source URLs.
8. Produces an initial structured research dataset.

### Stage 2 — Verification

`agent/verifier.py`

The verification layer:

1. Re-fetches stored evidence URLs.
2. Applies stricter detection rules.
3. Re-evaluates authentication.
4. Re-evaluates API surface and breadth.
5. Re-checks MCP evidence.
6. Re-evaluates credential access.
7. Recalculates buildability and blockers.
8. Compares first-pass and verification outputs.

This second pass is designed to reduce unsupported or ambiguous conclusions.

---

## 👤 Human Verification

A stratified sample of **20 applications** was created for human review.

Current status:

```text
20 sample records
├── 5 checked
└── 15 pending confirmation
```

The checked records are treated separately from the automated verification pipeline.

No final human-accuracy percentage is claimed until the sample has sufficient independent confirmation.

---

## 📁 Project Structure

```text
composio-ai-product-ops/
│
├── agent/
│   ├── researcher.py
│   ├── verifier.py
│   ├── analyzer.py
│   └── prompts.py
│
├── app/
│   └── index.html
│
├── data/
│   ├── apps.csv
│   ├── raw_research.json
│   ├── verified_results.json
│   ├── verification_sample.json
│   ├── human_verification_sample.json
│   └── analysis.json
│
├── scripts/
│   ├── build_report.py
│   ├── build_final_report.py
│   ├── check_dataset.py
│   ├── create_verification_sample.py
│   ├── update_human_verification.py
│   └── update_remaining_human_review.py
│
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── index.html
```

---

## ⚙️ Tech Stack

| Technology              | Purpose                               |
| ----------------------- | ------------------------------------- |
| Python                  | Research and data-processing pipeline |
| Requests                | Web-page retrieval                    |
| BeautifulSoup           | HTML parsing                          |
| JSON                    | Structured research outputs           |
| CSV                     | Application input dataset             |
| HTML / CSS / JavaScript | Interactive report                    |
| Git                     | Version control                       |
| GitHub Pages            | Live report hosting                   |

---

## 🚀 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/souravjha127/composio-ai-product-ops.git
cd composio-ai-product-ops
```

### 2. Create the environment

Using Conda:

```bash
conda create -n product_ops python=3.10
conda activate product_ops
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the dataset check

```bash
python scripts/check_dataset.py
```

### 5. Run the research collector

```bash
python agent/researcher.py
```

### 6. Run verification

```bash
python agent/verifier.py
```

### 7. Run analysis

```bash
python agent/analyzer.py
```

### 8. Build the report

```bash
python scripts/build_final_report.py
```

The generated report is available at:

```text
app/index.html
```

---

## 🔁 Reproducibility

The project separates:

**Input → Collection → Verification → Analysis → Presentation**

This makes it possible to inspect intermediate outputs instead of relying only on the final dashboard.

Important generated datasets include:

* `raw_research.json` — first-pass research
* `verified_results.json` — verification output
* `verification_sample.json` — stratified human-review sample
* `human_verification_sample.json` — human-review tracking
* `analysis.json` — aggregate analysis

---

## 🛡️ Data & Secret Handling

No private application credentials are required to reproduce the research pipeline.

Local secrets should be stored in `.env` and are excluded from Git using `.gitignore`.

Example environment configuration is provided through:

```text
.env.example
```

No real API keys or private credentials should be committed to the repository.

---

## 💡 Key Product-Ops Questions

The dataset is designed to answer questions such as:

### Authentication

What authentication methods does the application expose?

### Access

Can a developer obtain credentials through self-service, or is access gated?

### API Surface

Does the application expose REST, GraphQL, SDKs, or multiple surfaces?

### API Breadth

Is the available API narrow, moderate, or broad?

### MCP

Is there explicit evidence of MCP support?

### Buildability

Can an integration be built directly, does it require additional conditions, or is access currently blocked/unclear?

---

## 📌 Important Interpretation Notes

### `Unknown` does not mean `No`

If the available evidence was insufficient, the pipeline records `unknown`.

### `Blocked` does not necessarily mean technically impossible

A blocked classification can reflect access, credential, or other practical integration constraints.

### `Conditional` means additional requirements exist

Examples can include gated access, plan requirements, or other conditions that affect implementation.

### Evidence matters

The dataset stores evidence URLs so that findings can be inspected rather than treated as unsupported assertions.

---

## 📈 Why the Two-Pass Design?

A single automated pass can produce false positives when documentation pages contain:

* generic authentication language
* third-party integrations
* marketing claims
* pricing information unrelated to API access
* incomplete developer documentation

The verification pass therefore re-checks the original evidence and applies stricter rules before the final analysis.

---

## 📚 Repository Deliverables

This repository contains:

* ✅ 100-app research dataset
* ✅ Evidence-first collection pipeline
* ✅ Verification pipeline
* ✅ Structured JSON research outputs
* ✅ Human verification sample
* ✅ Aggregate analysis
* ✅ Interactive HTML report
* ✅ Reproducible scripts
* ✅ README and setup instructions
* ✅ GitHub Pages deployment

---

## 👨‍💻 Author

**Sourav Kumar Jha**

B.Tech — Computer Science & Engineering

Interested in:

* Data Analytics
* AI/ML
* AI Agents
* Product Operations
* API & Integration Research

### Profiles

* [GitHub](https://github.com/souravjha127)
* [LinkedIn](https://www.linkedin.com/in/souravkumarjha22)

---

## ⭐ Project

If you find the research workflow useful, feel free to explore the repository and the interactive report.

**Live Report:**
https://souravjha127.github.io/composio-ai-product-ops/

**Source Repository:**
https://github.com/souravjha127/composio-ai-product-ops/
