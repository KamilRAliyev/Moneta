import os

DEBUG = True
TESTING = os.getenv('TESTING', 'false').lower() == 'true'

ALLOWED_FILE_EXTENSIONS = [".csv", ".xlsx", ".xls"]

if TESTING:
    # Use separate test databases
    DATABASE_PATHS = {
        'main': os.path.join(os.path.dirname(__file__), '..', 'data', 'test_transactions.db'),
        'configurations': os.path.join(os.path.dirname(__file__), '..', 'data', 'test_configurations.db'),
    }
elif DEBUG:
    DATABASE_PATHS = {
        'main': os.path.join(os.path.dirname(__file__), '..', 'data', 'transactions_dev.db'),
        'configurations': os.path.join(os.path.dirname(__file__), '..', 'data', 'configurations_dev.db'),
    }
else:
    DATABASE_PATHS = {
        'main': os.path.join(os.path.dirname(__file__), '..', 'data', 'transactions.db'),
        'configurations': os.path.join(os.path.dirname(__file__), '..', 'data', 'configurations.db'),
    }

alembic_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


