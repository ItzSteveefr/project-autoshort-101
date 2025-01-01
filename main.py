from fastapi import FastAPI, HTTPException
from classes import GenerationPrompt, GenerationResponse, VideoType
from video import generate_genz_content, create_audio, get_word_timings, create_video
from deepgram import DeepgramClient, ClientOptionsFromEnv
from elevenlabs import ElevenLabs
from openai import OpenAI
import os
import uuid

# Initialize clients
openai_client = OpenAI()
deepgram_client = DeepgramClient(api_key=os.environ.get("DEEPGRAM_API_KEY"))
eleven_labs_client = ElevenLabs(api_key=os.environ.get("ELEVEN_API_KEY"))

app = FastAPI(title="GenZ Content Generator")

@app.post("/generate", response_model=GenerationResponse)
async def generate_content(prompt: GenerationPrompt):
    """Generate a GenZ-style video about any topic"""
    try:
        # Create unique filenames for this generation
        temp_audio_path = f"temp_{uuid.uuid4()}.mp3"
        output_video_path = f"output_{uuid.uuid4()}.mp4"
        
        # Generate content
        content = generate_genz_content(openai_client, prompt.topic)
        
        # Create audio
        create_audio(eleven_labs_client, content["content"], temp_audio_path)
        
        # Get word timings
        timings = get_word_timings(deepgram_client, temp_audio_path)
        
        # Create video
        video_path = create_video(
            audio_path=temp_audio_path,
            video_type=prompt.video_type,
            timings=timings,
            output_path=output_video_path
        )
        
        # Clean up temporary audio file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        
        return GenerationResponse(
            title=content["title"],
            content=content["content"],
            video_path=video_path
        )
        
    except Exception as e:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video-types")
async def get_video_types():
    """Get available background video types"""
    return [{"name": t.name, "value": t.value} for t in VideoType]
