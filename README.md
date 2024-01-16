# RAG POC Mixtral

Proof of Concept for Local RAG Extraction. We are using, mainly:

- Mistral
- ollama
- llamaindex

## Getting Started

Start a `mongo` server instance in Docker. Acts as unstructured data store:

```bash
docker run -p 27017:27017 --name rag-mongo -d mongo:latest
```

Start ChromaDB Server in Docker Container:

```bash
docker run -p 8000:8000 --name rag-chromadb -d chromadb/chroma:latest
```

Install `ollama`. On Linux:

```bash
curl https://ollama.ai/install.sh | sh
```

We will be using `ollama` to serve our local LLM as a POC. Keep this terminal open.

```bash
ollama serve
```

To interact with the model (and download it implicitly), you can also use a run command for a specific model:

```
ollama run dolphin-mixtral:latest
ollama run mixtral:latest
```

Note that some of these models are $> 26Gb$ in size.
