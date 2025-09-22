"""
Database Service
Handles database operations, session management, and query history
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from loguru import logger

try:
    from sqlalchemy import create_engine, Column, String, Text, DateTime, JSON
    from sqlalchemy.orm import declarative_base
    from sqlalchemy.orm import sessionmaker, Session
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning("SQLAlchemy not available, will use in-memory storage only")

Base = declarative_base() if SQLALCHEMY_AVAILABLE else object

class QueryHistory(Base if SQLALCHEMY_AVAILABLE else object):
    """
    Database model for query history
    """
    if SQLALCHEMY_AVAILABLE:
        __tablename__ = "query_history"
        
        id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
        session_id = Column(String, nullable=False, index=True)
        user_query = Column(Text, nullable=False)
        ai_response = Column(Text, nullable=False)
        data_result = Column(JSON, nullable=True)
        parsed_query = Column(JSON, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DatabaseService:
    """
    Handles all database operations for Float-Chat-AI
    """

    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.in_memory_storage = {}
        self.setup_database()

    def setup_database(self):
        """
        Initialize database connection and tables
        """
        if not SQLALCHEMY_AVAILABLE:
            logger.info("Using in-memory storage because SQLAlchemy is not installed.")
            self._setup_in_memory_storage()
            return
            
        try:
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                logger.warning("DATABASE_URL not found in .env file. Falling back to in-memory storage.")
                self._setup_in_memory_storage()
                return

            self.engine = create_engine(database_url)
            Base.metadata.create_all(bind=self.engine)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            with self.engine.connect() as connection:
                logger.info("Database connection established successfully.")
        except Exception as e:
            logger.warning(f"Could not connect to PostgreSQL: {e}")
            logger.info("Falling back to in-memory storage for session data.")
            self.engine = None
            self.SessionLocal = None
            self._setup_in_memory_storage()

    def _setup_in_memory_storage(self):
        """Initializes the structure for in-memory fallback."""
        self.in_memory_storage = {'sessions': {}, 'queries': {}}

    def get_db_session(self) -> Optional[Session]:
        """Get a new database session."""
        return self.SessionLocal() if self.SessionLocal else None

    async def save_query_history(self, session_id: str, user_query: str, ai_response: str, 
                                 data_result: Dict[str, Any], parsed_query: Dict[str, Any] = None) -> str:
        """Save query and response to history."""
        query_id = str(uuid.uuid4())
        
        if self.SessionLocal:
            db_session = self.get_db_session()
            try:
                query_record = QueryHistory(
                    id=query_id, session_id=session_id, user_query=user_query,
                    ai_response=ai_response, data_result=data_result, parsed_query=parsed_query
                )
                db_session.add(query_record)
                db_session.commit()
                logger.info(f"Saved query to database: {query_id}")
            except Exception as e:
                db_session.rollback()
                logger.error(f"Database save error: {str(e)}")
            finally:
                db_session.close()
        else:
            if session_id not in self.in_memory_storage['sessions']:
                self.in_memory_storage['sessions'][session_id] = []
            
            query_record = {
                'id': query_id, 'session_id': session_id, 'user_query': user_query,
                'ai_response': ai_response, 'data_result': data_result, 'parsed_query': parsed_query,
                'created_at': datetime.utcnow().isoformat()
            }
            self.in_memory_storage['sessions'][session_id].append(query_record)
            self.in_memory_storage['queries'][query_id] = query_record
            logger.info(f"Saved query to memory: {query_id}")
        
        return query_id

    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve query history for a session."""
        if self.SessionLocal:
            db_session = self.get_db_session()
            try:
                queries = db_session.query(QueryHistory).filter(QueryHistory.session_id == session_id)\
                                  .order_by(QueryHistory.created_at.desc()).limit(50).all()
                return [{c.name: getattr(q, c.name) for c in q.__table__.columns} for q in queries]
            finally:
                db_session.close()
        else:
            session_data = self.in_memory_storage['sessions'].get(session_id, [])
            return sorted(session_data, key=lambda x: x['created_at'], reverse=True)[:50]
            
    async def get_query_by_id(self, query_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific query by ID."""
        if self.SessionLocal:
            db_session = self.get_db_session()
            try:
                query = db_session.query(QueryHistory).filter(QueryHistory.id == query_id).first()
                return {c.name: getattr(query, c.name) for c in query.__table__.columns} if query else None
            finally:
                db_session.close()
        else:
            return self.in_memory_storage['queries'].get(query_id)

    async def delete_session_history(self, session_id: str) -> bool:
        """Delete all history for a session."""
        if self.SessionLocal:
            db_session = self.get_db_session()
            try:
                deleted_count = db_session.query(QueryHistory).filter(QueryHistory.session_id == session_id).delete()
                db_session.commit()
                logger.info(f"Deleted {deleted_count} queries for session {session_id}")
                return True
            except Exception as e:
                db_session.rollback()
                logger.error(f"Database delete error: {str(e)}")
                return False
            finally:
                db_session.close()
        else:
            if session_id in self.in_memory_storage['sessions']:
                for query in self.in_memory_storage['sessions'][session_id]:
                    if query.get('id') in self.in_memory_storage['queries']:
                        del self.in_memory_storage['queries'][query.get('id')]
                del self.in_memory_storage['sessions'][session_id]
                logger.info(f"Deleted session {session_id} from memory")
            return True

    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session."""
        history = await self.get_session_history(session_id)
        stats = {
            'total_queries': len(history), 'first_query_time': None, 'last_query_time': None,
            'most_common_variables': {}, 'query_types': {}
        }
        if history:
            stats['first_query_time'] = history[-1]['created_at']
            stats['last_query_time'] = history[0]['created_at']
            for query in history:
                parsed = query.get('parsed_query', {})
                if parsed:
                    var = parsed.get('variable', 'unknown')
                    op = parsed.get('operation', 'unknown')
                    stats['most_common_variables'][var] = stats['most_common_variables'].get(var, 0) + 1
                    stats['query_types'][op] = stats['query_types'].get(op, 0) + 1
        return stats

    async def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """Clean up old sessions."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        deleted_count = 0
        if self.SessionLocal:
            db_session = self.get_db_session()
            try:
                deleted_count = db_session.query(QueryHistory).filter(QueryHistory.created_at < cutoff_date).delete()
                db_session.commit()
                logger.info(f"Cleaned up {deleted_count} old queries from database")
            except Exception as e:
                db_session.rollback()
                logger.error(f"Database cleanup error: {str(e)}")
            finally:
                db_session.close()
        else:
            # Cleanup logic for in-memory storage can be added here if needed for long-running instances
            pass
        return deleted_count