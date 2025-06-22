import asyncio
import json
from typing import Dict, Any, List, Optional, Union
import psycopg2
from psycopg2.extras import RealDictCursor
import re
from urllib.parse import urlparse
from config.settings import Settings
from config.logging import get_logger
from datetime import datetime

# Initialize logger for scheme service
logger = get_logger('scheme_service')

class SchemeService:
    """MCP Tool for government scheme search using PostgreSQL with vector support."""
    
    def __init__(self):
        self.settings = Settings()
        self.db_config = self._parse_database_url()
    
    def _parse_database_url(self) -> str:
        """Parse DATABASE_URL to get connection string."""
        url = urlparse(self.settings.DATABASE_URL)
        
        # Build connection string
        if url.password:
            return f"postgresql://{url.username}:{url.password}@{url.hostname or 'localhost'}:{url.port or 5432}/{url.path.lstrip('/') or 'whatsapp_bot'}"
        else:
            return f"postgresql://{url.username}@{url.hostname or 'localhost'}:{url.port or 5432}/{url.path.lstrip('/') or 'whatsapp_bot'}"
    
    def _get_connection(self):
        """Get PostgreSQL connection."""
        return psycopg2.connect(self.db_config)
    
    async def search_schemes(self, query: str, age: int = 0, gender: str = "", state: str = "", category: str = "") -> Dict[str, Any]:
        """
        Search for government schemes using vector similarity and filters.
        
        Args:
            query: Search query
            age: User age for filtering
            gender: User gender for filtering
            state: User state for filtering
            category: User category (SC/ST/OBC/General) for filtering
            
        Returns:
            Raw scheme search results
        """
        try:
            logger.info(f"Searching schemes with query: '{query}', filters: age={age}, gender={gender}, state={state}, category={category}")
            
            if not query.strip():
                logger.warning("Empty search query provided")
                return {
                    "success": False,
                    "error": "Search query is required"
                }
            
            # Build search query with filters
            search_query = self._build_search_query(query, age, gender, state, category)
            logger.debug(f"Built search query: {search_query[:200]}...")
            
            # Execute search
            schemes = await self._execute_search(search_query, query)
            
            logger.info(f"Scheme search completed, found {len(schemes)} schemes")
            return {
                "success": True,
                "query": query,
                "filters": {
                    "age": age,
                    "gender": gender,
                    "state": state,
                    "category": category
                },
                "schemes": schemes,
                "total_count": len(schemes),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Scheme search failed: {str(e)}")
            return {
                "success": False,
                "error": f"Scheme search failed: {str(e)}"
            }
    
    async def _vector_search(self, query: str) -> List[Dict]:
        """Perform vector similarity search on scheme embeddings."""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # First, get query embedding (this would be done by Sarvam AI)
            # For now, we'll use text search as fallback
            cursor.execute('''
                SELECT s.*, 
                       ts_rank(to_tsvector('english', s.name || ' ' || s.description), plainto_tsquery('english', %s)) as rank
                FROM schemes s
                WHERE to_tsvector('english', s.name || ' ' || s.description) @@ plainto_tsquery('english', %s)
                ORDER BY rank DESC
                LIMIT 20
            ''', (query, query))
            
            results = cursor.fetchall()
            
            # If no results, try broader search
            if not results:
                cursor.execute('''
                    SELECT s.*, 1 as rank
                    FROM schemes s
                    WHERE LOWER(s.name) LIKE %s 
                       OR LOWER(s.description) LIKE %s
                       OR LOWER(s.category) LIKE %s
                    ORDER BY s.name
                    LIMIT 20
                ''', (f'%{query.lower()}%', f'%{query.lower()}%', f'%{query.lower()}%'))
                
                results = cursor.fetchall()
            
            return [dict(row) for row in results]
            
        finally:
            cursor.close()
            conn.close()
    
    async def _apply_eligibility_filters(self, schemes: List[Dict], user_age: Optional[int] = None,
                                       user_gender: Optional[str] = None, user_state: Optional[str] = None,
                                       user_caste: Optional[str] = None, is_minority: Optional[bool] = None,
                                       is_differently_abled: Optional[bool] = None, is_bpl: Optional[bool] = None,
                                       is_student: Optional[bool] = None) -> List[Dict]:
        """Apply eligibility filters to search results."""
        filtered_schemes = []
        
        for scheme in schemes:
            # State filter
            if user_state and scheme.get('state') and scheme['state'].lower() != 'all':
                if user_state.lower() not in scheme['state'].lower():
                    continue
            
            # Caste filter
            if user_caste and scheme.get('caste'):
                scheme_castes = [c.strip().lower() for c in scheme['caste'].split(',')]
                if user_caste.lower() not in scheme_castes and 'all' not in scheme_castes:
                    continue
            
            # Boolean filters
            if is_minority is not None and scheme.get('is_minority') and not is_minority:
                continue
                
            if is_differently_abled is not None and scheme.get('is_differently_abled') and not is_differently_abled:
                continue
                
            if is_bpl is not None and scheme.get('is_bpl') and not is_bpl:
                continue
                
            if is_student is not None and scheme.get('is_student') and not is_student:
                continue
            
            filtered_schemes.append(scheme)
        
        return filtered_schemes
    
    async def get_scheme_details(self, scheme_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific scheme."""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute('''
                SELECT * FROM schemes WHERE id = %s
            ''', (scheme_id,))
            
            scheme = cursor.fetchone()
            
            if not scheme:
                return {
                    "success": False,
                    "error": "Scheme not found"
                }
            
            return {
                "success": True,
                "scheme": dict(scheme)
            }
            
        finally:
            cursor.close()
            conn.close()
    
    async def get_schemes_by_category(self, category: str) -> Dict[str, Any]:
        """Get schemes filtered by category."""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute('''
                SELECT * FROM schemes 
                WHERE LOWER(category) LIKE %s
                ORDER BY name
                LIMIT 20
            ''', (f'%{category.lower()}%',))
            
            schemes = [dict(row) for row in cursor.fetchall()]
            
            return {
                "success": True,
                "category": category,
                "total_schemes": len(schemes),
                "schemes": schemes
            }
            
        finally:
            cursor.close()
            conn.close()
    
    async def get_popular_schemes(self, limit: int = 10) -> Dict[str, Any]:
        """Get popular schemes based on user matches."""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute('''
                SELECT s.*, COUNT(usm.id) as match_count
                FROM schemes s
                LEFT JOIN user_scheme_matches usm ON s.id = usm.scheme_id
                GROUP BY s.id
                ORDER BY match_count DESC, s.name
                LIMIT %s
            ''', (limit,))
            
            schemes = [dict(row) for row in cursor.fetchall()]
            
            return {
                "success": True,
                "total_schemes": len(schemes),
                "schemes": schemes
            }
            
        finally:
            cursor.close()
            conn.close()
