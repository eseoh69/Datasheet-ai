import pytest
from unittest.mock import patch, MagicMock
from llm_adapter.adapter import (
    build_prompt,
    query_llm,
    extract_sql,
    translate_to_sql,
)


# ════════════════════════════════════════════════════════════════
# build_prompt
# ════════════════════════════════════════════════════════════════
# build_prompt must combine schema context and user query into
# a prompt string. We don't test the exact wording, just that
# the key pieces are present.

class TestBuildPrompt:

    def test_returns_string(self):
        """build_prompt must return a string."""
        result = build_prompt("users: id, name", "show all users")
        assert isinstance(result, str)

    def test_contains_schema_context(self):
        """Schema context must appear in the prompt."""
        result = build_prompt("users: id, name", "show all users")
        assert "users: id, name" in result

    def test_contains_user_query(self):
        """User query must appear in the prompt."""
        result = build_prompt("users: id, name", "show all users")
        assert "show all users" in result

    def test_prompt_not_empty(self):
        """Prompt must not be empty."""
        result = build_prompt("users: id, name", "show all users")
        assert len(result) > 0

    def test_instructs_select_only(self):
        """Prompt must instruct the LLM to only generate SELECT queries."""
        result = build_prompt("users: id, name", "show all users")
        assert "SELECT" in result.upper()


# ════════════════════════════════════════════════════════════════
# extract_sql
# ════════════════════════════════════════════════════════════════
# extract_sql must pull just the SQL out of an LLM response.
# LLM output is untrusted so we test various response formats.

class TestExtractSql:

    def test_extracts_sql_from_formatted_response(self):
        """Should extract SQL from a properly formatted response."""
        response = "SQL Query: SELECT * FROM users\nExplanation: Returns all users."
        sql = extract_sql(response)
        assert sql == "SELECT * FROM users"

    def test_extracts_sql_case_insensitive(self):
        """Should handle lowercase 'sql query:' prefix."""
        response = "sql query: SELECT name FROM users\nExplanation: Returns names."
        sql = extract_sql(response)
        assert sql == "SELECT name FROM users"

    def test_fallback_to_select_line(self):
        """Should fall back to finding a line starting with SELECT."""
        response = "Here is your query:\nSELECT * FROM users\nHope that helps!"
        sql = extract_sql(response)
        assert "SELECT" in sql.upper()

    def test_raises_if_no_sql_found(self):
        """Should raise ValueError if no SQL can be extracted."""
        with pytest.raises(ValueError):
            extract_sql("Sorry, I cannot generate that query.")

    def test_returns_string(self):
        """extract_sql must return a string."""
        response = "SQL Query: SELECT * FROM users\nExplanation: All users."
        result = extract_sql(response)
        assert isinstance(result, str)


# ════════════════════════════════════════════════════════════════
# query_llm
# ════════════════════════════════════════════════════════════════
# query_llm calls the real Anthropic API — we mock it in tests
# so we don't make actual API calls or need a real key.

class TestQueryLlm:

    def test_returns_string(self):
        """query_llm must return a string response."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="SQL Query: SELECT * FROM users")]

        with patch("llm_adapter.adapter.anthropic.Anthropic") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_response
            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
                result = query_llm("test prompt")

        assert isinstance(result, str)

    def test_raises_without_api_key(self):
        """query_llm must raise ValueError if API key is missing."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                query_llm("test prompt")

    def test_calls_anthropic_api(self):
        """query_llm must actually call the Anthropic API."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="SQL Query: SELECT * FROM users")]

        with patch("llm_adapter.adapter.anthropic.Anthropic") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_response
            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
                query_llm("test prompt")

        mock_client.return_value.messages.create.assert_called_once()


# ════════════════════════════════════════════════════════════════
# translate_to_sql
# ════════════════════════════════════════════════════════════════
# translate_to_sql is the full pipeline. We mock query_llm so
# we test the pipeline logic without real API calls.

class TestTranslateToSql:

    def test_returns_string(self):
        """translate_to_sql must return a string."""
        with patch("llm_adapter.adapter.query_llm") as mock_llm:
            mock_llm.return_value = "SQL Query: SELECT * FROM users\nExplanation: All users."
            result = translate_to_sql("users: id, name", "show all users")
        assert isinstance(result, str)

    def test_returns_select_query(self):
        """translate_to_sql must return a SELECT query."""
        with patch("llm_adapter.adapter.query_llm") as mock_llm:
            mock_llm.return_value = "SQL Query: SELECT * FROM users\nExplanation: All users."
            result = translate_to_sql("users: id, name", "show all users")
        assert result.upper().startswith("SELECT")

    def test_calls_query_llm(self):
        """translate_to_sql must call query_llm as part of the pipeline."""
        with patch("llm_adapter.adapter.query_llm") as mock_llm:
            mock_llm.return_value = "SQL Query: SELECT * FROM users\nExplanation: All users."
            translate_to_sql("users: id, name", "show all users")
        mock_llm.assert_called_once()

    def test_raises_if_llm_returns_no_sql(self):
        """translate_to_sql must raise ValueError if LLM returns no SQL."""
        with patch("llm_adapter.adapter.query_llm") as mock_llm:
            mock_llm.return_value = "I cannot help with that."
            with pytest.raises(ValueError):
                translate_to_sql("users: id, name", "show all users")