from src.database.connection import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"DATABASE URL: {engine.url}")
print(f"EXISTING TABLES IN POSTGRES: {tables}")
