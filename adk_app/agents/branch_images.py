from adk import Agent

class ChoiceImageAgent(Agent):
    name: str = "choice_image"
    def run(self, state):
        labels = state["plan"]["branch_labels"]
        return {"choice_images": [
            {"label": labels[0], "image_uri": "https://picsum.photos/seed/payfull/640/360"},
            {"label": labels[1], "image_uri": "https://picsum.photos/seed/minpay/640/360"},
        ]}
