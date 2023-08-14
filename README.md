# This project is inspired by and uses parts of code from
https://github.com/daveshap/ChromaDB_Chatbot_Public
https://github.com/imartinez/privateGPT

# TODO

- Search internet <input type="checkbox" checked disabled />
- Conversation memory <input type="checkbox" checked disabled />
- Ingest files 
- Ingest directories <input type="checkbox" checked disabled />
- Work with video transcripts <input type="checkbox" checked disabled />
- Ingest video
- Ingest audio/podcasts
- Ingest websites
- ability for offline model to ask questions to online big model like gpt-4 if it does not know the answer
- Text to speech and speech to text interface
- ability to call different expert models for different topics - swarm mode
- ability to spawn autonomous agents 
- Ability to browse the web (maybe headless browser+selenium)
- Web interface
- Client-server architecture to run in the cloud (remember to think about database synchronization and backup)
- ability to use bing chat and google bard
- Personas. Different LLMs trained to behave like coaches, scientists, businessmen. Train open source models on publícally available content of top performers and make the base assistant interact with them to provide you necessary information.
- Ability to execute code in docker container 
- Multiple languages of communication  (encode database entries with universal meaning tokens independent of languages instead of words in different languages) that actually looks a lot like platonic “idea”. Text -> UMT encode -> tokenizer -> LLM -> response tokens -> UMT decode -> text
UMT может быть представлен как граф.
- incorporate MBTI cognitive architecture, pick priorities of functions according to pedagogue type of the user. User INTJ, AI ENTP. 