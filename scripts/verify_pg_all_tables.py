from sqlalchemy import inspect, text
from src.database.connection import engine

inspector = inspect(engine)
tables = sorted(inspector.get_table_names())

print("=" * 80)
print(" POSTGRESQL DATABASE 'contractrisk' SCHEMA & TABLE AUDIT")
print("=" * 80)
print(f"Total Tables Found: {len(tables)}\n")

with engine.connect() as conn:
    for t in tables:
        cols = inspector.get_columns(t)
        col_names = [c["name"] for c in cols]
        count_res = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        print(f"Table: '{t}' (Columns: {len(cols)}, Row Count: {count_res})")
        print(f"  Columns: {', '.join(col_names)}")
        print("-" * 80)

print("\nALEMBIC MIGRATION VERSION IN DATABASE:")
with engine.connect() as conn:
    ver = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    print(f"  Current Alembic Revision: {ver}")

print("=" * 80)
