# Tech Specs

## Business Goal

We want to create a program that will find lyrics off the internet for a target song in a specific langauge and produce vocabulary to be imported into our database.

## Technical Requirements

- Python 
- FastAPI
- Ollama via the Ollama Python SDK
  -  tinyllama
- Instructor (for structured json output)
- SQLite3 (for database)
- duckduckgo-search (to search for lyrics)


## Api Endpoints

### GetLyrics POST /api/get_lyrics  

- This endpoint goes to duckduckgo and returns the lyrics in the text format. 
This endpoint use a LLM


### Behaviour

This endpoint goes to our agent which is uses the react framework
so that it can go the internet, find the multiples possible version of lyrics and then extract out the correct lyrics and format the lyrics into vocabulary. 


Tools availables : 
 - tools/extract_vocabulary.py
 - tools/get_page_content.py
 - tools/search_web.py

### JSON Request Parameters

- 'message_request' (str): A string that describes the song and/or the artist to get lyrics for a song from the internet. 
- 'artist_name' (str): (optional) name of the artist. 

### JSON Response 

- lyrics (str): The lyrics of the song. 
- vocabulary (list): A list of vocabulary words found in the lyrics. 

### GetVocabulary /api/get_vocabulary 

- This endpoint takes a text file and returns a list of vocabulary words found in the lyrics in a specific json format.

