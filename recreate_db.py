#!/usr/bin/env python3
"""
Script to recreate the database with the new schema including dataset support.
"""

import os
from app import app
from models import db

def recreate_database():
    """Drop and recreate the database with new schema."""
    
    with app.app_context():
        # Drop all existing tables
        db.drop_all()
        
        # Create all tables with new schema
        db.create_all()
        
        print("Database recreated successfully.")

if __name__ == "__main__":
    recreate_database()
