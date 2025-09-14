- n8n: [n8n.io](https://n8n.io/)
    - N8n is a workflow orchestration tool that allows users to build integrations between different applications without necessarily writing code.
- ollama: https://ollama.com/
    - Ollama is a platform that provides tools and infrastructure for building, deploying, and managing machine learning models, particularly large language models (LLMs).
    - Set Up for local Ollama LLM
      - Install ollama from [ollama.com](https://ollama.com/)
      - Download a model, e.g., `ollama pull llama3.2`
      - Install the Python package: `pip install ollama`
      - Example code to interact with the model:
        ```python
        import ollama

        response = ollama.generate(model="llama3.2", prompt="What is Ollama?")
        print(response)
        ```