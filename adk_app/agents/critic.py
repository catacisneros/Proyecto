from adk import Agent

import re

def coverage_score(text: str, must: list[str]) -> float:
    text_l = text.lower()
    hits = sum(1 for kw in must if re.search(rf"\\b{re.escape(kw.lower())}\\b", text_l))
    return hits / max(1, len(must))

class PedagogyCriticAgent(Agent):
    name: str = "critic"
    def run(self, state):
        plan = state["plan"]
        must = plan["rubric"]["must_include_keywords"]
        prompt = plan["scenes"][0]["shot_prompt"]
        score = coverage_score(prompt, must)
        missing = [kw for kw in must if kw not in prompt.lower()]
        decision = "accept" if score >= plan["rubric"]["target_coverage"] else "revise"
        if decision == "revise" and missing:
            additions = "; ".join(missing[:2])
            plan["scenes"][0]["shot_prompt"] += f" Overlay labels for: {additions}."
        return {"critic": {"score": score, "decision": decision, "missing": missing}}
