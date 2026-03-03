# BA Agent — System Diagrams

---

## 1️⃣ Architecture Diagram
*What the system is made of and how parts connect*

```
┌─────────────────────────────────────────────────────────────┐
│                        USER                                 │
└──────────────────┬──────────────────────────┬───────────────┘
                   │                          │
       ┌───────────▼────────────┐  ┌──────────▼──────────────┐
       │     Streamlit Web UI   │  │     CLI Terminal        │
       │        (app.py)        │  │      (main.py)          │
       └───────────┬────────────┘  └──────────┬──────────────┘
                   │                          │
                   └────────────┬─────────────┘
                                │
                    ┌───────────▼────────────┐
                    │      AI Agent          │
                    │    (LangGraph)         │
                    │                        │
                    │  ┌──────────────────┐  │
                    │  │  chat_node       │  │
                    │  │  structure_node  │  │
                    │  │  pdf_node        │  │
                    │  └──────────────────┘  │
                    └────┬──────┬────────┬───┘
                         │      │        │
            ┌────────────▼─┐ ┌──▼──────┐ ┌▼────────────┐
            │  OpenRouter  │ │ SQLite  │ │  ChromaDB   │
            │  LLM API     │ │   DB    │ │  (Vector    │
            │  (Llama 4)   │ │         │ │   Memory)   │
            └──────────────┘ └─────────┘ └─────────────┘
                                               ▲
                                    ┌──────────┴──────────┐
                                    │   Uploaded PDFs     │
                                    │  (indexed via RAG)  │
                                    └─────────────────────┘

                         ┌─────────────────────┐
                         │   output/ folder    │
                         │   Generated PDFs    │
                         │   (user downloads)  │
                         └─────────────────────┘
```

---

## 2️⃣ Workflow Diagram
*Step-by-step user journey*

```
                    ┌──────────────────────┐
                    │      START           │
                    │   User opens app     │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Azura greets user   │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Casual Chat Mode    │◄────────────┐
                    │  (General Q&A)       │             │
                    └──────────┬───────────┘             │
                               │ "I want a PRD"          │
                    ┌──────────▼───────────┐             │
                    │  Interview Mode      │             │
                    │  Azura asks about:   │             │
                    │  • Project name      │             │
                    │  • Requirements      │             │
                    │  • Timeline          │             │
                    │  • Tech stack        │             │
                    └──────────┬───────────┘             │
                               │ all info collected      │
                    ┌──────────▼───────────┐             │
                    │  "Shall I generate?" │             │
                    └────┬─────────────┬───┘             │
                        No            Yes                │
                         │             │                 │
                         │  ┌──────────▼───────────┐     │
                         │  │  PDF Generated       │     │
                         │  │  Saved to output/    │     │
                         │  └──────────┬───────────┘     │
                         │             │                 │
                         │  ┌──────────▼───────────┐     │
                         │  │  User Downloads PDF  │     │
                         │  └──────────┬───────────┘     │
                         │             │                 │
                         │  ┌──────────▼───────────┐     │
                         └─►│  Review Mode         │─────┘
                            │  Ask Qs / Edit / Re- │ new project
                            │  generate new version│
                            └──────────────────────┘
```

---

## 3️⃣ State Diagram
*The 3 phases Azura operates in*

```
              ┌────────────────────────────────────┐
              │                                    │
     ┌────────▼────────┐                           │
     │      CHAT       │                           │
     │   General Q&A   │                           │
     └────────┬────────┘                           │
              │ user says "create a PRD"           │
     ┌────────▼────────┐                           │
     │   INTERVIEW     │                           │
     │  Gather all     │                           │
     │  requirements   │                           │
     └────────┬────────┘                           │
              │ user confirms "yes"                │
     ┌────────▼────────┐                           │
     │    REVIEW       │───── "new PRD" ───────────┘
     │  PDF ready      │
     │  Edit / Re-gen  │
     └─────────────────┘
```

---

## 4️⃣ Data Flow Diagram
*How data moves and changes inside the system*

```
┌──────────────────────────────┐
│  User's chat messages        │
│  (answers to questions)      │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│  Conversation Transcript     │
│  (plain text, all messages)  │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│  LLM  (OpenRouter / Llama 4) │
│  "structure this into JSON"  │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│  PRD JSON                    │
│  { project_name,             │
│    requirements,             │
│    milestones,               │
│    user_stories ... }        │
└──────┬────────────────┬──────┘
       │                │
┌──────▼──────┐   ┌─────▼──────┐
│  SQLite DB  │   │  ChromaDB  │
│  (versions) │   │  (memory)  │
└─────────────┘   └────────────┘
       │
┌──────▼───────────────────────┐
│  ReportLab PDF Builder       │
│  Renders A4 PRD Document     │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│  output/project_name.pdf     │
│  ✅ User Downloads           │
└──────────────────────────────┘
```
