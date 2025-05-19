import os
import tempfile
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple
import shlex

class AudioGenerator:
    def __init__(self):
        self.voices = {
            'male': ['Takumi'],
            'female': ['Kazuha'],
            'announcer': 'Takumi'
        }

        self.audio_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "frontend/static/audio"
        )
        os.makedirs(self.audio_dir, exist_ok=True)

    def validate_conversation_parts(self, parts: List[Tuple[str, str, str]]) -> bool:
        return bool(parts)

    def get_voice_for_gender(self, gender: str) -> str:
        return self.voices.get(gender, ['Takumi'])[0]

    def generate_audio_part(self, text: str, voice_name: str) -> str:
        try:
            temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
            # Remplacez 'mb-jp1' par 'mb'
            command = f'espeak -v mb -s 140 {shlex.quote(text)} --stdout > {temp_wav}'
            subprocess.run(command, shell=True, check=True)

            mp3_file = temp_wav.replace('.wav', '.mp3')
            subprocess.run([
                'ffmpeg', '-y', '-i', temp_wav, '-codec:a', 'libmp3lame', '-qscale:a', '2', mp3_file
            ], check=True)

            os.unlink(temp_wav)
            return mp3_file

        except Exception as e:
            print(f"Erreur génération audio: {str(e)}")
            return None

    def generate_silence(self, duration_ms: int) -> str:
        output_file = os.path.join(self.audio_dir, f'silence_{duration_ms}ms.mp3')
        if not os.path.exists(output_file):
            subprocess.run([
                'ffmpeg', '-f', 'lavfi', '-i',
                f'anullsrc=r=24000:cl=mono:d={duration_ms/1000}',
                '-c:a', 'libmp3lame', '-b:a', '48k',
                output_file
            ])
        return output_file

    def combine_audio_files(self, audio_files: List[str], output_file: str):
        try:
            txt_path = os.path.join(self.audio_dir, "inputs.txt")
            with open(txt_path, 'w') as f:
                for file in audio_files:
                    f.write(f"file '{file}'\n")
            subprocess.run([
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', txt_path, '-c', 'copy', output_file
            ], check=True)
            os.remove(txt_path)
            return True
        except Exception as e:
            print(f"Erreur de combinaison audio : {str(e)}")
            return False

    def generate_audio(self, question: Dict) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.audio_dir, f"question_{timestamp}.mp3")

        try:
            parts = [
                ('Announcer', '次の会話を聞いて、質問に答えてください。', 'male'),
                ('Student', 'すみません、この電車は新宿駅に止まりますか。', 'female'),
                ('Teacher', 'はい、止まります。', 'male')
            ]

            audio_parts = []
            for speaker, text, gender in parts:
                voice = self.get_voice_for_gender(gender)
                print(f"Génération audio pour {speaker} ({gender})")

                audio_file = self.generate_audio_part(text, voice)
                if audio_file:
                    audio_parts.append(audio_file)
                    audio_parts.append(self.generate_silence(500))

            if audio_parts and self.combine_audio_files(audio_parts, output_file):
                return output_file

            raise Exception("Échec de génération audio")

        except Exception as e:
            if os.path.exists(output_file):
                os.unlink(output_file)
            raise Exception(f"Erreur: {str(e)}")