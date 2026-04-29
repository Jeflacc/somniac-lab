import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace AIInstance with AIAgent
content = content.replace('AIInstance', 'AIAgent')
content = content.replace('ai_instances', 'ai_agents')

# active_ws dict
content = content.replace('active_ws: dict[int, set[WebSocket]] = {} # user_id -> websockets', 'active_ws: dict[int, set[WebSocket]] = {} # agent_id -> websockets')
content = content.replace('async def broadcast_to_user(user_id: int, msg: dict):', 'async def broadcast_to_user(agent_id: int, msg: dict):')
content = re.sub(r'if user_id not in active_ws:', 'if agent_id not in active_ws:', content)
content = re.sub(r'active_ws\[user_id\]', 'active_ws[agent_id]', content)

# Loops
content = re.sub(r'users = db\.query\(models\.User\)\.all\(\)\n\s+for user in users:', 'agents = db.query(models.AIAgent).all()\n            for agent in agents:', content)
content = content.replace('StateManager(user.id, db)', 'StateManager(agent.id, db)')
content = content.replace('JournalManager(user.id, db)', 'JournalManager(agent.id, db)')
content = content.replace('HouseManager(user.id, db)', 'HouseManager(agent.id, db)')
content = content.replace('broadcast_to_user(user.id,', 'broadcast_to_user(agent.id,')
content = content.replace('active_wa_handlers[user.id]', 'active_wa_handlers[agent.id]')
content = content.replace('user.id in active_ws', 'agent.id in active_ws')
content = content.replace('user.id in active_wa_handlers', 'agent.id in active_wa_handlers')

content = content.replace('await asyncio.to_thread(memory.search_memory, user.id,', 'await asyncio.to_thread(memory.search_memory, agent.id,')
content = content.replace('await asyncio.to_thread(memory.add_memory, user.id,', 'await asyncio.to_thread(memory.add_memory, agent.id,')

# WhatsApp queue process loop
content = content.replace('user_id, text, message = await wa_in_queue.get()', 'agent_id, text, message = await wa_in_queue.get()')
content = content.replace('HouseManager(user_id, db)', 'HouseManager(agent_id, db)')
content = content.replace('broadcast_to_user(user_id,', 'broadcast_to_user(agent_id,')
content = content.replace('User {user_id}', 'Agent {agent_id}')

# get_state endpoint
content = content.replace('''@app.get("/api/state")
async def get_state(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    state = StateManager(current_user.id, db)
    house = HouseManager(current_user.id, db)
    economy = EconomyManager(current_user.id, db)''', '''@app.get("/api/state")
async def get_state(agent_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verify ownership
    agent = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id, models.AIAgent.owner_id == current_user.id).first()
    if not agent: raise HTTPException(404, "Agent not found")
    state = StateManager(agent_id, db)
    house = HouseManager(agent_id, db)
    economy = EconomyManager(agent_id, db)''')

# chat endpoint
content = content.replace('''@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db), source: str = "web"):''', '''@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest, agent_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db), source: str = "web"):
    agent = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id, models.AIAgent.owner_id == current_user.id).first()
    if not agent: raise HTTPException(404, "Agent not found")''')

content = content.replace('StateManager(current_user.id, db)', 'StateManager(agent_id, db)')
content = content.replace('HouseManager(current_user.id, db)', 'HouseManager(agent_id, db)')
content = content.replace('EconomyManager(current_user.id, db)', 'EconomyManager(agent_id, db)')
content = content.replace('JournalManager(current_user.id, db)', 'JournalManager(agent_id, db)')
content = content.replace('memory.search_memory, current_user.id,', 'memory.search_memory, agent_id,')
content = content.replace('memory.add_memory, current_user.id,', 'memory.add_memory, agent_id,')
content = content.replace('broadcast_to_user(current_user.id,', 'broadcast_to_user(agent_id,')
content = content.replace('active_wa_handlers[current_user.id]', 'active_wa_handlers[agent_id]')
content = content.replace('current_user.id in active_wa_handlers', 'agent_id in active_wa_handlers')

content = content.replace('db.query(models.AIAgent).filter(models.AIAgent.owner_id == current_user.id).first()', 'agent')

# run_command endpoint
content = content.replace('''@app.post("/api/command")
async def run_command_endpoint(req: CommandRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):''', '''@app.post("/api/command")
async def run_command_endpoint(req: CommandRequest, agent_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    agent = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id, models.AIAgent.owner_id == current_user.id).first()
    if not agent: raise HTTPException(404, "Agent not found")''')

# topup endpoint
content = content.replace('''@app.post("/api/economy/topup")
async def topup(req: TopupRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):''', '''@app.post("/api/economy/topup")
async def topup(req: TopupRequest, agent_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    agent = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id, models.AIAgent.owner_id == current_user.id).first()
    if not agent: raise HTTPException(404, "Agent not found")''')

# websocket
content = content.replace('''@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str = None):''', '''@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str = None, agent_id: int = None):
    if not agent_id:
        await ws.accept()
        await ws.send_json({"type": "error", "msg": "agent_id is required."})
        await ws.close(code=1008)
        return''')

content = content.replace('''    user_id = user.id
    if user_id not in active_ws:
        active_ws[user_id] = set()
    active_ws[user_id].add(ws)
    logger.info(f"[WS] ✅ New connection for user '{username}' (id={user_id}). Total sockets: {len(active_ws[user_id])}")

    state = StateManager(user_id, db)
    house = HouseManager(user_id, db)
    economy = EconomyManager(user_id, db)''', '''    user_id = user.id
    agent = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id, models.AIAgent.owner_id == user_id).first()
    if not agent:
        db.close()
        await ws.send_json({"type": "error", "msg": "Agent not found or access denied."})
        await ws.close(code=1008)
        return

    if agent_id not in active_ws:
        active_ws[agent_id] = set()
    active_ws[agent_id].add(ws)
    logger.info(f"[WS] ✅ New connection for agent_id {agent_id} by user '{username}'. Total sockets: {len(active_ws[agent_id])}")

    state = StateManager(agent_id, db)
    house = HouseManager(agent_id, db)
    economy = EconomyManager(agent_id, db)''')

content = content.replace('''                try:
                    result = await chat_endpoint(req, user, db)''', '''                try:
                    result = await chat_endpoint(req, agent_id, user, db)''')

content = content.replace('''                try:
                    result = await run_command_endpoint(req, user, db)''', '''                try:
                    result = await run_command_endpoint(req, agent_id, user, db)''')

content = content.replace('''db.query(models.AIAgent).filter(models.AIAgent.owner_id == user_id).first()''', '''db.query(models.AIAgent).filter(models.AIAgent.id == agent_id).first()''')

content = content.replace('active_ws[user_id].discard(ws)', 'active_ws[agent_id].discard(ws)')

# Add Agents CRUD
agents_crud = """
class CreateAgentRequest(BaseModel):
    name: str
    base_persona: str = "Helpful and friendly AI assistant."

@app.post("/api/agents")
async def create_agent(req: CreateAgentRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_agent = models.AIAgent(owner_id=current_user.id, name=req.name, base_persona=req.base_persona)
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    
    # Initialize economies and states
    econ = models.Economy(agent_id=new_agent.id)
    house = models.HouseState(agent_id=new_agent.id)
    journal = models.JournalEntry(agent_id=new_agent.id, date_str=time.strftime("%Y-%m-%d"))
    db.add(econ)
    db.add(house)
    db.add(journal)
    db.commit()
    
    return {"id": new_agent.id, "name": new_agent.name, "persona": new_agent.base_persona}

@app.get("/api/agents")
async def list_agents(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    agents = db.query(models.AIAgent).filter(models.AIAgent.owner_id == current_user.id).all()
    return [{"id": a.id, "name": a.name, "persona": a.base_persona, "mood": a.mood} for a in agents]

"""

content = content.replace('@app.get("/health")', agents_crud + '\n@app.get("/health")')

# Replace ai_inst = db.query(models.AIAgent).filter(models.AIAgent.owner_id == current_user.id).first() -> agent
# Actually I already did that with `agent` replacement for chat_endpoint

# Update WA handler usages
content = content.replace('uid', 'agent_id') # in async_wa_chat

# Re-write the file
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated main.py")
