import os
import tempfile
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple
from gtts import gTTS

class AudioGenerator:
    def __init__(self):
        self.audio_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "frontend/static/audio"
        )
        os.makedirs(self.audio_dir, exist_ok=True)

    def generate_audio_part_wav(self, text: str) -> str:
        temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
        tts = gTTS(text, lang='ja')
        temp_mp3 = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False).name
        tts.save(temp_mp3)
        subprocess.run([
            'ffmpeg', '-y', '-i', temp_mp3, '-ar', '48000', '-ac', '2', temp_wav
        ], check=True)
        os.remove(temp_mp3)
        return temp_wav

    def generate_silence_wav(self, duration_ms: int) -> str:
        output_file = os.path.join(self.audio_dir, f'silence_{duration_ms}ms.wav')
        if not os.path.exists(output_file):
            subprocess.run([
                'ffmpeg', '-f', 'lavfi', '-i',
                f'anullsrc=r=48000:cl=stereo:d={duration_ms/1000}',
                output_file
            ], check=True)
        return output_file

    def combine_audio_files_wav(self, audio_files: List[str], output_file: str):
        txt_path = os.path.join(self.audio_dir, "inputs.txt")
        with open(txt_path, 'w') as f:
            for file in audio_files:
                f.write(f"file '{file}'\n")
        subprocess.run([
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', txt_path, '-ar', '48000', '-ac', '2', output_file
        ], check=True)
        os.remove(txt_path)

    def wav_to_mp3(self, input_wav: str, output_mp3: str):
        subprocess.run([
            'ffmpeg', '-y', '-i', input_wav, '-ar', '48000', '-ac', '2', '-b:a', '192k', output_mp3
        ], check=True)

    def generate_audio(self, question: Dict) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        combined_wav = os.path.join(self.audio_dir, f"question_{timestamp}.wav")
        final_mp3 = os.path.join(self.audio_dir, f"question_{timestamp}.mp3")

        try:
            # On attend que question["parts"] soit une liste de tuples (speaker, texte)
            parts = question.get("parts", [])
            if not parts:
                raise Exception("Aucune partie de texte à synthétiser reçue.")

            audio_parts = []
            for speaker, text in parts:
                print(f"Génération audio pour {speaker}")
                wav_file = self.generate_audio_part_wav(text)
                audio_parts.append(wav_file)
                silence_wav = self.generate_silence_wav(500)
                audio_parts.append(silence_wav)

            self.combine_audio_files_wav(audio_parts, combined_wav)
            self.wav_to_mp3(combined_wav, final_mp3)

            # Nettoyage des fichiers temporaires
            for f in audio_parts:
                if os.path.exists(f):
                    os.remove(f)
            if os.path.exists(combined_wav):
                os.remove(combined_wav)

            return final_mp3

        except Exception as e:
            if os.path.exists(final_mp3):
                os.unlink(final_mp3)
            raise Exception(f"Erreur: {str(e)}")

if __name__ == "__main__":
    audio_generator = AudioGenerator()
    question = {
        "parts": [
            ("Announcer", "Texte dynamique 1"),
            ("Student", "Texte dynamique 2"),
            ("Teacher", "Texte dynamique 3")
        ]
    }
    audio_generator.generate_audio(question)
