import asyncio
import json
from typing import Dict, Any, List, Optional
import sqlite3
from pathlib import Path
import re

from config.settings import Settings

class SchemeService:
    """Service for government scheme search with vector and parameter-based search."""
    
    def __init__(self):
        self.settings = Settings()
        self.db_path = Path(self.settings.VECTOR_DB_PATH) / "schemes.db"
        self._init_database()
        self._populate_sample_schemes()
    
    def _init_database(self):
        """Initialize SQLite database for schemes."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Create schemes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schemes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                benefits TEXT,
                eligibility TEXT,
                age_min INTEGER,
                age_max INTEGER,
                gender TEXT,
                state TEXT,
                category TEXT,
                income_limit INTEGER,
                application_process TEXT,
                required_documents TEXT,
                official_website TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create FTS (Full Text Search) virtual table
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS schemes_fts USING fts5(
                name, description, benefits, eligibility, tags,
                content='schemes',
                content_rowid='id'
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _populate_sample_schemes(self):
        """Populate database with sample government schemes."""
        sample_schemes = [
            {
                "name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
                "description": "Income support scheme for farmers providing ₹6000 per year in three installments",
                "benefits": "₹2000 every 4 months directly to farmers' bank accounts",
                "eligibility": "All landholding farmers' families",
                "age_min": 18,
                "age_max": 100,
                "gender": "All",
                "state": "All States",
                "category": "All",
                "income_limit": 0,
                "application_process": "Online through PM-KISAN portal or through Common Service Centers",
                "required_documents": "Aadhaar card, Bank account details, Land records",
                "official_website": "https://pmkisan.gov.in/",
                "tags": "farmer, agriculture, income support, kisan, rural"
            },
            {
                "name": "Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (AB-PMJAY)",
                "description": "Health insurance scheme providing ₹5 lakh health cover per family per year",
                "benefits": "Free treatment up to ₹5 lakh per family per year at empanelled hospitals",
                "eligibility": "Families identified in Socio-Economic Caste Census (SECC) 2011",
                "age_min": 0,
                "age_max": 100,
                "gender": "All",
                "state": "All States",
                "category": "BPL",
                "income_limit": 0,
                "application_process": "No application required, eligible families get golden cards",
                "required_documents": "Aadhaar card, SECC verification",
                "official_website": "https://pmjay.gov.in/",
                "tags": "health, insurance, medical, healthcare, poor, BPL"
            },
            {
                "name": "Beti Bachao Beti Padhao",
                "description": "Scheme to address declining child sex ratio and promote girl child education",
                "benefits": "Financial incentives for education, improved services for girls",
                "eligibility": "Girls from birth to education completion",
                "age_min": 0,
                "age_max": 25,
                "gender": "Female",
                "state": "All States",
                "category": "All",
                "income_limit": 0,
                "application_process": "Through district administration and schools",
                "required_documents": "Birth certificate, School enrollment proof, Bank account",
                "official_website": "https://wcd.nic.in/bbbp-scheme",
                "tags": "girl child, education, women empowerment, female, beti"
            },
            {
                "name": "Pradhan Mantri Awas Yojana (PMAY)",
                "description": "Housing for All scheme providing affordable housing to urban and rural poor",
                "benefits": "Interest subsidy on home loans, direct financial assistance",
                "eligibility": "Families without pucca house belonging to EWS, LIG, MIG categories",
                "age_min": 18,
                "age_max": 70,
                "gender": "All",
                "state": "All States",
                "category": "EWS/LIG/MIG",
                "income_limit": 1800000,
                "application_process": "Online through PMAY portal",
                "required_documents": "Income certificate, Aadhaar, Bank account, Property documents",
                "official_website": "https://pmaymis.gov.in/",
                "tags": "housing, home loan, subsidy, poor, shelter, awas"
            },
            {
                "name": "Mahatma Gandhi National Rural Employment Guarantee Act (MGNREGA)",
                "description": "Employment guarantee scheme providing 100 days of wage employment",
                "benefits": "Guaranteed 100 days of employment per rural household per year",
                "eligibility": "Adult members of rural households willing to do unskilled manual work",
                "age_min": 18,
                "age_max": 65,
                "gender": "All",
                "state": "All States",
                "category": "All",
                "income_limit": 0,
                "application_process": "Apply at Gram Panchayat with job card application",
                "required_documents": "Aadhaar card, Address proof, Passport size photo",
                "official_website": "https://nrega.nic.in/",
                "tags": "employment, rural, work, wage, job, NREGA, labor"
            },
            {
                "name": "Pradhan Mantri Mudra Yojana (PMMY)",
                "description": "Micro-finance scheme for small businesses and entrepreneurs",
                "benefits": "Collateral-free loans up to ₹10 lakh for micro-enterprises",
                "eligibility": "Individuals, proprietorship firms, partnership firms, companies",
                "age_min": 18,
                "age_max": 65,
                "gender": "All",
                "state": "All States",
                "category": "All",
                "income_limit": 0,
                "application_process": "Apply through participating banks and financial institutions",
                "required_documents": "Business plan, Identity proof, Address proof, Income proof",
                "official_website": "https://www.mudra.org.in/",
                "tags": "loan, business, entrepreneur, startup, micro-finance, mudra"
            }
        ]
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Check if schemes already exist
        cursor.execute("SELECT COUNT(*) FROM schemes")
        count = cursor.fetchone()[0]
        
        if count == 0:
            for scheme in sample_schemes:
                cursor.execute('''
                    INSERT INTO schemes (
                        name, description, benefits, eligibility, age_min, age_max,
                        gender, state, category, income_limit, application_process,
                        required_documents, official_website, tags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    scheme["name"], scheme["description"], scheme["benefits"],
                    scheme["eligibility"], scheme["age_min"], scheme["age_max"],
                    scheme["gender"], scheme["state"], scheme["category"],
                    scheme["income_limit"], scheme["application_process"],
                    scheme["required_documents"], scheme["official_website"], scheme["tags"]
                ))
            
            # Populate FTS table
            cursor.execute('''
                INSERT INTO schemes_fts(schemes_fts) VALUES('rebuild')
            ''')
            
            conn.commit()
        
        conn.close()
    
    async def search_schemes(self, query: str, age: int = 0, gender: str = "", 
                           state: str = "", category: str = "") -> str:
        """
        Search for relevant government schemes using semantic and parameter-based search.
        
        Args:
            query: Search query for schemes
            age: User age
            gender: User gender
            state: User state
            category: User category (SC/ST/OBC/General)
            
        Returns:
            Formatted search results
        """
        try:
            # Perform text search
            text_results = await self._text_search(query)
            
            # Apply filters
            filtered_results = await self._apply_filters(text_results, age, gender, state, category)
            
            # Format response
            response = self._format_scheme_results(filtered_results, query, age, gender, state, category)
            
            return response
            
        except Exception as e:
            return f"Scheme search error: {str(e)}"
    
    async def _text_search(self, query: str) -> List[Dict]:
        """Perform full-text search on schemes."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Clean and prepare search query
        search_terms = re.sub(r'[^\w\s]', '', query.lower()).split()
        fts_query = ' OR '.join(search_terms)
        
        try:
            # Full-text search
            cursor.execute('''
                SELECT s.*, rank
                FROM schemes_fts 
                JOIN schemes s ON schemes_fts.rowid = s.id
                WHERE schemes_fts MATCH ?
                ORDER BY rank
                LIMIT 20
            ''', (fts_query,))
            
            results = [dict(row) for row in cursor.fetchall()]
            
            # If no FTS results, fall back to LIKE search
            if not results:
                like_query = f"%{query.lower()}%"
                cursor.execute('''
                    SELECT * FROM schemes 
                    WHERE LOWER(name) LIKE ? 
                       OR LOWER(description) LIKE ? 
                       OR LOWER(tags) LIKE ?
                    ORDER BY name
                    LIMIT 20
                ''', (like_query, like_query, like_query))
                
                results = [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            # Fallback to simple search
            like_query = f"%{query.lower()}%"
            cursor.execute('''
                SELECT * FROM schemes 
                WHERE LOWER(name) LIKE ? 
                   OR LOWER(description) LIKE ?
                ORDER BY name
                LIMIT 20
            ''', (like_query, like_query))
            
            results = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    async def _apply_filters(self, results: List[Dict], age: int, gender: str, 
                           state: str, category: str) -> List[Dict]:
        """Apply parameter-based filters to search results."""
        filtered_results = []
        
        for scheme in results:
            # Age filter
            if age > 0:
                if scheme.get('age_min', 0) > age or (scheme.get('age_max', 100) < age and scheme.get('age_max', 100) > 0):
                    continue
            
            # Gender filter
            if gender and gender.lower() != 'all':
                scheme_gender = scheme.get('gender', '').lower()
                if scheme_gender not in ['all', ''] and scheme_gender != gender.lower():
                    continue
            
            # State filter
            if state:
                scheme_state = scheme.get('state', '').lower()
                if scheme_state not in ['all states', 'all', ''] and state.lower() not in scheme_state:
                    continue
            
            # Category filter
            if category:
                scheme_category = scheme.get('category', '').lower()
                if scheme_category not in ['all', ''] and category.lower() not in scheme_category:
                    continue
            
            filtered_results.append(scheme)
        
        return filtered_results
    
    def _format_scheme_results(self, schemes: List[Dict], query: str, age: int, 
                             gender: str, state: str, category: str) -> str:
        """Format search results into readable response."""
        if not schemes:
            return f"🔍 No schemes found matching your criteria.\n\nSearch query: {query}\nTry different keywords or contact your local government office for more schemes."
        
        response = f"🏛️ **Government Schemes Found** (Query: {query})\n\n"
        
        # Add filter summary
        filters = []
        if age > 0:
            filters.append(f"Age: {age}")
        if gender:
            filters.append(f"Gender: {gender}")
        if state:
            filters.append(f"State: {state}")
        if category:
            filters.append(f"Category: {category}")
        
        if filters:
            response += f"📋 **Filters Applied:** {', '.join(filters)}\n\n"
        
        # Display top 5 schemes
        for i, scheme in enumerate(schemes[:5], 1):
            response += f"**{i}. {scheme['name']}**\n"
            response += f"📝 {scheme['description']}\n"
            response += f"💰 Benefits: {scheme['benefits']}\n"
            response += f"✅ Eligibility: {scheme['eligibility']}\n"
            
            if scheme.get('age_min') or scheme.get('age_max'):
                age_range = f"{scheme.get('age_min', 0)}-{scheme.get('age_max', 100)} years"
                response += f"👥 Age: {age_range}\n"
            
            if scheme.get('income_limit'):
                response += f"💵 Income limit: ₹{scheme['income_limit']:,}\n"
            
            response += f"📞 Apply: {scheme.get('application_process', 'Contact local office')}\n"
            
            if scheme.get('official_website'):
                response += f"🌐 Website: {scheme['official_website']}\n"
            
            response += "\n"
        
        # Add more schemes info
        if len(schemes) > 5:
            response += f"📊 **{len(schemes) - 5} more schemes available.** Refine your search for specific results.\n\n"
        
        # Add general guidance
        response += "💡 **Need Help?**\n"
        response += "• Visit your nearest Common Service Center (CSC)\n"
        response += "• Contact District Collector's office\n"
        response += "• Call helpline: 1800-180-1551\n"
        response += "• Visit India.gov.in for more schemes\n"
        
        return response
    
    async def get_scheme_details(self, scheme_name: str) -> str:
        """Get detailed information about a specific scheme."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM schemes 
            WHERE LOWER(name) LIKE ?
            LIMIT 1
        ''', (f"%{scheme_name.lower()}%",))
        
        scheme = cursor.fetchone()
        conn.close()
        
        if not scheme:
            return f"❌ Scheme '{scheme_name}' not found in database."
        
        scheme = dict(scheme)
        
        response = f"📋 **{scheme['name']} - Detailed Information**\n\n"
        response += f"📝 **Description:**\n{scheme['description']}\n\n"
        response += f"💰 **Benefits:**\n{scheme['benefits']}\n\n"
        response += f"✅ **Eligibility:**\n{scheme['eligibility']}\n\n"
        
        if scheme.get('age_min') or scheme.get('age_max'):
            response += f"👥 **Age Criteria:** {scheme.get('age_min', 0)}-{scheme.get('age_max', 100)} years\n\n"
        
        if scheme.get('income_limit'):
            response += f"💵 **Income Limit:** ₹{scheme['income_limit']:,} per annum\n\n"
        
        response += f"📋 **Application Process:**\n{scheme.get('application_process', 'Contact local office')}\n\n"
        response += f"📄 **Required Documents:**\n{scheme.get('required_documents', 'Contact office for document list')}\n\n"
        
        if scheme.get('official_website'):
            response += f"🌐 **Official Website:** {scheme['official_website']}\n\n"
        
        response += "📞 **For More Information:**\n"
        response += "• Contact your district administration\n"
        response += "• Visit nearest Common Service Center\n"
        response += "• Call government helplines\n"
        
        return response
    
    async def get_schemes_by_category(self, category: str) -> str:
        """Get schemes filtered by category."""
        categories = {
            "farmer": "farmer, agriculture, kisan",
            "health": "health, medical, insurance",
            "education": "education, scholarship, student",
            "employment": "employment, job, work",
            "housing": "housing, awas, shelter",
            "women": "women, female, girl, beti",
            "business": "business, loan, entrepreneur"
        }
        
        search_terms = categories.get(category.lower(), category)
        return await self.search_schemes(search_terms)
    
    async def add_scheme(self, scheme_data: Dict) -> str:
        """Add a new scheme to the database (admin function)."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO schemes (
                    name, description, benefits, eligibility, age_min, age_max,
                    gender, state, category, income_limit, application_process,
                    required_documents, official_website, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                scheme_data.get("name", ""),
                scheme_data.get("description", ""),
                scheme_data.get("benefits", ""),
                scheme_data.get("eligibility", ""),
                scheme_data.get("age_min", 0),
                scheme_data.get("age_max", 100),
                scheme_data.get("gender", "All"),
                scheme_data.get("state", "All States"),
                scheme_data.get("category", "All"),
                scheme_data.get("income_limit", 0),
                scheme_data.get("application_process", ""),
                scheme_data.get("required_documents", ""),
                scheme_data.get("official_website", ""),
                scheme_data.get("tags", "")
            ))
            
            # Update FTS index
            cursor.execute("INSERT INTO schemes_fts(schemes_fts) VALUES('rebuild')")
            
            conn.commit()
            conn.close()
            
            return f"✅ Scheme '{scheme_data.get('name')}' added successfully!"
            
        except Exception as e:
            return f"❌ Error adding scheme: {str(e)}"
