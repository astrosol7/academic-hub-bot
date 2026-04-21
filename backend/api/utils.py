import os

def resolve_limit(requested: int | None, role: str = "public") -> int:
    """
    Safely resolve the limit for a query, enforcing configurable upper bounds.
    """
    default_limit = int(os.getenv("API_DEFAULT_LIMIT", "20"))
    
    if role == "admin":
        max_limit = int(os.getenv("API_MAX_LIMIT_ADMIN", "1000"))
    else:
        max_limit = int(os.getenv("API_MAX_LIMIT_PUBLIC", "100"))

    if requested is None:
        return default_limit
    
    # Enforce safe bounds: 1 <= limit <= max_limit
    return min(max(requested, 1), max_limit)
