
# Text2SQL: Autonomous BI Agent

A local, natural language-to-SQL business intelligence tool built with LangGraph, LangChain, Ollama, and Streamlit. It allows non-technical users to query sales and inventory data using plain English, validates queries for read-only safety, self-corrects SQL errors, and renders interactive charts.

## Features

- **Agentic Workflow:** Multi-step state graph (Schema Inspection -> SQL Generation -> Security Validation -> Execution -> Self-Correction -> Synthesis).
- **Read-Only Security:** Blocks destructive SQL commands (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, `REPLACE`).
- **Self-Correction Loop:** Automatically feeds database execution errors back to the LLM to fix invalid SQL queries.
- **Local LLM Support:** Runs locally via Ollama (`qwen2.5-coder:1.5b` and `llama3.2:1b`).
- **Interactive UI:** Streamlit interface with database table explorers, sample query buttons, and automated Plotly bar/scatter visualizations.

## Project Structure



```
text2sql/
├── app.py              # Streamlit UI and Plotly chart rendering
├── agent.py            # LangGraph state machine, nodes, and retry logic
├── database.py         # SQLite initialization and sample data seeding
├── security.py         # Read-only SQL query validation
└── requirements.txt    # Python dependencies
```



# Setup and Installation

1. Install Ollama and pull the required models:

   ```Shell
   ollama pull qwen2.5-coder:1.5b
   ollama pull llama3.2:1b
   ```
2. Install Python dependencies:

	`pip install -r requirements.txt`

1. Run the application:

	`streamlit run app.py`
