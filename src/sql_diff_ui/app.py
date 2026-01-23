"""Streamlit UI for SQL comparison."""

import streamlit as st

from sql_diff_ui.diff_engine import compare_sql
from sql_diff_ui.models import Severity
from sql_diff_ui.sql_validator import SQLValidator


@st.dialog("✅ SQL Validator")
def validate_single_query():
    """Dialog for validating a single SQL query."""
    st.markdown("Enter your SQL query below to validate syntax and structure.")
    
    # Dialect selection in dialog
    val_dialect = st.selectbox(
        "SQL Dialect",
        options=["auto", "tsql", "postgres", "mysql", "sqlite", "bigquery", "snowflake", "oracle", "redshift"],
        index=0,
        help="Select the SQL dialect for validation",
        key="validator_dialect"
    )
    
    # Text area for SQL input
    sql_input = st.text_area(
        "SQL Query",
        height=200,
        placeholder="Enter your SQL query here...",
        key="validator_sql"
    )
    
    # Validate button
    if st.button("🔍 Validate SQL", type="primary", use_container_width=True):
        if not sql_input.strip():
            st.error("⚠️ Please enter a SQL query to validate.")
        else:
            # Create validator with selected dialect
            validator = SQLValidator(dialect=val_dialect)
            
            # Validate the SQL
            with st.spinner("Validating SQL..."):
                is_valid, errors = validator.validate_sql(sql_input)
            
            # Show results
            if is_valid:
                st.success("✅ **SQL is Valid!**")
                st.balloons()
                
                # Try to beautify and show
                try:
                    beautified = validator.beautify_sql(sql_input)
                    with st.expander("🎨 View Beautified SQL", expanded=True):
                        st.code(beautified, language="sql")
                except Exception:
                    pass
            else:
                st.error("❌ **SQL Validation Failed**")
                st.markdown("**Errors found:**")
                for error in errors:
                    if hasattr(error, 'line') and error.line:
                        st.error(f"  **Line {error.line}:** {error.message}")
                    else:
                        st.error(f"  • {error}")
                
                # Show dialect warning if using auto-detect
                if val_dialect == "auto":
                    st.warning(
                        "⚠️ **Dialect Auto-Detection Failed**\n\n"
                        "Please select the specific SQL dialect from the dropdown above."
                    )

# Page config
st.set_page_config(
    page_title="SQL Diff UI",
    page_icon="🔍",
    layout="wide",
)

# Custom CSS for toast notification with light yellow background
st.markdown(
    """
    <style>
    /* Style for toast notifications with warning icon */
    div[data-testid="stToast"] {
        background-color: #fff8dc !important;
        border-left: 5px solid #ffd700 !important;
    }
    
    div[data-testid="stToast"] > div {
        background-color: #fff8dc !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title and description
st.title("🔍 SQL Query Comparison Tool")
st.markdown("Compare two SQL queries and see **semantic differences** with human-friendly notices.")
st.caption("💡 Tip: For SQL Server queries with [bracket notation], select 'tsql' dialect from options below")

# Options row with title and validator button in same line
col_options_title, col_validator = st.columns([5, 1])
with col_options_title:
    st.subheader("⚙️ Comparison Options")
with col_validator:
    # Add empty space and button to align with subheader height
    st.markdown("")  # Empty markdown for spacing
    if st.button("✅ Validate SQL", use_container_width=True, help="Validate a single SQL query", type="secondary"):
        validate_single_query()

col_opt1, col_opt2, col_opt3, col_opt4, col_opt5, col_opt6 = st.columns(6)

with col_opt1:
    dialect = st.selectbox(
        "SQL Dialect",
        options=["auto", "tsql", "postgres", "mysql", "sqlite", "bigquery", "snowflake", "oracle", "redshift"],
        index=0,
        help="Select 'tsql' for SQL Server/T-SQL syntax (required for bracket notation like [Column Name])",
    )

with col_opt2:
    ignore_whitespace = st.checkbox(
        "Ignore whitespace", value=True, help="Ignore whitespace differences in comparison"
    )

with col_opt3:
    case_insensitive = st.checkbox(
        "Case-insensitive keywords",
        value=True,
        help="Treat SQL keywords as case-insensitive",
    )

with col_opt4:
    semantic_diff = st.checkbox(
        "Semantic diff enabled",
        value=True,
        help="Enable semantic/structural analysis",
    )

with col_opt5:
    show_line_numbers = st.checkbox(
        "Show line numbers",
        value=True,
        help="Display SQL queries with line numbers",
    )

with col_opt6:
    show_text_diff = st.checkbox(
        "Show text diff",
        value=True,
        help="Display text difference between queries",
    )

st.markdown("---")

# Layout: Two columns for SQL inputs
col1, col2 = st.columns(2)

with col1:
    st.subheader("SQL A")
    default_sql_a = (
        "SELECT id, name, email\n"
        "FROM users\n"
        "WHERE status = 'active'\n"
        "ORDER BY created_at DESC\n"
        "LIMIT 10"
    )
    sql_a = st.text_area(
        "SQL A",
        value=default_sql_a,
        height=250,
        key="sql_a",
        label_visibility="collapsed",
    )

with col2:
    st.subheader("SQL B")
    default_sql_b = (
        "SELECT id, name, phone\n"
        "FROM users\n"
        "LEFT JOIN orders ON users.id = orders.user_id\n"
        "WHERE status = 'active' AND role = 'customer'\n"
        "ORDER BY created_at DESC\n"
        "LIMIT 20"
    )
    sql_b = st.text_area(
        "SQL B",
        value=default_sql_b,
        height=250,
        key="sql_b",
        label_visibility="collapsed",
    )

# Compare button
st.markdown("---")
if st.button("🔍 Compare SQL Queries", type="primary", use_container_width=True):
    if not sql_a.strip() or not sql_b.strip():
        st.error("⚠️ Please provide both SQL queries to compare.")
    else:
        # Create validator
        validator = SQLValidator(dialect=dialect)

        # Validate and beautify SQL A
        with st.spinner("Validating SQL A..."):
            is_valid_a, beautified_a, errors_a = validator.validate_and_beautify(sql_a)

        # Validate and beautify SQL B
        with st.spinner("Validating SQL B..."):
            is_valid_b, beautified_b, errors_b = validator.validate_and_beautify(sql_b)

        # Display validation errors only (no success messages)
        validation_errors = []
        
        if not is_valid_a:
            validation_errors.append(("SQL A", errors_a))
        if not is_valid_b:
            validation_errors.append(("SQL B", errors_b))
        
        # Show errors if any
        if validation_errors:
            for sql_name, errors in validation_errors:
                st.error(f"❌ **{sql_name} has validation errors:**")
                for error in errors:
                    # Check if error has line number for better formatting
                    if hasattr(error, 'line') and error.line:
                        st.error(f"  **Line {error.line}:** {error.message}")
                    else:
                        st.error(f"  • {error}")
                
                # Show dialect warning if using auto-detect and parsing failed
                if dialect == "auto":
                    st.warning(
                        "⚠️ **Dialect Auto-Detection Failed**\n\n"
                        "The query could not be parsed with auto-detection. "
                        "Please select the specific SQL dialect from the **SQL Dialect** dropdown above:\n"
                        "- **tsql** for SQL Server/T-SQL\n"
                        "- **postgres** for PostgreSQL\n"
                        "- **mysql** for MySQL\n"
                        "- **oracle** for Oracle\n"
                        "- Other dialects as needed"
                    )

        # Only proceed with comparison if both queries are valid
        if is_valid_a and is_valid_b:
            with st.spinner("Comparing SQL queries..."):
                # Use beautified SQL for comparison
                result = compare_sql(
                    sql_a=beautified_a,
                    sql_b=beautified_b,
                    normalize=True,
                    ignore_whitespace=ignore_whitespace,
                    case_insensitive_keywords=case_insensitive,
                    semantic_diff=semantic_diff,
                    dialect=dialect,
                )

                # Store result in session state
                st.session_state["comparison_result"] = result
                # Store beautified SQL for tabs
                st.session_state["beautified_a"] = beautified_a
                st.session_state["beautified_b"] = beautified_b
                # Clear validation error flag
                st.session_state["has_validation_errors"] = False
            
            # Show comparison status as toast notification
            if result.notices:
                st.toast(
                    f"SQL Queries Do Not Match! Found {len(result.notices)} differences.",
                    icon="⚠️"
                )
            else:
                st.toast("SQL Queries Match! Queries are structurally identical.", icon="✅")
        else:
            st.warning("⚠️ Cannot compare SQL queries with validation errors. Please fix the errors above and try again.")
            # Set validation error flag and show line numbers view
            st.session_state["has_validation_errors"] = True
            # Clear previous comparison results
            if "comparison_result" in st.session_state:
                del st.session_state["comparison_result"]

# Display results if available or if there are validation errors
if "comparison_result" in st.session_state or st.session_state.get("has_validation_errors", False):
    st.markdown("---")
    st.header("📊 Comparison Results")
    
    st.markdown("")  # Add spacing
    
    # If validation errors, show only line numbers tab
    if st.session_state.get("has_validation_errors", False):
        # SQL with Line Numbers view only when validation errors
        if show_line_numbers:
            view_col1, view_col2 = st.columns(2)
            
            with view_col1:
                st.markdown("**SQL A with line numbers**")
                lines = sql_a.split('\n')
                # Filter out completely blank lines but keep lines with whitespace
                numbered_sql = '\n'.join([f"{i+1:4d} | {line}" for i, line in enumerate(lines) if line.strip() or line])
                st.code(numbered_sql, language="sql", line_numbers=False)
            
            with view_col2:
                st.markdown("**SQL B with line numbers**")
                lines = sql_b.split('\n')
                # Filter out completely blank lines but keep lines with whitespace
                numbered_sql = '\n'.join([f"{i+1:4d} | {line}" for i, line in enumerate(lines) if line.strip() or line])
                st.code(numbered_sql, language="sql", line_numbers=False)
        else:
            st.info("Enable 'Show line numbers' option to view SQL queries with line numbers.")
    
    # If no validation errors, show full comparison results with tabs
    elif "comparison_result" in st.session_state:
        result = st.session_state["comparison_result"]
        beautified_a = st.session_state.get("beautified_a", "")
        beautified_b = st.session_state.get("beautified_b", "")

        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Difference Notices", "🎨 View Beautified SQL", "📝 SQL with Line Numbers", "📊 Text Diff"])
        
        with tab1:
            # Difference Notices tab
            if result.parse_error:
                st.warning(f"⚠️ {result.parse_error}")
                st.info("Showing text diff only.")

            if result.notices:
                # Count by severity
                info_count = sum(1 for n in result.notices if n.severity == Severity.INFO)
                warn_count = sum(1 for n in result.notices if n.severity == Severity.WARN)

                st.markdown(
                    f"**Breakdown:** {info_count} info, {warn_count} warnings"
                )

                # Group notices by category
                categories = {}
                for notice in result.notices:
                    cat = notice.category.value
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(notice)

                # Display notices by category
                for category, notices in sorted(categories.items()):
                    with st.expander(f"**{category}** ({len(notices)} changes)", expanded=True):
                        for notice in notices:
                            severity_icon = "⚠️" if notice.severity == Severity.WARN else "ℹ️"
                            severity_color = "orange" if notice.severity == Severity.WARN else "blue"

                            st.markdown(f":{severity_color}[{severity_icon}] **{notice.summary}**")
                            if notice.details:
                                st.caption(notice.details)
            else:
                st.success("✅ No differences found. The queries are structurally identical.")
        
        with tab2:
            # Beautified SQL tab
            beautify_col1, beautify_col2 = st.columns(2)

            with beautify_col1:
                st.markdown("**Beautified SQL A**")
                st.code(beautified_a, language="sql")

            with beautify_col2:
                st.markdown("**Beautified SQL B**")
                st.code(beautified_b, language="sql")
        
        with tab3:
            # SQL with Line Numbers tab
            if show_line_numbers:
                view_col1, view_col2 = st.columns(2)
                
                with view_col1:
                    st.markdown("**SQL A with line numbers**")
                    lines = sql_a.split('\n')
                    # Filter out completely blank lines but keep lines with whitespace
                    numbered_sql = '\n'.join([f"{i+1:4d} | {line}" for i, line in enumerate(lines) if line.strip() or line])
                    st.code(numbered_sql, language="sql", line_numbers=False)
                
                with view_col2:
                    st.markdown("**SQL B with line numbers**")
                    lines = sql_b.split('\n')
                    # Filter out completely blank lines but keep lines with whitespace
                    numbered_sql = '\n'.join([f"{i+1:4d} | {line}" for i, line in enumerate(lines) if line.strip() or line])
                    st.code(numbered_sql, language="sql", line_numbers=False)
            else:
                st.info("Enable 'Show line numbers' option to view SQL queries with line numbers.")
        
        with tab4:
            # Text Diff tab
            if show_text_diff and result.text_diff:
                st.caption("Lines with '-' (red) are removed from SQL A, lines with '+' (green) are added in SQL B")
                # Show diff without line numbers to preserve color coding
                st.code(result.text_diff, language="diff")
            elif not show_text_diff:
                st.info("Enable 'Show text diff' option to view text differences.")
            else:
                st.info("No text differences to display.")

# Footer
st.markdown("---")
st.caption("Built with Streamlit + sqlglot • No database connection required")
