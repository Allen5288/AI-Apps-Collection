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
- Open AI Api: [platform.openai.com](https://platform.openai.com/)
    - OpenAI provides a suite of APIs that allow developers to integrate advanced AI capabilities into their applications, including natural language processing, image generation, and more.
    - Set up:
      - Sign up at [platform.openai.com](https://platform.openai.com/) and create an API key.
      - Install the OpenAI Python package: `pip install openai`
      - Example code to interact with OpenAI's models:
        ```python
        import openai

        openai.api_key = 'your-api-key'

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is OpenAI?"}
            ]
        )

        print(response.choices[0].message['content'])
        ```