from langchain import SerpAPIWrapper
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
import langchain
import chromadb
from chromadb.config import Settings
from time import time
import os
from uuid import uuid4
import re
import warnings
from langchain.chains import RetrievalQA

config = {}
langchain.debug = True
langchain.verbose = True

def read_config(file_path):
    result_dict = {}
    
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()  # Remove leading/trailing whitespaces and newline characters
            if line:
                key, value = line.split('=')
                result_dict[key] = value
    
    return result_dict

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
        return infile.read()

def save_file(filepath, content):
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)

def chatbot(messages):
    llm = ChatOpenAI(temperature=0, model=config['OPENAI_MODEL'], openai_api_key=config['OPENAI_API_KEY'])
    search = SerpAPIWrapper(serpapi_api_key=config['SERPAPI_API_KEY'])

    def kb_query_text(query):
        return collection.query(query_texts=query)

    tools = [
    Tool(
        name="Search",
        func=search.run,
        description="Useful when you need to answer questions about current events. You should ask targeted questions.",
        ),
    Tool(
        name="Knowledge base",
        description="Useful when you need to remember things that were discussed previously or if you need to find specific notes or documents user provided you.",
        func=kb_query_text
        )
    ]

    mrkl = initialize_agent(
        tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, handle_parsing_errors=True
    )

    return mrkl.run(messages)

if __name__ == '__main__':
    config = read_config('.env')

    conversation = list()
    conversation.append({'role': 'system', 'content': open_file('prompts/system_default.txt')})
    user_messages = list()
    all_messages = list()

    chroma_client = chromadb.PersistentClient(path=config['CHROMADB_PERSIST_DIRECTORY'], settings=Settings(anonymized_telemetry=False))
    collection = chroma_client.get_or_create_collection(name="knowledge_base")

    # backup user profile
    save_file('data/user_profile_versions/user_profile_%s.txt' % time(), open_file('data/user_profile.txt'))

    while True:
        # get user input
        text = input('\n\nUSER: ')

        # ingestors
        if 'ingest' in text:
            # find what user is trying to ingest

            # TODO - add unix path matching
            windows_path_pattern = r".*([a-zA-Z]:.*)"
            match = re.search(windows_path_pattern, text)
            ingest_path = match.group(1).replace('"','')

            if os.path.isdir(ingest_path):
                # ingest directory
                print('Ingesting directory: ' + ingest_path)

                from skills.ingest_directory import process_documents
                documents = process_documents(ingest_path)
                ids = []
                for doc in documents:
                    print(doc)
                    collection.add(documents=doc.page_content, ids=[str(uuid4())], metadatas=doc.metadata)
                #print(collection.peek())
                continue
            elif os.path.isfile(ingest_path):
                # ingest file
                warnings.warn('INGESTING FILES NOT IMPLEMENTED' + ingest_path)
                continue
            elif 'http' in text:
                # ingest web resource
                warnings.warn('INGESTING WEB RESOURCES NOT IMPLEMENTED' + ingest_path)
                continue
            else:
                warnings.warn('UNKNOWN INGEST SOURCE' + ingest_path)
                continue

        user_messages.append(text)
        all_messages.append('USER: %s' % text)
        conversation.append({'role': 'user', 'content': text})
        save_file('data/chat_logs/chat_%s_user.txt' % time(), text)


        # update main scratchpad
        if len(all_messages) > 5:
            all_messages.pop(0)
        main_scratchpad = '\n\n'.join(all_messages).strip()


        # search KB, update default system
        current_profile = open_file('data/user_profile.txt')
        kb = 'No KB articles yet'
        if collection.count() > 0:
            results = collection.query(query_texts=[main_scratchpad], n_results=1)
            kb = results['documents'][0][0]
            #print('\n\nDEBUG: Found results %s' % results)
        default_system = open_file('prompts/system_default.txt').replace('<<PROFILE>>', current_profile).replace('<<KB>>', kb)
        #print('SYSTEM: %s' % default_system)
        conversation[0]['content'] = default_system


        # generate a response
        response = chatbot(conversation)
        save_file('data/chat_logs/chat_%s_chatbot.txt' % time(), response)
        conversation.append({'role': 'assistant', 'content': response})
        all_messages.append('CHATBOT: %s' % response)
        print('\n\nCHATBOT: %s' % response)


        # update user scratchpad
        if len(user_messages) > 3:
            user_messages.pop(0)
        user_scratchpad = '\n'.join(user_messages).strip()


        # update user profile
        print('\n\nUpdating user profile...')
        profile_length = len(current_profile.split(' '))
        profile_conversation = list()
        profile_conversation.append({'role': 'system', 'content': open_file('prompts/system_update_user_profile.txt').replace('<<UPD>>', current_profile).replace('<<WORDS>>', str(profile_length))})
        profile_conversation.append({'role': 'user', 'content': user_scratchpad})
        dirty_profile = chatbot(profile_conversation)
        pattern = r"\[{'role': 'assistant', 'content': '([^']+)'}\]"
        match = re.search(pattern, dirty_profile)
        if match != None:
            profile = match.group(1)
            save_file('data/user_profile.txt', profile)
        else:
            print('\n\nNo suitable output for user profile found, not updating')

        # update main scratchpad
        if len(all_messages) > 5:
            all_messages.pop(0)
        main_scratchpad = '\n\n'.join(all_messages).strip()


        # Update the knowledge base
        print('\n\nUpdating KB...')
        if collection.count() == 0:
            # yay first KB!
            kb_convo = list()
            kb_convo.append({'role': 'system', 'content': open_file('prompts/system_instantiate_new_kb.txt')})
            kb_convo.append({'role': 'user', 'content': main_scratchpad})
            article = chatbot(kb_convo)
            new_id = str(uuid4())
            collection.add(documents=[article],ids=[new_id])
            save_file('data/db_logs/log_%s_add.txt' % time(), 'Added document %s:\n%s' % (new_id, article))
        else:
            results = collection.query(query_texts=[main_scratchpad], n_results=1)
            kb = results['documents'][0][0]
            kb_id = results['ids'][0][0]
            
            # Expand current KB
            kb_convo = list()
            kb_convo.append({'role': 'system', 'content': open_file('prompts/system_update_existing_kb.txt').replace('<<KB>>', kb)})
            kb_convo.append({'role': 'user', 'content': main_scratchpad})
            article = chatbot(kb_convo)
            collection.update(ids=[kb_id],documents=[article])
            save_file('data/db_logs/log_%s_update.txt' % time(), 'Updated document %s:\n%s' % (kb_id, article))
            # TODO - save more info in DB logs, probably as YAML file (original article, new info, final article)
            
            # Split KB if too large
            kb_len = len(article.split(' '))
            if kb_len > 1000:
                kb_convo = list()
                kb_convo.append({'role': 'system', 'content': open_file('prompts/system_split_kb.txt')})
                kb_convo.append({'role': 'user', 'content': article})
                articles = chatbot(kb_convo).split('ARTICLE 2:')
                a1 = articles[0].replace('ARTICLE 1:', '').strip()
                a2 = articles[1].strip()
                collection.update(ids=[kb_id],documents=[a1])
                new_id = str(uuid4())
                collection.add(documents=[a2],ids=[new_id])
                save_file('data/db_logs/log_%s_split.txt' % time(), 'Split document %s, added %s:\n%s\n\n%s' % (kb_id, new_id, a1, a2))

            # re-print last response so it is not lost among langchain verbose output
            print('\n\nCHATBOT: %s' % response)