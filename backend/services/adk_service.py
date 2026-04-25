import os
import sys
import time
import datetime
import requests
import asyncio
import json
from celery import shared_task
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai.types import HttpRetryOptions
from google.adk.sessions import InMemorySessionService
from google.adk.core.runner import Runner
import google.genai.types as types
import google.adk.tools

# Ensure the parent backend directory is in the path for absolute imports during Celery execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.rag_service import query_module_content

def get_current_date_time() -> str:
    """Returns the current date and time."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@shared_task(name="tasks.generate_quiz")
def generate_quiz_sync(tenant_id: str, module_id: str, topic: str, channel_id: int = None, user_id: int = None):
    # Wrapper for Celery since shared_tasks generally don't run as async
    return asyncio.run(generate_quiz(tenant_id, module_id, topic, channel_id, user_id))

async def generate_quiz(tenant_id: str, module_id: str, topic: str, channel_id: int = None, user_id: int = None):
    """
    An asynchronous, compute-heavy task that uses a multi-agent orchestration layer (Google ADK)
    to perform multi-step reasoning for generating high-quality quizzes.
    Agents: Curriculum -> Retrieval -> Drafting -> Reviewer
    """
    print(f"[ADK Worker] Starting multi-agent quiz generation for tenant {tenant_id}, module {module_id}, topic: {topic}")

    # Tool definitions
    def retrieve_course_material(search_query: str) -> str:
        """
        Use this tool to search the course database and retrieve learning materials, 
        syllabus info, or textbook content based on the user's search_query.
        """
        print(f"[ADK Tool Executed] RAG retrieval triggered for query: {search_query}")
        return query_module_content(tenant_id, module_id, search_query)

    rag_tool = google.adk.tools.FunctionTool(retrieve_course_material)
    
    # Define Agents
    
    # Prevent API rate limit retries
    no_retry_model = Gemini(
        model="gemini-2.5-flash",
        retry_options=HttpRetryOptions(attempts=1) # 1 attempt means no retries
    )

    # 1. Curriculum Agent: Determines learning objectives
    curriculum_agent = Agent(
        name="CurriculumAgent",
        description="Analyzes the topic to determine core learning objectives that must be tested.",
        instruction=(
            "You are an expert Curriculum Designer. "
            "Given a topic, output a concise list of 3-5 core learning objectives that a student should understand about this topic. "
            "Return these objectives as a numbered list."
        ),
        model=no_retry_model
    )

    # 2. Retrieval Agent: Fetches context
    retrieval_agent = Agent(
        name="RetrievalAgent",
        description="Uses the retrieve_course_material tool to fetch specific context for learning objectives.",
        instruction=(
            "You are a Research Assistant. "
            "Given a list of learning objectives, use the retrieve_course_material tool to find relevant course material for EACH objective. "
            "Synthesize the retrieved information into a comprehensive study context document."
        ),
        tools=[rag_tool],
        model=no_retry_model
    )

    # 3. Drafting Agent: Constructs questions
    drafting_agent = Agent(
        name="DraftingAgent",
        description="Constructs quiz questions and plausible distractors based on the retrieved context.",
        instruction=(
            "You are a Quiz Master. "
            "Given the learning objectives and the retrieved study context, draft 3-5 multiple-choice questions. "
            "Each question MUST include: the question text, 4 options (one correct, three plausible distractors), and the correct answer. "
            "Output your draft in JSON format: [{'question': '...', 'options': ['A', 'B', 'C', 'D'], 'correct_answer': 'A'}, ...]"
        ),
        model=no_retry_model
    )

    # 4. Reviewer Agent: Validates factuality
    reviewer_agent = Agent(
        name="ReviewerAgent",
        description="Cross-references the drafted questions against the retrieved source material to verify factuality.",
        instruction=(
            "You are an academic Reviewer. "
            "Given the retrieved study context and the drafted quiz in JSON format, verify that EVERY correct answer is factually supported by the context. "
            "Reject or fix any flawed questions, trivial questions, or obvious distractors. "
            "Return ONLY the final, verified quiz in strict JSON format: [{'question': '...', 'options': ['A', 'B', 'C', 'D'], 'correct_answer': 'A'}, ...]. "
            "Do not include markdown blocks like ```json."
        ),
        model=no_retry_model
    )

    # Orchestration Layer (Basic Sequential Execution in ADK)
    session_service = InMemorySessionService()
    session_id = f"session_{channel_id or int(time.time())}"
    final_quiz_json = "[]"
    
    try:
        # Step 1: Curriculum
        runner1 = Runner(app_name="CragBot-Curriculum", agent=curriculum_agent, session_service=session_service, auto_create_session=True)
        events1 = runner1.run(
            user_id=str(user_id) if user_id else "anonymous",
            session_id=session_id, 
            new_message=types.Content(role="user", parts=[types.Part.from_text(text=f"Determine learning objectives for: {topic}")])
        )
        objectives = " ".join([str(event.message.content) for event in events1 if hasattr(event, "message")])
        print(f"[ADK Worker] Objectives generated: {objectives}")

        # Step 2: Retrieval
        runner2 = Runner(app_name="CragBot-Retrieval", agent=retrieval_agent, session_service=session_service, auto_create_session=True)
        events2 = runner2.run(
            user_id=str(user_id) if user_id else "anonymous",
            session_id=session_id, 
            new_message=types.Content(role="user", parts=[types.Part.from_text(text=f"Find context for these objectives: {objectives}")])
        )
        context = " ".join([str(event.message.content) for event in events2 if hasattr(event, "message")])
        print(f"[ADK Worker] Context retrieved.")

        # Step 3: Drafting
        runner3 = Runner(app_name="CragBot-Drafting", agent=drafting_agent, session_service=session_service, auto_create_session=True)
        events3 = runner3.run(
            user_id=str(user_id) if user_id else "anonymous",
            session_id=session_id, 
            new_message=types.Content(role="user", parts=[types.Part.from_text(text=f"Draft a quiz. Objectives:\n{objectives}\n\nContext:\n{context}")])
        )
        drafted_quiz = " ".join([str(event.message.content) for event in events3 if hasattr(event, "message")])
        print(f"[ADK Worker] Draft complete.")

        # Step 4: Review
        runner4 = Runner(app_name="CragBot-Reviewer", agent=reviewer_agent, session_service=session_service, auto_create_session=True)
        events4 = runner4.run(
            user_id=str(user_id) if user_id else "anonymous",
            session_id=session_id, 
            new_message=types.Content(role="user", parts=[types.Part.from_text(text=f"Review and output final JSON. Context:\n{context}\n\nDrafted Quiz:\n{drafted_quiz}")])
        )
        final_quiz_json = " ".join([str(event.message.content) for event in events4 if hasattr(event, "message")])
        final_quiz_json = final_quiz_json.strip()
        
        # Clean up markdown if the model hallucinates it despite instructions
        if final_quiz_json.startswith("```json"):
            final_quiz_json = final_quiz_json[7:-3].strip()
        elif final_quiz_json.startswith("```"):
            final_quiz_json = final_quiz_json[3:-3].strip()

        print(f"[ADK Worker] Review complete. Final output generated.")

        result_summary = final_quiz_json
    except Exception as e:
        print(f"[ADK Error]: {e}")
        result_summary = f"**Error executing ADK Multi-Agent pipeline:** {e}"
    if channel_id:
        bot_token = os.getenv("DISCORD_BOT_TOKEN")
        if bot_token:
            url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
            headers = {
                "Authorization": f"Bot {bot_token}",
                "Content-Type": "application/json"
            }
            content = f"<@{user_id}>, your asynchronous task is complete!\n\n> {result_summary}" if user_id else f"Your asynchronous task is complete!\n\n> {result_summary}"
            
            try:
                # Send the final document securely back to the Discord channel
                resp = requests.post(url, headers=headers, json={"content": content})
                resp.raise_for_status()
                print(f"[ADK Worker] Successfully posted result to Discord channel {channel_id}.")
            except Exception as e:
                print(f"[ADK Worker] Failed to post result back to Discord: {e}")
    
    return {"status": "success", "summary": result_summary, "tenant_id": tenant_id}