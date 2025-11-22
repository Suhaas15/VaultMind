# VaultMind Pro - Project Overview

## 🎯 What is VaultMind Pro?

**VaultMind Pro** is an intelligent medical record processing system that combines **privacy-first data protection** with **AI-powered clinical analysis**. It automatically processes patient medical documents, protects sensitive information (PII), and generates AI-powered clinical summaries while continuously learning and improving from doctor feedback.

### Core Value Proposition
- **🔒 Privacy-First**: Patient PII (names, SSNs, DOBs) is tokenized and stored securely in Skyflow Vault
- **🤖 AI-Powered**: Uses Anthropic's Claude AI to generate professional clinical summaries
- **📈 Self-Learning**: Continuously improves by learning from doctor feedback and optimizing prompts
- **⚡ Real-Time**: Live updates via WebSocket connections for instant patient processing status

---

## 🏗️ System Architecture

```
┌─────────────────┐
│   Frontend      │  React + TypeScript + Tailwind CSS
│   (React App)   │  Real-time UI with Socket.IO
└────────┬────────┘
         │ HTTP/WebSocket
         │
┌────────▼─────────────────────────────────────┐
│         Backend API (FastAPI)               │
│  ┌──────────────────────────────────────┐  │
│  │  API Routes                           │  │
│  │  - /api/patients (CRUD operations)    │  │
│  │  - /api/feedback (Doctor feedback)    │  │
│  │  - /api/webhooks (External events)    │  │
│  └──────────────────────────────────────┘  │
│  ┌──────────────────────────────────────┐  │
│  │  Services Layer                       │  │
│  │  - AgentService (AI Processing)      │  │
│  │  - SkyflowService (PII Protection)   │  │
│  │  - SanityService (Data Storage)        │  │
│  │  - PromptService (AI Optimization)    │  │
│  │  - MetricsService (Performance)       │  │
│  └──────────────────────────────────────┘  │
└────────┬─────────────────────────────────────┘
         │
    ┌────┴────┬──────────────┬──────────────┐
    │         │              │              │
┌───▼───┐ ┌──▼──────┐  ┌────▼─────┐  ┌───▼────┐
│Skyflow│ │ Sanity  │  │Anthropic │  │ Redis  │
│ Vault │ │  CMS    │  │  Claude  │  │(Celery)│
│       │ │         │  │    AI    │  │        │
└───────┘ └─────────┘  └──────────┘  └────────┘
```

---

## 🔧 Component Breakdown

### 1. **Frontend (React + TypeScript)**

**Location**: `frontend/`

**What it does**:
- Provides a modern, responsive web interface for doctors and medical staff
- Displays patient records with encrypted PII (tokens)
- Allows document uploads (TXT, PDF, DOCX)
- Shows real-time processing status via WebSocket
- Enables doctors to provide feedback on AI summaries

**Key Components**:
- `Dashboard.tsx`: Main interface showing patient list and statistics
- `PatientList.tsx`: Scrollable list of all patients
- `TokenViewer.tsx`: Displays patient details with decrypt functionality
- `DocumentUpload.tsx`: Drag-and-drop file upload interface
- `FeedbackDialog.tsx`: Allows doctors to rate AI summaries

**Technologies**:
- React 19.2
- TypeScript
- Tailwind CSS
- Socket.IO Client (real-time updates)
- Vite (build tool)

---

### 2. **Backend API (FastAPI)**

**Location**: `backend/`

**What it does**:
- RESTful API server handling all backend operations
- WebSocket server for real-time updates
- Routes HTTP requests to appropriate services
- Manages CORS and authentication

**Key Endpoints**:
- `POST /api/patients/upload-document`: Upload medical documents
- `GET /api/patients`: List all patients
- `POST /api/patients/{id}/decrypt`: Decrypt PII tokens (with auth)
- `POST /api/feedback`: Submit doctor feedback
- `GET /api/feedback/stats`: Get performance metrics

**Technologies**:
- FastAPI (Python web framework)
- Socket.IO (WebSocket support)
- Uvicorn (ASGI server)

---

### 3. **Skyflow Service** 🔒

**Location**: `backend/services/skyflow_service.py`

**What it does**:
- **PII Protection**: Tokenizes sensitive patient data (names, SSNs, DOBs)
- **PII Detection**: Automatically finds PII in unstructured documents
- **Detokenization**: Securely retrieves original PII when needed (with proper auth)
- **Vault Management**: Stores encrypted PII in Skyflow's secure vault

**Key Functions**:
- `tokenize()`: Converts PII → secure tokens
- `detokenize()`: Converts tokens → original PII (requires auth)
- `detect_pii()`: Finds PII in text using pattern matching or MCP server
- `invoke_function()`: Calls Skyflow Functions for vault-confined AI processing

**How it works**:
1. When a document is uploaded, Skyflow detects PII (names, SSNs, etc.)
2. PII is sent to Skyflow Vault and replaced with tokens (e.g., `sky_n_abc123`)
3. Only tokens are stored in the database
4. Original PII never leaves Skyflow's secure vault

**Example**:
```
Input:  "Patient Name: John Smith, SSN: 123-45-6789"
Output: "Patient Name: sky_n_abc123, SSN: sky_s_def456"
```

---

### 4. **Sanity Service** 📊

**Location**: `backend/services/sanity_service.py`

**What it does**:
- **Data Storage**: Stores patient records in Sanity CMS (headless CMS)
- **Query Interface**: Provides flexible querying of patient data
- **Schema Management**: Manages patient, feedback, and prompt template schemas

**What gets stored**:
- Patient tokens (not actual PII)
- Medical condition, department, priority
- Lab results (non-PII data)
- AI summaries
- Processing metadata (cost, tokens used, duration)
- Doctor feedback

**Why Sanity?**:
- Headless CMS allows flexible data modeling
- Real-time updates
- Easy to query and filter
- Good for structured medical data

**Schema Types**:
- `patient`: Patient records with tokens
- `feedback`: Doctor feedback on AI summaries
- `prompt_template`: AI prompt versions for A/B testing
- `performance_metrics`: System performance tracking

---

### 5. **Agent Service** 🤖

**Location**: `backend/services/agent_service.py`

**What it does**:
- **AI Processing**: Orchestrates AI clinical summary generation
- **Multi-Strategy**: Tries Skyflow Functions first, falls back to direct Claude API
- **Smart Fallback**: Detokenizes data if needed for AI processing
- **Document Processing**: Uses original document text when available

**Processing Flow**:
1. Receives patient data (with tokens)
2. Selects optimal prompt template (based on performance)
3. **Primary**: Tries Skyflow Function (vault-confined AI processing)
4. **Fallback**: Calls Anthropic Claude API directly
   - Uses original document text if available
   - Or detokenizes patient name for context
5. Generates clinical summary
6. Stores results in Sanity
7. Emits real-time update via WebSocket

**AI Models Used**:
- Claude 3.5 Sonnet (default)
- Configurable via prompt templates

**Output**:
- Professional clinical summary
- Processing metrics (tokens, cost, duration)
- Model version used

---

### 6. **Prompt Service** 📝

**Location**: `backend/services/prompt_service.py`

**What it does**:
- **Prompt Management**: Manages multiple prompt template versions
- **A/B Testing**: Tests different prompts to find best performers
- **Self-Learning**: Automatically selects best-performing prompts based on feedback
- **Optimization**: Tracks which prompts get best ratings from doctors

**Prompt Versions**:
- `v1.0`: Original baseline prompt
- `v2.0`: Enhanced with structured analysis
- `v3.0`: SOAP format (Subjective, Objective, Assessment, Plan)
- `v4.0`: XML-structured with few-shot examples

**Selection Strategy**:
- `best_performing`: Uses highest-rated prompt (default)
- `ab_test`: Randomly selects for A/B testing
- `latest`: Uses newest version

**How it learns**:
1. Doctor rates AI summary (1-5 stars)
2. System tracks which prompt version was used
3. Calculates average rating per prompt
4. Automatically switches to best-performing prompt

---

### 7. **Metrics Service** 📈

**Location**: `backend/services/metrics_service.py`

**What it does**:
- **Feedback Tracking**: Stores doctor feedback on AI summaries
- **Performance Analysis**: Calculates success rates, average ratings
- **Trend Analysis**: Tracks improvement over time
- **Optimization Recommendations**: Suggests improvements based on data

**Metrics Tracked**:
- Average accuracy rating (1-5 scale)
- Summary quality distribution
- Processing speed trends
- Cost efficiency improvements
- Prompt version performance

**Use Cases**:
- Dashboard statistics
- System improvement tracking
- Cost optimization insights

---

### 8. **Celery Workers** ⚙️

**Location**: `backend/workers/tasks.py`

**What it does**:
- **Background Processing**: Handles AI processing asynchronously
- **Queue Management**: Uses Redis to queue patient processing tasks
- **Scalability**: Allows multiple workers to process patients in parallel

**Why Celery?**:
- AI processing can take 5-30 seconds
- Prevents blocking the API
- Allows horizontal scaling
- Falls back to synchronous processing if Redis unavailable

**Task Flow**:
1. Patient uploaded → Task queued
2. Celery worker picks up task
3. Processes patient with AI
4. Updates Sanity
5. Emits WebSocket event

---

## 🔄 Complete Data Flow

### Document Upload Flow

```
1. Doctor uploads document (TXT/PDF/DOCX)
   ↓
2. Backend receives file
   ↓
3. Skyflow detects PII (name, SSN, DOB)
   ↓
4. PII tokenized → stored in Skyflow Vault
   ↓
5. Patient record created in Sanity (with tokens only)
   ↓
6. Processing task queued (Celery) or processed immediately
   ↓
7. Agent Service:
   a. Selects best prompt template
   b. Tries Skyflow Function (vault-confined)
   c. Falls back to Claude API if needed
   ↓
8. AI generates clinical summary
   ↓
9. Summary stored in Sanity
   ↓
10. WebSocket event → Frontend updates in real-time
```

### Decryption Flow (Viewing PII)

```
1. Doctor clicks "Decrypt PII" button
   ↓
2. Frontend calls /api/patients/{id}/decrypt
   ↓
3. Backend retrieves tokens from Sanity
   ↓
4. Skyflow detokenizes (requires auth)
   ↓
5. Original PII returned to frontend
   ↓
6. Displayed in red-highlighted box (visual indicator)
```

### Feedback Loop (Self-Learning)

```
1. Doctor reviews AI summary
   ↓
2. Doctor rates summary (1-5 stars) + optional corrections
   ↓
3. Feedback stored in Sanity
   ↓
4. Metrics Service updates prompt performance
   ↓
5. Prompt Service recalculates best performer
   ↓
6. Future patients use improved prompt automatically
```

---

## 🔐 Security Architecture

### PII Protection Strategy

1. **Tokenization**: All PII replaced with tokens before storage
2. **Vault Isolation**: Original PII only exists in Skyflow Vault
3. **Access Control**: Detokenization requires proper authentication
4. **Audit Trail**: All access logged (via Skyflow)

### Data Storage Layers

```
┌─────────────────────────────────────┐
│  Sanity CMS (Public Database)      │
│  - Stores: Tokens only             │
│  - No PII                           │
│  - Queryable, searchable            │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Skyflow Vault (Secure Vault)       │
│  - Stores: Original PII            │
│  - Encrypted at rest                │
│  - Access-controlled                │
│  - Compliant (HIPAA-ready)          │
└─────────────────────────────────────┘
```

---

## 🚀 Key Features

### 1. **Automatic PII Detection**
- Finds names, SSNs, DOBs in any document format
- No manual field mapping required
- Uses pattern matching + optional MCP server

### 2. **Intelligent AI Processing**
- Multiple prompt strategies
- Automatic optimization
- Fallback mechanisms for reliability

### 3. **Real-Time Updates**
- WebSocket connections
- Live processing status
- Instant UI updates

### 4. **Self-Learning System**
- Learns from doctor feedback
- Automatically improves prompts
- Tracks performance metrics

### 5. **Cost Optimization**
- Tracks token usage
- Calculates processing costs
- Optimizes prompts for efficiency

---

## 📦 Technology Stack

### Frontend
- **React 19.2** -** UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Vite** - Build tool
- **Socket.IO Client** - Real-time updates

### Backend
- **FastAPI** - Web framework
- **Python 3.x** - Programming language
- **Socket.IO** - WebSocket server
- **Celery** - Task queue
- **Redis** - Message broker

### External Services
- **Skyflow** - PII vault & tokenization
- **Sanity CMS** - Data storage
- **Anthropic Claude** - AI processing

### Infrastructure
- **Uvicorn** - ASGI server
- **Redis** - Celery broker
- **Docker** (optional) - Containerization

---

## 🎯 Use Cases

### 1. **Hospital Admins**
- Upload patient documents in bulk
- Monitor processing status
- View system performance metrics

### 2. **Doctors**
- Review AI-generated clinical summaries
- Provide feedback to improve system
- Access patient records securely

### 3. **Medical Staff**
- Upload individual patient documents
- View patient records (with encrypted PII)
- Track processing status

---

## 🔮 Future Enhancements

- **Multi-language Support**: Process documents in multiple languages
- **Advanced PII Detection**: ML-based detection improvements
- **Custom Prompt Templates**: Allow doctors to create custom prompts
- **Batch Processing**: Process multiple documents simultaneously
- **Export Features**: PDF/CSV export of patient records
- **Analytics Dashboard**: Advanced performance analytics

---

## 📝 Configuration

All configuration is done via `.env` file in project root:

```env
# Skyflow (PII Protection)
SKYFLOW_VAULT_ID=your_vault_id
SKYFLOW_VAULT_URL=https://your-vault.skyflowapis.com
SKYFLOW_BEARER_TOKEN=your_token

# Anthropic (AI Processing)
ANTHROPIC_API_KEY=your_api_key

# Sanity (Data Storage)
SANITY_PROJECT_ID=your_project_id
SANITY_API_TOKEN=your_token

# Redis (Optional - for background processing)
REDIS_URL=redis://localhost:6379/0
```

---

## 🏁 Getting Started

1. **Install Dependencies**
   ```bash
   # Backend
   pip install -r backend/requirements.txt
   
   # Frontend
   cd frontend && npm install
   ```

2. **Configure Environment**
   - Copy `.env.example` to `.env`
   - Fill in all API keys

3. **Start Services**
   ```bash
   ./run.sh
   ```

4. **Access Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000

---

## 📊 System Metrics

The system tracks:
- **Processing Speed**: Average time to generate summaries
- **AI Accuracy**: Average doctor ratings (1-5)
- **Cost Efficiency**: Token usage and cost per patient
- **Improvement Trends**: Performance over time

---

## 🤝 Contributing

This is a production-ready system designed for healthcare environments. All contributions should maintain:
- HIPAA compliance considerations
- Security best practices
- Performance optimization
- Code quality standards

---

## 📄 License

[Add license information here]

---

**Built with ❤️ for secure, intelligent medical record processing**

