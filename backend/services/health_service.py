import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import httpx
from mem0 import Memory

from config.settings import Settings

class HealthService:
    """Service for health record management and hospital finding."""
    
    def __init__(self):
        self.settings = Settings()
        
        # Initialize mem0 storage
        self.memory = Memory()
        
        # In-memory storage for health records (replace with database in production)
        self.health_records = {}
        self.prescriptions = {}
    
    async def manage_record(self, user_id: str, action: str, data: str = "") -> Dict[str, Any]:
        """
        Manage user health records and prescriptions.
        
        Args:
            user_id: User identifier
            action: Action to perform (store, retrieve, add_prescription)
            data: Health data in JSON format
            
        Returns:
            Raw operation result data
        """
        try:
            if action == "store":
                return await self._store_health_record(user_id, data)
            elif action == "retrieve":
                return await self._retrieve_health_record(user_id)
            elif action == "add_prescription":
                return await self._add_prescription(user_id, data)
            elif action == "get_prescriptions":
                return await self._get_prescriptions(user_id)
            elif action == "add_appointment":
                return await self._add_appointment(user_id, data)
            elif action == "get_appointments":
                return await self._get_appointments(user_id)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": ["store", "retrieve", "add_prescription", "get_prescriptions", "add_appointment", "get_appointments"]
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Health record management error: {str(e)}"
            }
    
    async def _store_health_record(self, user_id: str, data: str) -> Dict[str, Any]:
        """Store health record data."""
        try:
            if not user_id or not isinstance(user_id, str):
                return {
                    "success": False,
                    "error": "Invalid user ID provided"
                }

            # Convert WhatsApp ID to standardized format
            normalized_user_id = user_id.strip().lower()
            if '@' in normalized_user_id:
                normalized_user_id = normalized_user_id.split('@')[0]
                
            health_data = json.loads(data) if data else {}
            
            # Try to retrieve existing record from mem0 with user isolation
            existing_records = self.memory.search("health_record", 
                                                user_id=normalized_user_id,
                                                metadata={"type": "health_record", "owner": normalized_user_id})
            
            if not existing_records:
                record = {
                    "user_id": normalized_user_id,
                    "personal_info": {},
                    "medical_history": [],
                    "allergies": [],
                    "medications": [],
                    "emergency_contacts": [],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "last_accessed_from": user_id
                }
            else:
                record = existing_records[0]["content"]
                record["last_accessed_from"] = user_id
            
            # Update different sections based on data type
            if "personal_info" in health_data:
                record["personal_info"].update(health_data["personal_info"])
            
            if "medical_condition" in health_data:
                record["medical_history"].append({
                    "condition": health_data["medical_condition"],
                    "date_recorded": datetime.now().isoformat(),
                    "notes": health_data.get("notes", "")
                })
            
            if "allergy" in health_data:
                record["allergies"].append({
                    "allergen": health_data["allergy"],
                    "severity": health_data.get("severity", "unknown"),
                    "date_recorded": datetime.now().isoformat()
                })
            
            if "medication" in health_data:
                record["medications"].append({
                    "medication": health_data["medication"],
                    "dosage": health_data.get("dosage", ""),
                    "frequency": health_data.get("frequency", ""),
                    "start_date": health_data.get("start_date", datetime.now().isoformat()),
                    "end_date": health_data.get("end_date", ""),
                    "prescribed_by": health_data.get("prescribed_by", "")
                })
            
            record["updated_at"] = datetime.now().isoformat()
            
            # Store in mem0 with enhanced user isolation
            self.memory.add([{"role": "system", "content": record}], 
                          user_id=normalized_user_id, 
                          metadata={
                              "type": "health_record",
                              "owner": normalized_user_id,
                              "original_id": user_id,
                              "last_updated": datetime.now().isoformat()
                          })
            
            return {
                "success": True,
                "message": "Health record updated successfully",
                "user_id": normalized_user_id,
                "updated_at": record["updated_at"]
            }
            
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Invalid JSON format in health data"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error storing health record: {str(e)}"
            }
    
    async def _retrieve_health_record(self, user_id: str) -> Dict[str, Any]:
        """Retrieve user's health record."""
        if not user_id:
            return {
                "success": False,
                "error": "Invalid user ID provided"
            }
            
        # Normalize user ID
        normalized_user_id = user_id.strip().lower()
        if '@' in normalized_user_id:
            normalized_user_id = normalized_user_id.split('@')[0]
            
        # Search with user isolation
        records = self.memory.search("health_record", 
                                   user_id=normalized_user_id,
                                   metadata={"type": "health_record", "owner": normalized_user_id})
        
        if not records:
            return {
                "success": True,
                "user_id": normalized_user_id,
                "health_record": None,
                "message": "No health records found"
            }
        
        record = records[0]["content"]
        
        # Verify ownership
        if record.get("user_id") != normalized_user_id:
            return {
                "success": False,
                "error": "Access denied. This record belongs to another user"
            }
        
        return {
            "success": True,
            "user_id": normalized_user_id,
            "health_record": record,
            "last_updated": record.get("updated_at")
        }
    
    async def _add_prescription(self, user_id: str, data: str) -> Dict[str, Any]:
        """Add prescription to user's health record."""
        try:
            prescription_data = json.loads(data) if data else {}
            
            normalized_user_id = user_id.strip().lower()
            if '@' in normalized_user_id:
                normalized_user_id = normalized_user_id.split('@')[0]
            
            prescription = {
                "medication": prescription_data.get("medication", ""),
                "dosage": prescription_data.get("dosage", ""),
                "frequency": prescription_data.get("frequency", ""),
                "duration": prescription_data.get("duration", ""),
                "prescribed_by": prescription_data.get("prescribed_by", ""),
                "prescribed_date": datetime.now().isoformat(),
                "notes": prescription_data.get("notes", "")
            }
            
            # Store prescription in mem0
            self.memory.add([{"role": "system", "content": prescription}], 
                          user_id=normalized_user_id,
                          metadata={
                              "type": "prescription",
                              "owner": normalized_user_id,
                              "medication": prescription["medication"]
                          })
            
            return {
                "success": True,
                "message": "Prescription added successfully",
                "prescription": prescription
            }
            
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Invalid JSON format in prescription data"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error adding prescription: {str(e)}"
            }
    
    async def _get_prescriptions(self, user_id: str) -> Dict[str, Any]:
        """Get user's prescriptions."""
        try:
            normalized_user_id = user_id.strip().lower()
            if '@' in normalized_user_id:
                normalized_user_id = normalized_user_id.split('@')[0]
            
            prescriptions = self.memory.search("prescription", 
                                             user_id=normalized_user_id,
                                             metadata={"type": "prescription", "owner": normalized_user_id})
            
            prescription_list = [p["content"] for p in prescriptions]
            
            return {
                "success": True,
                "user_id": normalized_user_id,
                "prescriptions": prescription_list,
                "count": len(prescription_list)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error retrieving prescriptions: {str(e)}"
            }
    
    async def _add_appointment(self, user_id: str, data: str) -> Dict[str, Any]:
        """Add appointment to user's health record."""
        # Placeholder implementation
        return {
            "success": True,
            "message": "Appointment feature not implemented",
            "user_id": user_id
        }
    
    async def _get_appointments(self, user_id: str) -> Dict[str, Any]:
        """Get user's appointments."""
        # Placeholder implementation
        return {
            "success": True,
            "message": "Appointment feature not implemented",
            "user_id": user_id,
            "appointments": []
        }
    
    async def find_nearby_hospitals(self, location: str, emergency_type: str = "general") -> Dict[str, Any]:
        """Find nearby hospitals and medical facilities."""
        try:
            coords = await self._get_coordinates(location)
            if not coords:
                return {
                    "success": False,
                    "error": f"Could not find location: {location}"
                }
            
            lat, lon = coords
            hospitals = await self._search_nearby_hospitals(lat, lon, emergency_type)
            
            return {
                "success": True,
                "location": location,
                "coordinates": {"lat": lat, "lon": lon},
                "emergency_type": emergency_type,
                "hospitals": hospitals,
                "count": len(hospitals)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Hospital search error: {str(e)}"
            }
    
    async def _get_coordinates(self, location: str) -> Optional[tuple]:
        """Get coordinates for location using Open-Meteo geocoding."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={
                        "name": location,
                        "count": 1,
                        "language": "en",
                        "format": "json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("results"):
                        result = data["results"][0]
                        return (result["latitude"], result["longitude"])
            
            return None
            
        except Exception:
            return None
    
    async def _search_nearby_hospitals(self, lat: float, lon: float, emergency_type: str) -> List[Dict]:
        """Search for nearby hospitals using external APIs."""
        # Placeholder implementation
        return [
            {
                "name": "Sample Hospital",
                "distance": "2.5 km",
                "type": emergency_type,
                "address": "Sample Address",
                "phone": "Emergency: 108"
            }
        ]
    
    async def get_medication_reminder(self, user_id: str) -> Dict[str, Any]:
        """Get medication reminders for user."""
        try:
            normalized_user_id = user_id.strip().lower()
            if '@' in normalized_user_id:
                normalized_user_id = normalized_user_id.split('@')[0]
            
            # Get current medications
            health_record = await self._retrieve_health_record(user_id)
            
            if not health_record["success"] or not health_record["health_record"]:
                return {
                    "success": True,
                    "user_id": normalized_user_id,
                    "reminders": [],
                    "message": "No medications found"
                }
            
            medications = health_record["health_record"].get("medications", [])
            current_meds = [med for med in medications if not med.get("end_date") or 
                          datetime.fromisoformat(med["end_date"]) > datetime.now()]
            
            return {
                "success": True,
                "user_id": normalized_user_id,
                "medications": current_meds,
                "reminder_count": len(current_meds)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting medication reminders: {str(e)}"
            }
