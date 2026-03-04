from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os
import mysql.connector

# Ensure the database exists (Specific to local XAMPP setup)
def create_database_if_not_exists():
    try:
        # Check if we are running with a production Database URI, if so skip creation
        if os.getenv("DATABASE_URI"):
            return
            
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", "")
        )
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS job_board_db")
        cursor.close()
        conn.close()
        print("Database 'job_board_db' ensured.")
    except Exception as e:
        print(f"Error creating database: {e}")

# Create database before ORM connects
create_database_if_not_exists()

# Enterprise Grade ORM setup using SQLAlchemy
# Defaults to localhost XAMPP but overrides if deployed on Coolify
DATABASE_URI = os.getenv("DATABASE_URI", "mysql+mysqlconnector://root:@localhost/job_board_db")

engine = create_engine(DATABASE_URI, echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class JobPost(Base):
    __tablename__ = 'job_posts'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    salary = Column(String(255), nullable=True)
    job_url = Column(String(512), unique=True, nullable=False)  # For deduplication
    description = Column(Text, nullable=True)
    source_board = Column(String(100), nullable=False)
    scraped_at = Column(DateTime, default=datetime.datetime.utcnow)

# Create tables
Base.metadata.create_all(engine)
