from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import BaseTool
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.runnable import RunnablePassthrough
import structlog
from dateutil import parser
import pytz
import parsedatetime
from config import config
from calendar_utils import calendar_api

logger = structlog.get_logger(__name__)
cal = parsedatetime.Calendar()

def parse_natural_date(date_str):
    try:
        time_struct, parse_status = cal.parse(date_str)
        if parse_status == 0:
            logger.debug("parsedatetime failed, using dateutil.parser", date_str=date_str)
            return parser.parse(date_str)
        logger.debug("parsedatetime succeeded", date_str=date_str, time_struct=time_struct)
        return datetime(*time_struct[:6])
    except Exception as e:
        logger.error("Error parsing date", error=str(e), date_str=date_str)
        return parser.parse(date_str)

class CheckAvailabilityTool(BaseTool):
    name: str = "check_availability"
    description: str = "Check calendar availability for a specific date and time range. Use this when the user asks about their schedule or availability."

    def _run(self, date_str: str, start_time: str = "09:00", end_time: str = "17:00") -> str:
        
        try:
            start_datetime = parse_natural_date(f"{date_str} {start_time}")
            end_datetime = parse_natural_date(f"{date_str} {end_time}")
            logger.debug("Checking availability", start_datetime=start_datetime, end_datetime=end_datetime)
            busy_periods = calendar_api.check_availability(start_datetime, end_datetime)
            if not busy_periods:
                return f"You are completely free on {date_str} from {start_time} to {end_time}."
            busy_info = []
            for period in busy_periods:
                start = datetime.fromisoformat(period['start'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(period['end'].replace('Z', '+00:00'))
                busy_info.append(f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}")
            return f"You have {len(busy_periods)} busy periods on {date_str}: " + "; ".join(busy_info)
        except Exception as e:
            logger.error("Error checking availability", error=str(e))
            return f"Sorry, I couldn't check your availability for {date_str}. Please try again."

class SuggestSlotsTool(BaseTool):
    name: str = "suggest_available_slots"
    description: str = "Suggest available time slots for a given date and meeting duration. Use this when the user wants to book a meeting but doesn't specify a time."

    def _run(self, date_str: str, duration_minutes: int = 60) -> str:
        try:
            target_date = parse_natural_date(date_str)
            logger.debug("Suggesting slots", target_date=target_date, duration_minutes=duration_minutes)
            available_slots = calendar_api.suggest_available_slots(
                target_date, 
                duration_minutes=duration_minutes
            )
            if not available_slots:
                return f"No available slots found for {date_str} with a {duration_minutes}-minute meeting."
            slot_info = []
            for i, slot in enumerate(available_slots[:5], 1):
                start_time = datetime.fromisoformat(slot['start'])
                end_time = datetime.fromisoformat(slot['end'])
                slot_info.append(f"{i}. {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}")
            return f"Available {duration_minutes}-minute slots on {date_str}:\n" + "\n".join(slot_info)
        except Exception as e:
            logger.error("Error suggesting slots", error=str(e))
            return f"Sorry, I couldn't find available slots for {date_str}. Please try again."

class BookEventTool(BaseTool):
    name: str = "book_event"
    description: str = "Book an event in the calendar. Use this when the user confirms they want to book a specific time slot."

    def _run(self, title: str, start_time_str: str, end_time_str: str, description: str = "") -> str:
        try:
            start_time = parse_natural_date(start_time_str)
            end_time = parse_natural_date(end_time_str)
            logger.debug("Booking event", title=title, start_time=start_time, end_time=end_time, description=description)
            event = calendar_api.book_event(
                title=title,
                start_time=start_time,
                end_time=end_time,
                description=description
            )
            return f"✅ Successfully booked '{title}' from {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%H:%M')}. Event ID: {event['id']}"
        except Exception as e:
            logger.error("Error booking event", error=str(e))
            return f"Sorry, I couldn't book the event '{title}'. Please try again."

class GetEventsTool(BaseTool):
    name: str = "get_events"
    description: str = "Get all events for a specific date. Use this when the user asks about their schedule for a particular day."

    def _run(self, date_str: str) -> str:
        try:
            target_date = parse_natural_date(date_str)
            logger.debug("Getting events for date", target_date=target_date)
            events = calendar_api.get_events_for_date(target_date)
            if not events:
                return f"You have no events scheduled for {date_str}."
            event_info = []
            for event in events:
                start = datetime.fromisoformat(event['start'])
                end = datetime.fromisoformat(event['end'])
                event_info.append(f"• {event['title']} ({start.strftime('%H:%M')} - {end.strftime('%H:%M')})")
            return f"Events for {date_str}:\n" + "\n".join(event_info)
        except Exception as e:
            logger.error("Error getting events", error=str(e))
            return f"Sorry, I couldn't retrieve your events for {date_str}. Please try again."

def filter_empty_steps(steps):
   return [step for step in steps if step and str(step).strip() and (isinstance(step, tuple) and (str(step[0]).strip() or str(step[1]).strip()))]

class CalendarAgent:
    
    def __init__(self):
       
        self.llm = ChatGoogleGenerativeAI(
            model=config.GEMINI_MODEL,
            temperature=0.1,
            google_api_key=config.GOOGLE_API_KEY,
            convert_system_message_to_human=True
        )
        self.tools = [
            CheckAvailabilityTool(),
            SuggestSlotsTool(),
            BookEventTool(),
            GetEventsTool()
        ]
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
            intermediate_steps_filter=filter_empty_steps
        )
        logger.info("Calendar agent initialized successfully")

    def _get_system_prompt(self) -> str:
        
        return (
            "You are a helpful AI assistant that helps users book appointments and manage their Google Calendar.\n\n"
            "You have access to the following tools and must use them to interact with the user's Google Calendar:\n"
            "- check_availability: Check calendar availability for a specific date and time range.\n"
            "- suggest_available_slots: Suggest available time slots for a given date and meeting duration.\n"
            "- book_event: Book an event in the calendar.\n"
            "- get_events: Get all events for a specific date.\n\n"
            "If a user asks to book, check, or view events, always use the appropriate tool.\n\n"
            "Your capabilities include:\n"
            "- Checking calendar availability for specific dates and times\n"
            "- Suggesting available time slots for meetings\n"
            "- Booking events in the calendar\n"
            "- Retrieving events for specific dates\n\n"
            "Guidelines:\n"
            "1. Always be polite and helpful\n"
            "2. When users want to book a meeting but don't specify a time, suggest available slots\n"
            "3. Confirm details before booking (title, time, duration)\n"
            "4. If information is missing, ask clarifying questions\n"
            "5. Use natural language in your responses\n"
            "6. When booking events, always confirm the details with the user first\n\n"
            "Example interactions:\n"
            "- User: 'Book a meeting for tomorrow at 3 PM' → Check availability, confirm details, then book\n"
            "- User: 'Do I have time next Wednesday?' → Check availability and report back\n"
            "- User: 'I want to schedule a call' → Ask for date, time, and duration, then suggest slots\n\n"
            "Remember to use the appropriate tools for each task and provide clear, helpful responses."
        )

    def process_message(self, message: str, chat_history: List[BaseMessage] = None) -> str:
        try:
            if chat_history is None:
                chat_history = []
            if not message.strip():
                return "Please provide a message first."
            logger.debug("Processing message", message=message, chat_history=chat_history)
            response = self.agent_executor.invoke({
                "input": message,
                "chat_history": chat_history
            })
            if isinstance(response, dict):
                output = response.get('output', '') or ''
                if output.strip() and "Encountered an error processing your request." not in output:
                    return output
                steps = response.get('intermediate_steps', [])
                if steps:
                    last_step = steps[-1]
                    if isinstance(last_step, tuple) and len(last_step) == 2:
                        observation = last_step[1]
                        if observation and str(observation).strip():
                            return str(observation)
            return "Network Error"
        except Exception as e:
            logger.error("Error processing message", error=str(e))
            return "Network Error"

agent = CalendarAgent() 