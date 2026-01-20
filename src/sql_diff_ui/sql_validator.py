"""SQL validation and beautification utilities."""

from typing import Tuple

import sqlglot
from sqlglot.errors import ParseError


class ValidationError:
    """Represents a SQL validation error."""

    def __init__(self, message: str, line: int = None, column: int = None):
        """
        Initialize validation error.

        Args:
            message: Error message
            line: Line number where error occurred (if known)
            column: Column number where error occurred (if known)
        """
        self.message = message
        self.line = line
        self.column = column

    def __str__(self) -> str:
        """Return formatted error message."""
        if self.line and self.column:
            return f"Line {self.line}, Column {self.column}: {self.message}"
        elif self.line:
            return f"Line {self.line}: {self.message}"
        return self.message


class SQLValidator:
    """Validates and beautifies SQL queries."""

    def __init__(self, dialect: str = "auto"):
        """
        Initialize SQL validator.

        Args:
            dialect: SQL dialect to use for parsing
        """
        self.dialect = None if dialect == "auto" else dialect

    def validate_sql(self, sql: str) -> Tuple[bool, list[ValidationError]]:
        """
        Validate SQL syntax.

        Args:
            sql: SQL query string to validate

        Returns:
            Tuple of (is_valid, list of validation errors)
        """
        errors = []

        # Check if SQL is empty or just whitespace
        if not sql or not sql.strip():
            errors.append(ValidationError("SQL query is empty"))
            return False, errors

        # Try to parse the SQL with strict error handling
        try:
            parsed = sqlglot.parse_one(sql, dialect=self.dialect, error_level="raise")

            # Check if parsed successfully
            if parsed is None:
                errors.append(ValidationError("Failed to parse SQL query"))
                return False, errors

            # Additional validation checks
            errors.extend(self._validate_structure(parsed, sql))

            # Try to regenerate SQL - if this fails, there's a parse issue
            try:
                regenerated = parsed.sql()
                # If regenerated SQL is significantly shorter, something was lost in parsing
                if len(regenerated.strip()) < len(sql.strip()) * 0.5:
                    errors.append(
                        ValidationError(
                            "SQL parsing resulted in incomplete query - possible syntax error"
                        )
                    )
            except Exception as e:
                errors.append(ValidationError(f"Failed to regenerate SQL: {str(e)}"))

            if errors:
                return False, errors

            return True, []

        except ParseError as e:
            # Extract error details from ParseError
            error_msg = str(e)

            # Try to extract line/column information if available
            line = None
            column = None

            # ParseError may contain line/column info in the message
            # Format is typically "Error message. Line X, Col: Y"
            if "Line" in error_msg and "Col" in error_msg:
                try:
                    # Extract line number
                    line_match = error_msg.split("Line")[1].split(",")[0].strip()
                    line = int(line_match)
                    # Extract column number
                    col_match = error_msg.split("Col:")[1].split(".")[0].strip()
                    column = int(col_match)
                except (ValueError, IndexError):
                    pass

            errors.append(ValidationError(error_msg, line=line, column=column))
            return False, errors

        except Exception as e:
            errors.append(ValidationError(f"Unexpected error: {type(e).__name__}: {str(e)}"))
            return False, errors

    def _validate_structure(self, parsed, sql: str) -> list[ValidationError]:
        """
        Perform additional structural validation.

        Args:
            parsed: Parsed SQL expression
            sql: Original SQL string

        Returns:
            List of validation errors
        """
        errors = []

        # Check for common SQL issues
        sql_upper = sql.upper()

        # Check for unbalanced parentheses
        if sql.count("(") != sql.count(")"):
            errors.append(
                ValidationError(
                    f"Unbalanced parentheses: {sql.count('(')} opening, {sql.count(')')} closing"
                )
            )

        # Check for unbalanced quotes
        single_quotes = sql.count("'") - sql.count("\\'")
        if single_quotes % 2 != 0:
            errors.append(ValidationError("Unbalanced single quotes"))

        double_quotes = sql.count('"') - sql.count('\\"')
        if double_quotes % 2 != 0:
            errors.append(ValidationError("Unbalanced double quotes"))

        # Check if regenerated SQL loses significant content
        try:
            regenerated = parsed.sql()
            original_tokens = sql.split()
            regenerated_tokens = regenerated.split()
            
            # Check specifically for lost string literals first (most critical)
            import re
            original_strings = re.findall(r"'[^']*'", sql)
            regenerated_strings = re.findall(r"'[^']*'", regenerated)
            
            if len(original_strings) > len(regenerated_strings):
                missing_strings = set(original_strings) - set(regenerated_strings)
                errors.append(
                    ValidationError(
                        f"SQL contains syntax errors - lost string literals during parsing: {', '.join(missing_strings)}"
                    )
                )
            
            # If we lost more than 15% of tokens, something is wrong
            elif len(regenerated_tokens) < len(original_tokens) * 0.85:
                errors.append(
                    ValidationError(
                        "SQL contains syntax errors - significant content lost during parsing"
                    )
                )
        except:
            pass

        # Check for common SQL keywords typos
        common_typos = {
            "SELCT": "SELECT",
            "FORM": "FROM",
            "WHRE": "WHERE",
            "GROPU": "GROUP",
            "ODER": "ORDER",
            "HAVIG": "HAVING",
        }

        for typo, correct in common_typos.items():
            if typo in sql_upper:
                errors.append(ValidationError(f"Possible typo: '{typo}' (did you mean '{correct}'?)"))

        # Check for incomplete WHERE clauses - pattern like: column 'value' without operator
        import re
        # Look for: word followed by string literal without = or other comparison operator
        incomplete_where_pattern = r'\b(\w+)\s+(\'[^\']*\'|\"[^\"]*\")\b'
        matches = re.finditer(incomplete_where_pattern, sql)
        for match in matches:
            # Check if there's a comparison operator before the string
            start_pos = match.start()
            # Look back a few characters to see if there's an operator
            context_start = max(0, start_pos - 10)
            context = sql[context_start:start_pos].strip()
            
            # If no comparison operator found before this pattern, it's likely an error
            if not any(op in context[-3:] for op in ['=', '>', '<', '!', 'IN', 'LIKE']):
                column_name = match.group(1)
                string_value = match.group(2)
                errors.append(
                    ValidationError(
                        f"Incomplete comparison: '{column_name} {string_value}' - missing comparison operator (=, !=, >, <, etc.)"
                    )
                )

        return errors

    def beautify_sql(self, sql: str) -> str:
        """
        Beautify and format SQL query.

        Args:
            sql: SQL query string to beautify

        Returns:
            Beautified SQL string

        Raises:
            ValueError: If SQL cannot be parsed or loses content during parsing
        """
        if not sql or not sql.strip():
            raise ValueError("SQL query is empty")

        try:
            parsed = sqlglot.parse_one(sql, dialect=self.dialect, error_level="raise")
            # Use sqlglot's pretty printing with normalization
            beautified = parsed.sql(pretty=True, normalize=True)
            
            # Check for lost string literals
            import re
            original_strings = re.findall(r"'[^']*'", sql)
            beautified_strings = re.findall(r"'[^']*'", beautified)
            
            if len(original_strings) > len(beautified_strings):
                missing_strings = set(original_strings) - set(beautified_strings)
                raise ValueError(
                    f"SQL parsing resulted in lost string literals: {', '.join(missing_strings)}. "
                    "This indicates a syntax error (possibly missing comparison operator)."
                )
            
            # Verify the beautified SQL is not significantly shorter (indicating parsing issues)
            if len(beautified.strip()) < len(sql.strip()) * 0.5:
                raise ValueError(
                    "SQL parsing resulted in incomplete query - possible syntax error. "
                    "The beautified output is significantly shorter than the input."
                )
            
            return beautified

        except ParseError as e:
            raise ValueError(f"Failed to beautify SQL: {type(e).__name__}: {str(e)}")
        except ValueError:
            # Re-raise ValueError as is
            raise
        except Exception as e:
            raise ValueError(f"Failed to beautify SQL: {type(e).__name__}: {str(e)}")

    def validate_and_beautify(self, sql: str) -> Tuple[bool, str, list[ValidationError]]:
        """
        Validate and beautify SQL in one step.

        Args:
            sql: SQL query string

        Returns:
            Tuple of (is_valid, beautified_sql, validation_errors)
            If validation fails, beautified_sql will be the original SQL
        """
        is_valid, errors = self.validate_sql(sql)

        if is_valid:
            try:
                beautified = self.beautify_sql(sql)
                return True, beautified, []
            except ValueError as e:
                # If beautification fails but validation passed, return original
                errors.append(ValidationError(f"Beautification failed: {str(e)}"))
                return True, sql, errors

        # If validation failed, return original SQL with errors
        return False, sql, errors
