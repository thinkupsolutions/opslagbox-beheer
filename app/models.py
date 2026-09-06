from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    customer_type = Column(String, default="Particulier")
    address = Column(String, default="")
    postal_code = Column(String, default="")
    city = Column(String, default="")
    phone = Column(String, default="")
    email = Column(String, default="")
    company_name = Column(String, default="")
    kvk = Column(String, default="")
    monthly_amount = Column(Float, default=0)
    payment_day = Column(Integer, default=1)

class Box(Base):
    __tablename__ = "boxes"
    id = Column(Integer, primary_key=True)
    box_number = Column(String, unique=True, nullable=False)
    tag_number = Column(String, default="")
    rent = Column(Float, default=0)
    status = Column(String, default="Beschikbaar")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer = relationship("Customer")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    box_id = Column(Integer, ForeignKey("boxes.id"), nullable=False)
    amount = Column(Float, default=0)
    payment_date = Column(Date, nullable=False)
    reference = Column(String, default="")
    status = Column(String, default="Betaald")
    customer = relationship("Customer")
    box = relationship("Box")

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    invoice_number = Column(String, unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    box_id = Column(Integer, ForeignKey("boxes.id"), nullable=False)
    amount = Column(Float, default=0)
    due_date = Column(Date, nullable=False)
    paid = Column(Boolean, default=False)
    customer = relationship("Customer")
    box = relationship("Box")
