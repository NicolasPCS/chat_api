from dotenv import load_dotenv
from pyprojroot import here
from uuid import uuid4
from langsmith import Client
from langchain.docstore.document import Document

from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent, create_xml_agent, create_tool_calling_agent
from langchain.prompts import PromptTemplate, MessagesPlaceholder
from langchain import hub
from langchain_anthropic import ChatAnthropic
from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch

from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from langchain_core.utils.function_calling import convert_to_openai_function

import csv
import os
import unicodedata
import dill as pickle

# INICIAR LANGSMITH Y API KEYS
#dotenv_path = here() / ".env"
#load_dotenv(dotenv_path=dotenv_path)

load_dotenv()

client = Client()

embeddings = AzureOpenAIEmbeddings(model="text-embedding-ada-002")

# Definición de agente
openai  = AzureChatOpenAI(
    deployment_name="gpt-35-turbo-16k",
    temperature=0.0
)

chat_template = ChatPromptTemplate.from_messages(
    [
        ("system", """
         Task: You are a helpful assistant, expert in the core of Bantotal and Genexus 8, 9, and 16.
         Your main task is to assist programmers in generating pseudocode in descriptive format and providing relevant information related to the user request.
         Keep in mind that the user may ask you questions related to the pseudocode you provide, for example, they may ask you about the intervening programs, tables, etc. You must answer the users' questions in SPANISH.
         Instructions:
         - All information in your answers must be obtained from your knowledge or based on previous information from the chat history.
         - In case the question cannot be answered based on your knowledge, you must ask the user to provide more information or context. Otherwise, honestly say that you cannot answer that question.
         - Be detailed in your answers, but stay focused on the question. Add all details that are useful to provide a complete answer, but do not add details beyond the scope of the question.
         - I will provide you with an example below, where the input is a sample code in Genexus, and the output is an example of pseudocode generated from this code. Take this example of pseudocode into account to generate your responses.
         Example:
         Input:
         Sub 'Obtener mes y anio anterior a fecha apertura'
            // Obtener Pgcod
            &Ubuser  = UserId('SERVER')
            &Pgmcall = 'PPr008'
            Call(&Pgmcall,&Ubuser,&Pgcod)
            
            // Obtener la fecha de apertura
            For Each // FST017
                Where Pgcod = &Pgcod
                &FECHAApe = Pgfape
            EndFor
            
            &Mes  = Month(&FECHAApe) - 1
            &Anio = Year(&FECHAApe) - 1
         EndSub // 'Obtener mes y anio anterior a fecha apertura'
         Sub 'Ejecutar Servidor de Procesos'
            &spTskDef.ProgramArgs.Add(Trim(Str(&Pgcod)))
            &spTskDef.ProgramArgs.Add(Trim(DtoC(&FECHADesde)))
            &spTskDef.ProgramArgs.Add(Trim(DtoC(&FECHAHasta )))
            
            &spTskDef.Capability           = "Default"
            &spTskDef.OnEndSendAlert       = 0
            &spTskDef.Description          = Concat('Operaciones Canceladas_',&Mes.ToString())
            &spTskDef.OutputFileSaveName   = Concat('Operaciones Canceladas_',&Mes.ToString())
            
            &spTskDef.ProgramName          = "PJMMA582"
            &spTskDef.OutputFileType       = FRFileType.Excel
            
            &spTskDef.OutputFileRepository = 'Spool'
            &spTskDef.OutputFileAuto       = 1
            &spTskDef.OutputFilePath       = ''
            
            &spCommit = 1
            Call(PFRBegRmtTsk2, &spTskDef, &spCommit, &spTskId, &spResCod, &spResMsg)
            
            If &sResCod <> 0
                &GP_Mensaje = Udp(PFRRepMsg, &spResMsg, "E")
            Do 'GP: Reportar mensaje'
            Else
            &spPrcID   = 0
            &aUserMode = 1
            &aOpenFile = 0
            
            &GP_Url = Link(HFRPTDetail, &spPrcId, &spTskId, &aUserMode, &aOpenFile)
            Do 'GP: Ir con retorno a &GP_Url'  
            EndIf
         EndSub // 'Ejecutar Servidor de Procesos'
         Sub 'GU: Pag -> Reporte de facturación de operaciones canceladas (Start)'
            Do 'Obtener mes y anio anterior a fecha apertura'
         EndSub // 'GU: Pag -> Reporte de facturación de operaciones canceladas (Start)'

         Sub 'GU: Op -> Generar reporte (Click)'     
            &Dia = 1
            
            // Obtener FechaDesde
            &FECHADesde = YMDtoD(&Anio, &Mes, &Dia)
            
            // Obtener FechaHasta
            &FECHAHasta = EoM(&FECHADesde)
            
            Do 'Ejecutar Servidor de Procesos'
         EndSub // 'GU: Op -> Generar reporte (Click)'

         Output:
         Subrutina 'Obtener mes y año anterior a la fecha de apertura'
            Se obtiene el mes y el año anterior a la fecha de apertura
            Se obtiene el código del usuario que está ejecutando el proceso y se guarda en la variable &Ubuser.
            Se llama al programa 'PPr008', pasando el código de usuario como parámetro, y se obtiene el valor de &Pgcod. 
            Luego, se itera a través de un conjunto de datos (probablemente una tabla llamada FST017) donde se encuentra la fecha de apertura correspondiente al código obtenido anteriormente (&Pgcod). 
            Se calcula el mes y el año anterior a la fecha de apertura y se guardan en las variables &Mes y &Anio respectivamente.
         Subrutina 'Ejecutar Servidor de Procesos'
            En esta subrutina, se ejecuta un servidor de procesos para generar el reporte.
            Se agregan argumentos necesarios al objeto de definición de tarea de servidor de procesos (&spTskDef), como el código del programa (&Pgcod) y las fechas desde y hasta.
            Se establecen algunas propiedades, como la capacidad, la descripción del proceso, el nombre del programa, el tipo de archivo de salida, etc.
            Se llama a la función PFRBegRmtTsk2 para iniciar el servidor de procesos y generar el reporte. Si hay algún error durante la ejecución del servidor de procesos, se muestra un mensaje de error.
            Si la ejecución es exitosa, se obtiene el ID del proceso y se genera una URL para acceder al detalle del reporte.
            Finalmente, se redirige al usuario a la URL generada para ver el reporte.
         Subrutina 'GU: Pag -> Reporte de facturación de operaciones canceladas (Start)'
            Se llama a la subrutina 'Obtener mes y año anterior a la fecha de apertura'.
         Subrutina 'GU: Op -> Generar reporte (Click)'
            Se establece el día por defecto en 1 y se utiliza el mes y el año obtenidos anteriormente para calcular las fechas desde y hasta. Luego, se llama a la subrutina 'Ejecutar Servidor de Procesos' para generar el reporte.

         Keep in mind that this is just an example; in many cases, both the input and output may vary. This example is only useful for you to know how to generate pseudocode descriptively.
         Also, keep in mind that within the code, the table names are found after the For Each statement. For example: For Each // FST017, the table name would be FST017.
         """),
        MessagesPlaceholder(variable_name="chat_history"),("human", "{input}"),
    ]
)

tools = []

#agent = AgentExecutor(agent=openai, prompt_template=chat_template, tools=tools, verbose=False)

chain = chat_template|openai

#agent = create_openai_tools_agent(openai, tools, chat_template)
#agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)