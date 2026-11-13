def validate_sql_safety(sql_query: str) -> tuple[bool, str]:
    """Validates that the SQL query is strictly read-only and safe."""
    sql_upper = sql_query.upper()
    forbidden_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "REPLACE"]
    
    for word in forbidden_keywords:
        if word in sql_upper:
            return False, f"Security Violation: Query contains forbidden keyword '{word}'."
            
    if not sql_upper.strip().startswith("SELECT"):
        return False, "Security Violation: Only SELECT read-only queries are permitted."
        
    return True, ""