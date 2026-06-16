# quick_check.py

from app.database.db import Base

print(Base.metadata.tables.keys())