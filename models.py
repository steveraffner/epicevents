import enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# Définition des rôles selon le cahier des charges [cite: 8]
class UserRole(enum.Enum):
    MANAGEMENT = "management"
    COMMERCIAL = "commercial"
    SUPPORT = "support"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False) # On ne stocke jamais le mot de passe en clair 
    role = Column(Enum(UserRole), nullable=False)

    # Relations
    clients = relationship("Client", back_populates="commercial_contact")
    events = relationship("Event", back_populates="support_contact")

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    creation_date = Column(DateTime(timezone=True), server_default=func.now())
    last_contact_date = Column(DateTime(timezone=True), server_default=func.now())

    # Le client est associé à un commercial [cite: 12]
    commercial_contact_id = Column(Integer, ForeignKey("users.id"))
    commercial_contact = relationship("User", back_populates="clients")
    
    contracts = relationship("Contract", back_populates="client")

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    total_amount = Column(Float, nullable=False)
    remaining_amount = Column(Float, nullable=False)
    creation_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="false") # "false" pour non signé, "true" pour signé

    # Le contrat est lié à un client [cite: 30]
    client_id = Column(Integer, ForeignKey("clients.id"))
    client = relationship("Client", back_populates="contracts")
    
    events = relationship("Event", back_populates="contract")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_date_start = Column(DateTime(timezone=True), nullable=True)
    event_date_end = Column(DateTime(timezone=True), nullable=True)
    location = Column(String, nullable=True)
    attendees = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)

    # L'événement est lié à un contrat [cite: 13]
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    contract = relationship("Contract", back_populates="events")

    # L'événement est assigné à un membre du support [cite: 14]
    support_contact_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    support_contact = relationship("User", back_populates="events")