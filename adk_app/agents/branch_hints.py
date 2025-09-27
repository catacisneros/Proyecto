from adk import Agent


class ChoiceHintAgent(Agent):
    name: str = "choice_hint"
    def run(self, state):
        labels = state["plan"]["branch_labels"]
        hints = {
            labels[0]: "Paying the full statement balance avoids interest and keeps utilization low",
            labels[1]: "Paying only the minimum triggers interest on the remaining balance"
        }
        return {"choice_hints": [
            {"label": labels[0], "hint": hints[labels[0]]},
            {"label": labels[1], "hint": hints[labels[1]]},
        ]}
