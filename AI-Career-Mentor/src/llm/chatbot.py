import chromadb
from google import genai

# Setup ChromaDB for RAG context
chroma_client = chromadb.PersistentClient(path="./chroma_db")
try:
    collection = chroma_client.get_or_create_collection(name="student_context")
except Exception:
    collection = chroma_client.create_collection(name="student_context")

def update_context(user_id: str, profile: dict, project: dict, roadmap: list):
    """
    Updates the vector store with the student's current plan and profile.
    This acts as the memory for the AI Twin/Chatbot.
    """
    document = f"""
    Student Profile: {profile}
    Assigned Project: {project['title']} - {project['description']}
    Roadmap: {roadmap}
    """
    collection.upsert(
        documents=[document],
        ids=[f"user_{user_id}_context"],
        metadatas=[{"user_id": user_id}]
    )

def chat_with_mentor(user_id: str, message: str, ai_twin_state: dict = None) -> str:
    """
    Chatbot with RAG capabilities. Also incorporates 'AI Twin' state (progress, pace).
    """
    client = genai.Client()
    
    # Retrieve context from ChromaDB
    try:
        results = collection.query(
            query_texts=[message],
            n_results=1,
            where={"user_id": user_id}
        )
        context = results['documents'][0][0] if results['documents'] else "No prior context."
    except Exception:
        context = "Context unavailable."
        
    twin_prompt = ""
    if ai_twin_state:
        twin_prompt = f"""
        [AI Twin Status]: The student is {ai_twin_state.get('progress', 0)}% done. 
        They are currently {ai_twin_state.get('pace', 'on track')}. 
        If they are behind schedule, gently propose an adjusted plan.
        """
        
    system_prompt = f"""
    You are a patient mentor for this student's specific project. 
    Answer only using their context when relevant.
    
    Context: {context}
    {twin_prompt}
    """
    
    # We prepend the system prompt instructions to the message since 
    # some models prefer it or we use system instructions in config.
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt + "\n\nUser Question: " + message
        )
        return response.text
    except Exception as e:
        return f"Sorry, I couldn't process your request right now. ({str(e)})"
