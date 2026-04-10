import os
import anthropic
from dotenv import load_dotenv

load_dotenv()


def build_prompt(schema_context: str, user_query: str) -> str:
    """
    Builds a prompt to send to the LLM combining the database
    schema context and the user's natural language query.
    """
    return f"""You are an AI assistant that converts natural language queries into SQL statements.
The database uses SQLite and has the following structure:

{schema_context}

User Query: "{user_query}"

Your task is to:
1. Generate a SQL query that accurately answers the user's question.
2. Ensure the SQL is compatible with SQLite syntax.
3. Only generate SELECT queries — never INSERT, UPDATE, DELETE, or DROP.

Output Format:
SQL Query: <your SQL query here>
Explanation: <one sentence explaining what the query does>"""


def query_llm(prompt: str) -> str:
    """
    Sends a prompt to the Claude API and returns the raw response.
    NOTE: must NOT execute any SQL — only returns generated SQL string.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text


def extract_sql(llm_response: str) -> str:
    """
    Parses the LLM response and extracts just the SQL query.
    LLM output is treated as untrusted — must be validated before use.
    """
    for line in llm_response.split("\n"):
        if line.strip().upper().startswith("SQL QUERY:"):
            sql = line.split(":", 1)[1].strip()
            # Strip trailing semicolon — LLMs commonly add these
            sql = sql.rstrip(";").strip()
            if sql:
                return sql

    # Fallback: look for a line starting with SELECT
    for line in llm_response.split("\n"):
        if line.strip().upper().startswith("SELECT"):
            return line.strip().rstrip(";").strip()

    raise ValueError("No valid SQL found in LLM response")


def translate_to_sql(schema_context: str, user_query: str) -> str:
    """
    Full pipeline: build prompt -> call LLM -> extract SQL.
    Returns SQL string to be passed to the SQL Validator.
    NOTE: does NOT validate or execute the SQL.
    """
    prompt = build_prompt(schema_context, user_query)
    response = query_llm(prompt)
    return extract_sql(response)