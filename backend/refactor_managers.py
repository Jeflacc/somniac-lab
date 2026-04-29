import os
import re

managers = [
    'state_manager.py',
    'house_manager.py',
    'journal_manager.py',
    'economy_manager.py'
]

for file in managers:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Rename AIInstance to AIAgent
    content = content.replace('AIInstance', 'AIAgent')
    content = content.replace('ai_instances', 'ai_agents')

    # Replace user_id with agent_id in init and class signatures
    # Example: def __init__(self, user_id: int, db_session):
    content = content.replace('def __init__(self, user_id: int, db_session):', 'def __init__(self, agent_id: int, db_session):')
    content = content.replace('def __init__(self, user_id, db_session):', 'def __init__(self, agent_id, db_session):')
    content = content.replace('self.user_id = user_id', 'self.agent_id = agent_id')
    content = content.replace('self.user_id', 'self.agent_id')

    # Replace models.AIAgent.owner_id == self.user_id with models.AIAgent.id == self.agent_id
    content = content.replace('models.AIAgent.owner_id == self.agent_id', 'models.AIAgent.id == self.agent_id')

    # models.Economy.owner_id == self.user_id -> models.Economy.agent_id == self.agent_id
    content = content.replace('models.Economy.owner_id == self.agent_id', 'models.Economy.agent_id == self.agent_id')
    content = content.replace('owner_id=self.agent_id', 'agent_id=self.agent_id')

    # Replace house_state query
    content = content.replace('models.HouseState.owner_id == self.agent_id', 'models.HouseState.agent_id == self.agent_id')
    
    # Replace journal query
    content = content.replace('models.JournalEntry.owner_id == self.agent_id', 'models.JournalEntry.agent_id == self.agent_id')

    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
        
print("Updated managers")
