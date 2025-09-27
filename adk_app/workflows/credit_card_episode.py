# adk_app/workflows/credit_card_episode.py
from adk import SequentialAgent, ParallelAgent, LoopAgent

from adk_app.agents.story_planner import StoryPlannerAgent
from adk_app.agents.prompt_writer import PromptWriterAgent
from adk_app.agents.video_agent import VideoAgent
from adk_app.agents.branch_images import ChoiceImageAgent
from adk_app.agents.branch_hints import ChoiceHintAgent
from adk_app.agents.critic import PedagogyCriticAgent

# one episode pass
def episode_once(state: dict) -> dict:
    # plan
    state.update(StoryPlannerAgent().run(state))
    # write shot prompt with Gemini
    state.update(PromptWriterAgent().run(state))
    # generate Veo clip
    state.update(VideoAgent().run(state))
    # branch assets (sequential for now; easy to parallelize later)
    state.update(ChoiceImageAgent().run(state))
    state.update(ChoiceHintAgent().run(state))
    # pedagogy check
    state.update(PedagogyCriticAgent().run(state))
    return state

# simple loop controller (retries once if critic says to revise)
def run_episode_loop(initial_state: dict, max_iters: int = 2) -> dict:
    state = dict(initial_state)
    for _ in range(max_iters):
        state = episode_once(state)
        if state["critic"]["decision"] == "accept":
            break
    return state
