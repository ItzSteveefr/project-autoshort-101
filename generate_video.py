from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from classes import VideoType, GenerationPrompt
from video import generate_genz_content, create_audio, get_word_timings, create_video
from deepgram import DeepgramClient
from elevenlabs import ElevenLabs
from openai import OpenAI
import os
import uuid
from datetime import datetime

def main():
    # Initialize clients
    openai_client = OpenAI()
    deepgram_client = DeepgramClient(api_key=os.environ.get("DEEPGRAM_API_KEY"))
    eleven_labs_client = ElevenLabs(api_key=os.environ.get("ELEVEN_API_KEY"))
    
    # Generate random topic ideas for inspiration
    topic_ideas = generate_genz_content(openai_client, "give me 3 viral worthy topics for GenZ content")
    print("\n🎬 Welcome to GenZ Video Generator! 🎬")
    print("\nHere are some topic ideas for inspiration:")
    for i, topic in enumerate(topic_ideas.get("content", "").split("\n"), 1):
        if topic.strip():
            print(f"{i}. {topic.strip()}")
    
    # Get topic from user
    print("\n✨ Enter your topic (e.g., 'Why cats are better than dogs')")
    topic = input("Topic: ").strip()
    
    # Get background video type
    print("\n🎥 Choose your background video type:")
    print("1. Minecraft Parkour")
    print("2. Satisfying Videos")
    
    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice == "1":
            video_type = VideoType.MINECRAFT_PARKOUR
            break
        elif choice == "2":
            video_type = VideoType.SATISFYING
            break
        else:
            print("Please enter either 1 or 2")
    
    try:
        print("\n🎯 Generating GenZ content...")
        content = generate_genz_content(openai_client, topic)
        print(f"\n📝 Generated Title: {content['title']}")
        print(f"📝 Generated Script:\n{content['content']}")
        
        # Create unique filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_audio_path = f"temp_{uuid.uuid4()}.mp3"
        output_video_path = os.path.join("Outputs", f"video_{timestamp}.mp4")
        
        print("\n🎤 Creating voiceover...")
        create_audio(eleven_labs_client, content["content"], temp_audio_path)
        
        print("⚙️ Processing word timings...")
        timings = get_word_timings(deepgram_client, temp_audio_path)
        
        print("🎨 Creating final video...")
        video_path = create_video(
            audio_path=temp_audio_path,
            video_type=video_type,
            timings=timings,
            output_path=output_video_path
        )
        
        # Clean up temporary audio file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        
        print(f"\n✅ Video generated successfully!")
        print(f"📁 Output saved to: {video_path}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        return

if __name__ == "__main__":
    main() 