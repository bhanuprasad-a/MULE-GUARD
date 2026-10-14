import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from fastapi.routing import APIRoute

def get_all_routes(router, prefix=""):
    routes = []
    for r in router.routes:
        if hasattr(r, "routes"):
            new_prefix = prefix + getattr(r, "prefix", "")
            routes.extend(get_all_routes(r, new_prefix))
        elif hasattr(r, "router"):
            new_prefix = prefix + getattr(r.router, "prefix", "")
            routes.extend(get_all_routes(r.router, new_prefix))
        elif isinstance(r, APIRoute):
            routes.append(r)
    return routes

all_routes = get_all_routes(app.router)
print(f"Total discovered APIRoutes: {len(all_routes)}")

# Also inspect OpenAPI schema
schema = app.openapi()
paths = schema.get("paths", {})
print(f"Total OpenAPI paths: {len(paths)}")

for p, methods in sorted(paths.items()):
    for m, details in methods.items():
        summary = details.get("summary", "")
        tags = ",".join(details.get("tags", []))
        op_id = details.get("operation_id", "")
        print(f"{m.upper():6} | {p:50} | {tags:25} | {op_id}")
