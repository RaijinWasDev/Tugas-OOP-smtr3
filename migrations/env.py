from alembic import context
from database import engine

with engine.connect() as conn:
    conn.exec_driver_sql("BEGIN")
    try:
        context.configure(connection=conn, transactional_ddl=True)
        with context.begin_transaction():
            context.run_migrations()
        conn.commit()
    except Exception:
        conn.rollback()
        raise
