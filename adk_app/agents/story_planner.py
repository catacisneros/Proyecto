from adk import Agent
from datetime import date

CORE_OBJECTIVES = [
    "pay_on_time", "avoid_interest",
    "keep_utilization_low", "understand_minimum_vs_full"
]

DEFAULT_SCENE = {
  "title": "First Statement Incoming",
  "shot_prompt": "placeholder, will be set by PromptWriterAgent",
  "duration": 6,
  "learning_focus": ["pay_on_time", "avoid_interest", "understand_minimum_vs_full"]
}

class StoryPlannerAgent(Agent):
    name: str = "story_planner"
    def run(self, state):
        spec = {
            "episode": 1,
            "theme": "credit_card_basics",
            "date": str(date.today()),
            "learner_profile": {
                "level": state.get("level", "beginner"),
                "budget": state.get("monthly_budget")
            },
            "objectives": CORE_OBJECTIVES,
            "scenario": state.get("user_goal", "first month using a new credit card"),
            "scenes": [DEFAULT_SCENE.copy()],
            "rubric": {
                "must_include_keywords": [
                    "due date", "interest", "minimum payment",
                    "statement balance", "utilization"
                ],
                "target_coverage": 0.7
            },
            "branch_labels": [
                "Pay full balance now",
                "Pay minimum and buy concert tickets"
            ]
        }
        return {"plan": spec}
