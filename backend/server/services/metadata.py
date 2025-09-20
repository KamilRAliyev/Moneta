from server.models.main import TransactionMetadata
from datetime import datetime


def update_transaction_metadata(session, ingested: dict, computed: dict):
    """
    Update transaction metadata using the provided session.
    
    Args:
        session: Database session (should be passed from the calling context)
        ingested: Dictionary of ingested column data
        computed: Dictionary of computed column data
    """
    try:
        meta = session.query(TransactionMetadata).first()

        if not meta:
            meta = TransactionMetadata(id="1", ingested_columns={}, computed_columns={})
            session.add(meta)
        
        def update_columns(existing: dict, new_data: dict):
            for key, value in new_data.items():
                if key in existing:
                    existing[key] = value
                else:
                    existing[key] = value
            return existing
        
        meta.ingested_columns = update_columns(meta.ingested_columns, ingested)
        meta.computed_columns = update_columns(meta.computed_columns, computed)
        
        # Update the updated_at timestamp
        meta.updated_at = datetime.utcnow()
        
        # Don't commit here - let the calling context handle the commit
        session.flush()  # Flush changes to the database without committing
    except Exception as e:
        session.rollback()
        raise e
