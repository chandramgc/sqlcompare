.PHONY: setup run test fmt lint clean help

# Ensure uv is in PATH
export PATH := $(HOME)/.local/bin:$(PATH)

# Default target
help:
	@echo "SQL Diff UI - Available make targets:"
	@echo "  make setup    - Install dependencies using uv"
	@echo "  make run      - Run the Streamlit app"
	@echo "  make test     - Run pytest tests"
	@echo "  make fmt      - Format code with ruff"
	@echo "  make lint     - Lint code with ruff"
	@echo "  make clean    - Remove cache files"

# Install dependencies
setup:
	@echo "Installing dependencies with uv..."
	uv sync --extra dev
	@echo "Setup complete! Run 'make run' to start the app."

# Run the Streamlit app
run:
	@echo "Starting Streamlit app..."
	uv run streamlit run src/sql_diff_ui/app.py

# Run tests
test:
	@echo "Running tests..."
	uv run pytest tests/ -v

# Format code
fmt:
	@echo "Formatting code..."
	uv run ruff format src/ tests/

# Lint code
lint:
	@echo "Linting code..."
	uv run ruff check src/ tests/

# Clean cache files
clean:
	@echo "Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean complete!"
