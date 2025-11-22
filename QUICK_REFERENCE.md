# VaultMind Pro - Quick Reference Guide

## 🎯 What Does This Project Do?

**VaultMind Pro** = **Secure Medical Document Processing** + **AI Clinical Summaries** + **Self-Learning System**

Think of it as a smart assistant that:
1. Takes patient medical documents
2. Protects sensitive info (names, SSNs) by encrypting them
3. Uses AI to generate clinical summaries
4. Learns from doctor feedback to get better over time

---

## 🧩 What Each Component Does

### 🔵 **Frontend (React App)**
**Role**: The user interface doctors see
- Shows patient list
- Upload documents
- View AI summaries
- Give feedback

**Tech**: React, TypeScript, Tailwind CSS

---

### 🟢 **Backend API (FastAPI)**
**Role**: The brain that coordinates everything
- Receives requests from frontend
- Routes to appropriate services
- Sends real-time updates

**Tech**: Python, FastAPI, Socket.IO

---

### 🔴 **Skyflow Service** 🔒
**Role**: The security guard for patient data
- **Tokenizes**: Converts "John Smith" → `sky_n_abc123`
- **Detects**: Finds PII in documents automatically
- **Protects**: Stores real PII in secure vault
- **Decrypts**: Shows real data when authorized

**What it protects**:
- Patient names
- Social Security Numbers (SSN)
- Dates of birth (DOB)
- Addresses

**Key Point**: Original PII never stored in main database, only tokens!

---

### 🟡 **Sanity Service** 📊
**Role**: The database that stores everything (except real PII)
- Stores patient records (with tokens, not real names)
- Stores AI summaries
- Stores doctor feedback
- Stores performance metrics

**What gets stored**:
- ✅ Tokens (encrypted identifiers)
- ✅ Medical conditions
- ✅ Lab results
- ✅ AI summaries
- ❌ NOT real patient names/SSNs

**Tech**: Sanity CMS (headless database)

---

### 🟣 **Agent Service** 🤖
**Role**: The AI processor that generates clinical summaries
- Takes patient data
- Selects best AI prompt
- Calls Claude AI (Anthropic)
- Generates professional clinical summary
- Stores results

**AI Models**: Claude 3.5 Sonnet

**Two Strategies**:
1. **Primary**: Skyflow Function (processes inside secure vault)
2. **Fallback**: Direct Claude API call

---

### 🟠 **Prompt Service** 📝
**Role**: The optimizer that makes AI better
- Manages different prompt versions
- Tracks which prompts doctors like best
- Automatically uses best-performing prompts
- Enables A/B testing

**How it learns**:
- Doctor rates summary: ⭐⭐⭐⭐⭐
- System notes: "Prompt v4.0 got 5 stars"
- System switches to v4.0 for future patients
- Gets better over time automatically!

---

### ⚪ **Metrics Service** 📈
**Role**: The analyst that tracks performance
- Collects doctor feedback
- Calculates average ratings
- Tracks improvement trends
- Provides insights

**Metrics**:
- Average accuracy (1-5 stars)
- Processing speed
- Cost per patient
- Improvement over time

---

### ⚫ **Celery Workers** ⚙️
**Role**: Background processors
- Handles AI processing in background
- Prevents API from blocking
- Allows parallel processing
- Uses Redis queue

**Why needed**: AI processing takes 5-30 seconds, can't block the API!

---

## 🔄 Simple Flow Example

### When Doctor Uploads a Document:

```
1. Doctor uploads "patient_report.txt"
   ↓
2. Skyflow finds: "John Smith, SSN: 123-45-6789"
   ↓
3. Skyflow encrypts: "sky_n_abc123, SSN: sky_s_def456"
   ↓
4. Sanity stores: Patient record with tokens
   ↓
5. Agent Service: Calls Claude AI
   ↓
6. Claude generates: "Clinical Summary: Patient presents with..."
   ↓
7. Summary stored in Sanity
   ↓
8. Frontend updates: Shows new patient with summary
```

### When Doctor Views Patient:

```
1. Doctor clicks patient
   ↓
2. Sees: "sky_n_abc123" (encrypted name)
   ↓
3. Clicks "Decrypt PII"
   ↓
4. Backend calls Skyflow: "Decrypt this token"
   ↓
5. Skyflow returns: "John Smith"
   ↓
6. Frontend shows: "John Smith" (highlighted in red)
```

---

## 🎨 Visual Architecture

```
┌─────────────────────────────────────────┐
│         DOCTOR (User)                    │
│    Uploads documents, views summaries   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      FRONTEND (React App)               │
│  - Dashboard                            │
│  - Patient List                         │
│  - Document Upload                      │
└──────────────┬──────────────────────────┘
               │ HTTP/WebSocket
               ▼
┌─────────────────────────────────────────┐
│      BACKEND API (FastAPI)              │
│  Coordinates all services               │
└───┬──────┬──────┬──────┬──────┬────────┘
    │      │      │      │      │
    ▼      ▼      ▼      ▼      ▼
┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
│Sky- │ │Sani-│ │Agent│ │Promp│ │Metr-│
│flow │ │ty   │ │Serv │ │t    │ │ics  │
│     │ │     │ │     │ │     │ │     │
└─────┘ └─────┘ └─────┘ └─────┘ └─────┘
  │       │       │
  │       │       └──► Anthropic Claude AI
  │       │
  │       └──► Sanity CMS Database
  │
  └──► Skyflow Vault (Secure PII Storage)
```

---

## 🔐 Security Model

### Two-Layer Protection:

**Layer 1: Tokenization**
- Real PII → Encrypted tokens
- Tokens stored in main database
- Example: "John Smith" → `sky_n_abc123`

**Layer 2: Vault Storage**
- Real PII stored in Skyflow Vault
- Encrypted at rest
- Access-controlled
- Compliant with healthcare regulations

**Result**: Even if database is compromised, attackers only get tokens, not real data!

---

## 📊 Key Metrics Tracked

| Metric | What It Means |
|--------|---------------|
| **AI Accuracy** | Average doctor rating (1-5 stars) |
| **Processing Speed** | Time to generate summary |
| **Cost Efficiency** | Cost per patient processed |
| **Improvement Trend** | Getting better over time? |

---

## 🚀 Quick Start

1. **Setup**:
   ```bash
   pip install -r backend/requirements.txt
   cd frontend && npm install
   ```

2. **Configure**:
   - Edit `.env` file
   - Add API keys (Skyflow, Anthropic, Sanity)

3. **Run**:
   ```bash
   ./run.sh
   ```

4. **Access**:
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000

---

## 💡 Key Concepts

### Tokenization
**What**: Converting sensitive data to meaningless tokens
**Why**: Protects PII while allowing system to work
**Example**: "John Smith" → `sky_n_abc123`

### Self-Learning
**What**: System improves automatically from feedback
**How**: Tracks which prompts get best ratings, uses them
**Result**: Gets better over time without manual updates

### Vault-Confined Processing
**What**: AI processes data inside secure vault
**Why**: PII never leaves secure environment
**Fallback**: Direct API call if vault processing unavailable

---

## 🎯 Use Cases

1. **Hospital**: Process incoming patient documents
2. **Clinic**: Generate quick clinical summaries
3. **Research**: Analyze patient data (anonymized)
4. **Compliance**: Maintain HIPAA-compliant records

---

## 🔧 Troubleshooting

| Problem | Solution |
|--------|----------|
| No AI summaries | Check `ANTHROPIC_API_KEY` in `.env` |
| Can't decrypt PII | Check `SKYFLOW_BEARER_TOKEN` |
| No patients showing | Check `SANITY_API_TOKEN` |
| Processing slow | Check Redis/Celery running |

---

## 📚 File Structure

```
VaultMind/
├── frontend/          # React app
├── backend/          # FastAPI server
│   ├── api/          # API routes
│   ├── services/     # Core services
│   └── workers/      # Background tasks
├── vaultmind-hack/   # Sanity CMS config
└── .env              # Configuration
```

---

**Remember**: This system protects patient privacy while providing intelligent AI assistance! 🔒🤖

