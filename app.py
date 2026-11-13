import streamlit as st
import plotly.express as px
from database import init_db, get_table_data
from agent import create_agent_graph

# Page Config
st.set_page_config(page_title="Text2SQL Agentic BI", layout="wide")

# Initialize DB
conn = init_db()

# Initialize session state for question input
if "query_input" not in st.session_state:
    st.session_state.query_input = ""

def set_question(q: str):
    st.session_state.query_input = q

# Sidebar: Model Selection & Database Expanders
with st.sidebar:
    st.header("Configuration")
    selected_model = st.selectbox(
        "Select Ollama Model",
        options=["qwen2.5-coder:1.5b", "llama3.2:1b"],
        index=0  # Default to qwen2.5-coder:1.5b for accurate SQL generation
    )
    
    st.divider()
    st.header("Database Explorer")
    
    with st.expander("Sales Table", expanded=True):
        st.dataframe(get_table_data("sales", conn), hide_index=True)
        
    with st.expander("Inventory Table", expanded=True):
        st.dataframe(get_table_data("inventory", conn), hide_index=True)

# Compile agent graph with selected model
app_graph = create_agent_graph(conn, model_name=selected_model)

# Main UI Layout
st.title("Text2SQL: Autonomous BI Agent")
st.markdown("Ask natural language questions to analyze sales and inventory securely with multi-step agent validation.")

# Sample Question Buttons (populates the input box for Ollama to process)
st.markdown("**Try a sample question:**")
sample_questions = [
    "What are total sales grouped by category?",
    "Show stock levels across warehouses",
    "Which product generated the highest revenue?",
    "List all products and their current stock levels"
]

cols = st.columns(len(sample_questions))
for i, question in enumerate(sample_questions):
    with cols[i]:
        st.button(question, on_click=set_question, args=(question,), use_container_width=True)

# Text Input bound to session state
user_query = st.text_input(
    "Enter business question:",
    key="query_input",
    placeholder="e.g., What are total sales grouped by category?"
)

if user_query:
    with st.spinner(f"Agentic workflow in progress using {selected_model}..."):
        initial_state = {
            "user_query": user_query,
            "schema_info": "",
            "sql_query": "",
            "is_safe": True,
            "query_result": None,
            "error_message": "",
            "final_answer": ""
        }
        
        result = app_graph.invoke(initial_state)
        
        st.subheader("Generated SQL Query")
        st.code(result.get("sql_query", "N/A"), language="sql")
        
        if result.get("error_message"):
            st.error(result["error_message"])
        else:
            st.subheader("Business Insight")
            st.write(result.get("final_answer"))
            
            df = result.get("query_result")
            if df is not None and not df.empty:
                st.subheader("Query Results Data")
                st.dataframe(df, hide_index=True)
                
                st.subheader("Automatic Interactive Visualization")
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                
                if numeric_cols and cat_cols:
                    fig = px.bar(
                        df, 
                        x=cat_cols[0], 
                        y=numeric_cols[0], 
                        title=f"{numeric_cols[0]} by {cat_cols[0]}"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                elif len(numeric_cols) >= 2:
                    fig = px.scatter(
                        df, 
                        x=numeric_cols[0], 
                        y=numeric_cols[1], 
                        title=f"{numeric_cols[1]} vs {numeric_cols[0]}"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Single metric returned — add a category or grouping to generate a chart.")