# Real Estate CRM Automation Agent

**Brand:** Datawebify | [datawebify.com](https://datawebify.com)  
**Live Demo:** [crm.datawebify.com/health](https://crm.datawebify.com/health)  
**Stack:** Python 3.12 · FastAPI · LangGraph · GPT-4o · n8n · GoHighLevel · Supabase · Docker · Railway

---

## What This System Does

A production-grade hybrid automation system that runs real estate wholesaling operations inside GoHighLevel CRM. The system eliminates manual lead handling by combining n8n workflow automation with a GPT-4o AI backend to qualify leads, manage pipeline stages, and trigger follow-up sequences automatically.

Every inbound lead gets contacted within 60 seconds. Every conversation gets analyzed by AI. Every qualified lead gets moved to the right pipeline stage without a human touching it.

---

## Business Outcomes

| Metric | Result |
|---|---|
| Speed to first contact | Under 60 seconds |
| Lead qualification | Automated via GPT-4o 4-pillar scoring |
| Pipeline management | Zero manual stage movement |
| Missed call recovery | Automatic text-back within 30 seconds |
| Nurture sequences | Fully automated SMS and email drip |
| Audit trail | Every event logged to Supabase |

---

## System Architecture
GHL Webhooks → n8n Router → FastAPI Backend → GPT-4o Agent
↓               ↓
Pipeline Management   Supabase Logging
↓
GHL CRM (Contacts, Opportunities, SMS)

**n8n handles:**
- GHL webhook receiving and event routing
- Conversation sync from AI agent to GHL unified inbox
- Pipeline stage movement triggers
- SMS and email nurture sequence scheduling
- Missed call text-back automation
- Speed-to-lead SMS within 60 seconds

**Python/FastAPI handles:**
- GPT-4o lead qualification with 4-pillar data extraction
- LangGraph orchestration for qualification decision logic
- GHL Contact and Opportunity API calls
- Supabase logging and full audit trail
- Webhook signature verification

---

## Lead Qualification: 4-Pillar Scoring

GPT-4o analyzes every conversation transcript and scores the lead across 4 pillars. Each pillar is scored 0-25 for a maximum total of 100.

| Pillar | What It Measures | Max Score |
|---|---|---|
| Motivation | Urgency behind the sale (foreclosure, divorce, relocation) | 25 |
| Timeline | How quickly the seller needs to close | 25 |
| Asking Price | Price relative to estimated ARV | 25 |
| Property Condition | Repair needs and distress level | 25 |

**Score to Pipeline Stage Mapping:**

| Score | Stage | Action |
|---|---|---|
| 75-100 | Hot Lead | Immediate outreach triggered |
| 50-74 | Warm Lead | Follow-up within 24 hours |
| 25-49 | Cold Lead | Added to nurture sequence |
| 0-24 | Dead Lead | Archived |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Workflow Automation | n8n (self-hosted Docker) |
| AI Model | GPT-4o via OpenAI API |
| Agent Framework | LangGraph |
| Backend API | FastAPI + Uvicorn |
| Database | Supabase (PostgreSQL) |
| CRM | GoHighLevel API v2 |
| SMS/Email | GHL native channels |
| Deployment | Docker + Railway |
| Language | Python 3.12 |

---

## n8n Workflows (6 Total)

1. **GHL Webhook Router** — receives all GHL events and routes by type
2. **Conversation Sync** — posts AI agent messages into GHL unified inbox
3. **Pipeline Management** — creates contacts, updates stages, triggers qualification
4. **SMS Nurture Sequences** — hot/warm/cold drip campaigns with Wait nodes
5. **Missed Call Text-Back** — automatic SMS response within 30 seconds
6. **Speed to Lead** — instant SMS on new lead, qualification triggered after 5 minutes

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | System health check |
| POST | `/qualify/lead` | Run GPT-4o qualification on transcript |
| POST | `/webhooks/ghl` | Receive GHL webhook events |
| POST | `/webhooks/conversation-sync` | Sync AI agent messages to GHL inbox |

---

## Project Structure
├── app/
│   ├── agents/
│   │   └── qualification_agent.py   # LangGraph + GPT-4o pipeline
│   ├── api/
│   │   ├── health.py                # Health check endpoint
│   │   ├── qualification.py         # Qualification endpoint
│   │   └── webhooks.py              # GHL webhook receiver
│   ├── clients/
│   │   ├── ghl_client.py            # GoHighLevel API client
│   │   └── supabase_client.py       # Supabase database client
│   ├── models/
│   │   ├── qualification.py         # Pydantic qualification models
│   │   └── webhook.py               # Pydantic webhook models
│   └── utils/
│       ├── config.py                # Environment variable management
│       └── logger.py                # Structured logging via structlog
├── n8n/
│   └── docker-compose.yml           # n8n Docker configuration
├── tests/                           # 42 passing tests
├── Dockerfile                       # Multi-stage production Docker build
├── railway.json                     # Railway deployment configuration
├── requirements.txt
└── .env.example

---

## Deployment

**Live URL:** `https://crm.datawebify.com`  
**Platform:** Railway (auto-deploys on every GitHub push)  
**Container:** Docker multi-stage build on Python 3.12-slim  

---

## Built By

**Muhammad Umair** — Agentic AI Specialist and Enterprise Consultant  
[datawebify.com](https://datawebify.com) · [github.com/umair801](https://github.com/umair801) · [Upwork](https://upwork.com/freelancers/umair801)

> Building production-grade Agentic AI systems for real estate wholesalers, property investors, and GoHighLevel agencies.