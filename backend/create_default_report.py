"""
Script to create a default report for testing the Reports system
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server.models.main import Base, Report
from server.settings import DATABASE_PATHS
from datetime import datetime

def create_default_report():
    """Create a default report with sample widgets"""
    
    # Connect to database
    db_path = DATABASE_PATHS['main']
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if any reports exist
        existing_reports = db.query(Report).count()
        
        if existing_reports > 0:
            print(f"✓ Found {existing_reports} existing report(s)")
            return
        
        # Create default report
        default_report = Report(
            name="Dashboard Overview",
            widgets=[
                {
                    "id": "1",
                    "type": "heading",
                    "x": 0,
                    "y": 0,
                    "w": 12,
                    "h": 1,
                    "config": {
                        "text": "Financial Overview",
                        "level": "h1"
                    }
                },
                {
                    "id": "2",
                    "type": "chart",
                    "x": 0,
                    "y": 1,
                    "w": 6,
                    "h": 4,
                    "config": {
                        "title": "Expenses by Category",
                        "chartType": "bar",
                        "x_field": "category",
                        "y_field": "amount",
                        "aggregation": "sum"
                    }
                },
                {
                    "id": "3",
                    "type": "chart",
                    "x": 6,
                    "y": 1,
                    "w": 6,
                    "h": 4,
                    "config": {
                        "title": "Spending Distribution",
                        "chartType": "donut",
                        "x_field": "category",
                        "y_field": "amount",
                        "aggregation": "sum"
                    }
                },
                {
                    "id": "4",
                    "type": "divider",
                    "x": 0,
                    "y": 5,
                    "w": 12,
                    "h": 1,
                    "config": {
                        "thickness": "medium"
                    }
                },
                {
                    "id": "5",
                    "type": "heading",
                    "x": 0,
                    "y": 6,
                    "w": 12,
                    "h": 1,
                    "config": {
                        "text": "Trends",
                        "level": "h2"
                    }
                },
                {
                    "id": "6",
                    "type": "chart",
                    "x": 0,
                    "y": 7,
                    "w": 12,
                    "h": 4,
                    "config": {
                        "title": "Spending Over Time",
                        "chartType": "line",
                        "x_field": "date",
                        "y_field": "amount",
                        "aggregation": "sum"
                    }
                }
            ],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(default_report)
        db.commit()
        
        print(f"✓ Created default report: '{default_report.name}' (ID: {default_report.id})")
        print(f"  - Contains {len(default_report.widgets)} widgets")
        print(f"  - 3 charts (bar, donut, line)")
        print(f"  - 2 headings")
        print(f"  - 1 divider")
        
    except Exception as e:
        print(f"✗ Error creating default report: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating default report...")
    create_default_report()
    print("\nDefault report setup complete!")
    print("Visit http://localhost:5173/reports to view the report.")

