from google.adk import Agent
from adk_app.tools.veo_tool import generate_video


class VideoAgent(Agent):
    name: str = "video_agent"
    def run(self, state):
        spec = state["plan"]
        scene = spec["scenes"][0]
        prompt = f"{scene['shot_prompt']} Natural light. Subtle camera pan. Clear UI overlays."
        v = generate_video(prompt=prompt, duration=scene["duration"], aspect_ratio="16:9", resolution="1080p")
        uri = v["gcs_uris"][0] if v["gcs_uris"] else None
        b64 = v["base64_mp4s"][0] if v["base64_mp4s"] else None
        return {"video_uri": uri, "video_b64": b64, "rai": v.get("rai_info", {})}
