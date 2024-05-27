import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import OpenAI

# Load and access environment variables
load_dotenv()
key = os.getenv("OPEN_API_KEY")

# FastAPI app instance
app = FastAPI()

# Working variables
my_main_prompt = "Proporciona un pequeño resumen de cada uno de los capitulos de la novela."
persist_directory = 'db'

# Initialize the vector DB and retriever outside of endpoint for reuse
loader = PyPDFDirectoryLoader("pdf")
document = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
text = text_splitter.split_documents(document)
embedding = OpenAIEmbeddings()

vectordb = Chroma.from_documents(documents=text, embedding=embedding, persist_directory=persist_directory)
vectordb.persist()
vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding)
retriever = vectordb.as_retriever(search_kwargs={"k": 2})

llm = OpenAI(openai_api_key=key)
qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True)

class Query(BaseModel):
    question: str

def process_llm_response(llm_response):
    result = llm_response['result']
    sources = "\n\nSources:\n" + "\n".join([source.metadata['source'] for source in llm_response["source_documents"]])
    return result + sources

@app.post("/query/")
async def query_api(query: Query):
    try:
        llm_response = qa_chain(query.question)
        final_response = process_llm_response(llm_response)
        return {"answer": final_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
