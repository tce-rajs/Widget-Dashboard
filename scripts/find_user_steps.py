import json

path = r'C:\Users\v_CrystalQA3\.gemini\antigravity\brain\f3079d64-eabf-438b-bac4-f5596cf2bcbd\.system_generated\logs\transcript.jsonl'
with open(path, 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        if data.get('type') == 'USER_INPUT':
            content = data.get('content', '')
            print(f"Step {data.get('step_index')}: {content}")
