# RAG CVE System with Privacy Protection

A Retrieval Augmented Generation (RAG) system for cybersecurity CVE information retrieval with privacy protection.

## Features

- **Dual-source RAG**: CVE vulnerability data + Personal information database
- **Privacy Protection**: Multi-layer PII detection and output sanitization
- **Local LLM**: Uses Ollama (default) - no API key required
- **Conversation Memory**: Multi-turn context support
- **Benchmark Integration**: API client for evaluation

## Quick Start

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

## Requirements

- Python 3.10+
- [Ollama](https://ollama.ai/) with llama3.2 installed (default)
- Or: Groq API key / OpenAI API key (alternative)

### Installing Ollama Model

```bash
ollama pull llama3.2
```

## Configuration

Edit `.env` to configure:

```bash
# LLM Provider: "ollama" (default), "groq", or "openai"
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

## Project Structure

```
RAG2/
├── src/                    # Core components
│   ├── config.py           # Configuration
│   ├── data_loader.py      # HuggingFace datasets
│   ├── embeddings.py       # sentence-transformers
│   ├── vector_store.py     # ChromaDB operations
│   ├── rag_pipeline.py     # Main pipeline
│   ├── privacy_guard.py    # PII protection
│   ├── llm_client.py       # LLM integration
│   └── memory.py           # Conversation history
├── benchmark/              # Benchmark API client
├── docs/                   # Documentation
│   ├── ieee_paper.tex      # IEEE format paper
│   └── RAG_CVE_Presentation.pptx
├── main.py                 # Entry point
├── test_system.py          # Test suite
└── requirements.txt        # Dependencies
```

## Architecture

```
User Query → Embedding → Vector Search (CVE + Personal)
                              ↓
            Unfiltered Context → LLM (Ollama/llama3.2)
                              ↓
            Privacy Guard → Safe Response
```

**Key Design**: RAG returns unfiltered data; privacy protection operates only at output level.

## Testing

```bash
# Run all unit tests
pytest test_system.py -v

# Run quick system validation
python main.py --test
```

## Datasets

- **CVE**: [stasvinokur/cve-and-cwe-dataset-1999-2025](https://huggingface.co/datasets/stasvinokur/cve-and-cwe-dataset-1999-2025) (latest 200 entries)
- **Personal**: [nvidia/Nemotron-Personas-USA](https://huggingface.co/datasets/nvidia/Nemotron-Personas-USA) (first 100 entries)

## License

MIT
