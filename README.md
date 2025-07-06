# Calendar Booking AI Agent

A full-stack conversational AI agent that helps users book appointments on Google Calendar via natural chat.

## Features

- 🤖 Natural language understanding for appointment booking
- 📅 Google Calendar integration with service account
- 💬 Multi-turn conversations for clarifications
- ⏰ Availability checking and time slot suggestions
- ✅ Confirmation-based booking system
- 🎨 Modern Streamlit chat interface

## Tech Stack

- **Backend**: FastAPI (Python)
- **AI Agent**: LangChain with custom tools
- **Frontend**: Streamlit web app
- **LLM**: Google Gemini Pro (configurable)
- **Calendar**: Google Calendar API with Service Account

## Project Structure

```
calendar-booking-agent/
├── backend/
│   ├── main.py               # FastAPI server
│   ├── agent.py              # LangChain agent with tools
│   ├── calendar_utils.py     # Google Calendar API wrapper
│   └── config.py             # Configuration and credentials
├── frontend/
│   └── app.py                # Streamlit chat UI
├── credentials/
│   └── service_account.json  # Google API credentials (not included)
├── .env                      # Environment variables
├── requirements.txt
└── README.md
```

## Setup Instructions

### 1. Google Calendar Service Account Setup
     Read credentials/README.md for setup

### 2. Environment Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create `.env` file:
   ```bash
   cp env.template .env
   ```

4. Find your Calendar ID:
   It can be your email or any uuid

### 4. Running the Application

1. Start the backend server:
   ```bash
   python start.py
   ```

3. Open your browser to `http://localhost:8501`


## API Endpoints

- `POST /chat` - Send message to AI agent
- `GET /health` - Health check endpoint

## Custom Tools

The agent uses the following LangChain tools:

- `CheckAvailabilityTool` - Check calendar availability
- `SuggestSlotsTool` - Suggest available time slots
- `BookEventTool` - Book confirmed appointments


## Troubleshooting

1. **Calendar not found**: Ensure the calendar ID is correct and the service account has access
2. **Authentication errors**: Verify the service account JSON file is properly placed
3. **API rate limits**: The app includes rate limiting and error handling
