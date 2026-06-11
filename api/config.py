import os

USE_SQLITE = os.environ.get("USE_SQLITE", "1") == "1"

if USE_SQLITE:
    DATABASE_URL = "sqlite+aiosqlite:///./visit_system.db"
else:
    DATABASE_URL = "mysql+asyncmy://root:root@127.0.0.1:3306/visit_system"

JWT_SECRET = "visit-system-secret-key-2024"
JWT_EXPIRATION_HOURS = 24
