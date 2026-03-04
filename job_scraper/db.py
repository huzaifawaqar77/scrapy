from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os
import mysql.connector
from urllib.parse import urlparse, unquote

# Ensure the database exists (Works for both local and production)
def create_database_if_not_exists():
    try:
        db_uri = os.getenv("DATABASE_URI", "mysql+mysqlconnector://root:@localhost:3306/job_board_db")
        
        # Parse the URI to get host, user, password, port, and db name
        parsed = urlparse(db_uri)
        db_user = unquote(parsed.username) if parsed.username else "root"
        db_pass = unquote(parsed.password) if parsed.password else ""
        db_host = parsed.hostname or "localhost"
        db_port = parsed.port or 3306
        db_name = parsed.path.lstrip('/') or "job_board_db"

        # Connect to MySQL server (without specifying the database) to create it if missing
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_pass,
            port=db_port
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.close()
        conn.close()
        print(f"Database '{db_name}' ensured on {db_host}:{db_port}.")
    except Exception as e:
        print(f"Error creating database: {e}")

# Create database before ORM connects
create_database_if_not_exists()

# Enterprise Grade ORM setup using SQLAlchemy
# Defaults to localhost XAMPP but overrides if deployed on Coolify
DATABASE_URI = os.getenv("DATABASE_URI", "mysql+mysqlconnector://root:@localhost:3306/job_board_db")

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
