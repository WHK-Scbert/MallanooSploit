from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
from glob import glob
from lib.config import ip as current_ip
from lib.workflow import SMBCraker_Builder, FTPAnonymousCheck_Builder
from lib.map_func import build_nodes
from lib.json_builder import organize_results_by_ip
from lib.ai import AICSNode

app = Flask(__name__)
CORS(app)  # Allow all origins

# --- CONFIG ---
IP_FILE = "./target_ip.txt"
RESULT_DIR = "./results"

# --- AICS Setup ---
aics_node = AICSNode()

# --- ROUTES ---

@app.route("/")
def index():
    return jsonify({"message": "Welcome to SploitRAG Flask API"})

@app.route("/ip", methods=["GET"])
def get_current_ip():
    return jsonify({"ip": current_ip})

@app.route("/ip", methods=["POST"])
def update_target_ip():
    data = request.get_json()
    try:
        with open(IP_FILE, "w") as f:
            f.write(data["ip"].strip())
        return jsonify({"message": "IP updated successfully", "new_ip": data["ip"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/run", methods=["POST"])
def run_workflow():
    data = request.get_json()
    try:
        nodes = build_nodes(data["ip"].strip())
        SMB_Cracker_wf = SMBCraker_Builder(nodes)
        result1 = SMB_Cracker_wf.execute()

        FTPAnonymous_wf = FTPAnonymousCheck_Builder(nodes)
        result2 = FTPAnonymous_wf.execute()

        return jsonify({"message": "Workflow executed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/run_node", methods=["POST"])
def run_node():
    data = request.get_json()
    try:
        nodes = build_nodes(data["ip"].strip())
        result = nodes[data["node"].strip()].execute()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/result", methods=["GET"])
def get_results():
    if not os.path.exists(RESULT_DIR):
        return jsonify({"error": "Results directory not found."}), 404

    filtered_results = {}
    for file_path in glob(os.path.join(RESULT_DIR, "*.json")):
        try:
            with open(file_path, "r") as f:
                result = json.load(f)
                for key, value in result.items():
                    if "success" in value and value["success"]:
                        filtered_results[key] = value
        except Exception as e:
            print(f"[!] Failed to parse {file_path}: {e}")

    if not filtered_results:
        return jsonify({"error": "No valid filtered result data found."}), 404

    filtered_file_path = os.path.join(RESULT_DIR, "filtered_results.json")
    try:
        with open(filtered_file_path, "w") as f:
            json.dump(filtered_results, f, indent=4)
    except Exception as e:
        return jsonify({"error": f"Failed to save filtered results: {e}"}), 500

    try:
        organize_results_by_ip(filtered_file_path)
    except Exception as e:
        return jsonify({"error": "Failed to organize results by IP."}), 500

    result_by_ip_path = os.path.join(RESULT_DIR, "result_by_ip.json")
    if not os.path.exists(result_by_ip_path):
        return jsonify({"error": "result_by_ip.json not found."}), 404

    try:
        with open(result_by_ip_path, "r") as f:
            result_by_ip = json.load(f)
    except Exception as e:
        return jsonify({"error": "Failed to read result_by_ip.json"}), 500

    return jsonify(result_by_ip)

@app.route("/raw_results", methods=["GET"])
def get_all_results():
    if not os.path.exists(RESULT_DIR):
        return jsonify({"error": "Results directory not found."}), 404

    merged_results = {}
    for file_path in glob(os.path.join(RESULT_DIR, "*.json")):
        try:
            with open(file_path, "r") as f:
                result = json.load(f)
                merged_results.update(result)
        except Exception as e:
            print(f"[!] Failed to parse {file_path}: {e}")

    if not merged_results:
        return jsonify({"error": "No valid result data found."}), 404

    return jsonify(merged_results)

@app.route("/chat", methods=["POST"])
def chat_with_aics():
    data = request.get_json()
    try:
        result = aics_node.handle_request(data["ip"].strip(), data["message"].strip())
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- MAIN ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8800)
