from google.adk import Agent
from adk_app.tools.gemini_tool import generate_shot_prompt

class PromptWriterAgent(Agent):
    name: str = "prompt_writer"
    def run(self, state):
        plan = state["plan"]
        fin = {
            "persona": state.get("persona", "college student"),
            "monthly_budget": state.get("monthly_budget", 600),
            "current_balance": state.get("current_balance", 480),
            "days_until_due": state.get("days_until_due", 10),
            "apr_percent": state.get("apr_percent", 24.99),
            "utilization_percent": state.get("utilization_percent", 32),
            "goal": state.get("user_goal", "avoid interest and build credit"),
            "scene_title": plan["scenes"][0]["title"],
        }
        shot = generate_shot_prompt(fin)
        plan["scenes"][0]["shot_prompt"] = shot
        return {"plan": plan, "shot_prompt": shot}
