import os
import secrets

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date
from starlette.middleware.sessions import SessionMiddleware

from .database import Base, engine, SessionLocal
from .models import Customer, Box, Payment, Invoice

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Opslagbox Beheer")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", secrets.token_urlsafe(48)),
    https_only=os.getenv("COOKIE_SECURE", "false").lower() == "true",
    same_site="lax",
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "wijzig-mij")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def logged_in(request: Request):
    return request.session.get("authenticated") is True

def number_or_default(value: str, default: float = 0):
    try:
        return float(value.replace(",", ".")) if value.strip() else default
    except ValueError:
        return default

def day_or_default(value: str, default: int = 1):
    try:
        return min(31, max(1, int(value))) if value.strip() else default
    except ValueError:
        return default

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    if not logged_in(request):
        return RedirectResponse("/login", status_code=302)
    customers = db.query(Customer).all()
    boxes = db.query(Box).all()
    payments = db.query(Payment).order_by(Payment.payment_date.desc()).all()
    invoices = db.query(Invoice).all()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "customers": customers,
        "boxes": boxes,
        "payments": payments,
        "invoices": invoices,
        "today": date.today(),
    })

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if not secrets.compare_digest(username, ADMIN_USER) or not secrets.compare_digest(password, ADMIN_PASSWORD):
        return RedirectResponse("/login?error=1", status_code=302)
    request.session.clear()
    request.session["authenticated"] = True
    return RedirectResponse("/", status_code=302)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/customers")
def add_customer(
    request: Request,
    name: str = Form(...),
    customer_type: str = Form("Particulier"),
    address: str = Form(""),
    postal_code: str = Form(""),
    city: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    company_name: str = Form(""),
    kvk: str = Form(""),
    monthly_amount: str = Form(""),
    payment_day: str = Form(""),
    db: Session = Depends(get_db)
):
    if not logged_in(request):
        raise HTTPException(401)
    c = Customer(
        name=name, customer_type=customer_type, address=address,
        postal_code=postal_code, city=city, phone=phone, email=email,
        company_name=company_name, kvk=kvk,
        monthly_amount=number_or_default(monthly_amount), payment_day=day_or_default(payment_day)
    )
    db.add(c); db.commit()
    return RedirectResponse("/#klanten", status_code=302)

@app.post("/customers/{customer_id}/edit")
def edit_customer(
    customer_id: int, request: Request, name: str = Form(...),
    customer_type: str = Form("Particulier"), address: str = Form(""),
    postal_code: str = Form(""), city: str = Form(""), phone: str = Form(""),
    email: str = Form(""), company_name: str = Form(""), kvk: str = Form(""),
    monthly_amount: str = Form(""), payment_day: str = Form(""),
    db: Session = Depends(get_db)
):
    if not logged_in(request):
        raise HTTPException(401)
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(404, "Klant niet gevonden")
    customer.name, customer.customer_type = name, customer_type
    customer.address, customer.postal_code, customer.city = address, postal_code, city
    customer.phone, customer.email = phone, email
    customer.company_name, customer.kvk = company_name, kvk
    customer.monthly_amount = number_or_default(monthly_amount)
    customer.payment_day = day_or_default(payment_day)
    db.commit()
    return RedirectResponse("/?message=Klant+bijgewerkt#klanten", status_code=302)

@app.post("/customers/{customer_id}/delete")
def delete_customer(customer_id: int, request: Request, db: Session = Depends(get_db)):
    if not logged_in(request):
        raise HTTPException(401)
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(404, "Klant niet gevonden")
    in_use = (
        db.query(Box).filter(Box.customer_id == customer_id).first()
        or db.query(Payment).filter(Payment.customer_id == customer_id).first()
        or db.query(Invoice).filter(Invoice.customer_id == customer_id).first()
    )
    if in_use:
        return RedirectResponse("/?error=Verwijderen+kan+niet:+er+zijn+nog+boxen,+betalingen+of+facturen+gekoppeld#klanten", status_code=302)
    db.delete(customer)
    db.commit()
    return RedirectResponse("/?message=Klant+verwijderd#klanten", status_code=302)

@app.post("/customers-with-box")
def add_customer_with_box(
    request: Request,
    name: str = Form(...), customer_type: str = Form("Particulier"),
    address: str = Form(""), postal_code: str = Form(""), city: str = Form(""),
    phone: str = Form(""), email: str = Form(""), company_name: str = Form(""),
    kvk: str = Form(""), monthly_amount: str = Form(""), payment_day: str = Form(""),
    box_number: str = Form(...), tag_number: str = Form(""), rent: str = Form(""),
    status: str = Form("Verhuurd"), db: Session = Depends(get_db)
):
    if not logged_in(request):
        raise HTTPException(401)
    if db.query(Box).filter(Box.box_number == box_number).first():
        return RedirectResponse("/?error=Dit+boxnummer+bestaat+al#klanten", status_code=302)
    customer = Customer(
        name=name, customer_type=customer_type, address=address,
        postal_code=postal_code, city=city, phone=phone, email=email,
        company_name=company_name, kvk=kvk,
        monthly_amount=number_or_default(monthly_amount),
        payment_day=day_or_default(payment_day),
    )
    db.add(customer)
    db.flush()
    db.add(Box(
        box_number=box_number, tag_number=tag_number,
        rent=number_or_default(rent), status=status, customer_id=customer.id,
    ))
    db.commit()
    return RedirectResponse("/?message=Klant+en+box+opgeslagen#klanten", status_code=302)

@app.post("/boxes")
def add_box(
    request: Request,
    box_number: str = Form(...),
    tag_number: str = Form(""),
    rent: str = Form(""),
    status: str = Form("Beschikbaar"),
    customer_id: str = Form(""),
    db: Session = Depends(get_db)
):
    if not logged_in(request):
        raise HTTPException(401)
    cid = int(customer_id) if customer_id else None
    box = Box(box_number=box_number, tag_number=tag_number, rent=number_or_default(rent), status=status, customer_id=cid)
    db.add(box); db.commit()
    return RedirectResponse("/#boxen", status_code=302)

@app.post("/boxes/{box_id}/edit")
def edit_box(
    box_id: int,
    request: Request,
    box_number: str = Form(...),
    tag_number: str = Form(""),
    rent: str = Form(""),
    status: str = Form("Beschikbaar"),
    customer_id: str = Form(""),
    db: Session = Depends(get_db),
):
    if not logged_in(request):
        raise HTTPException(401)
    box = db.get(Box, box_id)
    if not box:
        raise HTTPException(404, "Box niet gevonden")
    duplicate = db.query(Box).filter(Box.box_number == box_number, Box.id != box_id).first()
    if duplicate:
        return RedirectResponse("/?error=Dit+boxnummer+bestaat+al#boxen", status_code=302)
    cid = int(customer_id) if customer_id else None
    if cid is not None and not db.get(Customer, cid):
        return RedirectResponse("/?error=De+gekozen+klant+bestaat+niet#boxen", status_code=302)
    box.box_number = box_number
    box.tag_number = tag_number
    box.rent = number_or_default(rent)
    box.status = status
    box.customer_id = cid
    db.commit()
    return RedirectResponse("/?message=Box+bijgewerkt#boxen", status_code=302)

@app.post("/payments")
def add_payment(
    request: Request,
    customer_id: int = Form(...),
    box_id: int = Form(...),
    amount: float = Form(...),
    payment_date: str = Form(...),
    reference: str = Form(""),
    status: str = Form("Betaald"),
    db: Session = Depends(get_db)
):
    if not logged_in(request):
        raise HTTPException(401)
    p = Payment(
        customer_id=customer_id, box_id=box_id, amount=amount,
        payment_date=date.fromisoformat(payment_date),
        reference=reference, status=status
    )
    db.add(p); db.commit()
    return RedirectResponse("/#betalingen", status_code=302)

@app.post("/invoices")
def add_invoice(
    request: Request,
    invoice_number: str = Form(...),
    customer_id: int = Form(...),
    box_id: int = Form(...),
    amount: float = Form(...),
    due_date: str = Form(...),
    paid: str = Form(""),
    db: Session = Depends(get_db)
):
    if not logged_in(request):
        raise HTTPException(401)
    inv = Invoice(
        invoice_number=invoice_number, customer_id=customer_id, box_id=box_id,
        amount=amount, due_date=date.fromisoformat(due_date), paid=(paid == "on")
    )
    db.add(inv); db.commit()
    return RedirectResponse("/#facturen", status_code=302)
