from deepgram import DeepgramClient, PrerecordedOptions
from classes import AudioTiming, VideoType
from elevenlabs import ElevenLabs, save
from openai import OpenAI
import moviepy.editor as mp
import random
import json
import os

def generate_genz_content(openai_client: OpenAI, topic: str) -> dict:
    """Generate GenZ-style content about a given topic"""
    print('Generating GenZ content...')
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": f"""Create a GenZ-style script about {topic}. Use trendy language, slang, and engaging content.
            Make it fun and educational while maintaining GenZ appeal. Use words like "fr fr", "no cap", "bussin", etc.
            Keep it around 30-45 seconds when spoken. Make it viral-worthy.
            
            Return a JSON with:
            - title (3-6 catchy words)
            - content (the actual script)"""
        }],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)

def create_audio(eleven_labs: ElevenLabs, content: str, output_path: str):
    """Generate audio from content using ElevenLabs"""
    print('Creating audio...')
    audio = eleven_labs.generate(
        text=content,
        voice="Adam",  # Using Adam voice for that TikTok feel
        model="eleven_monolingual_v1"
    )
    save(audio, output_path)

def get_word_timings(deepgram: DeepgramClient, audio_path: str) -> list[AudioTiming]:
    """Get word timings from audio file using Deepgram"""
    print('Getting word timings...')
    with open(audio_path, "rb") as file:
        buffer = file.read()

    options = PrerecordedOptions(
        smart_format=True,
        model="nova-2",
        language="en",
        detect_language=True,
        punctuate=True,
        utterances=True,
    )

    response = deepgram.listen.rest.v("1").transcribe_file({"buffer": buffer}, options)
    words = []
    for word in response.results.channels[0].alternatives[0].words:
        timing = AudioTiming(
            word=word.word,
            start_time=word.start,
            end_time=word.end
        )
        words.append(timing)
    return words

def create_video(audio_path: str, video_type: VideoType, timings: list[AudioTiming], output_path: str):
    """Create final video with background and captions"""
    print('Creating video...')
    # Get background video path
    video_name = f"{video_type.value}.mp4"
    background_path = os.path.join("assets", "videos", video_name)
    
    if not os.path.exists(background_path):
        raise FileNotFoundError(f"Background video not found: {background_path}. Please add {video_name} to the assets/videos directory.")
    
    # Load video and audio
    background = mp.VideoFileClip(background_path)
    audio = mp.AudioFileClip(audio_path)
    
    # Calculate random start time (leaving enough duration for the audio)
    max_start = max(0, background.duration - audio.duration - 1)  # -1 for safety margin
    random_start = random.uniform(0, max_start) if max_start > 0 else 0
    
    # Adjust background video: random start time, mute audio, and match duration
    background = (background
                 .subclip(random_start, random_start + audio.duration)
                 .without_audio()  # Completely mute background video
                 .with_volume(0))  # Extra safety for muting
    
    # Add only the voiceover audio
    final_clip = background.with_audio(audio)
    
    # Add captions
    font_path = "./assets/Arial.ttf"
    text_clips = []
    
    for timing in timings:
        text_clip = (mp.TextClip(
            text=timing.word,
            font_size=70,
            color='white',
            stroke_color='black',
            stroke_width=2,
            font=font_path
        )
        .with_position('center')
        .with_start(timing.start_time)
        .with_duration(timing.end_time - timing.start_time))
        text_clips.append(text_clip)
    
    # Combine everything
    final_video = mp.CompositeVideoClip([final_clip] + text_clips)
    final_video.write_videofile(output_path, audio_codec='aac', fps=24, threads=8)
    
    return output_path
