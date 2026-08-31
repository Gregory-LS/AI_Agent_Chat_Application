from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, Boolean, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./conversations.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    archived = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

class ArchiveRequest(BaseModel):
    archived: bool

@app.patch("/conversations/{conversation_id}/archive", tags=["conversations"])
def archive_conversation(conversation_id: int, request: ArchiveRequest, db=Depends(get_db)):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conversation.archived = request.archived
    db.commit()
    db.refresh(conversation)
    return {"id": conversation.id, "archived": conversation.archived}
