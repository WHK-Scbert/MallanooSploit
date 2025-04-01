from lib.nodes import BaseNode
import openai
import json

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


