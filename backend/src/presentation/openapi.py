OPENAPI_TAGS: list[dict[str, str]] = [
    {
        "name": "Preservation Metadata Engine",
        "description": (
            "Endpoints for ingesting, querying, updating, and removing music album aggregates."
        ),
    },
    {
        "name": "Master Entity Registry",
        "description": (
            "Lookup endpoints for Artists, Circles, Events, Franchises, Labels, and Publishers."
        ),
    },
    {
        "name": "Identity Session Authentication Plane",
        "description": (
            "Authentication management, token rotation, and active session termination."
        ),
    },
    {
        "name": "Users Identity Engine",
        "description": "User registration and current profile resolution.",
    },
    {
        "name": "System Stability Checks",
        "description": "Health check probe endpoint.",
    },
]
