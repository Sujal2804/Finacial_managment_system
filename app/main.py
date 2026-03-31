from fastapi import FastAPI
from .database import engine, Base
from . import models
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import engine, Base, get_db
from . import models, schemas
from .auth import hash_password, verify_password, create_access_token
from .auth import get_current_user
from fastapi import UploadFile, File, Form
import shutil
import os
from .rag.rag_pipeline import process_document, store_embeddings, search
from .rag.llm import generate_answer
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {"message": "Auth system ready 🚀"}

@app.post("/auth/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pwd = hash_password(user.password)

    new_user = models.User(
        email=user.email,
        password=hashed_pwd
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully"}


@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email = form_data.username
    password = form_data.password

    db_user = db.query(models.User).filter(models.User.email == email).first()

    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")

    if not verify_password(password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid password")

    token = create_access_token(data={"sub": db_user.email})

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@app.get("/protected")
def protected_route(current_user = Depends(get_current_user)):
    return {
        "message": "You are authorized",
        "user": current_user.email
    }
UPLOAD_DIR = "uploads"

@app.post("/documents/upload")
def upload_document(
    title: str = Form(...),
    company_name: str = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Save file
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Save metadata in DB
    new_doc = models.Document(
        title=title,
        company_name=company_name,
        document_type=document_type,
        file_path=file_path,
        uploaded_by=current_user.email
    )

    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    return {"message": "Document uploaded successfully"}

@app.get("/documents")
def get_documents(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    docs = db.query(models.Document).all()
    return docs

@app.get("/documents/{doc_id}")
def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return doc

@app.delete("/documents/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

  
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    
    db.delete(doc)
    db.commit()

    return {"message": "Document deleted successfully"}

@app.get("/documents/search")
def search_documents(
    company_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    docs = db.query(models.Document).filter(
        models.Document.company_name.contains(company_name)
    ).all()

    return docs

@app.post("/rag/index-document")
def index_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = process_document(doc.file_path)
    store_embeddings(chunks)

    return {"message": "Document indexed successfully"}

@app.post("/rag/search")
def rag_search(query: str, current_user = Depends(get_current_user)):
    results = search(query)

    context = " ".join(results)

    answer = generate_answer(query, context)

    return {
        "answer": answer,
        "context": results
    }