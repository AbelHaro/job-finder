from alembic import context
from sqlalchemy import create_engine, pool
from job_finder.database.models import Base
from job_finder.database.sqlite import database_url


def run_migrations():
    if context.is_offline_mode():
        context.configure(url=database_url(), target_metadata=Base.metadata,
                          literal_binds=True, dialect_opts={"paramstyle": "named"})
        with context.begin_transaction():
            context.run_migrations()
    else:
        engine = create_engine(database_url(), poolclass=pool.NullPool)
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=Base.metadata, render_as_batch=True)
            with context.begin_transaction():
                context.run_migrations()
        engine.dispose()


run_migrations()
