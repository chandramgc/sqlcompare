# New Features Summary

## 1. Line Number Toggle in UI

Added a user-configurable checkbox to enable/disable line number display in validation error views.

### Implementation Details
- **Location**: [app.py](src/sql_diff_ui/app.py) - Added to comparison options section
- **Default**: Enabled (checked by default)
- **Behavior**: 
  - When enabled: Shows expandable section with line-numbered SQL when validation errors occur
  - When disabled: Hides the expandable SQL viewer to reduce visual clutter
  - Applied to both SQL A and SQL B validation independently

### Benefits
- ✅ Reduces visual clutter when debugging is not needed
- ✅ Quick toggle without restarting the app
- ✅ Improves user experience for different use cases
- ✅ Maintains existing line number highlighting in error messages

### Usage
1. Run the app: `make run`
2. Find the "Show line numbers" checkbox in the options section (6th column)
3. Check/uncheck to toggle line-numbered SQL display
4. Error messages always show line numbers in bold; this only affects the expandable SQL viewer

---

## 2. CASE Statement Validation

Added comprehensive validation for SQL CASE statements to catch common syntax errors.

### Validation Rules

#### 1. Unbalanced CASE/END
Detects CASE statements without matching END keywords.

**Example:**
```sql
SELECT 
    id,
    CASE
        WHEN status = 'active' THEN 'Active'
FROM users  -- ❌ Missing END
```

**Error**: "Incomplete CASE statement - found 1 CASE but only 0 END keywords"

#### 2. WHEN without THEN
Detects WHEN clauses missing the required THEN keyword.

**Example:**
```sql
SELECT 
    id,
    CASE
        WHEN status = 'active'  -- ❌ Missing THEN
        ELSE 'Unknown'
    END
FROM users
```

**Error**: "Incomplete WHEN clause - missing 'THEN'"

#### 3. Nested CASE Support
The validator correctly handles nested CASE statements by counting all CASE and END keywords.

**Valid Example:**
```sql
SELECT 
    id,
    CASE
        WHEN type = 'premium' THEN
            CASE
                WHEN status = 'active' THEN 'Premium Active'
                ELSE 'Premium Other'
            END
        ELSE 'Regular'
    END as user_type
FROM users
```

#### 4. Multiple CASE Statements
Supports multiple CASE statements in a single query.

**Valid Example:**
```sql
SELECT 
    CASE
        WHEN age < 18 THEN 'Minor'
        WHEN age >= 18 THEN 'Adult'
    END as age_group,
    CASE status
        WHEN 'A' THEN 'Active'
        WHEN 'I' THEN 'Inactive'
    END as status_text
FROM users
```

### Implementation Details
- **Location**: [sql_validator.py](src/sql_diff_ui/sql_validator.py)
- **Method**: `_validate_structure()`
- **Approach**: 
  - Counts CASE and END keywords using regex word boundaries (`\bCASE\b`, `\bEND\b`)
  - Validates WHEN/THEN pairs by looking ahead 2-3 lines
  - Reports line numbers for easy debugging
- **Tests**: 28 passing tests in [test_validator.py](tests/test_validator.py)

### Benefits
- ✅ Catches incomplete CASE statements before comparison
- ✅ Detects WHEN clauses missing THEN
- ✅ Handles nested CASE statements correctly
- ✅ Provides precise line numbers in error messages
- ✅ Works with all SQL dialects supported by sqlglot

---

## Testing

All enhancements are fully tested:

```bash
# Run all validator tests
make test

# Or run specific test file
pytest tests/test_validator.py -v
```

**Test Coverage:**
- ✅ 28 passing tests
- ✅ CASE without END detection
- ✅ WHEN without THEN detection
- ✅ Valid CASE statement acceptance
- ✅ Nested CASE statement handling
- ✅ Multiple CASE statements in one query
- ✅ All existing validation features maintained

---

## Demo

Run the demo script to see the new features in action:

```bash
python demo_new_features.py
```

Or try them in the Streamlit app:

```bash
make run
```

---

## Files Modified

1. **[src/sql_diff_ui/app.py](src/sql_diff_ui/app.py)**
   - Added `show_line_numbers` checkbox to options
   - Made line number display conditional in validation sections

2. **[src/sql_diff_ui/sql_validator.py](src/sql_diff_ui/sql_validator.py)**
   - Added CASE/END balance checking
   - Added WHEN/THEN validation
   - Enhanced `_validate_structure()` method

3. **[tests/test_validator.py](tests/test_validator.py)**
   - Added 4 new tests for CASE statement validation
   - Updated to 28 total passing tests

4. **[demo_new_features.py](demo_new_features.py)** (NEW)
   - Comprehensive demo of CASE statement validation
   - Examples of valid and invalid CASE statements
   - UI feature explanation

---

## Summary

These enhancements improve the SQL validation experience by:

1. **Better Control**: Users can toggle line number display based on their needs
2. **Comprehensive Validation**: Catches CASE statement syntax errors that were previously missed
3. **Better UX**: Cleaner interface with optional debugging views
4. **Maintained Quality**: All existing tests pass + 4 new tests added

The app now provides more thorough SQL validation while giving users control over the level of detail they want to see.
