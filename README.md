# DataSheet AI

A natural language interface for querying structured data using SQLite and an LLM.
Built for EC530 at Boston University.

## System Overview

DataSheet AI allows users to load CSV files into a SQLite database and query
them using plain English. The system translates natural language into SQL using
an LLM, validates the generated SQL before execution, and returns formatted results.

### Architecture

The system has two independent flows:

**Data Ingestion Flow:**
CSV File → CSV Loader → Schema Manager → SQLite Database

**Query Processing Flow:**
User → CLI → Query Service → SQL Validator → SQLite Database
                    ↕
              LLM Adapter (natural language → SQL)

### Modules

- **CSV Loader** — reads CSV files and inserts data row by row into SQLite
- **Schema Manager** — infers schema from CSV, manages table creation and comparison
- **Query Service** — main entry point for all queries, enforces validation before execution
- **SQL Validator** — validates SQL queries for safety and correctness before execution
- **LLM Adapter** — translates natural language to SQL using the Anthropic Claude API
- **CLI** — user-facing interface, never accesses the database directly

### Key Design Decisions

- The CLI never accesses the database directly — all queries go through the Query Service
- LLM output is treated as untrusted input — always validated before execution
- The SQL Validator only allows SELECT queries — INSERT, UPDATE, DELETE, DROP are blocked
- Semicolons are rejected to prevent SQL injection attacks
- Table and column names are normalized to lowercase for case-insensitive matching

## How to Run

### Prerequisites
- Python 3.13
- An Anthropic API key

### Setup

```bash
git clone https://github.com/eseoh69/Datasheet-ai.git
cd Datasheet-ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Create a `.env` file in the project root:
ANTHROPIC_API_KEY=your_key_here

### Running the CLI

```bash
python cli/main.py
```

### Available Commands

| Command | Description |
|---------|-------------|
| `load <file.csv>` | Load a CSV file into the database |
| `tables` | List all tables in the database |
| `ask <question>` | Query using natural language |
| `sql <query>` | Run a raw SQL SELECT query |
| `exit` | Quit the program |

### Example Session

load sales.csv
Table 'sales' created.
Successfully loaded 100 rows into 'sales'.

tables
Tables in database:
sales: (id, product, quantity, revenue)

ask show me the top 3 products by revenue
Generated SQL: SELECT product, revenue FROM sales ORDER BY revenue DESC LIMIT 3
Results:
product | revenue

Widget A | 9500.0
Widget B | 7200.0
Widget C | 6100.0

exit

## How to Run Tests

```bash
pytest tests/ -v
```

### Test Coverage

- `test_csv_loader.py` — CSV reading and data insertion
- `test_schema_manager.py` — schema inference, comparison, table creation
- `test_query_service.py` — query execution, validation pipeline, result formatting
- `test_sql_validator.py` — SQL safety checks, table/column validation
- `test_llm_adapter.py` — prompt building, SQL extraction, API mocking

## Use of AI

This project was built with AI assistance in accordance with EC530 guidelines:

- **LLM used as implementation assistant** for CSV Loader, Schema Manager,
  Query Service, and LLM Adapter modules
- **SQL Validator** — API and unit tests designed independently; LLM used
  to help implement; tests caught a bug where `table.column` notation was
  not handled correctly, which was then fixed
- **Unit tests** — generated with LLM assistance per professor guidelines
- All generated code was reviewed and understood before submission
- No LLM output was used without understanding

## Known Limitations

- SQL parser uses regex which works for simple queries but may struggle
  with complex nested queries or subqueries
- Column validation is skipped for `SELECT *` queries
- No support for aggregation functions like `COUNT`, `SUM` in column validation