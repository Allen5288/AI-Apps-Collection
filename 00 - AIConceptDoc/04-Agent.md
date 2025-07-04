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
