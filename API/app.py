from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
from lib.config import ip as current_ip
import os
from lib.workflow import SMBCraker_Builder
from lib.map_func import build_nodes

# --- CONFIG ---
IP_FILE = "./target_ip.txt"
RESULT_FILE = "workflow_results.json"

# --- FASTAPI SETUP ---
app = FastAPI(title="MallanooSploit API", version="1.0")

# --- MODELS ---
class IPRequest(BaseModel):
    ip: str

# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {"message": "Welcome to SploitRAG FastAPI API"}

@app.get("/ip")
def get_current_ip():
    return {"ip": current_ip}

@app.post("/ip")
def update_target_ip(req: IPRequest):
    try:
        with open(IP_FILE, "w") as f:
            f.write(req.ip.strip())
        return {"message": "IP updated successfully", "new_ip": req.ip}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run")
def run_workflow():
    try:
        nodes = build_nodes()
        SMB_Cracker_wf = SMBCraker_Builder(nodes)
        results = SMB_Cracker_wf.execute()
        return {"message": "Workflow executed", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results")
def get_last_results():
    if os.path.exists(RESULT_FILE):
        with open(RESULT_FILE, "r") as f:
            data = json.load(f)
        return data
    else:
        raise HTTPException(status_code=404, detail="No result file found")
