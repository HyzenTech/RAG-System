# RAG CVE System with Privacy Protection

A Retrieval Augmented Generation (RAG) system for cybersecurity CVE information retrieval with privacy protection. This project implements a complete RAG pipeline that retrieves vulnerability information while preventing personal data leakage.

## 📊 Project Status

| Component | Status |
|-----------|--------|
| Core RAG System | ✅ Complete |
| Privacy Protection | ✅ Complete |
| LLM Integration (Ollama) | ✅ Complete |
| Conversation Memory | ✅ Complete |
| Unit Tests | ✅ 12/12 Passing |
| Benchmark API | ⏳ Waiting for API availability |

> **Note:** The benchmark evaluation at `https://infosec.simpan.cv/benchmark` is currently not accessible. The system is fully implemented and ready for evaluation once the API becomes available.

## ✨ Features

- **Dual-source RAG**: CVE vulnerability data (200 entries) + Personal information database (100 entries)
- **Privacy Protection**: Multi-layer PII detection and output sanitization
- **Local LLM**: Uses Ollama by default - no API key required
- **Conversation Memory**: Multi-turn context support
- **Benchmark Integration**: Automated client for evaluation API

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run system test
python main.py --test

# Interactive mode
python main.py --interactive

# Run benchmark (when API available)
python main.py --benchmark
```

## 📋 Requirements

- Python 3.10+
- [Ollama](https://ollama.ai/) with llama3.2 installed

### Installing Ollama Model

```bash
ollama pull llama3.2
```

## ⚙️ Configuration

Edit `.env` to configure the LLM provider:

```bash
# LLM Provider: "ollama" (default), "groq", or "openai"
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

## 📁 Project Structure

```
RAG2/
├── src/                    # Core components
│   ├── config.py           # Configuration management
│   ├── data_loader.py      # HuggingFace dataset loading
│   ├── embeddings.py       # Sentence-transformers wrapper
│   ├── vector_store.py     # ChromaDB operations
│   ├── rag_pipeline.py     # Main RAG pipeline
│   ├── privacy_guard.py    # PII detection & sanitization
│   ├── llm_client.py       # LLM integration (Ollama/Groq/OpenAI)
│   └── memory.py           # Conversation history
├── benchmark/              # Benchmark API client
├── docs/                   # Documentation
│   ├── RAG.tex             # IEEE format paper
│   └── RAG_CVE_Presentation.pptx
├── main.py                 # Entry point
├── test_system.py          # Test suite
└── requirements.txt        # Dependencies
```

## 🏗️ Architecture

```
User Query → Embedding → Vector Search (CVE + Personal)
                              ↓
            Unfiltered Context → LLM (Ollama/llama3.2)
                              ↓
            Privacy Guard → Safe Response
```

**Key Design Decision:** The RAG system returns unfiltered data as per requirements. Privacy protection operates only at the output level through:
1. Intent detection (blocks personal info requests)
2. Regex sanitization (removes SSN, phone, email, etc.)
3. CVE-ID preservation (protects CVE-XXXX-NNNNN patterns)

## 🧪 Testing

```bash
# Run all unit tests
pytest test_system.py -v

# Run quick system validation
python main.py --test
```

## 📚 Datasets

- **CVE**: [stasvinokur/cve-and-cwe-dataset-1999-2025](https://huggingface.co/datasets/stasvinokur/cve-and-cwe-dataset-1999-2025) (latest 200 entries)
- **Personal**: [nvidia/Nemotron-Personas-USA](https://huggingface.co/datasets/nvidia/Nemotron-Personas-USA) (first 100 entries)

## 📄 License

MIT
