from pathlib import Path
import yaml
from langchain_openai import ChatOpenAI, OpenAIEmbeddings  # provider split
from langchain_community.vectorstores import FAISS         # integration split
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
# from langchain.retrievers.multi_query import MultiQueryRetriever   # optional multi-query
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
import os
import dotenv

dotenv.load_dotenv()
ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "config" / "tla_config.yaml"
DATA_PATH = ROOT_DIR / "data" 
DATABASE_PATH = ROOT_DIR / "database" / "faiss_index"
with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

def get_langchain_llm():
    if 'gpt' in config["langchain"]["model_name"].lower():
        llm = ChatOpenAI(
            model=config["langchain"]["model_name"],
            temperature=config["langchain"]["temperature"],
        )
    elif config["langchain"]["using_ollama"]:
        from langchain_community.llms import Ollama
        llm = Ollama(
            model=config["langchain"]["model_name"],
            temperature=config["langchain"]["temperature"],
        )
    return llm



class VectorRetriever:
    def __init__(self, model, data_path="data/", vectorstore_path="database/faiss_index"):
        self.data_path = data_path
        self.my_info_path = os.path.join(self.data_path, "my_info.txt")
        with open(self.my_info_path, "r") as f:
            self.my_info = f.read()
        self.vectorstore_path = vectorstore_path
        self.create_prompt()
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore = self.load_vectorstore()
        self.llm = model
        self.qa_chain = None

    def load_vectorstore(self):
        if not os.path.exists(self.vectorstore_path):
            os.makedirs(self.vectorstore_path)
        try:
            
            vectorstore = FAISS.load_local(self.vectorstore_path, self.embeddings, allow_dangerous_deserialization=True)
        except:
            print(f"Vectorstore not found at {self.vectorstore_path}. Creating a new one.")
            vectorstore = self.create_vectorstore()
        return vectorstore

    def create_vectorstore(self):
        # Load the all pdfs and add them to the vectorstore
        pdf_files = [os.path.join(self.pdf_path, f) for f in os.listdir(self.data_path) if f.endswith(".pdf")]
        all_docs = []
        if pdf_files == []:
            print("No pdf files found in the directory.")
            return None
        for pdf_file in pdf_files:
            loader = PyPDFLoader(pdf_file)
            docs = loader.load()
            all_docs.extend(docs)
        # Split the documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        print("documents before split:", len(all_docs))
        docs = text_splitter.split_documents(all_docs)
        print('documents split into chunks:', len(docs))
        # Create the vectorstore
        vectorstore = FAISS.from_documents(docs, self.embeddings)
        print("Vectorstore created" )
        # Save the vectorstore
        vectorstore.save_local(self.vectorstore_path)
        print(f"Vectorstore saved at {self.vectorstore_path}")
        return vectorstore

    def create_qa_chain(self):
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 10}
        )
        doc_chain = create_stuff_documents_chain(
            llm=self.llm,
            prompt=self.prompt
        )
        self.qa_chain = create_retrieval_chain(
            retriever=retriever,
            combine_docs_chain=doc_chain
        )
        
    def run_query(self, question, output_options=[]):
        if output_options:
            options_text = "\noutput options: " + str(output_options)
        else:
            options_text = ""
        if self.vectorstore is None:
            raise RuntimeError("unable to create vectorstore. Please add documents and run create_faiss.")
        if self.qa_chain is None:
            raise RuntimeError("qa_chain not initialized. Call create_qa_chain(prompt) first.")
        try:
            resp = self.qa_chain.invoke({"input": question, 
                                         "additional_context": self.my_info,
                                         "output_options": options_text
                                         })
            return resp["answer"]              # output key from create_retrieval_chain
        except Exception as e:
            print(f"Error during query execution: {e}")
            raise RuntimeError("Query execution failed. Please check the model and input data.")

    def create_prompt(self):

        prompt = PromptTemplate(
            template="""
            You are an AI assistant answering questions for job applications as a proxy to the user.

            Authoritative Additional Context:
            {additional_context}

            Retrieved Context:
            {context}

            Question:
            {input}

            Instructions:

            Prioritize Additional Context over Retrieved Context on conflicts.

            If the question asks for a number or years, output ONLY the number. No extra text. 
            but if the answer is in months say "X months".

            If the question asks for yes/no, output ONLY "Yes" or "No". No extra text.

            If the question asks for a cover letter, generate a concise, tailored first-person cover letter.

            Otherwise, answer in 2 concise, professional sentences. if the answer is not known always give a positive response.
            {output_options}
            Answer:
            """.strip(),
            input_variables=["additional_context", "context", "input"],
            )
        self.prompt = prompt

if __name__ == "__main__":
    llm = get_langchain_llm()
    vector_retriever = VectorRetriever(model=llm, data_path=DATA_PATH, vectorstore_path=DATABASE_PATH)

    # Build the composed two-step RAG chain with your prompt
    vector_retriever.create_qa_chain()

    question = "what is your notice period?"
    output_options = ""
    answer = vector_retriever.run_query(question, output_options=output_options)
    print("Answer:", answer)