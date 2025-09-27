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
    'db': os.getenv('MYSQL_DATABASE', 'frisor_lafata'),
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
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            yield connection, cursor

# Utility functions for JSON handling
def serialize_for_db(data: Any) -> Any:
    """Serialize data for database storage"""
    if isinstance(data, (list, dict)):
        return json.dumps(data, default=str)
    elif isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, date):
        return data.isoformat()
    elif isinstance(data, time):
        return data.strftime('%H:%M:%S')
    return data

def deserialize_from_db(data: Any) -> Any:
    """Deserialize data from database"""
    if isinstance(data, str):
        try:
            return json.loads(data)
        except (json.JSONDecodeError, ValueError):
            return data
    return data

def prepare_record_for_response(record: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare database record for API response"""
    if not record:
        return record
    
    result = {}
    for key, value in record.items():
        if key in ['specialties', 'portfolio_images', 'available_hours', 'services', 'categories', 'tags', 'images', 'videos']:
            # Deserialize JSON fields
            result[key] = deserialize_from_db(value) if value else []
        elif isinstance(value, datetime):
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
        if key in ['specialties', 'portfolio_images', 'available_hours', 'services', 'categories', 'tags', 'images', 'videos']:
            # Serialize JSON fields
            result[key] = serialize_for_db(value) if value else None
        elif isinstance(value, (datetime, date, time)):
            result[key] = serialize_for_db(value)
        else:
            result[key] = value
    
    return result

async def execute_query(query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False) -> Any:
    """Execute a database query"""
    async with get_db_connection() as (connection, cursor):
        try:
            await cursor.execute(query, params or ())
            
            if fetch_one:
                result = await cursor.fetchone()
                return prepare_record_for_response(result) if result else None
            elif fetch_all:
                results = await cursor.fetchall()
                return [prepare_record_for_response(row) for row in results]
            else:
                return cursor.rowcount
        except Exception as e:
            print(f"Database query error: {e}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            raise

async def insert_record(table: str, data: Dict[str, Any]) -> str:
    """Insert a record and return the ID"""
    prepared_data = prepare_data_for_insert(data)
    
    columns = list(prepared_data.keys())
    placeholders = ['%s'] * len(columns)
    values = list(prepared_data.values())
    
    query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
    
    async with get_db_connection() as (connection, cursor):
        try:
            await cursor.execute(query, values)
            return data.get('id', str(cursor.lastrowid))
        except Exception as e:
            print(f"Insert error: {e}")
            print(f"Query: {query}")
            print(f"Values: {values}")
            raise

async def update_record(table: str, record_id: str, data: Dict[str, Any]) -> int:
    """Update a record and return affected rows"""
    prepared_data = prepare_data_for_insert(data)
    
    set_clauses = [f"{col} = %s" for col in prepared_data.keys()]
    values = list(prepared_data.values()) + [record_id]
    
    query = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE id = %s"
    
    async with get_db_connection() as (connection, cursor):
        try:
            await cursor.execute(query, values)
            return cursor.rowcount
        except Exception as e:
            print(f"Update error: {e}")
            print(f"Query: {query}")
            print(f"Values: {values}")
            raise

async def delete_record(table: str, record_id: str) -> int:
    """Delete a record and return affected rows"""
    query = f"DELETE FROM {table} WHERE id = %s"
    
    async with get_db_connection() as (connection, cursor):
        try:
            await cursor.execute(query, (record_id,))
            return cursor.rowcount
        except Exception as e:
            print(f"Delete error: {e}")
            print(f"Query: {query}")
            print(f"ID: {record_id}")
            raise