# CODEBUDDY.md

## Project Overview

This is a comprehensive educational repository for Large Language Model (LLM) application development, focusing on OpenAI API integration and LangChain-based GenAI applications. The project serves as a learning resource with practical examples, tutorials, and hands-on implementations.

## Development Environment Setup

### Python Environment
- **Python Version**: 3.10 (required)
- **Package Manager**: pip with conda for environment management
- **Virtual Environment**: Create conda environment named `langchain`

```bash
conda create -n langchain python=3.10
conda activate langchain
pip install -r requirements.txt
```

### Required Environment Variables
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Jupyter Lab Setup
The project is primarily developed using Jupyter notebooks for interactive development:

```bash
conda install -c conda-forge jupyterlab
jupyter lab --generate-config

# Background startup
nohup jupyter lab --port=8000 --NotebookApp.token='your-password' --notebook-dir=./ &
```

## Project Architecture

### Core Directories Structure

1. **openai_api/**: Direct OpenAI API examples and tutorials
   - Contains Jupyter notebooks demonstrating core OpenAI features
   - Examples: embeddings, function calling, DALLE, GPT-4V, TTS, Whisper
   - Each feature has dedicated `.ipynb` files with step-by-step implementations

2. **langchain/**: LangChain-based applications and advanced use cases
   - **sales_chatbot/**: RAG-based sales chatbot using FAISS vector store
   - **openai-translator/**: Full-featured PDF translation app with LangChain
   - **chatglm/**: ChatGLM integration examples
   - **langgraph/**: LangGraph workflow examples
   - **langsmith/**: LangSmith integration for monitoring

3. **openai-translator/**: Standalone translation application
   - Modular architecture with separate model, translator, and utility layers
   - Supports both OpenAI and GLM models
   - Configuration-driven design using YAML config files

4. **chatgpt-plugins/**: ChatGPT plugin development examples
   - **todo-list/**: Simple todo list plugin
   - **weather-forecast/**: Weather forecasting plugin

### Key Application Patterns

#### Translation App Architecture (`openai-translator/`)
- **Model Layer**: Abstracted model interfaces (`model/`) supporting OpenAI and GLM
- **Translator Layer**: PDF parsing and translation logic (`translator/`)
- **Book Layer**: Document structure management (`book/`)
- **Utils Layer**: Configuration, logging, and argument parsing (`utils/`)

#### Sales Chatbot Pattern (`langchain/sales_chatbot/`)
- RAG implementation using FAISS vector store
- Gradio-based web interface
- Retrieval with similarity score thresholding
- Fallback response system for unmatched queries

## Common Development Commands

### Running Applications

**Translation App:**
```bash
cd openai-translator
python ai_translator/main.py --config config.yaml
```

**Sales Chatbot:**
```bash
cd langchain/sales_chatbot
python sales_chatbot.py
```

**ChatGPT Plugins:**
```bash
cd chatgpt-plugins/todo-list
python main.py
```

### Jupyter Notebook Development
Most tutorials and examples are in Jupyter notebooks. Start Jupyter Lab and navigate to the relevant directory:
```bash
jupyter lab
```

## Key Dependencies and Their Roles

- **openai**: Core OpenAI API client
- **langchain**: Framework for LLM application development
- **langchain-openai**: OpenAI integration for LangChain
- **chromadb, faiss-cpu**: Vector databases for RAG applications
- **gradio**: Web UI framework for ML applications
- **unstructured**: Document parsing and preprocessing
- **tiktoken**: Token counting for OpenAI models

## Configuration Management

Applications use YAML configuration files (e.g., `config.yaml` in openai-translator) for:
- Model selection and API keys
- File paths and formats
- Application-specific settings

## Development Notes

- All applications require OPENAI_API_KEY environment variable
- Most examples are educational and self-contained
- Vector stores (FAISS) need to be pre-built for RAG applications
- Gradio applications typically run on `0.0.0.0` for accessibility
- No formal testing framework - examples are demonstration-focused