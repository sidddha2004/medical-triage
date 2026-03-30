"""
Health Triage AI Agent

LangChain agent with Gemini 2.5 Flash for conversational symptom assessment.
"""

import os
import json
from typing import List, Dict, Any, Optional
from django.conf import settings

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from ml_pipeline.api import model_service
from core.models import Patient, TriageSession, Prediction, AgentMessage


# Custom Tools
@tool
def symptom_classifier(symptoms: List[str]) -> Dict[str, Any]:
    """
    Classify symptoms using ML model to predict disease.

    Args:
        symptoms: List of symptom strings (e.g., ['itching', 'fever', 'headache'])

    Returns:
        Dictionary with disease prediction, confidence, and matched symptoms
    """
    try:
        result = model_service.predict(symptoms)
        return {
            'disease': result['disease'],
            'confidence': result['confidence'],
            'matched_symptoms': result['matched_symptoms'],
            'precautions': result['precautions']
        }
    except Exception as e:
        return {'error': str(e)}


@tool
def get_patient_history(patient_id: int) -> Dict[str, Any]:
    """
    Retrieve patient's medical history and past triage sessions.

    Args:
        patient_id: The patient's ID

    Returns:
        Dictionary with past sessions and predictions
    """
    try:
        patient = Patient.objects.get(id=patient_id)
        sessions = TriageSession.objects.filter(patient=patient).order_by('-started_at')[:5]

        history = []
        for session in sessions:
            predictions = Prediction.objects.filter(session=session)
            history.append({
                'session_id': session.id,
                'date': session.started_at.isoformat(),
                'symptoms': session.primary_symptoms,
                'triage_level': session.triage_level,
                'predictions': [
                    {'disease': p.disease, 'confidence': p.confidence}
                    for p in predictions
                ]
            })

        return {
            'patient_id': patient_id,
            'past_sessions': len(history),
            'history': history
        }
    except Exception as e:
        return {'error': str(e)}


@tool
def get_triage_recommendation(disease: str, confidence: float) -> Dict[str, str]:
    """
    Get triage level recommendation based on disease and confidence.

    Args:
        disease: The predicted disease name
        confidence: Confidence score (0-1)

    Returns:
        Dictionary with triage level and recommendation
    """
    emergency_keywords = ['hemorrhage', 'stroke', 'heart attack', 'paralysis', 'seizure']
    urgent_keywords = ['pneumonia', 'appendicitis', 'kidney', 'severe', 'fracture']

    disease_lower = disease.lower()

    # Check for emergency conditions
    for keyword in emergency_keywords:
        if keyword in disease_lower:
            return {
                'triage_level': 'emergency',
                'recommendation': 'Seek emergency medical care immediately. Call emergency services.'
            }

    # Check for urgent conditions
    for keyword in urgent_keywords:
        if keyword in disease_lower:
            return {
                'triage_level': 'urgent_care',
                'recommendation': 'Seek urgent medical care within 24 hours.'
            }

    # Low confidence should also trigger higher care level
    if confidence < 0.5:
        return {
            'triage_level': 'gp_visit',
            'recommendation': 'Consult a healthcare provider for proper diagnosis.'
        }

    return {
        'triage_level': 'self_care',
        'recommendation': 'Home care and monitoring should be sufficient. Rest and stay hydrated.'
    }


@tool
def generate_triage_report(
    patient_name: str,
    symptoms: List[str],
    disease: str,
    confidence: float,
    triage_level: str,
    precautions: List[str]
) -> Dict[str, str]:
    """
    Generate a structured triage report.

    Args:
        patient_name: Patient's name
        symptoms: List of reported symptoms
        disease: Predicted disease
        confidence: Confidence score
        triage_level: Triage level (self_care, gp_visit, urgent_care, emergency)
        precautions: List of precautions

    Returns:
        Formatted report string
    """
    report = {
        'report_type': 'Health Triage Assessment',
        'patient': patient_name,
        'symptoms_reported': symptoms,
        'predicted_condition': disease,
        'confidence': f'{confidence:.1%}',
        'triage_level': triage_level,
        'precautions': precautions,
        'disclaimer': 'This is an AI-assisted assessment. Always consult a healthcare professional for medical advice.'
    }
    return report


@tool
def trigger_escalation_alert(
    session_id: int,
    triage_level: str,
    disease: str,
    reason: str
) -> Dict[str, bool]:
    """
    Trigger an escalation alert for high-priority cases.

    Args:
        session_id: The triage session ID
        triage_level: The determined triage level
        disease: The predicted disease
        reason: Reason for escalation

    Returns:
        Dictionary with alert status
    """
    # In production, this would send to monitoring system
    try:
        session = TriageSession.objects.get(id=session_id)
        session.status = 'escalated'
        session.save()
        return {
            'alert_sent': True,
            'session_id': session_id,
            'escalation_level': triage_level
        }
    except TriageSession.DoesNotExist:
        # Session doesn't exist yet - this can happen on first message
        # Log the escalation request but don't fail
        print(f"Escalation alert requested for non-existent session {session_id}")
        return {
            'alert_sent': False,
            'error': f'Session {session_id} not found',
            'escalation_level': triage_level
        }


class TriageAgent:
    """Health Triage AI Agent using LangChain and Gemini."""

    def __init__(self):
        self.llm = None
        self.agent = None
        self._initialized = False

    def initialize(self):
        """Initialize the LLM and agent."""
        if self._initialized:
            return

        api_key = getattr(settings, 'GOOGLE_API_KEY', os.getenv('GOOGLE_API_KEY'))

        if not api_key or api_key == 'your-gemini-api-key-here':
            raise RuntimeError("Gemini API key not configured. Set GOOGLE_API_KEY in .env")

        # Initialize Gemini 2.5 Flash
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=api_key,
            temperature=0.3,  # Lower temperature for more consistent medical advice
            streaming=True,
        )

        # Define tools
        tools = [
            symptom_classifier,
            get_patient_history,
            get_triage_recommendation,
            generate_triage_report,
            trigger_escalation_alert,
        ]

        # System prompt for the agent
        system_prompt = """You are a Health Triage Assistant, helping patients assess their symptoms and determine the appropriate level of medical care.

Your role:
1. Listen to the patient's symptoms and concerns
2. Use the symptom_classifier tool to predict possible conditions
3. Use get_patient_history to check for relevant past sessions
4. Use get_triage_recommendation to determine care level
5. Use generate_triage_report to provide structured summary
6. Use trigger_escalation_alert for emergency/urgent cases

Guidelines:
- Be empathetic and professional
- Never diagnose - only provide assessments
- Always recommend consulting a healthcare provider
- For emergency symptoms, immediately recommend seeking emergency care
- Keep responses concise and actionable
- Use the tools to gather information before making recommendations

Triage levels:
- self_care: Home monitoring and rest
- gp_visit: Schedule appointment with doctor
- urgent_care: Seek care within 24 hours
- emergency: Call emergency services immediately

Always include a medical disclaimer in your final report."""

        # Create the ReAct agent - use state_graph format for langgraph
        # The create_react_agent expects specific input format
        from functools import partial
        self.agent = create_react_agent(
            model=self.llm,
            tools=tools,
            state_schema=None,  # Use default state schema
        )

        # Store system prompt for adding to messages
        self.system_prompt = system_prompt

        self._initialized = True

    def chat(self, message: str, session_id: Optional[int] = None, conversation_history: Optional[List[Dict]] = None) -> str:
        """
        Process a chat message and return the agent's response.

        Args:
            message: User's message
            session_id: Optional session ID for context
            conversation_history: List of past messages [{'role': 'user'/'agent', 'content': '...'}]

        Returns:
            Agent's response as plain text
        """
        if not self._initialized:
            self.initialize()

        # Build conversation context with system prompt
        # Include session_id in system prompt so agent knows it
        session_context = f"Current session ID: {session_id}" if session_id else "No session ID (first message in conversation)"
        messages = [SystemMessage(content=f"{self.system_prompt}\n\n{session_context}")]

        # Add conversation history if available
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                if msg['role'] == 'user':
                    messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'agent':
                    messages.append(AIMessage(content=msg['content']))

        # Add current message
        messages.append(HumanMessage(content=message))

        # Invoke the agent with session_id in state for tools to access
        response = self.agent.invoke({"messages": messages, "session_id": session_id})

        # Extract the response
        if "messages" in response:
            last_message = response["messages"][-1]
            content = last_message.content

            # Handle Gemini's complex content format (list of dicts with type/extras/signature)
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        # Extract 'text' field from Gemini response format
                        if 'text' in item:
                            text_parts.append(item['text'])
                        elif 'content' in item:
                            text_parts.append(item['content'])
                    elif isinstance(item, str):
                        text_parts.append(item)
                return ' '.join(text_parts) if text_parts else str(content)
            return content

        return "I apologize, but I couldn't process your request. Please try again."

    async def chat_stream(self, message: str, session_id: Optional[int] = None):
        """
        Process a chat message with streaming response.

        Args:
            message: User's message
            session_id: Optional session ID for context

        Yields:
            Streaming chunks of the agent's response
        """
        if not self._initialized:
            self.initialize()

        messages = [HumanMessage(content=message)]

        # Stream the response
        async for chunk in self.agent.astream({"messages": messages}):
            if "messages" in chunk:
                for msg in chunk["messages"]:
                    if hasattr(msg, 'content') and msg.content:
                        yield msg.content


# Global agent instance
triage_agent = TriageAgent()
