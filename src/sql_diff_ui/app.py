"""Streamlit UI for SQL comparison."""

import streamlit as st

from sql_diff_ui.diff_engine import compare_sql
from sql_diff_ui.models import Severity

# Page config
st.set_page_config(
    page_title="SQL Diff UI",
    page_icon="🔍",
    layout="wide",
)

# Title and description
st.title("🔍 SQL Query Comparison Tool")
st.markdown("Compare two SQL queries and see **semantic differences** with human-friendly notices.")

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

# Options row
st.markdown("---")
st.subheader("⚙️ Comparison Options")

col_opt1, col_opt2, col_opt3, col_opt4, col_opt5 = st.columns(5)

with col_opt1:
    normalize_sql = st.checkbox("Normalize SQL", value=True, help="Normalize SQL formatting")

with col_opt2:
    ignore_whitespace = st.checkbox(
        "Ignore whitespace", value=True, help="Ignore whitespace differences in text diff"
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
    dialect = st.selectbox(
        "SQL Dialect",
        options=["auto", "postgres", "mysql", "sqlite", "bigquery", "snowflake"],
        index=0,
        help="SQL dialect for parsing",
    )

# Compare button
st.markdown("---")
if st.button("🔍 Compare SQL Queries", type="primary", use_container_width=True):
    if not sql_a.strip() or not sql_b.strip():
        st.error("⚠️ Please provide both SQL queries to compare.")
    else:
        with st.spinner("Comparing SQL queries..."):
            result = compare_sql(
                sql_a=sql_a,
                sql_b=sql_b,
                normalize=normalize_sql,
                ignore_whitespace=ignore_whitespace,
                case_insensitive_keywords=case_insensitive,
                semantic_diff=semantic_diff,
                dialect=dialect,
            )

            # Store result in session state
            st.session_state["comparison_result"] = result

# Display results if available
if "comparison_result" in st.session_state:
    result = st.session_state["comparison_result"]

    st.markdown("---")
    st.header("📊 Comparison Results")

    # Section 1: Diff Notices
    st.subheader("📋 Difference Notices")

    if result.parse_error:
        st.warning(f"⚠️ {result.parse_error}")
        st.info("Showing text diff only.")

    if result.notices:
        # Count by severity
        info_count = sum(1 for n in result.notices if n.severity == Severity.INFO)
        warn_count = sum(1 for n in result.notices if n.severity == Severity.WARN)

        st.markdown(
            f"**Found {len(result.notices)} differences** "
            f"({info_count} info, {warn_count} warnings)"
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
        st.success("✅ No semantic differences found. The queries are structurally identical.")

    # Section 2: Text Diff
    st.markdown("---")
    st.subheader("📝 Text Diff")

    if result.text_diff:
        # Display diff in a code block
        st.code(result.text_diff, language="diff", line_numbers=False)
    else:
        st.info("No text differences found.")

    # Optional: Show normalized SQL if available
    if result.sql_a_normalized and result.sql_b_normalized:
        with st.expander("🔧 View Normalized SQL"):
            col_norm1, col_norm2 = st.columns(2)

            with col_norm1:
                st.markdown("**Normalized SQL A**")
                st.code(result.sql_a_normalized, language="sql")

            with col_norm2:
                st.markdown("**Normalized SQL B**")
                st.code(result.sql_b_normalized, language="sql")

# Footer
st.markdown("---")
st.caption("Built with Streamlit + sqlglot • No database connection required")
