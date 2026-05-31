# Docs RAG AI

A production-ready **Retrieval-Augmented Generation (RAG)** application with a **FastAPI** backend and **Next.js** frontend. Upload documents, index them into a FAISS vector store, and ask questions answered by OpenAI using retrieved context.

---

## Repository Structure

```text
docs-rag-ai/
│
├── frontend/                     # Next.js 14+ (TypeScript, App Router)
│   ├── app/
│   │   ├── globals.css           # Design system & styles
│   │   ├── layout.tsx            # Root layout with SEO metadata
│   │   └── page.tsx              # Main page (Document + Chat panels)
│   ├── components/
│   │   ├── Header.tsx            # App header with health indicator
│   │   ├── DocumentPanel.tsx     # Drag-and-drop upload & document list
│   │   └── ChatPanel.tsx         # Chat interface with source citations
│   ├── lib/
│   │   ├── api.ts                # API client (reads NEXT_PUBLIC_API_URL)
│   │   └── types.ts              # TypeScript interfaces
│   ├── public/
│   ├── .env.local.example        # Frontend env template
│   └── package.json
│
├── backend/                      # FastAPI + LangChain + FAISS
│   ├── app/
│   │   ├── main.py               # FastAPI entry point
│   │   ├── core/
│   │   │   └── config.py         # Settings from environment variables
│   │   ├── api/
│   │   │   ├── routes.py         # API endpoints
│   │   │   └── schemas.py        # Pydantic request/response models
│   │   └── services/
│   │       ├── document_processor.py  # File loading & chunking
│   │       ├── vector_store.py        # FAISS index management
│   │       └── rag_chain.py           # RAG pipeline (retrieve + generate)
│   ├── data/
│   │   └── uploads/              # Uploaded files (gitignored)
│   ├── vectorstore/              # FAISS index files (gitignored)
│   ├── .env.example              # Backend env template
│   ├── pyproject.toml            # Python dependencies (uv)
│   └── requirements.txt          # Python dependencies (pip)
│
├── .gitignore
├── docker-compose.yml            # Optional Docker setup
└── README.md
```

---

## Environment Setup

### Backend `.env`

Copy the example file and fill in your OpenAI API key:

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env`:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4.1-mini

FAISS_INDEX_PATH=vectorstore/faiss_index
UPLOAD_DIR=data/uploads

FRONTEND_URL=http://localhost:3000
```

| Variable           | Description                      | Required |
| ------------------ | -------------------------------- | -------- |
| `OPENAI_API_KEY`   | Your OpenAI API key              | ✅ Yes   |
| `OPENAI_MODEL`     | OpenAI model name                | No       |
| `FAISS_INDEX_PATH`  | Path to FAISS index directory    | No       |
| `UPLOAD_DIR`       | Path to uploaded files directory | No       |
| `FRONTEND_URL`     | Frontend URL for CORS            | No       |

### Frontend `.env.local`

```bash
cd frontend
cp .env.local.example .env.local
```

Edit `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

| Variable               | Description        | Required |
| ---------------------- | ------------------ | -------- |
| `NEXT_PUBLIC_API_URL`  | Backend API URL    | ✅ Yes   |

---

## Backend Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Install & Run

**Using uv (recommended):**

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

**Using pip:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend will start at **http://localhost:8000**.

### API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### API Endpoints

| Method   | Endpoint                       | Description                     |
| -------- | ------------------------------ | ------------------------------- |
| `POST`   | `/api/upload`                  | Upload and index a document     |
| `POST`   | `/api/query`                   | Ask a question                  |
| `GET`    | `/api/documents`               | List uploaded documents         |
| `DELETE` | `/api/documents/{filename}`    | Delete a document               |
| `GET`    | `/api/health`                  | Health check                    |

---

## Frontend Setup

### Prerequisites

- Node.js 18+
- npm

### Install & Run

```bash
cd frontend
npm install
npm run dev
```

The frontend will start at **http://localhost:3000**.

---

## Running the Full Application

1. **Start the backend** (Terminal 1):
   ```bash
   cd backend
   uv run uvicorn app.main:app --reload
   ```

2. **Start the frontend** (Terminal 2):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open your browser** at http://localhost:3000

4. **Upload documents** using the sidebar panel (PDF, TXT, MD, or DOCX)

5. **Ask questions** in the chat — the AI will answer using your documents

---

## Docker (Optional)

```bash
docker compose up --build
```

---

## Troubleshooting

### Common Errors

| Error | Solution |
| ----- | -------- |
| `OPENAI_API_KEY is required` | Set your OpenAI API key in `backend/.env` |
| `CORS error in browser` | Ensure `FRONTEND_URL` in `backend/.env` matches your frontend URL |
| `Connection refused` | Make sure the backend is running on port 8000 |
| `No documents indexed` | Upload at least one document before querying |
| `Unsupported file type` | Only `.pdf`, `.txt`, `.md`, and `.docx` are supported |

### OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy it into `backend/.env` as `OPENAI_API_KEY`

### FAISS Storage

- The FAISS vector index is stored at `backend/vectorstore/faiss_index/`
- It persists across server restarts
- Delete the directory to reset the index

### Upload Storage

- Uploaded files are saved to `backend/data/uploads/`
- Files are kept on disk for reference
- Delete files via the API or the frontend UI

---

## Tech Stack

| Layer    | Technology                                |
| -------- | ----------------------------------------- |
| Frontend | Next.js 14+, TypeScript, Vanilla CSS      |
| Backend  | FastAPI, Python 3.11+                     |
| AI/LLM   | LangChain, OpenAI (GPT-4.1-mini)         |
| Vectors  | FAISS (CPU), OpenAI Embeddings            |
| Docs     | PyPDF, python-docx, Unstructured          |

---

## License

MIT
