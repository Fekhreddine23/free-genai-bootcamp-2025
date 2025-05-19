
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.audio_generator import AudioGenerator
gen = AudioGenerator()
fichier_audio = gen.generate_audio({})
print("✅ Audio généré :", fichier_audio)
