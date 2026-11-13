import pandas as pd
from typing import TypedDict, Dict, Any
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from security import validate_sql_safety

class AgentState(TypedDict):
    user_query: str
    schema_info: str
    sql_query: str
    is_safe: bool
    query_result: pd.DataFrame
    error_message: str
    final_answer: str
    retry_count: int

def create_agent_graph(db_conn, model_name: str = "qwen2.5-coder:1.5b"):
    llm = ChatOllama(model=model_name, temperature=0)
    
    def get_schema_node(state: AgentState) -> Dict[str, Any]:
        cursor = db_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        schema_lines = []
        for table in tables:
            t_name = table[0]
            cursor.execute(f"PRAGMA table_info({t_name});")
            columns = [col[1] for col in cursor.fetchall()]
            schema_lines.append(f"Table '{t_name}' with columns: {', '.join(columns)}")
        return {"schema_info": "\n".join(schema_lines), "retry_count": 0}

    def generate_sql_node(state: AgentState) -> Dict[str, Any]:
        # If there's a previous execution error, instruct Ollama to fix it
        error_context = ""
        if state.get("error_message") and state.get("sql_query"):
            error_context = f"\nPrevious Failed SQL: {state['sql_query']}\nDatabase Error: {state['error_message']}\nPlease fix the query."

        prompt = f"""
        Given the database schema below, write a read-only SQLite query to answer the user's question.
        Return ONLY the raw SQL query inside a markdown code block (e.g. ```sql ... ```).

        Schema:
        {state['schema_info']}
        {error_context}

        User Question: {state['user_query']}
        """
        response = llm.invoke(prompt)
        content = response.content
        
        if "```sql" in content:
            sql = content.split("```sql")[1].split("```")[0].strip()
        elif "```" in content:
            sql = content.split("```")[1].split("```")[0].strip()
        else:
            sql = content.strip()
            
        return {"sql_query": sql}

    def security_validator_node(state: AgentState) -> Dict[str, Any]:
        is_safe, error_msg = validate_sql_safety(state["sql_query"])
        return {"is_safe": is_safe, "error_message": error_msg}

    def execute_query_node(state: AgentState) -> Dict[str, Any]:
        if not state["is_safe"]:
            return {"query_result": pd.DataFrame()}
        try:
            df = pd.read_sql_query(state["sql_query"], db_conn)
            return {"query_result": df, "error_message": ""}
        except Exception as e:
            current_retries = state.get("retry_count", 0) + 1
            return {"query_result": pd.DataFrame(), "error_message": str(e), "retry_count": current_retries}

    def synthesize_answer_node(state: AgentState) -> Dict[str, Any]:
        if state["error_message"]:
            return {"final_answer": f"Execution failed after retries: {state['error_message']}"}
            
        df = state["query_result"]
        if df.empty or (len(df) == 1 and df.iloc[0, 0] is None):
            return {"final_answer": "No matching records found in the database."}
            
        prompt = f"""
        Provide a concise, direct, professional business answer to the user's question based strictly on the query result table below. Do not hallucinate or add unnecessary filler text.
        
        User Question: {state['user_query']}
        Query Results:
        {df.to_string(index=False)}
        """
        response = llm.invoke(prompt)
        return {"final_answer": response.content}

    # Build Workflow Graph with Self-Correction Loop
    workflow = StateGraph(AgentState)

    workflow.add_node("get_schema", get_schema_node)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("security_validator", security_validator_node)
    workflow.add_node("execute_query", execute_query_node)
    workflow.add_node("synthesize_answer", synthesize_answer_node)

    workflow.set_entry_point("get_schema")
    workflow.add_edge("get_schema", "generate_sql")
    workflow.add_edge("generate_sql", "security_validator")

    def check_safety(state: AgentState):
        return "execute" if state["is_safe"] else "end"

    workflow.add_conditional_edges(
        "security_validator",
        check_safety,
        {"execute": "execute_query", "end": END}
    )

    # Self-Correction Decision Edge: If execution fails and retries < 2, loop back to generate_sql!
    def check_execution(state: AgentState):
        if state["error_message"] and state.get("retry_count", 0) < 2:
            return "retry"
        elif state["error_message"]:
            return "synthesize" # Give up and let synthesizer show the error
        else:
            return "synthesize"

    workflow.add_conditional_edges(
        "execute_query",
        check_execution,
        {
            "retry": "generate_sql",
            "synthesize": "synthesize_answer"
        }
    )

    workflow.add_edge("synthesize_answer", END)

    return workflow.compile()