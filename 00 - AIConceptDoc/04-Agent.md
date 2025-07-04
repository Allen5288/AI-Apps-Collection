# Agent

## Using the crewAI

This guide explains how to set up and use the [crewai](https://github.com/joaomdmoura/crewai) Python package for agent-based workflows. Below are step-by-step instructions with explanations and example commands.

### 1. Install crewai

Install the crewai package using pip:

```bash
pip install crewai
```

### 2. Create a Python virtual environment (recommended)

A virtual environment keeps dependencies isolated for your project.

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Initialize a new crewai project

Use the crewai CLI to create a new project. This will prompt you to select different providers (e.g., OpenAI, Ollama, etc.):

```bash
crewai create crew my-agent-project
```

- Replace `my-agent-project` with your desired project name.
- Follow the prompts to select your preferred LLM provider and configure credentials.

### 4. (Optional) Use Ollama as a local LLM provider

Ollama allows you to run LLMs locally. You can list and pull models as follows:

```bash
ollama list           # List available models
ollama pull llama3    # Download the llama3 model (or any other model you want)
```

### 5. Configure your crewai project

Edit the generated `config.yaml` or similar config file in your project directory to set the target model/provider and any other settings (e.g., API keys, model name, etc.).

### 6. Run your crewai agent

Start the agent with:

```bash
crewai run
```

This will launch the agent using your configuration. You can now interact with your agent as defined in your project setup.

---

**Summary of Steps:**

1. Install crewai and dependencies
2. Create and activate a virtual environment
3. Initialize a new crewai project
4. (Optional) Set up Ollama for local LLMs
5. Configure your project (API keys, model, etc.)
6. Run your agent

For more details, see the [crewai documentation](https://github.com/joaomdmoura/crewai).


## Using Docker Model

This section explains how to use AI models with Docker, which allows you to run models in isolated containers without installing them directly on your system. This is useful for running lightweight or large models, testing, and keeping your environment clean.

### 1. Pull a Model Image

Use the following command to pull a model image from a Docker registry (e.g., Docker Hub):

```bash
docker pull ai/smollm2  # You can pull any model; this example uses a lightweight model
```
- Replace `ai/smollm2` with the name of the model you want to use.
- Make sure you have Docker installed and running on your machine.

### 2. Run the Model Container

Start the model in a Docker container. This will launch the model server and allow you to interact with it (e.g., via API or CLI):

```bash
docker run -it --rm -p 11434:11434 ai/smollm2
```
- `-it` runs the container interactively.
- `--rm` removes the container after it stops.
- `-p 11434:11434` maps the model's port to your local machine (adjust as needed).

You can now send requests to the model (for example, using curl or a client library) at `localhost:11434`.

### 3. Interact with the Model

Depending on the model, you can interact via HTTP API, CLI, or other means. For example, with Ollama-compatible models:

```bash
ollama run smollm2
```

Or, for a REST API:

```bash
curl http://localhost:11434/api/generate -d '{"prompt": "Hello, world!"}'
```

### 4. Remove the Model Image (Optional)

To free up disk space, you can remove the model image when you no longer need it:

```bash
docker rmi ai/smollm2
```

---

**Summary of Docker Model Steps:**
1. Pull the model image with `docker pull`
2. Run the model container with `docker run`
3. Interact with the model (API, CLI, etc.)
4. (Optional) Remove the image with `docker rmi`

**Tips:**
- Always check the model's documentation for specific usage instructions and required ports.
- You can run multiple models in parallel by using different ports.
- Use Docker Compose for more complex multi-container setups.

For more details, see the [Docker documentation](https://docs.docker.com/) and the model provider's instructions.