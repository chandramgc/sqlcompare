# SQL Diff UI

A polished, local Python app for comparing SQL queries with semantic analysis. Built with Streamlit and sqlglot.

## Features

### Core Comparison Features
- ✅ **SQL Validation**: Validates SQL syntax before comparison with clear error messages
- 🎨 **SQL Beautification**: Automatically formats and beautifies SQL queries
- 🔍 **Text Diff**: Side-by-side unified diff with color-coded additions/removals
- 🧠 **Semantic Diff**: AST-based analysis that detects structural changes:
  - SELECT column additions/removals/renames
  - FROM table changes
  - JOIN modifications (type, table, conditions)
  - WHERE predicate changes
  - GROUP BY/HAVING changes
  - ORDER BY/LIMIT/OFFSET changes
  - Subquery detection and comparison
- 🎯 **User-Friendly Notices**: Clear, categorized difference summaries with severity levels

### UI Features
- 📋 **Tabbed Results View**: Organized comparison results with tabs for:
  - Difference Notices
  - Beautified SQL
  - SQL with Line Numbers
  - Text Diff
- ⚠️ **Smart Notifications**: Toast notifications with color-coded alerts
- 🔧 **Single Query Validator**: Popup dialog for validating individual SQL queries
- ⚙️ **Configurable Options**: 
  - SQL Dialect selection (auto, T-SQL, PostgreSQL, MySQL, and more)
  - Whitespace handling
  - Case sensitivity
  - Line numbers toggle
  - Text diff toggle
  - Semantic analysis toggle
- 🌐 **Multi-Dialect Support**: Support for 9+ SQL dialects with auto-detection
- 🚫 **No Database Required**: Pure string/AST comparison
- 🏠 **100% Local**: No cloud services or authentication needed

## Validation Features

The app validates SQL queries before comparison and detects:
- ❌ Empty or whitespace-only queries
- ❌ Syntax errors with detailed error messages
- ❌ Unbalanced parentheses
- ❌ Unbalanced quotes (single and double)
- ❌ Common SQL keyword typos (SELCT → SELECT, FORM → FROM, etc.)
- ✅ Structural validation of parsed queries

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) for dependency management

## Quick Start

```bash
# 1. Install dependencies
make setup

# 2. Run the app
make run

# 3. Open your browser (usually http://localhost:8501)
```

## Usage

### Running the App

```bash
make run
```

Or directly:

```bash
uv run streamlit run src/sql_diff_ui/app.py
```

### Running Tests

```bash
make test
```

Or with pytest options:

```bash
uv run pytest tests/ -v
uv run pytest tests/test_diff_engine.py::test_compare_sql_select_column_added -v
```

### Demo Scripts

Run the validation demo to see SQL validation and beautification in action:

```bash
uv run python demo_validator.py
```

Run the comparison demo:

```bash
uv run python demo.py
```

### Code Quality

```bash
# Format code
make fmt

# Lint code
make lint

# Clean cache files
make clean
```

## Project Structure

```
sql_diff_ui/
├── src/sql_diff_ui/
│   ├── __init__.py
│   ├── app.py           # Streamlit UI
│   ├── diff_engine.py   # Core comparison logic
│   ├── sql_validator.py # SQL validation & beautification
│   └── models.py        # Data models
├── tests/
│   ├── __init__.py
│   ├── test_diff_engine.py
│   ├── test_validator.py
│   └── test_subqueries.py
├── demo.py              # Demo script for comparison
├── demo_validator.py    # Demo script for validation
├── pyproject.toml       # PEP 621 project config
├── Makefile
└── README.md
```

## How It Works

### SQL Validation

Before comparison, each SQL query is validated:
1. **Empty Check**: Verifies the query is not empty or whitespace-only
2. **Parse Check**: Attempts to parse the SQL using sqlglot
3. **Structural Validation**: Checks for:
   - Balanced parentheses
   - Balanced quotes
   - Common keyword typos
4. **Error Reporting**: Provides clear, actionable error messages with line numbers when available

### SQL Beautification

Valid SQL is automatically beautified:
- Proper indentation and line breaks
- Consistent keyword casing
- Normalized spacing around operators
- Clean formatting of complex queries (subqueries, joins, etc.)

### Text Diff

Uses Python's `difflib` to generate unified diffs with options to:
- Ignore whitespace
- Compare line-by-line with context

### Semantic Diff

1. **Parse**: Uses `sqlglot` to parse SQL into an Abstract Syntax Tree (AST)
2. **Extract**: Extracts structured components (SELECT, FROM, JOIN, WHERE, etc.)
3. **Compare**: Compares components element-by-element
4. **Generate Notices**: Creates human-friendly difference descriptions

### Supported SQL Dialects

- Auto-detect (default)
- PostgreSQL
- MySQL
- SQLite
- BigQuery
- Snowflake

## Example Notices

The app generates notices like:

- ℹ️ [SELECT] Added column/expression: `phone`
- ⚠️ [SELECT] Removed column/expression: `email`
- ℹ️ [JOIN] Added JOIN: LEFT JOIN orders ON users.id = orders.user_id
- ⚠️ [WHERE] Removed WHERE condition: `status = 'active'`
- ℹ️ [GROUP_BY] Added GROUP BY column: category
- ℹ️ [ORDER_BY] Added ORDER BY: created_at DESC
- ℹ️ [LIMIT] Changed LIMIT from 10 to 20

## Development

### Adding New Features

1. Add logic to [diff_engine.py](src/sql_diff_ui/diff_engine.py)
2. Update models in [models.py](src/sql_diff_ui/models.py) if needed
3. Add tests in [tests/test_diff_engine.py](tests/test_diff_engine.py)
4. Update UI in [app.py](src/sql_diff_ui/app.py)

### Testing

```bash
# Run all tests
make test

# Run with coverage
uv run pytest tests/ --cov=src/sql_diff_ui --cov-report=html

# Run specific test
uv run pytest tests/test_diff_engine.py::test_compare_sql_where_predicate_added -v
```

### Code Style

This project uses:
- **ruff** for linting and formatting
- **Type hints** everywhere
- **Docstrings** for public functions

## Limitations

- Parses SELECT queries primarily (INSERT/UPDATE/DELETE/DDL support varies)
- Requires valid SQL syntax for semantic diff (falls back to text diff on errors)
- Complex subqueries may not be fully decomposed
- Expression equivalence uses string matching after normalization

## License

MIT

## Credits

Built with:
- [Streamlit](https://streamlit.io/) - Web UI framework
- [sqlglot](https://github.com/tobymao/sqlglot) - SQL parser and transpiler
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager
