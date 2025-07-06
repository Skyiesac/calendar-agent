"""
Google Calendar API utilities for the Calendar Booking Agent.
Handles calendar operations like checking availability, suggesting slots, and booking events.
"""

from datetime import datetime, timedelta, time
from typing import List, Dict, Optional, Tuple
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import structlog
from config import config

logger = structlog.get_logger(__name__)

class GoogleCalendarAPI:
    def __init__(self):
        
        self.calendar_id = config.get_calendar_id()
        self.timezone = pytz.timezone(config.TIMEZONE)
        
        try:
           
            credentials = service_account.Credentials.from_service_account_file(
                config.CREDENTIALS_PATH,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            
            self.service = build('calendar', 'v3', credentials=credentials)
            logger.info("Google Calendar API initialized successfully", calendar_id=self.calendar_id)
            
        except Exception as e:
            logger.error("Failed to initialize Google Calendar API", error=str(e))
            raise
    
    def check_availability(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        
        try:
            time_min = start_date.isoformat() + 'Z'
            time_max = end_date.isoformat() + 'Z'
            
            body = {
                'timeMin': time_min,
                'timeMax': time_max,
                'items': [{'id': self.calendar_id}]
            }
            
            events_result = self.service.freebusy().query(body=body).execute()
            busy_periods = events_result['calendars'][self.calendar_id]['busy']
            
            logger.info("Availability checked", 
                       start_date=start_date.isoformat(),
                       end_date=end_date.isoformat(),
                       busy_periods_count=len(busy_periods))
            
            return busy_periods
            
        except HttpError as e:
            logger.error("Failed to check availability", error=str(e))
            raise
    
    def suggest_available_slots(self, 
                              target_date: datetime, 
                              duration_minutes: int = 60,
                              start_hour: int = 9,
                              end_hour: int = 17) -> List[Dict]:
       
        try:
            target_date = self.timezone.localize(target_date)
            
            day_start = target_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            day_end = target_date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
            
            busy_periods = self.check_availability(day_start, day_end)
            
            available_slots = []
            current_time = day_start
            
            while current_time + timedelta(minutes=duration_minutes) <= day_end:
                slot_end = current_time + timedelta(minutes=duration_minutes)
                
                is_available = True
                for busy_period in busy_periods:
                    busy_start = datetime.fromisoformat(busy_period['start'].replace('Z', '+00:00'))
                    busy_end = datetime.fromisoformat(busy_period['end'].replace('Z', '+00:00'))
                    
                    busy_start = busy_start.astimezone(self.timezone)
                    busy_end = busy_end.astimezone(self.timezone)
                    
                    if (current_time < busy_end and slot_end > busy_start):
                        is_available = False
                        break
                
                if is_available:
                    available_slots.append({
                        'start': current_time.isoformat(),
                        'end': slot_end.isoformat(),
                        'duration_minutes': duration_minutes
                    })
                
                
                current_time += timedelta(minutes=30)
            
            logger.info("Available slots suggested", 
                       date=target_date.date().isoformat(),
                       duration_minutes=duration_minutes,
                       slots_count=len(available_slots))
            
            return available_slots
            
        except Exception as e:
            logger.error("Failed to suggest available slots", error=str(e))
            raise
    
    def book_event(self, 
                   title: str, 
                   start_time: datetime, 
                   end_time: datetime,
                   description: str = "",
                   attendees: List[str] = None) -> Dict:
        
        try:
            if start_time.tzinfo is None:
                start_time = self.timezone.localize(start_time)
            if end_time.tzinfo is None:
                end_time = self.timezone.localize(end_time)
            
            event_body = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': config.TIMEZONE,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': config.TIMEZONE,
                },
            }
            
            
            if attendees:
                event_body['attendees'] = [{'email': email} for email in attendees]
            
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event_body
            ).execute()
            
            logger.info("Event booked successfully", 
                       event_id=event['id'],
                       title=title,
                       start_time=start_time.isoformat(),
                       end_time=end_time.isoformat())
            
            return {
                'id': event['id'],
                'title': event['summary'],
                'start_time': event['start']['dateTime'],
                'end_time': event['end']['dateTime'],
                'html_link': event['htmlLink']
            }
            
        except HttpError as e:
            logger.error("Failed to book event", error=str(e))
            raise
    
    def get_events_for_date(self, target_date: datetime) -> List[Dict]:
        
        try:
            target_date = self.timezone.localize(target_date)
            
            day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=day_start.isoformat(),
                timeMax=day_end.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                formatted_events.append({
                    'id': event['id'],
                    'title': event['summary'],
                    'start': start,
                    'end': end,
                    'description': event.get('description', '')
                })
            
            logger.info("Events retrieved for date", 
                       date=target_date.date().isoformat(),
                       events_count=len(formatted_events))
            
            return formatted_events
            
        except HttpError as e:
            logger.error("Failed to get events for date", error=str(e))
            raise
    
    def delete_event(self, event_id: str) -> bool:
        
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info("Event deleted successfully", event_id=event_id)
            return True
            
        except HttpError as e:
            logger.error("Failed to delete event", error=str(e), event_id=event_id)
            return False

calendar_api = GoogleCalendarAPI() 