"""
Database connection and utilities for MySQL
"""
import os
import json
import aiomysql
from datetime import datetime, date, time, timezone
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'db': os.getenv('MYSQL_DATABASE', 'target_lafata'),
    'charset': 'utf8mb4',
    'autocommit': True
}

# Global connection pool
pool = None

async def init_db():
    """Initialize database connection pool"""
    global pool
    pool = await aiomysql.create_pool(**DB_CONFIG)
    print(f"MySQL connection pool created for database: {DB_CONFIG['db']}")

async def close_db():
    """Close database connection pool"""
    global pool
    if pool:
        pool.close()
        await pool.wait_closed()
        print("MySQL connection pool closed")

@asynccontextmanager
async def get_db_connection():
    """Get database connection from pool"""
    global pool
    if not pool:
        await init_db()
    
    async with pool.acquire() as connection:
        yield connection

async def execute_query(connection, query: str, params: Optional[tuple] = None):
    """Execute a query and return results"""
    async with connection.cursor() as cursor:
        await cursor.execute(query, params or ())
        result = await cursor.fetchall()
        return result

async def insert_record(connection, table: str, data: Dict[str, Any]):
    """Insert a record into the specified table"""
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    
    async with connection.cursor() as cursor:
        await cursor.execute(query, tuple(data.values()))
        await connection.commit()

async def update_record(connection, table: str, data: Dict[str, Any], record_id: str, id_column: str = 'id'):
    """Update a record in the specified table"""
    set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
    query = f"UPDATE {table} SET {set_clause} WHERE {id_column} = %s"
    
    async with connection.cursor() as cursor:
        values = list(data.values()) + [record_id]
        await cursor.execute(query, tuple(values))
        await connection.commit()

async def delete_record(connection, table: str, record_id: str, id_column: str = 'id'):
    """Delete a record from the specified table"""
    query = f"DELETE FROM {table} WHERE {id_column} = %s"
    
    async with connection.cursor() as cursor:
        await cursor.execute(query, (record_id,))
        await connection.commit()

def prepare_record_for_response(record: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a database record for API response"""
    if not record:
        return {}
    
    result = {}
    for key, value in record.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, date):
            result[key] = value.isoformat()
        elif isinstance(value, time):
            result[key] = value.strftime('%H:%M:%S')
        else:
            result[key] = value
    
    return result

def prepare_data_for_insert(data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare data for database insertion"""
    result = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            result[key] = value
        elif isinstance(value, date):
            result[key] = value
        elif isinstance(value, time):
            result[key] = value
        elif value is None:
            result[key] = None
        else:
            result[key] = value
    
    # Add created_at timestamp if not present
    if 'created_at' not in result:
        result['created_at'] = datetime.now(timezone.utc)
    
    return result