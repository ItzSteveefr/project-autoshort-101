from enum import Enum
from pydantic import BaseModel

class VideoType(str, Enum):
    MINECRAFT_PARKOUR = "minecraft_parkour"
    SATISFYING = "satisfying"

class AudioTiming(BaseModel):
    word: str
    start_time: float
    end_time: float

class GenerationPrompt(BaseModel):
    topic: str
    style: str = "genz"  # Default to GenZ style
    video_type: VideoType = VideoType.MINECRAFT_PARKOUR  # Default to Minecraft Parkour

class GenerationResponse(BaseModel):
    title: str
    content: str
    video_path: str
