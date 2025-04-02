from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
from lib.config import ip as current_ip
import os
from lib.workflow import SMBCraker_Builder, FTPAnonymousCheck_Builder
from lib.map_func import build_nodes
from glob import glob

# --- CONFIG ---
IP_FILE = "./target_ip.txt"
RESULT_DIR = "./results"  # Folder containing multiple result JSON files

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

# @app.post("/run")
# def run_workflow():
#     try:
#         nodes = build_nodes()
#         SMB_Cracker_wf = SMBCraker_Builder(nodes)
#         results = SMB_Cracker_wf.execute()
#         return {"message": "Workflow executed", "results": results}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.post("/run")
def run_workflow(req: IPRequest):
    try:
        nodes = build_nodes(req.ip.strip())
        SMB_Cracker_wf = SMBCraker_Builder(nodes)
        result1 = SMB_Cracker_wf.execute()

        FTPAnnonymous_wf = FTPAnonymousCheck_Builder(nodes)
        result2 = FTPAnnonymous_wf.execute()
        return {"message": "Workflow executed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @app.post("/run")
# def run_workflow():
#     try:
#         nodes = build_nodes()
#         SMB_Cracker_wf = SMBCraker_Builder(nodes)
#         results = SMB_Cracker_wf.execute()
#         return {"message": "Workflow executed", "results": results}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.get("/result")
def get_results():
    if not os.path.exists(RESULT_DIR):
        raise HTTPException(status_code=404, detail="Results directory not found.")

    filtered_results = {}

    for file_path in glob(os.path.join(RESULT_DIR, "*.json")):
        try:
            with open(file_path, "r") as f:
                result = json.load(f)
                
                for key, value in result.items():
                    if "success" in value and value["success"]:
                        filtered_results[key] = value

        except json.JSONDecodeError as e:
            print(f"[!] Error parsing {file_path}: {e}")
        except Exception as e:
            print(f"[!] Failed to read {file_path}: {e}")

    if not filtered_results:
        raise HTTPException(status_code=404, detail="No valid filtered result data found.")

    # Save the filtered results to a file
    filtered_file_path = os.path.join(RESULT_DIR, "filtered_results.json")
    try:
        with open(filtered_file_path, "w") as f:
            json.dump(filtered_results, f, indent=4)
        print(f"[💾] Filtered results saved to {filtered_file_path}")
    except Exception as e:
        print(f"[!] Failed to write filtered results: {e}")

    return filtered_results



@app.get("/raw_results")
def get_all_results():
    if not os.path.exists(RESULT_DIR):
        raise HTTPException(status_code=404, detail="Results directory not found.")

    merged_results = {}

    for file_path in glob(os.path.join(RESULT_DIR, "*.json")):
        try:
            with open(file_path, "r") as f:
                result = json.load(f)
                merged_results.update(result)  # Merge top-level keys (e.g. node IDs)
        except json.JSONDecodeError as e:
            print(f"[!] Error parsing {file_path}: {e}")
        except Exception as e:
            print(f"[!] Failed to read {file_path}: {e}")

    if not merged_results:
        raise HTTPException(status_code=404, detail="No valid result data found.")
    
    return merged_results
