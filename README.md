# 🕵️‍♂️ AI Business Analyst — Azura

> **Azura** is an intelligent AI-powered Business Analyst agent built by **Vaival Technologies**. She conducts structured requirements-gathering interviews, then automatically generates professional **Product Requirements Documents (PRDs)** as downloadable PDFs — all through a sleek chat interface.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture & Modules](#-architecture--modules)
- [User Roles & Permissions](#-user-roles--permissions)
- [Tech Stack](#-tech-stack)
- [Setup & Installation](#-setup--installation)
- [Running the App](#-running-the-app)
- [How to Use](#-how-to-use)
- [Project Structure](#-project-structure)
- [Environment Variables](#-environment-variables)
- [Database](#-database)
- [Long-Term Memory (RAG)](#-long-term-memory-rag)
- [PDF Generation](#-pdf-generation)
- [FAQ](#-faq)
- [Contributing](#-contributing)

---

## 🧠 Overview

The **AI Business Analyst** (Azura) is a conversational agent designed to replace the tedious manual effort of writing Product Requirement Documents. It:

1. Engages users in a **natural language interview** to gather project requirements.
2. Uses an **LLM via OpenRouter** (Meta Llama 4 Scout by default) to structure conversation transcripts into a validated PRD JSON.
3. Renders a **professionally formatted PDF** (via ReportLab) complete with milestones, user stories, deliverables, functional/non-functional/technical requirements, and signatory sections.
4. Persists all sessions and PRD versions in a **SQLite (or PostgreSQL) database** for version history and audit trails.
5. Maintains **long-term memory via ChromaDB** (vector store) so Azura can recall context from previously uploaded documents or past PRDs.

The system is accessible through:
- A **Streamlit web UI** (`app.py`) — the primary interface.
- A **Rich CLI runner** (`main.py`) — for terminal-based usage.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🤖 **AI Interviewer** | Azura conducts a structured, multi-phase requirements interview |
| 📄 **Automated PRD Generation** | Full PRD (PDF) output from conversation transcript, no manual writing needed |
| 🔄 **PRD Versioning** | Each regeneration creates a new version; full history shown in sidebar |
| 📎 **PDF Upload & RAG** | Users can upload reference PDFs; content is indexed in ChromaDB for semantic retrieval |
| 🧠 **Long-Term Memory** | Vector DB stores past PRDs and document content for cross-session recall |
| 🔁 **Review & Modify** | After generation, users can request changes and regenerate updated PDFs |
| 💬 **Multi-Phase Conversation** | Automatically transitions between `chat → interview → review` phases |
| 🖥️ **Dual Interface** | Streamlit web app + Rich CLI terminal runner |
| 🗄️ **Production-Ready DB** | SQLite by default; swap to PostgreSQL with a single env variable change |
| 📋 **User Stories** | LLM auto-generates 5–10 user stories based on gathered functional requirements |

---

## 🏗️ Architecture & Modules

### Agent Layer (`agent/`)

| File | Purpose |
|---|---|
| `graph.py` | Defines the **LangGraph** `StateGraph`; wires `chat → structure → generate_pdf` nodes with conditional edges |
| `nodes.py` | Contains the three graph nodes: `chat_node`, `structure_node`, `generate_pdf_node` |
| `state.py` | `AgentState` TypedDict — the shared state passed between all graph nodes |

### Services Layer (`services/`)

| File | Purpose |
|---|---|
| `llm_service.py` | Single LLM invocation point via OpenRouter API (LangChain `ChatOpenAI`); logs latency and token usage |
| `prd_service.py` | Structures conversation transcripts into PRD JSON via LLM; handles JSON repair retries; persists versions to DB |
| `pdf_service.py` | Converts raw PRD dict → `AnalysisReport` Pydantic model → PDF via `report_builder` |
| `doc_service.py` | Extracts text from user-uploaded PDFs using **PyMuPDF** (`fitz`) |
| `memory_service.py` | ChromaDB RAG store: chunks text, embeds via `sentence-transformers`, stores/retrieves for context injection |

### Database Layer (`db/`)

| File | Purpose |
|---|---|
| `models.py` | SQLAlchemy ORM models: `ChatSession` and `PRDVersion` |
| `database.py` | Engine setup, `SessionLocal` factory, `init_db()`, `get_db()` context manager |
| `repository.py` | CRUD operations (repository pattern): session creation, phase updates, PRD version save/fetch |

### PDF Generator (`pdf_generator/`)

| File | Purpose |
|---|---|
| `report_builder.py` | Full ReportLab PDF builder: cover page, service provider/client info, all 7 PRD sections + user stories table + signatory blocks |

### Schemas (`schemas/`)

| File | Purpose |
|---|---|
| `output_schema.py` | Pydantic models: `AnalysisReport`, `ProjectOverview`, `MilestoneItem`, `Deliverables`, `FunctionalRequirements`, `NonFunctionalRequirements`, `TechnicalRequirements`, `UserStory`, `Signatory` |

### Core (`core/`)

| File | Purpose |
|---|---|
| `config.py` | Centralized `Settings` dataclass; all config sourced from `.env` via `python-dotenv` |
| `logging_config.py` | Structured logging setup for the entire application |

### Entry Points

| File | Purpose |
|---|---|
| `app.py` | **Streamlit web UI** — main user-facing application |
| `main.py` | **CLI runner** — terminal interface using `rich` for formatted output |
| `config.py` (root) | Backward-compatibility shim re-exporting `core.config.settings` |

---

## 👥 User Roles & Permissions

> This system is designed for internal business use. There is currently **no authentication layer** — all users have equal access. Roles are gathered as *project metadata* during the interview process and embedded into the PRD document.

### Roles Captured in Generated PRDs

| Role | Description |
|---|---|
| **Project Manager** | Oversees project execution and timeline |
| **Development Team** | Implements the software system |
| **Business Stakeholder** | Defines requirements and approves deliverables |
| **End User** | The final consumer of the product being specified |
| **QA / Tester** | Validates software against acceptance criteria |
| **Client** | External party commissioning the project |
| **Service Provider** | Vaival Technologies (or the delivering team) |

> Custom roles are captured dynamically during the Azura interview and reflected in user stories and functional requirements sections of the PRD.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Meta Llama 4 Scout 17B via [OpenRouter](https://openrouter.ai/) |
| **Agent Framework** | [LangGraph](https://langchain-ai.github.io/langgraph/) + LangChain |
| **Frontend** | [Streamlit](https://streamlit.io/) |
| **CLI** | [Rich](https://github.com/Textualize/rich) |
| **PDF Generation** | [ReportLab](https://www.reportlab.com/) |
| **PDF Parsing** | [PyMuPDF](https://pymupdf.readthedocs.io/) (`fitz`) |
| **Vector Memory** | [ChromaDB](https://www.trychroma.com/) + `sentence-transformers/all-MiniLM-L6-v2` |
| **Database ORM** | [SQLAlchemy](https://www.sqlalchemy.org/) 2.0 |
| **Database** | SQLite (default) / PostgreSQL (production swap) |
| **Migrations** | [Alembic](https://alembic.sqlalchemy.org/) |
| **Schema Validation** | [Pydantic](https://docs.pydantic.dev/) v2 |
| **Config Management** | `python-dotenv` |

---

## ⚙️ Setup & Installation

### Prerequisites

- Python **3.10+**
- `pip`
- An **OpenRouter API Key** — get one free at [openrouter.ai](https://openrouter.ai/)

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd "BA Agent"
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note (Linux):** If ChromaDB fails on SQLite version, `pysqlite3-binary` is already included in `requirements.txt` and the `memory_service.py` handles the override automatically.

### 4. Configure Environment Variables

Copy the example environment and fill in your credentials:

```bash
cp .env .env.local   # or edit .env directly
```

Edit `.env`:

```dotenv
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MODEL_NAME=meta-llama/llama-4-scout-17b-16e-instruct

# Database (SQLite default — no setup required)
DATABASE_URL=sqlite:///./ba_agent.db

# Optional: switch to PostgreSQL
# DATABASE_URL=postgresql://postgres:password@localhost:5432/ba_agent
```

### 5. (Optional) Run Database Migrations

For SQLite, tables are auto-created on first launch. For PostgreSQL or schema changes, use Alembic:

```bash
alembic upgrade head
```

---

## 🚀 Running the App

### Option A: Streamlit Web UI (Recommended)

```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501**

### Option B: CLI Terminal Interface

```bash
python main.py
```

---

## 💡 How to Use

### Step-by-Step Flow

#### 1. Start a Conversation
- Open the Streamlit app or run `python main.py`
- Azura greets you: *"Hi! I'm Azura. How can I help you?"*
- Chat casually — she will answer general questions like a helpful assistant.

#### 2. Trigger PRD Mode
- Say something like: *"I want to create a PRD for my new app"* or *"Let's document my project requirements"*
- Azura automatically switches to **Interview Mode** and begins asking structured questions.

#### 3. Answer Interview Questions
Azura will gather information across all PRD sections:
- **Project Overview** — name, brief, outcomes, stakeholders, timeline, milestones
- **Project Deliverables** — modules, docs, training materials
- **Functional Requirements** — user roles, UI specs, data management, integrations
- **Non-Functional Requirements** — performance, reliability, scalability, compliance
- **Technical Requirements** — languages, frameworks, database, hosting, security
- **Service Provider & Client Info** (optional)

#### 4. Confirm Generation
- When Azura says *"I now have all the information I need — shall I generate the PRD?"*, type **"yes"** or **"go ahead"**.
- Azura generates a structured JSON from your conversation and renders it as a PDF.

#### 5. Download Your PRD
- A **Download** button appears in the chat and in the **sidebar** (Version History).
- Each generation creates a new versioned file (e.g., `my_project_20250227_123456.pdf`).

#### 6. Upload Reference Documents (Optional)
- Click the **📎 paperclip button** (bottom-left of chat input) to upload a PDF.
- Azura reads it, indexes it in ChromaDB, and can answer questions about it or pull content into the PRD.

#### 7. Modify & Regenerate
- After PRD generation, switch to **Review Mode** automatically.
- Ask Azura to change specific sections, then confirm to regenerate an updated version.

---

## 📁 Project Structure

```
BA Agent/
├── app.py                    # Streamlit web UI entry point
├── main.py                   # CLI terminal runner
├── config.py                 # Backward-compat config shim
├── requirements.txt          # Python dependencies
├── alembic.ini               # Alembic migration config
├── ba_agent.db               # SQLite database (auto-created)
│
├── agent/                    # LangGraph agent
│   ├── graph.py              # StateGraph definition & edges
│   ├── nodes.py              # chat_node, structure_node, generate_pdf_node
│   └── state.py              # AgentState TypedDict
│
├── services/                 # Business logic / service layer
│   ├── llm_service.py        # LLM invocation via OpenRouter
│   ├── prd_service.py        # PRD structuring + DB persistence
│   ├── pdf_service.py        # AnalysisReport builder + PDF writer
│   ├── doc_service.py        # PDF text extraction (PyMuPDF)
│   └── memory_service.py     # ChromaDB long-term memory / RAG
│
├── pdf_generator/
│   └── report_builder.py     # Full ReportLab A4 PDF layout
│
├── schemas/
│   └── output_schema.py      # Pydantic models for PRD structure
│
├── db/
│   ├── models.py             # ChatSession + PRDVersion ORM models
│   ├── database.py           # Engine, session factory, init_db
│   └── repository.py        # CRUD repository pattern
│
├── core/
│   ├── config.py             # Settings dataclass (env-driven)
│   └── logging_config.py     # Structured logging setup
│
├── alembic/                  # Database migration scripts
├── output/                   # Generated PDFs are saved here
└── data/
    └── vector_store/         # ChromaDB persistent storage
```

---

## 🔐 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | *(required)* | Your OpenRouter API key |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter endpoint |
| `MODEL_NAME` | `meta-llama/llama-4-scout-17b-16e-instruct` | LLM model to use |
| `MAX_TOKENS` | `8000` | Max tokens per LLM response |
| `TEMPERATURE` | `0.7` | LLM creativity/temperature |
| `MAX_RETRIES` | `3` | JSON structuring retry attempts |
| `RETRY_DELAY` | `4` | Seconds between retries |
| `DATABASE_URL` | `sqlite:///./ba_agent.db` | SQLAlchemy DB connection string |
| `OUTPUT_DIR` | `output` | Directory for generated PDFs |
| `CHROMA_PATH` | `data/vector_store` | ChromaDB persistent storage path |
| `INPUT_PDF_DIR` | `data/input_pdfs` | Optional input PDF directory |

---

## 🗄️ Database

The app uses **SQLAlchemy 2.0** with two tables:

### `chat_sessions`
Tracks each browser/CLI session and its current phase.

| Column | Type | Description |
|---|---|---|
| `id` | `VARCHAR(36)` | UUID primary key |
| `created_at` | `DATETIME` | Session creation timestamp |
| `updated_at` | `DATETIME` | Auto-updated on every change |
| `phase` | `VARCHAR(20)` | `chat` \| `interview` \| `review` |
| `session_metadata` | `JSON` | Optional extra metadata |

### `prd_versions`
Stores each generated PRD version, linked to its session.

| Column | Type | Description |
|---|---|---|
| `id` | `VARCHAR(36)` | UUID primary key |
| `session_id` | `VARCHAR(36)` | FK → `chat_sessions.id` |
| `version_number` | `INTEGER` | Auto-incremented per session (1, 2, 3…) |
| `project_name` | `VARCHAR(255)` | Project name extracted from PRD |
| `prd_json` | `JSON` | Full structured PRD JSON |
| `pdf_path` | `VARCHAR(512)` | File path to generated PDF |
| `created_at` | `DATETIME` | Version creation timestamp |

> **SQLite → PostgreSQL migration:** Change `DATABASE_URL` in `.env` to your PostgreSQL connection string. Run `alembic upgrade head` for schema migrations. No code changes needed.

---

## 🧠 Long-Term Memory (RAG)

Azura uses **ChromaDB** as a persistent vector store for long-term memory:

- **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (runs locally, no API needed)
- **Chunk Size:** 1000 characters with 200-character overlap
- **Collection Name:** `ba_agent_memory`
- **Similarity Metric:** Cosine similarity

### What Gets Stored
| Source | When |
|---|---|
| Uploaded PDF documents | When user attaches a PDF in the UI |
| Generated PRD JSON | After each successful PRD generation |

### How It's Used
Before each LLM call in `chat_node`, Azura runs a semantic search against ChromaDB using the user's latest message. The top-4 most relevant chunks are injected into the system prompt as **"PAST KNOWLEDGE & MEMORY"**, enabling Azura to reference previous projects and documents across sessions.

---

## 📄 PDF Generation

Generated PRDs are **A4 PDF files** (`output/*.pdf`) built with **ReportLab**. Each PDF contains:

1. **Cover Page** — Company branding, project name, date, service provider and client details
2. **Section 1:** Introduction
3. **Section 2:** Project Overview (brief, outcomes, stakeholders, timeline, milestones with acceptance criteria)
4. **Section 3:** Project Deliverables (software modules, documentation, training materials, user manuals)
5. **Section 4:** Functional Requirements (user roles, UI/UX specs, data management, integrations)
6. **Section 5:** Non-Functional Requirements (performance, reliability, usability, compatibility, compliance, scalability, maintainability)
7. **Section 6:** Technical Requirements (languages/frameworks, DB, hosting, security, performance/scalability)
8. **Section 7:** User Stories (ID, role, action, benefit, acceptance criteria — table format)
9. **Signatory Section** — Service Provider and Client signature blocks

---

## ❓ FAQ

**Q: Why does the app swap out `sqlite3` for `pysqlite3` at startup?**
A: ChromaDB requires SQLite 3.35+. Many Linux distributions ship with an older version. The `memory_service.py` performs this swap automatically using `pysqlite3-binary`.

**Q: Can I use a different LLM?**
A: Yes. In `.env`, set `MODEL_NAME` to any model available on [OpenRouter](https://openrouter.ai/models). The system uses LangChain's `ChatOpenAI` with OpenRouter's base URL, so any compatible model works.

**Q: Can I use a different embedding model?**
A: Yes, but this requires changing `EMBEDDING_MODEL` in `core/config.py` and re-indexing your ChromaDB collection (delete `data/vector_store/` to reset).

**Q: The PRD JSON was malformed — what happens?**
A: `prd_service.py` automatically retries up to `MAX_RETRIES` (3 by default) times, sending the parse error back to the LLM as a repair hint on each retry.

**Q: Where are generated PDFs saved?**
A: In the `output/` directory at the project root. Filenames follow the pattern `<project_name>_<YYYYMMDD_HHMMSS>.pdf`.

**Q: Can I run this in production with multiple concurrent users?**
A: For production deployments, switch to PostgreSQL and run Streamlit behind a reverse proxy (e.g., nginx). The `check_same_thread=False` flag handles SQLite multi-threading for local/single-user use only.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

### Code Style Guidelines
- Follow existing module separation: agent nodes are orchestrators only (no business logic inside)
- All LLM calls must go through `services/llm_service.py`
- All DB access must go through `db/repository.py`
- New configurations must be added to `core/config.py`

---

## 📬 Contact

**Vaival Technologies**  
*AI-powered software solutions*

> Built with ❤️ by Isha Sarwar @ Vaival Technologies
