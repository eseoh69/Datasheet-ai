import os
import sys
from dotenv import load_dotenv

from csv_loader.loader import load_csv, insert_data
from schema_manager.manager import get_schema, infer_schema, compare_schema, create_table
from query_service.service import get_schema_context, process_query, format_results
from llm_adapter.adapter import translate_to_sql

load_dotenv()

DB_PATH = "datasheet.db"


def handle_load(file_path: str):
    """Loads a CSV file into the database."""
    print(f"\nLoading {file_path}...")

    # Step 1: Load CSV
    try:
        df = load_csv(file_path)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Step 2: Infer schema from CSV
    incoming_schema = infer_schema(df)

    # Step 3: Get table name from file name
    table_name = os.path.splitext(os.path.basename(file_path))[0].lower()

    # Step 4: Check if table exists and compare schemas
    existing_schema = get_schema(DB_PATH)

    if table_name in existing_schema:
        action = compare_schema(existing_schema[table_name], incoming_schema)
        if action == "append":
            print(f"Table '{table_name}' exists with matching schema. Appending data...")
        else:
            print(f"Table '{table_name}' exists but schema differs.")
            choice = input("Options: [o]verwrite, [r]ename, [s]kip: ").strip().lower()
            if choice == "o":
                from schema_manager.manager import drop_table
                drop_table(DB_PATH, table_name)
                create_table(DB_PATH, table_name, incoming_schema)
                print(f"Table '{table_name}' overwritten.")
            elif choice == "r":
                table_name = input("Enter new table name: ").strip().lower()
                create_table(DB_PATH, table_name, incoming_schema)
                print(f"Data will be loaded into new table '{table_name}'.")
            else:
                print("Skipped.")
                return
    else:
        create_table(DB_PATH, table_name, incoming_schema)
        print(f"Table '{table_name}' created.")

    # Step 5: Insert data
    insert_data(df, table_name, DB_PATH)
    print(f"Successfully loaded {len(df)} rows into '{table_name}'.")


def handle_query(user_input: str):
    """Translates natural language to SQL and executes it."""
    print("\nTranslating your query...")

    try:
        # Step 1: Get schema context for LLM
        schema_context = get_schema_context(DB_PATH)

        # Step 2: Translate to SQL via LLM
        sql = translate_to_sql(schema_context, user_input)
        print(f"Generated SQL: {sql}")

        # Step 3: Validate and execute via Query Service
        results = process_query(DB_PATH, sql)

        # Step 4: Format and display results
        print("\nResults:")
        print(format_results(results))

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def handle_tables():
    """Lists all tables in the database."""
    schema = get_schema(DB_PATH)
    if not schema:
        print("\nNo tables found in the database.")
        return
    print("\nTables in database:")
    for table, columns in schema.items():
        col_names = ", ".join(c["name"] for c in columns)
        print(f"  {table}: ({col_names})")


def main():
    print("=" * 50)
    print("  DataSheet AI — Natural Language SQL Interface")
    print("=" * 50)
    print("Commands:")
    print("  load <file.csv>  — load a CSV into the database")
    print("  tables           — list all tables")
    print("  ask <question>   — query in natural language")
    print("  sql <query>      — run a raw SQL SELECT query")
    print("  exit             — quit")
    print("=" * 50)

    while True:
        try:
            user_input = input("\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            sys.exit(0)

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        elif user_input.lower() == "tables":
            handle_tables()

        elif user_input.lower().startswith("load "):
            file_path = user_input[5:].strip()
            handle_load(file_path)

        elif user_input.lower().startswith("ask "):
            question = user_input[4:].strip()
            handle_query(question)

        elif user_input.lower().startswith("sql "):
            sql = user_input[4:].strip()
            try:
                results = process_query(DB_PATH, sql)
                print("\nResults:")
                print(format_results(results))
            except ValueError as e:
                print(f"Error: {e}")

        else:
            print("Unknown command. Type 'exit' to quit.")


if __name__ == "__main__":
    main()