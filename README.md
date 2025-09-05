# 🤖 LinkedIn Automation RAG

An **AI-powered Retrieval-Augmented Generation (RAG) pipeline** that scrapes LinkedIn posts, indexes them into a vector database, and generates **human-like summaries and insights**.  
Built with **LangChain**, **FAISS**, and **local LLaMA models** to keep everything private and efficient.

---

## ✨ Features
- 🔍 **Scraping** – Extracts top LinkedIn posts based on a topic.
- 📚 **Vector Database** – Embeds and stores content for fast retrieval.
- 🧠 **RAG Pipeline** – Uses embeddings + local LLaMA model for Q&A and summarization.
- 📝 **Summaries & Insights** – Generates concise, human-like summaries of posts.
- 🛡️ **Environment Variables** – All API keys and tokens stored securely in `.env`.

---

## 🚀 Tech Stack
- **Python 3.12+**
- **LangChain** – RAG orchestration
- **FAISS** – Vector store
- **LLaMA (via Ollama)** – Local inference
- **Hugging Face** – Embeddings & model APIs
- **Playwright + BeautifulSoup** – Web scraping

---

## 📂 Project Structure
├── pipeline/ # Core pipeline logic
│ ├── management/commands/ # Automation scripts
├── search_scrape.py # Fetch & scrape LinkedIn posts
├── requirements.txt # Python dependencies
├── .env.sample # Environment variable template
└── README.md # Project documentation
