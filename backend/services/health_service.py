import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import httpx
from geopy.geocoders import Nominatim
from mem0 import Memory

from config.settings import Settings

class HealthService:
    """Service for health record management and hospital finding."""
    
    def __init__(self):
        self.settings = Settings()
        self.geolocator = Nominatim(user_agent="whatsapp_health_bot")
        
        # Initialize mem0 storage
        self.memory = Memory()
    
    async def manage_record(self, user_id: str, action: str, data: str = "") -> str:
        """
        Manage user health records and prescriptions.
        
        Args:
            user_id: User identifier
            action: Action to perform (store, retrieve, add_prescription)
            data: Health data in JSON format
            
        Returns:
            Result of the operation
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
                return f"Unknown action: {action}. Available actions: store, retrieve, add_prescription, get_prescriptions, add_appointment, get_appointments"
                
        except Exception as e:
            return f"Health record management error: {str(e)}"
    
    async def _store_health_record(self, user_id: str, data: str) -> str:
        """Store health record data."""
        try:
            if not user_id or not isinstance(user_id, str):
                return "❌ Invalid user ID provided."

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
                    "user_id": normalized_user_id,  # Store user_id in record
                    "personal_info": {},
                    "medical_history": [],
                    "allergies": [],
                    "medications": [],
                    "emergency_contacts": [],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "last_accessed_from": user_id  # Track original user ID format
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
            
            return "✅ Health record updated successfully!"
            
        except json.JSONDecodeError:
            return "❌ Invalid JSON format in health data."
        except Exception as e:
            return f"❌ Error storing health record: {str(e)}"
    
    async def _retrieve_health_record(self, user_id: str) -> str:
        """Retrieve user's health record."""
        if not user_id:
            return "❌ Invalid user ID provided."
            
        # Normalize user ID
        normalized_user_id = user_id.strip().lower()
        if '@' in normalized_user_id:
            normalized_user_id = normalized_user_id.split('@')[0]
            
        # Search with user isolation
        records = self.memory.search("health_record", 
                                   user_id=normalized_user_id,
                                   metadata={"type": "health_record", "owner": normalized_user_id})
        
        if not records:
            return "📋 No health records found. Start by adding your basic information."
        
        record = records[0]["content"]
        
        # Verify ownership
        if record.get("user_id") != normalized_user_id:
            return "❌ Access denied. This record belongs to another user."
        
        response = "📋 **Your Health Record**\n\n"
        
        # Personal information
        if record["personal_info"]:
            response += "👤 **Personal Information:**\n"
            for key, value in record["personal_info"].items():
                response += f"• {key.replace('_', ' ').title()}: {value}\n"
            response += "\n"
        
        # Medical history
        if record["medical_history"]:
            response += "🏥 **Medical History:**\n"
            for condition in record["medical_history"][-5:]:  # Last 5 conditions
                date = datetime.fromisoformat(condition["date_recorded"]).strftime("%Y-%m-%d")
                response += f"• {condition['condition']} (Recorded: {date})\n"
                if condition["notes"]:
                    response += f"  Notes: {condition['notes']}\n"
            response += "\n"
        
        # Allergies
        if record["allergies"]:
            response += "⚠️ **Allergies:**\n"
            for allergy in record["allergies"]:
                response += f"• {allergy['allergen']} (Severity: {allergy['severity']})\n"
            response += "\n"
        
        # Current medications
        if record["medications"]:
            response += "💊 **Current Medications:**\n"
            for med in record["medications"][-5:]:  # Last 5 medications
                response += f"• {med['medication']}\n"
                if med["dosage"]:
                    response += f"  Dosage: {med['dosage']}\n"
                if med["frequency"]:
                    response += f"  Frequency: {med['frequency']}\n"
            response += "\n"
        
        response += f"📅 Last updated: {datetime.fromisoformat(record['updated_at']).strftime('%Y-%m-%d %H:%M')}"
        
        return response
    
    async def _add_prescription(self, user_id: str, data: str) -> str:
        """Add prescription to user's record."""
        try:
            prescription_data = json.loads(data) if data else {}
            
            # Get existing prescriptions count for ID generation
            existing_prescriptions = self.memory.search("prescription", user_id=user_id)
            prescription_count = len(existing_prescriptions)
            
            prescription = {
                "id": f"rx_{prescription_count + 1}",
                "doctor_name": prescription_data.get("doctor_name", ""),
                "clinic_hospital": prescription_data.get("clinic_hospital", ""),
                "date_prescribed": prescription_data.get("date", datetime.now().isoformat()),
                "medications": prescription_data.get("medications", []),
                "diagnosis": prescription_data.get("diagnosis", ""),
                "instructions": prescription_data.get("instructions", ""),
                "next_visit": prescription_data.get("next_visit", ""),
                "created_at": datetime.now().isoformat()
            }
            
            # Store in mem0
            self.memory.add([{"role": "system", "content": prescription}],
                          user_id=user_id,
                          metadata={"type": "prescription"})
            
            # Also add medications to health record
            if prescription["medications"]:
                for med in prescription["medications"]:
                    med_data = {
                        "medication": med.get("name", ""),
                        "dosage": med.get("dosage", ""),
                        "frequency": med.get("frequency", ""),
                        "prescribed_by": prescription["doctor_name"]
                    }
                    await self._store_health_record(user_id, json.dumps(med_data))
            
            return f"💊 Prescription added successfully! (ID: {prescription['id']})"
            
        except json.JSONDecodeError:
            return "❌ Invalid JSON format in prescription data."
        except Exception as e:
            return f"❌ Error adding prescription: {str(e)}"
    
    async def _get_prescriptions(self, user_id: str) -> str:
        """Get user's prescriptions."""
        prescriptions_data = self.memory.search("prescription", user_id=user_id)
        
        if not prescriptions_data:
            return "💊 No prescriptions found."
        
        prescriptions = [p["content"] for p in prescriptions_data]
        response = "💊 **Your Prescriptions**\n\n"
        
        for prescription in prescriptions[-5:]:  # Last 5 prescriptions
            response += f"📋 **Prescription {prescription['id']}**\n"
            response += f"👨‍⚕️ Doctor: {prescription['doctor_name']}\n"
            response += f"🏥 Clinic/Hospital: {prescription['clinic_hospital']}\n"
            response += f"📅 Date: {datetime.fromisoformat(prescription['date_prescribed']).strftime('%Y-%m-%d')}\n"
            
            if prescription['diagnosis']:
                response += f"🔍 Diagnosis: {prescription['diagnosis']}\n"
            
            if prescription['medications']:
                response += "💊 Medications:\n"
                for med in prescription['medications']:
                    response += f"  • {med.get('name', 'Unknown')}"
                    if med.get('dosage'):
                        response += f" - {med['dosage']}"
                    if med.get('frequency'):
                        response += f" ({med['frequency']})"
                    response += "\n"
            
            if prescription['instructions']:
                response += f"📝 Instructions: {prescription['instructions']}\n"
            
            if prescription['next_visit']:
                response += f"📅 Next visit: {prescription['next_visit']}\n"
            
            response += "\n"
        
        return response
    
    async def _add_appointment(self, user_id: str, data: str) -> str:
        """Add medical appointment."""
        # Implementation for appointment management
        return "📅 Appointment feature coming soon! Please use external appointment systems."
    
    async def _get_appointments(self, user_id: str) -> str:
        """Get user's appointments."""
        # Implementation for appointment retrieval
        return "📅 Appointment feature coming soon! Please use external appointment systems."
    
    async def find_nearby_hospitals(self, location: str, emergency_type: str = "general") -> str:
        """
        Find nearest hospitals or medical facilities using the configured hospital API.
        
        Args:
            location: User location
            emergency_type: Type of emergency or medical need
            
        Returns:
            List of nearby hospitals with contact information
        """
        try:
            if not self.settings.HOSPITAL_API_URL:
                return "Hospital search API not configured. Please contact emergency services if urgent."
                
            # Get coordinates
            coords = await self._get_coordinates(location)
            if not coords:
                return f"Could not find location: {location}"
            
            lat, lon = coords
            
            # Call real hospital API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.settings.HOSPITAL_API_URL}/search",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "type": emergency_type,
                        "limit": 5
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"API error: {response.status_code}")
                    
                hospitals = response.json()
            
            if not hospitals:
                return "No hospitals found nearby. Please contact emergency services if urgent."
            
            response = f"🏥 **Nearby Hospitals/Clinics near {location}**\n\n"
            
            for i, hospital in enumerate(hospitals, 1):
                response += f"**{i}. {hospital.get('name', 'Unknown')}**\n"
                response += f"📍 Address: {hospital.get('address', 'N/A')}\n"
                response += f"📞 Phone: {hospital.get('phone', 'N/A')}\n"
                if hospital.get('distance'):
                    response += f"🚗 Distance: {hospital['distance']}\n"
                if hospital.get('emergency_services'):
                    response += "🚨 24/7 Emergency Services Available\n"
                response += "\n"
            
            # Add emergency information
            response += "🚨 **Emergency Numbers:**\n"
            response += "• Ambulance: 108\n"
            response += "• Police: 100\n"
            response += "• Fire: 101\n"
            response += "• National Emergency: 112\n"
            
            return response
            
        except Exception as e:
            return f"Hospital search error: {str(e)}. Please call emergency services if urgent."
    
    async def _get_coordinates(self, location: str) -> Optional[tuple]:
        """Get latitude and longitude for location."""
        try:
            # Check if location is already coordinates
            if "," in location:
                parts = location.split(",")
                if len(parts) == 2:
                    try:
                        lat = float(parts[0].strip())
                        lon = float(parts[1].strip())
                        return (lat, lon)
                    except ValueError:
                        pass
            
            # Geocode location name
            location_data = self.geolocator.geocode(location)
            if location_data:
                return (location_data.latitude, location_data.longitude)
            
            return None
            
        except Exception:
            return None
    
    async def _search_nearby_hospitals(self, lat: float, lon: float, emergency_type: str) -> List[Dict]:
        """Search for nearby hospitals using configured API."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.settings.HOSPITAL_API_URL}/search",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "type": emergency_type,
                        "limit": 10
                    }
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Hospital API error: {str(e)}")
                return []
    
    async def get_medication_reminder(self, user_id: str) -> str:
        """Get medication reminders for the user."""
        records = self.memory.search("health_record", user_id=user_id)
        
        if not records:
            return "💊 No medication records found. Add your prescriptions first."
        
        medications = records[0]["content"].get("medications", [])
        
        if not medications:
            return "💊 No current medications found."
        
        response = "💊 **Medication Reminders**\n\n"
        
        for med in medications:
            response += f"💊 **{med['medication']}**\n"
            if med['dosage']:
                response += f"📏 Dosage: {med['dosage']}\n"
            if med['frequency']:
                response += f"⏰ Frequency: {med['frequency']}\n"
            if med['prescribed_by']:
                response += f"👨‍⚕️ Prescribed by: {med['prescribed_by']}\n"
            response += "\n"
        
        response += "⏰ **Reminder Tips:**\n"
        response += "• Set phone alarms for medication times\n"
        response += "• Use pill organizers for daily doses\n"
        response += "• Never skip doses without consulting doctor\n"
        response += "• Keep emergency contact handy\n"
        
        return response
