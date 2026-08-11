#!/usr/bin/env python3
import sys
import asyncio
import edge_tts

async def save_speech(text, output_file, voice="en-US-JennyNeural"):
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: edge_tts_helper.py <text> <output_file>")
        sys.exit(1)
    
    text = sys.argv[1]
    output_file = sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else "en-US-JennyNeural"
    
    # Add venv site-packages to path
    import os
    venv_path = os.path.join(os.path.dirname(__file__), "venv", "lib", "python3.13", "site-packages")
    if venv_path not in sys.path:
        sys.path.insert(0, venv_path)
    
    asyncio.run(save_speech(text, output_file, voice))
