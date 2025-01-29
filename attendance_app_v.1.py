import streamlit as st
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import smtplib
from email.message import EmailMessage

# Use a path relative to the app's current working directory
db_path = os.path.join(os.getcwd(), 'attendance.db')
engine = create_engine(f"sqlite:///{db_path}")

# Database setup
# engine = create_engine("sqlite:///attendance.db")
Base = declarative_base()

# Employee table
class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    passkey = Column(String, nullable=False)
    email = Column(String, nullable=False)
    registered_id = Column(String, nullable=False)
    contact_number = Column(String, nullable=False)

# Attendance table
class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    registered_id = Column(String, nullable=False)
    clock_in = Column(DateTime, nullable=True)
    clock_out = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)

# Leave table
class Leave(Base):
    __tablename__ = "leaves"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    registered_id = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    reason = Column(String, nullable=False)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Streamlit app
st.title("Attendance and Leave Management System")

# State to manage the current stage
if "current_stage" not in st.session_state:
    st.session_state.current_stage = "login"  # Default stage
if "clock_in_time" not in st.session_state:
    st.session_state.clock_in_time = None  # To store the clock-in time

# Login stage
if st.session_state.current_stage == "login":
    st.header("Qurocare - ALMS Portal")
    
    # Dropdown with default placeholder
    employee_names = ["Select"] + [e.name for e in session.query(Employee).all()]
    name = st.selectbox("Select your name", employee_names)
    
    # Validation for dropdown
    if name == "Select":
        st.warning("Please select your name.")
        st.stop()
    
    passkey = st.text_input("Enter your passkey", type="password")
    if st.button("Next"):
        # Validate passkey
        employee = session.query(Employee).filter_by(name=name).first()
        if employee and employee.passkey == passkey:
            st.success("Login successful!")
            st.session_state.current_stage = "main"  # Automatically move to main stage
            st.session_state.logged_in_user = {
                "name": employee.name,
                "email": employee.email,
                "registered_id": employee.registered_id,
            }
            st.experimental_rerun()  # Refresh the page to move to the main stage
        else:
            st.error("Invalid passkey. Please try again.")

# Main stage
elif st.session_state.current_stage == "main":
    user = st.session_state.logged_in_user
    st.header(f"Welcome, {user['name']}")

    # Attendance Section
    st.subheader("Attendance")
    if st.session_state.clock_in_time is None:  # No clock-in yet
        if st.button("Clock In"):
            st.session_state.clock_in_time = datetime.now()
            st.success(f"Clocked in at {st.session_state.clock_in_time.strftime('%Y-%m-%d %H:%M:%S')}")
            # Save clock-in time to DB
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
            duration = (clock_out_time - st.session_state.clock_in_time).total_seconds() / 3600  # in hours
            st.success(f"Clocked out at {clock_out_time.strftime('%Y-%m-%d %H:%M:%S')}, Duration: {duration:.2f} hours")
            # Update clock-out time and duration in DB
            last_entry = session.query(Attendance).filter_by(
                name=user["name"], clock_out=None
            ).order_by(Attendance.id.desc()).first()
            if last_entry:
                last_entry.clock_out = clock_out_time
                last_entry.duration = duration
                session.commit()
            st.session_state.clock_in_time = None  # Reset clock-in time

    # Leave Section
    st.subheader("Leave Application")
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")
    reason = st.text_area("Reason for Leave")
    if st.button("Apply"):
        if start_date > end_date:
            st.error("Start date cannot be after end date.")
        else:
            new_leave = Leave(
                name=user["name"],
                email=user["email"],
                registered_id=user["registered_id"],
                start_date=start_date,
                end_date=end_date,
                reason=reason,
            )
            session.add(new_leave)
            session.commit()
            st.success("Leave applied successfully!")
            
            # Send email notification to admin
            try:
                msg = EmailMessage()
                msg["Subject"] = "New Leave Application"
                msg["From"] = "rshm.jp07@gmail.com"  # Update with a valid email
                msg["To"] = "vysakharaghavan@gmail.com"
                msg.set_content(
                    f"Employee Name: {user['name']}\n"
                    f"Email: {user['email']}\n"
                    f"Start Date: {start_date}\n"
                    f"End Date: {end_date}\n"
                    f"Reason: {reason}"
                )
                
                with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
                    smtp.starttls()
                    smtp.login("rshm.jp07@gmail.com", "sipw aiba yfcr elkd")  # Replace with your email credentials
                    smtp.send_message(msg)
                
                st.info("Admin has been notified via email.")
            except Exception as e:
                st.error(f"Failed to send email: {e}")
