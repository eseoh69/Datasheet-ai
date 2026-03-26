def build_prompt(schema_context: str, user_query: str) -> str:
    """
    Builds a prompt to send to the LLM combining the database
    schema context and the user's natural language query.

    Args:
        schema_context: formatted schema string from query_service.get_schema_context()
        user_query: natural language query from the user
    Returns:
        formatted prompt string ready to send to the LLM
    """
    pass


def query_llm(prompt: str) -> str:
    """
    Sends a prompt to the LLM API and returns the raw response.
    NOTE: must NOT execute any SQL — only returns generated SQL string.

    Args:
        prompt: formatted prompt string from build_prompt()
    Returns:
        raw response string from the LLM
    Raises:
        ConnectionError: if LLM API is unreachable
        ValueError: if API key is missing
    """
    pass


def extract_sql(llm_response: str) -> str:
    """
    Parses the LLM response and extracts just the SQL query.
    LLM output is treated as untrusted — must be validated before use.

    Args:
        llm_response: raw response string from query_llm()
    Returns:
        extracted SQL string
    Raises:
        ValueError: if no valid SQL found in response
    """
    pass


def translate_to_sql(schema_context: str, user_query: str) -> str:
    """
    Full pipeline: build prompt → call LLM → extract SQL.
    Returns SQL string to be passed to the SQL Validator.
    NOTE: does NOT validate or execute the SQL.

    Args:
        schema_context: formatted schema string
        user_query: natural language query from the user
    Returns:
        extracted SQL string from LLM response
    Raises:
        ValueError: if SQL cannot be extracted
        ConnectionError: if LLM API is unreachable
    """
    pass