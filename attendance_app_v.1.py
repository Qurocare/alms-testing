import os
import streamlit as st
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import smtplib
from email.message import EmailMessage

# ✅ Declare the base
Base = declarative_base()

# ✅ Establish database connection
try:
    db_url = st.secrets["connections"]["attendance_db"]["url"]
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    conn = Session()
    st.success("✅ Database connected successfully!")

    # Print the database URL to check where it's being stored
    st.write(f"Database URL: {db_url}")

except Exception as e:
    st.error(f"❌ Database connection failed: {e}")

# ✅ Define Models
class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    passkey = Column(String, nullable=False)
    email = Column(String, nullable=False)
    registered_id = Column(String, nullable=False)
    contact_number = Column(String, nullable=False)

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    registered_id = Column(String, nullable=False)
    clock_in = Column(DateTime, nullable=True)
    clock_out = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)

class Leave(Base):
    __tablename__ = "leaves"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    registered_id = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    reason = Column(String, nullable=False)

# ✅ Create all tables
Base.metadata.create_all(engine)

# ✅ Initialize session
Session = sessionmaker(bind=engine)
session = Session()

# ✅ Initialize session state
if "current_stage" not in st.session_state:
    st.session_state.current_stage = "login"

if "clock_in_time" not in st.session_state:
    st.session_state.clock_in_time = None

# ✅ Streamlit App
st.title("Attendance and Leave Management System")

# ✅ Login stage
if st.session_state.current_stage == "login":
    st.header("Qurocare - ALMS Portal")
    employee_names = ["Select"] + [e.name for e in session.query(Employee).all()]
    name = st.selectbox("Select your name", employee_names)

    if name == "Select":
        st.warning("Please select your name.")
        st.stop()

    passkey = st.text_input("Enter your passkey", type="password")
    if st.button("Next"):
        employee = session.query(Employee).filter_by(name=name).first()
        if employee and employee.passkey == passkey:
            st.success("✅ Login successful!")
            st.session_state.current_stage = "main"
            st.session_state.logged_in_user = {
                "name": employee.name,
                "email": employee.email,
                "registered_id": employee.registered_id,
            }
        else:
            st.error("❌ Invalid passkey. Please try again.")

# ✅ Main stage
elif st.session_state.current_stage == "main":
    user = st.session_state.logged_in_user
    st.header(f"Welcome, {user['name']}")

    st.subheader("Attendance")
    if st.session_state.clock_in_time is None:
        if st.button("Clock In"):
            st.session_state.clock_in_time = datetime.now()
            st.success(f"Clocked in at {st.session_state.clock_in_time.strftime('%Y-%m-%d %H:%M:%S')}")
            new_entry = Attendance(
                name=user["name"],
                email=user["email"],
                registered_id=user["registered_id"],
                clock_in=st.session_state.clock_in_time,
            )
            session.add(new_entry)
            session.commit()
    else:
        st.write(f"Clocked in at: {st.session_state.clock_in_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if st.button("Clock Out"):
            clock_out_time = datetime.now()
            duration = (clock_out_time - st.session_state.clock_in_time).total_seconds() / 3600
            st.success(f"Clocked out at {clock_out_time.strftime('%Y-%m-%d %H:%M:%S')}, Duration: {duration:.2f} hours")
            last_entry = session.query(Attendance).filter_by(name=user["name"], clock_out=None).first()
            if last_entry:
                last_entry.clock_out = clock_out_time
                last_entry.duration = duration
                session.commit()
            st.session_state.clock_in_time = None

    # ✅ Log Out Button
    if st.button("Log Out"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]  # ✅ Clear session state
        st.experimental_rerun()
