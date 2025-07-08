# ZUS API

A robust API system for ZUS Coffee data management, featuring web scraping, data processing, semantic search, and RESTful endpoints for both product and outlet data.

---

## How to Run

### Option 1: Streamlit Chatbot Interface (Recommended for Free Deployment)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd zus-api
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Create a `.env` file in the project root or export variables in your shell:
     ```env
     OPENAI_API_KEY=your-openai-key
     PINECONE_API_KEY=your-pinecone-key
     CORS_ORIGINS=*
     ```

4. **(Optional) Scrape and update data**
   - If you want to refresh product/outlet data:
     ```bash
     cd data_pipeline
     python scrape_zus.py
     cd ..
     ```

5. **Start the Streamlit chatbot**
   ```bash
   streamlit run streamlit_app.py
   ```

6. **Access the chatbot**
   - Chatbot Interface: [http://localhost:8501](http://localhost:8501)

### Option 2: FastAPI REST API

1. **Follow steps 1-4 above**

2. **Start the API server**
   ```bash
   cd app
   python app.py
   ```

3. **Access the API**
   - API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

## Project Structure

```
zus-api/
├── app/
│   ├── app.py            # FastAPI application entry point
│   ├── src/
│   │   ├── vectorstore.py # Product vector search logic
│   │   ├── text2SQL.py    # Outlet SQL logic and DB auto-creation
│   │   ├── utils.py       # General utilities and config loading
│   │   ├── openai_chain.py # LLM prompt chains
│   │   └── router.py      # API route handlers
│   ├── data/              # Data files (CSV, SQL, DB)
├── data_pipeline/         # Web scraping scripts
│   └── scrape_zus.py
├── streamlit_app.py       # Streamlit chatbot interface
├── config.json            # Application configuration
├── requirements.txt       # Python dependencies
├── Dockerfile             # Containerization
├── render.yaml            # Render deployment config
└── README.md
```

---

## Features

- **Web Scraping:** Automated extraction of product and outlet data from ZUS Coffee websites.
- **Semantic Product Search:** Vector database (Pinecone) for product queries.
- **Outlet SQL Search:** SQLite database for outlet/location queries, auto-created from CSV if missing.
- **LLM Integration:** OpenAI-powered responses and intent classification.
- **RESTful API:** FastAPI endpoints for products, outlets, and chat.
- **Streamlit Chatbot:** Beautiful web interface for direct interaction.
- **Robust Error Handling:** Graceful fallback and clear error messages.
- **Environment-based Configuration:** Secure handling of API keys and settings.

---

## Installation

### Prerequisites
- Python 3.8+
- Chrome & ChromeDriver (for scraping)
- [Pinecone](https://www.pinecone.io/) and [OpenAI](https://platform.openai.com/) accounts for API keys

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd zus-api

# Install dependencies
pip install -r requirements.txt
```

---

## Configuration

Edit `config.json` to set file paths and model settings.  
**Set environment variables** (or use a `.env` file):

```env
OPENAI_API_KEY=your-openai-key
PINECONE_API_KEY=your-pinecone-key
CORS_ORIGINS=*
```

Example `config.json`:
```json
{
  "models": { ... },
  "pinecone": { ... },
  "filepaths": {
    "products": {
      "csv": "data/zus_products.csv"
    },
    "outlets": {
      "csv": "data/zus_outlets_final.csv",
      "sql": "data/zus_outlets.sql",
      "db": "data/zus_outlets.db"
    },
    "data_directory": "data/"
  }
}
```

---

## Data Pipeline

To scrape and update product/outlet data:

```bash
cd data_pipeline
python scrape_zus.py
```

This will generate CSV and SQL files in `app/data/`.

---

## API Endpoints

### Product Endpoints (Vector Search)
- `GET /products?query=...` — Semantic product search

### Outlet Endpoints (SQL Search)
- `GET /outlets?query=...` — Location-based outlet search

### Chat Endpoint
- `POST /chat` — Conversational interface

### Health Check
- `GET /health` — Service status

---

## Example API Request

```http
GET /products?query=black tumbler
```
**Response:**
```json
{
  "summary": "The ZUS Coffee Black Tumbler is a popular product...",
  "retrieved_products": [
    {
      "name": "Black Tumbler",
      "category": "Drinkware",
      "price": "$19.99",
      "color": "Black",
      "image": "https://...",
      "snippet": "A stylish black tumbler...",
      "score": 0.92
    }
  ]
}
```

---

## Development & Testing

```bash
# Run tests
python -m pytest

# API test
curl http://localhost:8000/health

# Streamlit test
streamlit run streamlit_app.py
```

---

## Deployment

### Render (Free Tier)
The `render.yaml` is configured for free deployment on Render using Streamlit.

### Local Development
```bash
# Streamlit
streamlit run streamlit_app.py

# FastAPI
cd app && python app.py
```

---

## Troubleshooting

- **Missing API keys:** Ensure `OPENAI_API_KEY` and `PINECONE_API_KEY` are set.
- **CORS errors:** Set `CORS_ORIGINS` appropriately for your environment.
- **DB not found:** The app will auto-create the SQLite DB from CSV if missing.
- **Streamlit issues:** Make sure all dependencies are installed with `pip install -r requirements.txt`.

---

## Contributing

1. Fork the repo and create a feature branch.
2. Make your changes and add tests.
3. Submit a pull request.

---

## License

MIT License. See `LICENSE` for details.

---

## Support

- Open an issue on GitHub
- Review the API docs at `/docs`

---

## Roadmap

- [ ] Enhanced semantic search
- [ ] Real-time data updates
- [ ] Mobile API client
- [ ] Analytics dashboard
- [ ] Multi-language support
