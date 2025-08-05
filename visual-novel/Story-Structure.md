# Visual Novel Story Structure

## Core Framework

- Linear progression through scenes
- Each scene features one character with the player
- Key decision points that lead to specific branches
- All interactions flow naturally from one to the next

## Story Data Structure Example

This is an example of a story scene in JSON format that is stored in the outputs/scenes/ directory.

```json

{
    id: "scene001",
    title: "Welcome to Japan",
    location_id: "apartment",
    character_id: "alex",
    dialog: {
        "000": {
            speaker: "player",
            japanese: "あなたは新しいアパートにおり、朝日の光が窓の中を流すように、あなたは起きた。",
            english: "You wake up in your new apartment in Japan. The morning sunlight streams through the blinds as you hear someone in the kitchen.",
            default_next_id: "001"
        },
        "001": {
            speaker: "alex",
            japanese: "おはよう！起きた？",
            english: "Oh, you're up! Good morning!",
            choices: [
                {
                    english: "Good morning. You must be Alex?",
                    japanese: "おはようございます。アレックスさんですか？"
                    next_id: "002"
                },
                ...
            ]
        }
        ...
        "030": {
            speaker: "alex",
            japanese: "...",
            english: "See you later, remember to visit the post office!"
            next_scene_id: "scene003"
        }
        
    }
}
```
- speaker is always the player or another character
- there is no narrator, the player's inner monologue would act like narration when needed.
- if there is no choices that the default_next_id will transition to the next scene
- choices are always from the perspective of the player

Sometimes you want to have a response for a specific choice but the choice always leads to the next default is so there there is a nested response eg.

```json
{
    "id": "scene002",
    "dialog": {
        "000": {
            "speaker": "alex",
            "japanese": "おはよう！起きた？",
            "english": "Oh, you're up! Good morning!",
            "default_next_id": "001",

            "choices": [
                {
                    "english": "Good morning. You must be Alex?",
                    "japanese": "おはようございます。アレックスさんですか？",
                    "response": {
                        "speaker": "alex",
                        "japanese": "そうだよ！アレックスです。",
                        "english": "That's right! I'm Alex. "
                    }
                },
                {
                    "english": "Hello. Nice to meet you.",
                    "japanese": "こんにちは。はじめまして。",
                    "response": {
                        "speaker": "alex",
                        "japanese": "はじめまして！アレックスです。日本に来たばかりだね？",
                        "english": "Nice to meet you! I'm Alex. You just arrived in Japan"
                    }
                }
            ]
        }
    }

}






```


## Story Structure


### Chapter 1 : First Day in Japan

1. **Scene 1**: Player wakes up in their apartment, Alex (roommate) welcomes them to Japan
2. **Scene 2**: Alex gives basic information about the neighborhood and language school
3. **Scene 3**: Player arrives at language school, meets Yamamoto Sensei
4. **Scene 4**: First basic Japanese lesson with Yamamoto
5. **Scene 5**: Yamamoto assigns homework - visit the post office to mail a form


### Chapter 2: Getting Oriented
1. **Scene 1**: Visit to post office, meeting Tanaka Hiroshi
2. **Scene 2**: Language challenge with forms (player practices formal Japanese)
3. **Scene 3**: Return to apartment, Alex suggests visiting café for practice
4. **Scene 4**: Visit to café, meeting Nakamura Yuki