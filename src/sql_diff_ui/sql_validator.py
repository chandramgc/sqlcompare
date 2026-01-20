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

        # Check for unbalanced parentheses - track line numbers
        open_parens = []  # Stack to track opening parens with line numbers
        unmatched_close_parens = []  # List of closing parens with no matching open
        
        lines = sql.split('\n')
        for line_num, line in enumerate(lines, 1):
            for char_pos, char in enumerate(line):
                if char == '(':
                    open_parens.append((line_num, char_pos))
                elif char == ')':
                    if open_parens:
                        open_parens.pop()  # Match with opening paren
                    else:
                        unmatched_close_parens.append((line_num, char_pos))  # Extra closing paren
        
        # Report unbalanced parentheses with line numbers
        total_open = sum(1 for line in lines for c in line if c == '(')
        total_close = sum(1 for line in lines for c in line if c == ')')
        
        if open_parens:
            # Unmatched opening parentheses
            unmatched_lines = sorted(set([line for line, pos in open_parens]))[:5]
            line_info = f" - Missing closing ')' - Check lines: {', '.join(map(str, unmatched_lines))}"
            errors.append(
                ValidationError(
                    f"Unbalanced parentheses: {total_open} opening, {total_close} closing{line_info}",
                    line=unmatched_lines[0] if unmatched_lines else None
                )
            )
        
        if unmatched_close_parens:
            # Extra closing parentheses
            unmatched_lines = sorted(set([line for line, pos in unmatched_close_parens]))[:5]
            line_info = f" - Extra closing ')' on lines: {', '.join(map(str, unmatched_lines))}"
            errors.append(
                ValidationError(
                    f"Unbalanced parentheses: {total_open} opening, {total_close} closing{line_info}",
                    line=unmatched_lines[0] if unmatched_lines else None
                )
            )

        # Check for unbalanced quotes - track line numbers
        single_quote_lines = []
        double_quote_lines = []
        
        for line_num, line in enumerate(lines, 1):
            # Count non-escaped single quotes
            single_quotes = 0
            double_quotes = 0
            i = 0
            while i < len(line):
                if line[i] == "'" and (i == 0 or line[i-1] != '\\'):
                    single_quotes += 1
                elif line[i] == '"' and (i == 0 or line[i-1] != '\\'):
                    double_quotes += 1
                i += 1
            
            if single_quotes % 2 != 0:
                single_quote_lines.append(line_num)
            if double_quotes % 2 != 0:
                double_quote_lines.append(line_num)
        
        # Report unbalanced quotes with line numbers
        if single_quote_lines:
            lines_info = f" on lines: {', '.join(map(str, single_quote_lines[:10]))}"
            if len(single_quote_lines) > 10:
                lines_info += f" (and {len(single_quote_lines) - 10} more)"
            errors.append(
                ValidationError(
                    f"Unbalanced single quotes{lines_info}",
                    line=single_quote_lines[0]
                )
            )

        if double_quote_lines:
            lines_info = f" on lines: {', '.join(map(str, double_quote_lines[:10]))}"
            if len(double_quote_lines) > 10:
                lines_info += f" (and {len(double_quote_lines) - 10} more)"
            errors.append(
                ValidationError(
                    f"Unbalanced double quotes{lines_info}",
                    line=double_quote_lines[0]
                )
            )

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

        # Check for empty SQL clauses (keywords without values)
        # Note: Need to handle multi-line SQL where a keyword appears on its own line
        # but the values continue on the next line
        sql_lines = sql.upper().split('\n')
        
        for i, line in enumerate(sql_lines):
            line_stripped = line.strip()
            
            # Skip empty lines
            if not line_stripped:
                continue
            
            # Check if the next line exists and has content (for multi-line statements)
            next_line_has_content = False
            next_line_is_keyword = False
            
            if i + 1 < len(sql_lines):
                next_line = sql_lines[i + 1].strip()
                # Check if next line is a SQL keyword/clause
                next_line_is_keyword = bool(next_line) and re.match(
                    r'^(SELECT|FROM|WHERE|GROUP\s+BY|GROUP|ORDER\s+BY|ORDER|BY|HAVING|LIMIT|OFFSET|UNION|JOIN|LEFT|RIGHT|INNER|OUTER|CROSS|AND|OR|THEN|ELSE|END|WHEN|CASE)\b',
                    next_line
                )
                # Check if next line has actual content (not just another keyword or empty)
                next_line_has_content = bool(next_line) and not next_line_is_keyword
            
            # If current line is a clause keyword and next line is also a keyword (or empty),
            # then current clause is empty
            is_clause_empty = not next_line_has_content
            
            # Check for incomplete multi-word keywords
            # ORDER without BY
            if re.match(r'^ORDER\s*$', line_stripped):
                # Check if next line starts with BY
                if i + 1 < len(sql_lines):
                    next_line = sql_lines[i + 1].strip()
                    if not re.match(r'^BY\b', next_line):
                        errors.append(
                            ValidationError(f"Incomplete keyword 'ORDER' - missing 'BY' (should be 'ORDER BY')", line=i+1)
                        )
                else:
                    errors.append(
                        ValidationError(f"Incomplete keyword 'ORDER' - missing 'BY' (should be 'ORDER BY')", line=i+1)
                    )
            
            # GROUP without BY
            if re.match(r'^GROUP\s*$', line_stripped):
                # Check if next line starts with BY
                if i + 1 < len(sql_lines):
                    next_line = sql_lines[i + 1].strip()
                    if not re.match(r'^BY\b', next_line):
                        errors.append(
                            ValidationError(f"Incomplete keyword 'GROUP' - missing 'BY' (should be 'GROUP BY')", line=i+1)
                        )
                else:
                    errors.append(
                        ValidationError(f"Incomplete keyword 'GROUP' - missing 'BY' (should be 'GROUP BY')", line=i+1)
                    )
            
            # Only flag as empty if there's no content on the next line OR next line is another keyword
            # Check for SELECT with nothing after it (on same line or next line)
            if re.match(r'^SELECT\s*$', line_stripped) and is_clause_empty:
                errors.append(
                    ValidationError(f"Empty SELECT clause - no columns specified", line=i+1)
                )
            
            # Check for FROM with nothing after it
            if re.match(r'^FROM\s*$', line_stripped) and is_clause_empty:
                errors.append(
                    ValidationError(f"Empty FROM clause - no table specified", line=i+1)
                )
            
            # Check for WHERE with nothing after it
            if re.match(r'^WHERE\s*$', line_stripped) and is_clause_empty:
                errors.append(
                    ValidationError(f"Empty WHERE clause - no condition specified", line=i+1)
                )
            
            # Check for ORDER BY with nothing after it
            if re.match(r'^ORDER\s+BY\s*$', line_stripped) and is_clause_empty:
                errors.append(
                    ValidationError(f"Empty ORDER BY clause - no columns specified", line=i+1)
                )
            
            # Check for GROUP BY with nothing after it
            if re.match(r'^GROUP\s+BY\s*$', line_stripped) and is_clause_empty:
                errors.append(
                    ValidationError(f"Empty GROUP BY clause - no columns specified", line=i+1)
                )
            
            # Check for LIMIT with nothing after it
            if re.match(r'^LIMIT\s*$', line_stripped) and is_clause_empty:
                errors.append(
                    ValidationError(f"Empty LIMIT clause - no value specified", line=i+1)
                )
            
            # Check for OFFSET with nothing after it
            if re.match(r'^OFFSET\s*$', line_stripped) and is_clause_empty:
                errors.append(
                    ValidationError(f"Empty OFFSET clause - no value specified", line=i+1)
                )
            
            # Check for HAVING with nothing after it
            if re.match(r'^HAVING\s*$', line_stripped) and is_clause_empty:
                errors.append(
                    ValidationError(f"Empty HAVING clause - no condition specified", line=i+1)
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
