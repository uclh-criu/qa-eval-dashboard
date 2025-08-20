#!/usr/bin/env python3
"""
Script to view and analyze the database schema
"""

from app import app
from models import db, User, Dataset, QuestionAnswerPair, Feedback, user_dataset_access
from sqlalchemy import inspect

def view_schema():
    """Display detailed information about the database schema"""
    
    with app.app_context():
        # Create inspector
        inspector = inspect(db.engine)
        
        print("=" * 60)
        print("MEDICAL Q&A FEEDBACK SYSTEM - DATABASE SCHEMA")
        print("=" * 60)
        
        # Get all table names
        tables = inspector.get_table_names()
        print(f"\n📋 TABLES ({len(tables)}):")
        for table in tables:
            print(f"  • {table}")
        
        print("\n" + "=" * 60)
        print("TABLE DETAILS:")
        print("=" * 60)
        
        # For each table, show columns and details
        for table_name in tables:
            print(f"\n🗂️  TABLE: {table_name.upper()}")
            print("-" * 40)
            
            columns = inspector.get_columns(table_name)
            print("Columns:")
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = f" DEFAULT: {col['default']}" if col['default'] else ""
                print(f"  • {col['name']:<20} {str(col['type']):<15} {nullable}{default}")
            
            # Show foreign keys
            fks = inspector.get_foreign_keys(table_name)
            if fks:
                print("\nForeign Keys:")
                for fk in fks:
                    print(f"  • {fk['constrained_columns'][0]} → {fk['referred_table']}.{fk['referred_columns'][0]}")
            
            # Show indexes
            indexes = inspector.get_indexes(table_name)
            if indexes:
                print("\nIndexes:")
                for idx in indexes:
                    unique = "UNIQUE" if idx['unique'] else "INDEX"
                    print(f"  • {idx['name']} ({unique}): {', '.join(idx['column_names'])}")
        
        print("\n" + "=" * 60)
        print("RELATIONSHIPS:")
        print("=" * 60)
        
        relationships = [
            ("User", "accessible_datasets", "Dataset", "Many-to-Many", "via user_dataset_access"),
            ("Dataset", "authorized_users", "User", "Many-to-Many", "via user_dataset_access"),
            ("Dataset", "qa_pairs", "QuestionAnswerPair", "One-to-Many", "dataset_id FK"),
            ("QuestionAnswerPair", "feedback", "Feedback", "One-to-Many", "qa_pair_id FK"),
            ("User", "feedback", "Feedback", "One-to-Many", "user_id FK"),
        ]
        
        for source, attr, target, relationship_type, details in relationships:
            print(f"  • {source}.{attr} → {target} ({relationship_type}) - {details}")
        
        print("\n" + "=" * 60)
        print("CURRENT DATA SUMMARY:")
        print("=" * 60)
        
        try:
            user_count = User.query.count()
            dataset_count = Dataset.query.count()
            qa_count = QuestionAnswerPair.query.count()
            feedback_count = Feedback.query.count()
            
            print(f"  👥 Users: {user_count}")
            print(f"  📊 Datasets: {dataset_count}")
            print(f"  ❓ Q&A Pairs: {qa_count}")
            print(f"  💬 Feedback Entries: {feedback_count}")
            
            if user_count > 0:
                admin_count = User.query.filter_by(access_level='admin').count()
                print(f"  🔑 Admin Users: {admin_count}")
                
        except Exception as e:
            print(f"  ⚠️  Cannot query data: {e}")
            print("  (Database may be empty or not initialized)")

if __name__ == "__main__":
    view_schema()
