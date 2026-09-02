# AI Trust Layer — The Firewall for AI Agents

An intelligent oversight system that intercepts AI agent actions **before execution**, analyzes each action across **financial risk, privacy, and company policy compliance**, and either **approves, escalates, or blocks** it — with a persistent audit trail.

---

## What It Does

AI agents can send emails, transfer money, execute code, and access confidential documents. But nothing inherently prevents them from making dangerous or unauthorized decisions.

The **AI Trust Layer** sits between an AI agent and the real world. It intercepts every action before execution, evaluates the associated risks, and determines whether the action should proceed.

### Supported Action Types

| Action           | What It Represents                              |
| ---------------- | ----------------------------------------------- |
| `transfer_money` | Financial payments and bank transfers           |
| `send_email`     | Outgoing emails with or without attachments     |
| `execute_code`   | Database queries and scripts in any environment |

---

## Evaluation Pipeline

```text
User Instruction
       ↓
Worker Agent builds action object
       ↓
Interceptor catches action before execution
       ↓
Three checkers run simultaneously
       ├── Financial Checker
       │     └── Checks amount, recipient, currency
       │
       ├── Privacy Checker
       │     └── Detects CNIC, phone numbers, and personal data
       │
       └── Policy Checker
             └── Enforces company rules by action type
       ↓
Scorer combines checker results
       ↓
Weighted final risk score
       ↓
Decision Engine applies thresholds
       ↓
Result logged to SQLite audit database
       ↓
Dashboard displays decision and reasoning
```

---

## Decision Bands

|  Score | Decision                  | What Happens                                              |
| -----: | ------------------------- | --------------------------------------------------------- |
|   0–40 | **Approved**              | Action proceeds automatically                             |
|  41–70 | **Approved with Warning** | Action proceeds and warning is logged                     |
|  71–89 | **Escalated**             | Action is paused and requires human approval or rejection |
| 90–100 | **Blocked**               | Action is stopped and full reasoning is recorded          |

---

## Checker Weights by Action Type

Different action types require different risk priorities.

| Action           | Financial | Privacy | Policy |
| ---------------- | --------: | ------: | -----: |
| `transfer_money` |       40% |     30% |    30% |
| `send_email`     |       20% |     50% |    30% |
| `execute_code`   |       30% |     20% |    50% |

---

## Repository Structure

```text
ai-trust-layer/
│
├── action_schema.py          # Standard action object format
├── config.py                 # API key, paths, thresholds, and checker weights
│
├── worker/
│   └── agent.py              # Action builder functions
│
├── trust/
│   ├── interceptor.py        # Intercepts actions before execution
│   ├── trust_agent.py        # Runs all three checkers
│   ├── scorer.py             # Combines scores and determines decision
│   └── checkers/
│       ├── financial.py      # Financial risk checker
│       ├── privacy.py        # Privacy and PII checker
│       └── policy.py         # Company policy checker
│
├── database/
│   └── audit.py              # SQLite audit log
│
├── api/
│   └── main.py               # FastAPI backend
│
├── dashboard/
│   └── app.py                # Streamlit monitoring dashboard
│
├── rag/                      # Optional RAG modules
│   ├── loader.py             # Loads company policy into ChromaDB
│   └── retriever.py          # Retrieves relevant policy sections
│
└── policies/
    └── company_policy.pdf    # Optional company policy document
```

---

## Installation

### Step 1 — Clone the Repository

Replace the placeholder GitHub URL with your actual repository URL.

```bash
git clone https://github.com/your-username/ai-trust-layer.git
cd ai-trust-layer
```

### Step 2 — Create a Virtual Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux

```bash
python -m venv venv
source venv/bin/activate
```

### Step 3 — Install Dependencies

```bash
pip install python-dotenv streamlit fastapi pydantic "uvicorn[standard]" google-generativeai
```

---

## Configuration

### Create Your `.env` File

Create a file named `.env` in the project root:

```text
GOOGLE_API_KEY=your-gemini-api-key-here
```

You can obtain a Gemini API key from [Google AI Studio](https://aistudio.google.com).

> **Security:** Never commit your `.env` file or API keys to GitHub.

Add the following to `.gitignore`:

```text
.env
venv/
__pycache__/
database/audit.db
*.pyc
```

---

## Running the Dashboard

The Streamlit dashboard provides the easiest way to interact with and monitor the system.

Run the following command from the project root:

```bash
python -m streamlit run dashboard/app.py
```

The dashboard will be available at:

```text
http://localhost:8501
```

### Dashboard Features

* **Metrics Panel**

  * Total actions
  * Open escalations
  * Average risk score
  * Decision counts

* **Audit Log**

  * Complete history of intercepted actions
  * Expandable action details
  * Risk scores and checker reasoning

* **Review Queue**

  * Escalated actions awaiting human review
  * Approve or reject pending actions

* **Submit Test Action**

  * Five built-in scenarios
  * Manual submission for all three action types

* **Sidebar Filters**

  * Filter by decision type
  * Filter by action type

---

## Built-in Test Presets

The dashboard includes five predefined scenarios for testing the trust layer.

| Preset                           | Expected Decision         |
| -------------------------------- | ------------------------- |
| Routine PKR transfer             | **Approved**              |
| Production cleanup command       | **Approved with Warning** |
| High-risk transfer               | **Escalated**             |
| Email containing a CNIC          | **Escalated**             |
| International high-risk transfer | **Blocked**               |

---

## Running the API

Run the FastAPI backend from the project root:

```bash
python -m uvicorn api.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

---

## API Routes

| Method | Route                   | Description                                        |
| ------ | ----------------------- | -------------------------------------------------- |
| `GET`  | `/health`               | Confirms that the service is running               |
| `POST` | `/actions`              | Submits an action for trust evaluation             |
| `GET`  | `/actions`              | Returns the audit trail                            |
| `POST` | `/actions/{id}/resolve` | Records a human resolution for an escalated action |

---

## Submit an Action

### Request Body

Example `transfer_money` request:

```json
{
  "action_type": "transfer_money",
  "details": {
    "amount": 500000,
    "currency": "PKR",
    "recipient": "unknown_account",
    "description": "Vendor payment"
  },
  "triggered_by": "Worker Agent"
}
```

---

## Action Detail Fields

### `transfer_money`

```text
amount          number   Payment amount
currency        string   PKR for local, other currencies for international transfers
recipient       string   Destination account or recipient name
description     string   Purpose of the transfer
```

### `send_email`

```text
to               string   Recipient email address
subject          string   Email subject line
body             string   Email body text
has_attachment   boolean  Whether an attachment is included
attachment_name  string   Filename of the attachment
```

### `execute_code`

```text
code          string   Query or script to execute
environment   string   development, staging, or production
language      string   SQL, Python, Bash, etc.
```

---

## Resolve an Escalated Action

An escalated action can be resolved through the API after human review.

### Request Body

```json
{
  "resolved_by": "Ahmed Khan",
  "resolution": "approved"
}
```

The resolution should indicate whether the human reviewer approved or rejected the action.

---

## Smoke Test

The following Python example submits an action expected to trigger escalation:

```python
import requests

response = requests.post(
    "http://localhost:8000/actions",
    json={
        "action_type": "transfer_money",
        "details": {
            "amount": 250000,
            "currency": "PKR",
            "recipient": "Unverified Vendor",
            "description": "Please call 03001234567 before processing"
        },
        "triggered_by": "Worker Agent"
    }
)

result = response.json()

print(result["decision"])
print(result["final_score"])
print(result["reasons"])
```

Expected output should contain:

```text
escalated
```

along with a risk score and the reasons generated by the trust checkers.

---

## Audit Database

Every evaluated action — whether approved, approved with warning, escalated, or blocked — is stored in the SQLite audit database:

```text
database/audit.db
```

The database is created automatically when the application runs.

It contains submitted action details and evaluation results and should therefore be treated as **sensitive data**.

### Important Security Notes

Do not commit the database to version control.

Add it to `.gitignore`:

```text
database/audit.db
```

The current dashboard and API do not implement authentication and are intended for **localhost/development use only**.

> Do not expose the dashboard or API directly to a public network without implementing appropriate authentication, authorization, and security controls.

---

## Optional RAG Modules

The `rag/` directory contains optional Retrieval-Augmented Generation components.

These modules are **not part of the current trust scoring pipeline**.

```text
rag/
├── loader.py
└── retriever.py
```

The current policy checker uses its own built-in rules and does not depend on the RAG modules.

### Install RAG Dependencies

If you want to experiment with RAG-based company policy retrieval:

```bash
pip install chromadb PyPDF2 sentence-transformers
```

### Add a Company Policy

Place your policy document at:

```text
policies/company_policy.pdf
```

Then load it into the vector store:

```bash
python -c "from rag.loader import load_policy_vector_store; load_policy_vector_store()"
```

---

## Troubleshooting

### `ModuleNotFoundError`

Make sure you are running commands from the project root rather than from inside a subfolder.

Example:

```text
ai-trust-layer/
```

Run your commands from this directory.

### Port Already in Use

If port `8501` is already occupied, use another Streamlit port:

```bash
python -m streamlit run dashboard/app.py --server.port 8502
```

If port `8000` is occupied, use another API port:

```bash
python -m uvicorn api.main:app --reload --port 8001
```

### `GOOGLE_API_KEY` Not Found

Make sure:

1. A `.env` file exists in the project root.
2. The variable is named exactly `GOOGLE_API_KEY`.
3. The API key is valid.
4. The `.env` file does not have an additional extension such as `.env.txt`.

Example:

```text
GOOGLE_API_KEY=your-gemini-api-key-here
```

### `database/audit.db` Path Error

Always launch the dashboard and API from the project root:

```text
ai-trust-layer/
```

The database path is relative to the project structure.

---

## Security Considerations

This project is designed as a **development and research prototype**.

Before deploying it in a production environment, consider implementing:

* Authentication and authorization
* Role-based access control
* Secure API endpoints
* Encrypted secrets management
* Database encryption or appropriate access controls
* HTTPS/TLS
* Rate limiting
* Input validation
* Production-grade database infrastructure
* Secure logging and log retention
* Human approval authentication
* Monitoring and alerting

---

## Project Architecture

At a high level, the system follows this architecture:

```text
                    ┌───────────────────┐
                    │   User / Agent    │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │  Worker Agent     │
                    │  Action Builder   │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   Interceptor     │
                    └─────────┬─────────┘
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
          ┌────────────┐ ┌──────────┐ ┌──────────┐
          │ Financial  │ │ Privacy  │ │  Policy  │
          │  Checker   │ │ Checker  │ │ Checker  │
          └─────┬──────┘ └────┬─────┘ └────┬─────┘
                │             │             │
                └─────────────┼─────────────┘
                              ▼
                    ┌───────────────────┐
                    │      Scorer       │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │  Decision Engine  │
                    └─────────┬─────────┘
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
            ┌─────────┐ ┌───────────┐ ┌─────────┐
            │ Approve │ │ Escalate  │ │  Block  │
            └─────────┘ └─────┬─────┘ └─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   Audit Database  │
                    │      SQLite       │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Streamlit         │
                    │ Dashboard         │
                    └───────────────────┘
```

---

## Technology Stack

| Component                 | Technology            |
| ------------------------- | --------------------- |
| Language                  | Python                |
| AI Model                  | Google Gemini         |
| API                       | FastAPI               |
| Dashboard                 | Streamlit             |
| Data Validation           | Pydantic              |
| Database                  | SQLite                |
| Environment Configuration | python-dotenv         |
| Optional Vector Database  | ChromaDB              |
| Optional Embeddings       | Sentence Transformers |

---

## Project Status

**Status:** Development / Research Prototype

The current implementation demonstrates an AI agent trust and oversight layer capable of:

* Intercepting agent actions
* Evaluating financial risk
* Detecting sensitive personal information
* Applying policy-based rules
* Combining multiple risk signals
* Producing risk-based decisions
* Escalating high-risk actions for human review
* Blocking critical actions
* Maintaining an audit trail
* Providing a monitoring dashboard
* Exposing a REST API

---

## License

Add your preferred license before publishing the repository.

For example:

```text
MIT License
```

If this project is part of an academic submission, also include the relevant course, institution, or research attribution as required.

---

## Disclaimer

This project is a research and development prototype intended to demonstrate AI agent oversight, risk evaluation, and human-in-the-loop decision making.

It should not be considered a production-ready financial, privacy, security, or compliance system without additional validation, security controls, testing, and regulatory review.
