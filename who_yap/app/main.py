from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.supabase_client import supabase

from typing import List, Optional
from sentence_transformers import SentenceTransformer
import tempfile
import os
import datetime
from app.core.llama3_client import llama3_chat

app = FastAPI(title="WhoYap API")

# CORS for all origins (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load embedding model once
embedding_model = SentenceTransformer("BAAI/bge-base-en-v1.5")

@app.on_event("startup")
def test_supabase_connection():
    try:
        resp = supabase.table("group_chats").select("id").limit(1).execute()
        print("Supabase connection successful.")
    except Exception as e:
        print(f"Supabase connection failed: {e}")

@app.get("/")
def root():
    return {"status": "ok", "supabase_url": supabase.url}

@app.get("/health")
def health_check():
    try:
        resp = supabase.table("group_chats").select("id").limit(1).execute()
        return {"supabase": "ok", "details": resp.data}
    except Exception as e:
        return {"supabase": "error", "error": str(e)}

# --- 1. Upload WhatsApp .txt file ---
@app.post("/upload")
def upload_file(username: str = Form(...), file: UploadFile = File(...)):
    # Save file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name
    # Return temp file path (in real app, use a better storage)
    return {"temp_path": tmp_path, "filename": file.filename}

# --- 2. Parse file, store chats/messages/participants ---
@app.post("/parse")
def parse_file(username: str = Form(...), chat_name: str = Form(...), temp_path: str = Form(...)):
    # Parse WhatsApp .txt file
    participants = set()
    messages = []
    with open(temp_path, "r", encoding="utf-8") as f:
        for line in f:
            # Simple WhatsApp export format: '12/31/20, 10:00 PM - John Doe: Hello!'
            try:
                if " - " in line and ": " in line:
                    ts_part, rest = line.split(" - ", 1)
                    sender, msg = rest.split(": ", 1)
                    timestamp = datetime.datetime.strptime(ts_part, "%m/%d/%y, %I:%M %p")
                    participants.add(sender.strip())
                    messages.append({
                        "sender_name": sender.strip(),
                        "timestamp": timestamp.isoformat(),
                        "message_text": msg.strip()
                    })
            except Exception:
                continue
    # Store group_chat
    group_chat = supabase.table("group_chats").insert({
        "chat_name": chat_name,
        "uploaded_by_username": username
    }).execute().data[0]
    group_chat_id = group_chat["id"]
    # Store participants
    participant_map = {}
    for name in participants:
        p = supabase.table("participants").insert({
            "group_chat_id": group_chat_id,
            "name_on_whatsapp": name
        }).execute().data[0]
        participant_map[name] = p["id"]
    # Store messages and embeddings
    for m in messages:
        part_id = participant_map.get(m["sender_name"])
        msg_row = supabase.table("messages").insert({
            "group_chat_id": group_chat_id,
            "participant_id": part_id,
            "timestamp": m["timestamp"],
            "message_text": m["message_text"]
        }).execute().data[0]
        # Embedding
        emb = embedding_model.encode([m["message_text"]])[0].tolist()
        supabase.table("message_embeddings").insert({
            "message_id": msg_row["id"],
            "embedding": emb
        }).execute()
    os.remove(temp_path)
    return {"group_chat_id": group_chat_id, "participants": list(participants), "message_count": len(messages)}

# --- 3. Create game session ---
@app.post("/create-session")
def create_session(username: str = Form(...), group_chat_id: str = Form(...)):
    session = supabase.table("game_sessions").insert({
        "group_chat_id": group_chat_id,
        "created_by_username": username
    }).execute().data[0]
    return {"session_id": session["id"]}

# --- 4. Request to join session ---
@app.post("/request-join")
def request_join(username: str = Form(...), session_id: str = Form(...)):
    req = supabase.table("join_requests").insert({
        "session_id": session_id,
        "requested_by_username": username,
        "status": "pending"
    }).execute().data[0]
    return {"request_id": req["id"]}

# --- 5. Approve/decline join request ---
@app.post("/approve-join")
def approve_join(request_id: str = Form(...), approve: bool = Form(...)):
    status = "approved" if approve else "declined"
    supabase.table("join_requests").update({"status": status}).eq("id", request_id).execute()
    return {"request_id": request_id, "status": status}

# --- 6. Get next quiz question ---
@app.get("/next-question")
def next_question(session_id: str):
    # Pick a random message for the session's group_chat
    session = supabase.table("game_sessions").select("group_chat_id").eq("id", session_id).execute().data[0]
    group_chat_id = session["group_chat_id"]
    messages = supabase.table("messages").select("id, message_text, participant_id").eq("group_chat_id", group_chat_id).execute().data
    import random
    msg = random.choice(messages)
    correct_participant = msg["participant_id"]
    # Get all participants
    participants = supabase.table("participants").select("id, name_on_whatsapp").eq("group_chat_id", group_chat_id).execute().data
    # Pick 3-4 options
    options = random.sample([p for p in participants if p["id"] != correct_participant], k=min(3, len(participants)-1))
    options.append(next(p for p in participants if p["id"] == correct_participant))
    random.shuffle(options)
    return {
        "message_id": msg["id"],
        "message_text": msg["message_text"],
        "options": [o["name_on_whatsapp"] for o in options],
        "correct_answer": next(o["name_on_whatsapp"] for o in options if o["id"] == correct_participant)
    }

# --- 7. Submit answer ---
@app.post("/submit-answer")
def submit_answer(session_id: str = Form(...), player_username: str = Form(...), message_id: str = Form(...), selected_participant_id: str = Form(...)):
    # Get correct participant
    msg = supabase.table("messages").select("participant_id").eq("id", message_id).execute().data[0]
    is_correct = (msg["participant_id"] == selected_participant_id)
    supabase.table("session_answers").insert({
        "session_id": session_id,
        "player_username": player_username,
        "message_id": message_id,
        "selected_participant_id": selected_participant_id,
        "is_correct": is_correct
    }).execute()
    return {"is_correct": is_correct}

# --- 8. Vector similarity search endpoint ---
@app.post("/search")
def search_similar(group_chat_id: str = Form(...), query: str = Form(...)):
    # Embed query
    emb = embedding_model.encode([query])[0].tolist()
    # Use Supabase RPC or raw SQL for vector search (pseudo, as supabase-py may not support pgvector natively)
    # Here, just return a stub
    return {"results": []}  # Implement with custom SQL or RPC in production 

@app.post("/llama3-chat")
def chat_with_llama3(prompt: str = Form(...)):
    response = llama3_chat(prompt)
    return {"response": response} 