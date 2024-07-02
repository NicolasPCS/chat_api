# IMPORTS
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
import os

import csv
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompt_values import PromptValue

from chain import chain

import uvicorn
import pandas as pd

app = FastAPI()

# Static HTML file handling using Jinja2
templates = Jinja2Templates(directory="templates")

# Global variables
ultima_respuesta = {}
ultima_pregunta = {}
chat_histories = {}
model = 0
feedback_file = 'feedback.csv'

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("pagina_web.html", {"request": request})

@app.get("/health")
def health_check():
    return 'OK'

# JS Associated functions
async def generate_data(message, tab_id):
    global ultima_respuesta
    global ultima_pregunta
    global model
    chat_history = chat_histories[tab_id]
    chat_history_string = ""

    for m in chat_history:
        chat_history_string += f"{m.type}: {m.content} \n"
    resp = ""

    if model == 0:
        async for chunk in chain.astream({"input": message, "chat_history": chat_history}):
            if chunk.content:
                content = chunk.content.replace("\n", "||")
                #print(content)
                resp += chunk.content
                #print(resp)
                yield f"data: {content}\n\n"
    else:
        return
    
    ultima_respuesta[tab_id] = resp
    chat_history.append(HumanMessage(content = message))
    chat_history.append(AIMessage(content = resp))

    if len(chat_history) >= 6:
        chat_history = chat_history[-6:]
    chat_histories[tab_id] = chat_history
    yield "data: done\n\n"

@app.post("/send")
async def send(request: Request):
    global ultima_pregunta

    data = await request.json()
    tab_id = data['tabId']
    if tab_id not in chat_histories:
        chat_histories[tab_id] = []
    ultima_pregunta[tab_id] = data['message']
    return JSONResponse(content = {'status': 'success'})

@app.get("/stream")
def stream(request: Request):
    tab_id = request.query_params['tabId']
    print(f"Respondiendo pregunta de {tab_id}")
    global ultima_pregunta
    return StreamingResponse(generate_data(ultima_pregunta[tab_id], tab_id), media_type='text/event-stream')

@app.post("/new_chat")
async def handle_new_chat(request: Request):
    global chat_histories
    data = await request.json()
    tab_id = data['tabId']
    chat_histories[tab_id] = []
    return JSONResponse(content={'status': f'new chat for {tab_id}'})

# Verificar que el archivo CSV exista y tenga las columnas adecuadas
if not os.path.isfile(feedback_file):
    df = pd.DataFrame(columns=['tabId', 'pregunta', 'respuesta', 'feedback', 'positive'])
    df.to_csv(feedback_file, index=False)

@app.post("/feedback")
async def feedback(request: Request):
    global ultima_respuesta
    global ultima_pregunta

    data = await request.json()
    feedback_text = data.get('feedback')
    positive = data.get('positive')
    tabId = data.get('tabId')

    # Lee el archivo CSV existente
    df = pd.read_csv(feedback_file)

    # Añade el nuevo feedback al DataFrame

    # Añade el nuevo feedback al DataFrame
    question = ultima_pregunta.get(tabId, "")
    answer = ultima_respuesta.get(tabId, "")

    new_feedback = pd.DataFrame([{
            'tabId': tabId, 
            'pregunta': question,
            'respuesta': answer,
            'feedback': feedback_text, 
            'positive': positive
        }])
    df = pd.concat([df, new_feedback], ignore_index=True)

    # Guarda el DataFrame de vuelta al archivo CSV
    df.to_csv(feedback_file, index=False)

    return JSONResponse(content={'status': 'success'})

if __name__ == '__main__':
    load_dotenv()
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', "127.0.0.1")
    uvicorn.run(app, host=host, port=port)