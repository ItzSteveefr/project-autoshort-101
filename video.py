from deepgram import DeepgramClient, PrerecordedOptions
from classes import AudioTiming, VideoType
from elevenlabs import ElevenLabs, save
from openai import OpenAI
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
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
    """Create final video with background and captions using OpenCV"""
    print('Creating video...')
    
    # Get background video path
    video_name = f"{video_type.value}.mp4"
    background_path = os.path.join("assets", "videos", video_name)
    
    if not os.path.exists(background_path):
        raise FileNotFoundError(f"Background video not found: {background_path}. Please add {video_name} to the assets/videos directory.")
    
    # Open video and audio files
    cap = cv2.VideoCapture(background_path)
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Calculate random start frame
    audio_duration = timings[-1].end_time if timings else 30  # Use last word's end time
    required_frames = int(audio_duration * fps)
    max_start_frame = max(0, total_frames - required_frames)
    start_frame = random.randint(0, max_start_frame) if max_start_frame > 0 else 0
    
    # Set up video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    
    # Set up font
    font_size = int(frame_height * 0.07)  # Adjust font size based on video height
    try:
        font = ImageFont.truetype("./assets/Arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Process frames
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    frame_count = 0
    
    while frame_count < required_frames:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Convert frame to PIL Image for text drawing
        frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(frame_pil)
        
        # Find current words based on frame time
        current_time = frame_count / fps
        current_words = [
            timing.word for timing in timings 
            if timing.start_time <= current_time <= timing.end_time
        ]
        
        # Draw text
        if current_words:
            text = " ".join(current_words)
            # Get text size
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Calculate position (center of screen)
            x = (frame_width - text_width) // 2
            y = frame_height - text_height - 50  # 50 pixels from bottom
            
            # Draw text shadow (outline)
            shadow_offset = 2
            for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                draw.text(
                    (x + dx * shadow_offset, y + dy * shadow_offset),
                    text,
                    font=font,
                    fill='black'
                )
            
            # Draw main text
            draw.text((x, y), text, font=font, fill='white')
        
        # Convert back to OpenCV format and write
        frame = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)
        out.write(frame)
        frame_count += 1
    
    # Clean up
    cap.release()
    out.release()
    
    # Combine video with audio using ffmpeg
    temp_video = output_path + '.temp.mp4'
    os.rename(output_path, temp_video)
    os.system(f'ffmpeg -i {temp_video} -i {audio_path} -c:v copy -c:a aac -strict experimental {output_path} -y')
    os.remove(temp_video)
    
    return output_path
