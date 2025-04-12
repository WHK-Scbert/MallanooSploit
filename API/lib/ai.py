from lib.nodes import BaseNode
import openai
from openai import OpenAI
import json
import os
import json
from datetime import datetime
from openai.types.chat import ChatCompletionMessageParam
from lib.prompt import background_prompt

class ChatGPTNode(BaseNode):
    def __init__(self, node_id, name, parameters):
        super().__init__(node_id, name, parameters)
        self.node_type = 'ChatGPTNode'
        self.api_key = parameters.get("api_key")
        self.model = parameters.get("model", "gpt-3.5-turbo")

        # New style: use a client instance
        self.client = openai.OpenAI(api_key=self.api_key)

    def execute(self, input_data=None):
        prompt_template = self.parameters.get("prompt", "Say something about: {input}")
        temperature = float(self.parameters.get("temperature", 0.0))

        # Prompt logic
        if input_data is not None:
            prompt = prompt_template + str(input_data)
        else:
            prompt = prompt_template

        print("This is the prompt \n\n" + prompt)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            content = response.choices[0].message.content.strip()

            # Try to parse JSON response if valid
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                parsed = content

            self.output = {
                "output": "Good",
                "success": {
                    self.name: parsed
                },
                "data": {
                    self.name: {
                        "status": "Good",
                        "details": parsed
                    }
                }
            }

        except Exception as e:
            self.output = {
                "output": "Error",
                "success": {},
                "data": {
                    self.name: {
                        "status": "Error",
                        "details": str(e)
                    }
                }
            }

        return self.output



class AICSNode:
    def __init__(self, 
                 history_dir="./chat_history", 
                 result_file="./results/result_by_ip.json", 
                 model="gpt-3.5-turbo",
                 aics_prompt= background_prompt):
        
        self.history_dir = history_dir
        self.result_file = result_file
        self.model = model
        self.aics_prompt = aics_prompt.strip()

        os.makedirs(self.history_dir, exist_ok=True)

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing OpenAI API key. Set OPENAI_API_KEY env variable.")

        self.client = OpenAI(api_key=api_key)

    def _get_history_path(self, ip: str) -> str:
        return os.path.join(self.history_dir, f"{ip}.json")

    def _get_scan_context(self, ip: str):
        try:
            if os.path.exists(self.result_file):
                with open(self.result_file, "r") as f:
                    results = json.load(f)
                    if ip in results:
                        return {
                            "role": "system",
                            "message": (
                                f"Victim scan data:\n{json.dumps(results[ip], ensure_ascii=False, indent=2)}"
                            ),
                            "timestamp": datetime.now().isoformat()
                        }
        except Exception as e:
            print(f"[!] Failed to load context for {ip}: {e}")
        return None

    def load_history(self, ip: str):
        path = self._get_history_path(ip)

        # Create base history with your custom background prompt
        history = [{
            "role": "system",
            "message": self.aics_prompt,
            "timestamp": datetime.now().isoformat()
        }]

        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    file_data = json.load(f)
                    # Skip re-adding prompt if already present
                    return history + [msg for msg in file_data if msg["role"] != "system"]
            except Exception as e:
                print(f"[!] Failed to load previous chat for {ip}: {e}")
        else:
            scan_context = self._get_scan_context(ip)
            if scan_context:
                history.append(scan_context)

        return history

    def save_history(self, ip: str, history):
        path = self._get_history_path(ip)
        with open(path, "w") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def format_for_chatgpt(self, history: list) -> list[ChatCompletionMessageParam]:
        return [
            {
                "role": h["role"],
                "content": h.get("message", "")  # convert "message" -> "content"
            }
            for h in history
            if h and "role" in h and ("message" in h or "content" in h)
        ]


    def query_chatgpt(self, history: list) -> str:
        try:
            messages = self.format_for_chatgpt(history)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.6,
                max_tokens=500
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[!] ChatGPT error: {e}")
            return "⚠️ Error getting response from AI."

    def handle_request(self, ip: str, message: str) -> dict:
        ip = ip.strip()
        history = self.load_history(ip)

        user_entry = {
            "role": "user",
            "message": message.strip(),
            "timestamp": datetime.now().isoformat()
        }
        history.append(user_entry)

        ai_response = self.query_chatgpt(history)

        ai_entry = {
            "role": "assistant",  # ✅ Valid
            "message": ai_response,
            "timestamp": datetime.now().isoformat()
        }
        history.append(ai_entry)

        self.save_history(ip, history)

        return {
            "ip": ip,
            "response": ai_response,
            "history": history[-10:]  # Last 10 for frontend display
        }