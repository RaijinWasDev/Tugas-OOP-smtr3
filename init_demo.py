"""Inisialisasi database demo ketika Alembic belum terpasang."""
from migration_sql import UP
from database import engine

def init_demo():
    with engine.begin() as con:
        con.exec_driver_sql("BEGIN IMMEDIATE")
        version_exists = con.exec_driver_sql("SELECT name FROM sqlite_master WHERE name='alembic_version'").first()
        if version_exists and con.exec_driver_sql("SELECT version_num FROM alembic_version").scalar() == "001_pmb":
            return
        for sql in UP:
            con.exec_driver_sql(sql)
        con.exec_driver_sql("CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)")
        con.exec_driver_sql("INSERT INTO alembic_version VALUES ('001_pmb')")

if __name__ == "__main__":
    init_demo()
    print("Database demo siap.")
