# Financial Reports RAG System

A comprehensive full-stack application for intelligent processing, analysis, and querying of financial reports using Retrieval-Augmented Generation (RAG) technology.

## 1. Problem Statement and Business Context

### Business Problem

Financial analysts, investors, and accounting professionals face significant challenges when working with financial reports:

- **Manual Data Extraction**: Extracting key financial indicators (revenue, net income, total debt, EBIT, etc.) from complex PDF tables is error-prone, time-consuming, and resource-intensive.
- **Information Retrieval**: Navigating through lengthy financial documents to find specific information requires extensive manual review.
- **Data Structuring**: Converting unstructured PDF content into organized, queryable formats is labor-intensive.
- **Quick Decision Making**: Lack of automated tools prevents real-time financial analysis and comparison across multiple companies.

### Target Users

- Financial analysts evaluating company performance
- Investment professionals conducting due diligence
- Corporate accountants processing financial statements
- Business intelligence teams aggregating financial data

### Vietnamese Market Focus

The system specifically handles Vietnamese financial reports (Báo cáo tài chính), supporting:
- Vietnamese accounting standards and formats
- Local currency representations (VND with comma/dot separators)
- Specific financial metrics and structures used in Vietnamese financial statements

## 2. Solutions and Objectives

### Core Objectives

1. **Automate Financial Data Extraction**
   - Use advanced LLMs (OpenAI GPT, LandingAI Extract API) to automatically identify and extract financial metrics
   - Support 20+ financial indicators including assets, liabilities, revenue, and profitability ratios
   - Achieve high accuracy with fallback mechanisms for API failures

2. **Enable Natural Language Document Querying**
   - Implement RAG (Retrieval-Augmented Generation) system for intelligent Q&A
   - Support both simple and complex query routing
   - Provide streaming responses for enhanced user experience

3. **Provide Intelligent Financial Analysis**
   - Compute key financial ratios (Debt-to-Assets, ROI, Interest Coverage, etc.)
   - Enable comparative analysis across multiple companies
   - Generate dashboard visualizations of financial metrics

4. **Ensure Data Integrity and Accessibility**
   - Store structured financial data in MongoDB for scalability
   - Implement semantic search via embeddings
   - Support batch processing of multiple financial documents

### Key Features

- 📄 **PDF Processing**: Intelligent parsing of financial PDFs with table preservation
- 🔍 **Semantic Search**: Vector-based similarity search using embeddings
- 🤖 **Dual RAG Strategy**: Simple RAG for factual queries + Agent-based RAG for complex analysis
- 💾 **Data Management**: MongoDB storage for documents, embeddings, and extracted metrics
- 📊 **Financial Metrics**: Automatic extraction of 20+ financial indicators
- 📈 **Ratio Calculation**: Automatic computation of financial ratios
- 💬 **Interactive Chat**: Streaming chatbot interface for document interaction
- 🎯 **Dashboard**: Visualization of financial data and metrics

## 3. System Architecture

### 3.1 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              Frontend (Next.js + React)              │
│  - Document Upload Interface                        │
│  - Chat Interface with Streaming Support            │
│  - Dashboard & Visualizations                       │
│  - Financial Metrics Display                        │
└────────────────────┬────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────▼────────────────────────────────┐
│           FastAPI Backend (Python)                   │
├────────────────────────────────────────────────────┤
│ Routes:                                              │
│ - /api/upload     : Document ingestion              │
│ - /api/chat       : Q&A endpoint                    │
│ - /api/dashboard  : Financial metrics               │
│ - /api/statistics : Analytics data                  │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──┐  ┌─────▼────┐  ┌───▼────────┐
│ MongoDB  │  │  LLM     │  │ LandingAI  │
│ Storage  │  │ Services │  │ Parser API │
│          │  │ (OpenAI) │  │            │
└──────────┘  └──────────┘  └────────────┘
```

### 3.2 Processing Pipeline

```
PDF Upload
    ↓
[1. PDF Parsing] → LandingAI Extract → Parse JSON
    ↓
[2. Chunking] → Create chunks with metadata
    ↓
[3. Storage] → MongoDB (chunks collection)
    ↓
[4. Embedding Generation] → OpenAI/LandingAI embeddings
    ↓
[5. Embedding Storage] → MongoDB (embeddings collection)
    ↓
[6. Financial Data Extraction] → FinancialStatementSchema
    ↓
[7. Ratio Computation] → Calculate financial ratios
    ↓
[8. Final Storage] → MongoDB (variables collection)
    ↓
Complete: Document ready for querying
```

### 3.3 Query Processing

```
User Query
    ↓
[Question Classification] → Analyze complexity
    ↓
[Routing Decision]
    ├─→ Simple Query → Simple RAG → Semantic Search
    │       ↓
    │   [Retrieve Chunks] → [Generate Answer] → Stream Response
    │
    └─→ Complex Query → Agent RAG → Multi-step Analysis
            ↓
        [Search] → [Analyze] → [Verify] → [Synthesize] → Stream Response
    ↓
Return Answer with Metadata
```

### 3.4 Technology Stack

#### Backend
- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn 0.24.0
- **Database**: MongoDB 4.6.1
- **LLM**: OpenAI API (GPT-4/4-mini)
- **Document Processing**: 
  - LandingAI (primary PDF parser)
  - PyMuPDF (14.0.2)
- **Data Processing**: Pandas, NumPy, PyArrow
- **Vectorization**: OpenAI Embeddings API

#### Frontend
- **Framework**: Next.js 16.1.2
- **Language**: TypeScript
- **UI Library**: React 19.2.3
- **UI Components**: Radix UI
- **Styling**: Tailwind CSS
- **Charts**: Recharts 3.8.0
- **Markdown**: React-markdown with rehype-raw

#### Infrastructure
- **Dev Server**: Node.js LTS
- **Python Runtime**: 3.10+
- **Port Configuration**:
  - Frontend: 3333
  - Backend: 2602

### 3.5 Module Structure

```
project/
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── upload.py      # Document upload endpoint
│   │   │   ├── chat.py        # Q&A endpoint
│   │   │   ├── chat_stream.py # SSE streaming responses
│   │   │   ├── dashboard.py   # Metrics visualization
│   │   │   └── statistics.py  # Analytics
│   │   ├── schemas/           # Pydantic models
│   │   └── main.py            # FastAPI app setup
│   ├── implementations/
│   │   ├── financial_extractor.py   # LLM-based extraction
│   │   ├── answers.py               # Q&A logic (hybrid RAG)
│   │   ├── mongodb_manager.py       # DB operations
│   │   ├── embedding_processor.py   # Embeddings
│   │   ├── question_classifier.py   # Query routing
│   │   ├── agent_integration.py     # Agent tools
│   │   └── invest.py                # Processing pipeline
│   ├── parser/
│   │   ├── landingai_parse.py       # LandingAI integration
│   │   └── pdf_parser.py            # PDF chunking
│   ├── pre_processing/
│   │   └── pdf_preprocessing.py     # Pre-processing utilities
│   └── data/                        # Data storage
│
├── frontend/
│   ├── src/
│   │   ├── app/                  # Next.js pages
│   │   ├── components/           # React components
│   │   ├── hooks/                # Custom React hooks
│   │   ├── lib/                  # Utility functions
│   │   ├── stores/               # State management
│   │   └── types/                # TypeScript definitions
│   ├── public/                   # Static assets
│   └── components.json           # Tailwind UI config
│
├── agents/
│   ├── agent.py             # Base agent class
│   ├── deals.py             # Deal processing
│   └── scanner_agent.py     # Financial analysis agent
│
├── parse_results/           # Extracted parse outputs
├── data/                    # Sample financial data
└── requirements.txt         # Python dependencies
```

### 3.6 Data Schema

#### Financial Statement Schema
```json
{
  "don_vi_tien_te": "VND",
  "nam_bao_cao": 2024,
  "ten_cong_ty": "Company Name",
  "tai_san_tong_cong": 1000000000,
  "tai_san_luu_dong": 500000000,
  "tai_san_co_dinh": 500000000,
  "no_phai_tra_tong_cong": 600000000,
  "no_ngan_han": 200000000,
  "no_dai_han": 400000000,
  "von_chu_so_huu": 400000000,
  "doanh_thu_ban_hang": 900000000,
  "chi_phi_hoat_dong": 200000000,
  "loi_nhuan_truoc_thue": 100000000,
  "chi_phi_lai_vay": 20000000,
  "tien_lai_nhan_duoc": 5000000
}
```

#### Chunk Structure
```json
{
  "_id": "ObjectId",
  "document_id": "file_hash",
  "chunk_number": 1,
  "content": "Chunk text...",
  "page_number": 1,
  "metadata": {
    "company": "Company Name",
    "year": 2024,
    "type": "financial_report"
  },
  "embedding": [0.123, 0.456, ...],
  "created_at": "2024-01-01T00:00:00Z"
}
```

## 4. Installation Guide

### Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher
- **npm/pnpm**: Latest version
- **MongoDB**: 4.6+ (local or cloud)
- **Environment**: Windows/macOS/Linux

### Step 1: Setup Environment Variables

Create a `.env` file in the project root:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# LandingAI Configuration (optional, for document parsing)
LANDINGAI_API_KEY=your_landingai_api_key

# MongoDB Configuration
MONGODB_CONNECTION=mongodb+srv://user:password@cluster.mongodb.net/database_name

# Langfuse (optional, for monitoring)
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key

# Server Configuration
BACKEND_PORT=2602
FRONTEND_PORT=3333
```

### Step 2: Backend Setup

```bash
# 1. Navigate to project root
cd "e:\TaiLieu\Master's\Semeter2\MoHinhTT_and_UngDung\project"

# 2. Create virtual environment (Windows)
python -m venv venv
.\venv\Scripts\activate

# 3. Or for macOS/Linux
python3 -m venv venv
source venv/bin/activate

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Verify dependencies
pip list
```

### Step 3: Frontend Setup

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies (using pnpm - recommended)
pnpm install

# Or using npm
npm install

# 3. Verify installation
npm list next react
```

### Step 4: Database Setup

```bash
# 1. Create MongoDB database
# - Create cluster in MongoDB Atlas OR
# - Run local MongoDB instance

# 2. Create required collections
# - documents
# - chunks
# - embeddings
# - variables
# - ratios

# 3. Create indexes (recommended for performance)
# - Index on chunks: document_id, page_number
# - Index on embeddings: document_id
# - Index on variables: company_name, year
```

### Step 5: Running the Application

#### Terminal 1 - Backend Server

```bash
# Windows
.\venv\Scripts\activate
uvicorn backend.api.main:app --reload --port 2602

# macOS/Linux
source venv/bin/activate
uvicorn backend.api.main:app --reload --port 2602

# Access API documentation at http://localhost:2602/docs
```

#### Terminal 2 - Frontend Server

```bash
# Windows
cd frontend
pnpm dev
# Or: npm run dev

# Access application at http://localhost:3333
```

### Step 6: Verify Installation

1. **Backend Health Check**
   ```bash
   curl http://localhost:2602/api/status
   ```

2. **Frontend Access**
   - Open browser: http://localhost:3333
   - Should see upload interface

3. **API Documentation**
   - Browse to: http://localhost:2602/docs
   - Test endpoints interactively

### Troubleshooting

#### Issue: Python Module Not Found
```bash
# Ensure virtual environment is activated
# Add PYTHONPATH to system if needed
set PYTHONPATH=%PYTHONPATH%;e:\TaiLieu\Master's\Semeter2\MoHinhTT_and_UngDung\project
```

#### Issue: MongoDB Connection Failed
```bash
# Check connection string in .env
# Verify MongoDB is running
# Check authentication credentials
# For local MongoDB: mongodb://localhost:27017/financial_db
```

#### Issue: Port Already in Use
```bash
# Change port in .env or use different ports
# Check what's using the port and terminate if needed
netstat -ano | findstr :2602  # Windows
lsof -i :2602  # macOS/Linux
```

#### Issue: API Key Errors
```bash
# Verify .env file exists in project root
# Check API keys are correct and have appropriate scopes
# Ensure .env is not committed to git
```

## 5. Usage Guide

### 5.1 Uploading Financial Documents

1. Navigate to http://localhost:3333
2. Use the document upload interface
3. Select PDF file from computer
4. Wait for processing (parsing, extraction, embedding generation)
5. View document in dashboard once complete

### 5.2 Querying Documents

1. After upload, access the chat interface
2. Type your question in natural language
3. Examples:
   - "What is the total assets of [Company X]?"
   - "Calculate the debt-to-asset ratio"
   - "Compare revenue across companies"
4. System will:
   - Classify question complexity
   - Route to appropriate strategy
   - Retrieve relevant sections
   - Generate informed answer

### 5.3 Viewing Financial Metrics

1. Access Dashboard tab
2. View extracted financial indicators
3. Analyze ratios and trends
4. Export data as needed

## 6. API Endpoints Reference

### Document Upload
```
POST /api/upload
Content-Type: multipart/form-data

Request:
{
  "file": <PDF file>
}

Response:
{
  "document_id": "hash",
  "status": "success",
  "message": "Document processed successfully"
}
```

### Chat Query
```
POST /api/chat-stream
Content-Type: application/json

Request:
{
  "query": "What is total revenue?",
  "history": []
}

Response: Server-Sent Events streaming
```

### Financial Metrics
```
GET /api/dashboard?company=HPG&year=2024

Response:
{
  "company": "HPG",
  "year": 2024,
  "metrics": {
    "total_assets": 1000000000,
    "net_income": 100000000,
    ...
  }
}
```

## 7. Development Notes

### Code Quality

- Use type hints throughout (Pydantic models)
- Follow PEP 8 style guide
- Add docstrings to functions
- Use pytest for testing

### Testing

```bash
# Run backend tests
pytest tests/

# Run specific test
pytest tests/test_pipeline.py -v

# Test API endpoints
pytest tests/test_extract.py
```

### Monitoring and Logging

- Backend logs via stdout
- Monitor LLM calls via Langfuse (if enabled)
- Check MongoDB for data integrity
- Review API response times in browser DevTools

## 8. Performance Optimization

### Database Optimization
- Create indexes on frequently queried fields
- Use batch operations for multiple documents
- Implement pagination for large result sets

### LLM Optimization
- Cache embeddings to avoid recomputation
- Use smaller models for simple queries (gpt-4o-mini)
- Implement rate limiting to prevent API exhaustion

### Frontend Optimization
- Enable Next.js caching
- Implement client-side caching for API responses
- Use lazy loading for data visualizations

## 9. License and Attribution

This project was developed as part of the CS311 course (Software Engineering) at Ho Chi Minh City University of Technology.

## 10. Support and Contact

For issues or questions:
- Check the API documentation at `/docs`
- Review existing issues in the repository
- Consult the project report: `Nhom_7_Final_Report_CS311.docx`

---

**Last Updated**: March 2024
**Version**: 1.0.0
