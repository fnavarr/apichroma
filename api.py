import os
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
# from flask import jsonify
import json
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import OpenAI
from flask_cors import CORS
from typing import List
import shutil

# Load and access environment variables
load_dotenv()
key = os.getenv("OPEN_API_KEY")

# FastAPI app instance
app = FastAPI()

# Working variables
persist_directory = 'db'
pdf_directory = "pdf"

# Initialize the vector DB and retriever outside of endpoint for reuse
loader = PyPDFDirectoryLoader(pdf_directory)
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


# Setup CORS
#app.add_middleware(
# CORSMiddleware,
# allow_origins=["http://localhost:5001"], # Add your frontend origin here
# allow_credentials=True,
# allow_methods=["*"],
# allow_headers=["*"],
# )

def process_llm_response(llm_response):
    result = llm_response['result']
    sources = "\n\n *** Sources:\n" + "\n".join([source.metadata['source'] for source in llm_response["source_documents"]])
    return result + sources

@app.post("/query/")
@cross_origin()
async def query_api(query: Query):
    try:
        llm_response = qa_chain(query.question)
        final_response = process_llm_response(llm_response)
        # print("Mi respuesta a tu pregunta: " + final_response)
        return {"answer": final_response}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_pdfs/")
@cross_origin()
async def upload_pdfs(files: List[UploadFile] = File(...)):
    # print("==> Files tiene: " + File(...))
    try:
        for file in files:
            file_path = os.path.join(pdf_directory, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        # Reload documents
        loader = PyPDFDirectoryLoader(pdf_directory)
        document = loader.load()
        # Create chunks for the new document
        text = text_splitter.split_documents(document)

        # To cleanup, you can delete the collection
        """ vectordb.delete_collection()
        vectordb.persist() """

        # Re-create the Vector DB with the new documents
        vectordb = Chroma.from_documents(documents=text, embedding=embedding, persist_directory=persist_directory)
        vectordb.persist()
        vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding)

        # Update retriever with new vectordb
        global retriever
        retriever = vectordb.as_retriever(search_kwargs={"k": 2})

        global qa_chain
        qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True)

        return {"detail": "PDFs uploaded and processed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/list_files")
@cross_origin()
def list_files():
    try:
        files = [f for f in os.listdir(pdf_directory)]
        return json.dumps({"files": files})    
    except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
