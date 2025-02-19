# app3.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import random
import calendar
import numpy as np
import os

from utils.data_loader import load_patient_data
from utils.booking_manager import BookingManager
from utils.risk_analyzer import RiskAnalyzer

# Create utils directory if it doesn't exist
if not os.path.exists('utils'):
    os.makedirs('utils')

# Create data_loader.py
with open('utils/data_loader.py', 'w') as f:
    f.write('''
import pandas as pd
import random
from datetime import datetime, timedelta

def load_patient_data():
    """Generate sample patient booking data"""
    if not hasattr(load_patient_data, "data"):
        # Generate sample data
        patient_ids = [f"P{str(i).zfill(3)}" for i in range(1, 51)]
        dates = [(datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d') 
                for i in range(14)]  # Next 2 weeks
        times = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
                "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"]
        
        data = []
        for _ in range(100):  # Generate 100 bookings
            data.append({
                'patient_id': random.choice(patient_ids),
                'date': random.choice(dates),
                'appointment_time': random.choice(times),
                'default_risk': random.randint(0, 100),
                'status': random.choice(['Confirmed', 'Pending', 'Completed'])
            })
        
        load_patient_data.data = pd.DataFrame(data)
    
    return load_patient_data.data
''')

# Create booking_manager.py
with open('utils/booking_manager.py', 'w') as f:
    f.write('''
import pandas as pd

class BookingManager:
    def __init__(self):
        self.MAX_SLOTS = 4
        self.HIGH_RISK_THRESHOLD = 70
        self.df = None
    
    def set_data(self, df):
        """Initialize or update the internal DataFrame"""
        self.df = df.copy()
        return self.df
    
    def add_booking(self, patient_id, date, time, default_risk):
        """Add a new booking if slot is available and meets risk criteria"""
        if self.df is None:
            raise ValueError("DataFrame not initialized. Call set_data() first.")
            
        # Check current bookings for the time slot
        date_str = date.strftime('%Y-%m-%d')
        current_bookings = self.df[
            (self.df['date'] == date_str) & 
            (self.df['appointment_time'] == time)
        ]
        
        # Check if slot is fully booked
        if len(current_bookings) >= self.MAX_SLOTS:
            return False, self.df, "Time slot is fully booked (max 4 patients)"
        
        # For low-risk patients (< 70%), only allow booking if slot is empty
        if default_risk < self.HIGH_RISK_THRESHOLD:
            if not current_bookings.empty:
                return False, self.df, "Low-risk patients can only book empty time slots"
        
        # For any patient, prevent booking if slot has low-risk patients
        if not current_bookings.empty:
            low_risk_bookings = current_bookings[current_bookings['default_risk'] < self.HIGH_RISK_THRESHOLD]
            if not low_risk_bookings.empty:
                return False, self.df, "Cannot book slot with low-risk patients"
            
        # Add new booking
        new_booking = pd.DataFrame([{
            'patient_id': patient_id,
            'date': date_str,
            'appointment_time': time,
            'default_risk': default_risk,
            'status': 'Confirmed'
        }])
        
        self.df = pd.concat([self.df, new_booking], ignore_index=True)
        return True, self.df, "Booking successful"
    
    def analyze_time_slots(self):
        """Analyze booking patterns by time slot"""
        if self.df is None:
            raise ValueError("DataFrame not initialized. Call set_data() first.")
            
        slot_analysis = self.df.groupby('appointment_time').agg({
            'patient_id': 'count',
            'default_risk': 'mean'
        }).reset_index()
        
        slot_analysis.columns = ['time_slot', 'patient_count', 'avg_risk']
        return slot_analysis
''')

# Create risk_analyzer.py
with open('utils/risk_analyzer.py', 'w') as f:
    f.write('''
import pandas as pd

class RiskAnalyzer:
    def __init__(self, high_risk_threshold=70):
        self.high_risk_threshold = high_risk_threshold
    
    def analyze_overbooking(self, df):
        """Analyze slots with multiple high-risk patients"""
        # Group by date and time
        grouped = df.groupby(['date', 'appointment_time']).agg({
            'patient_id': 'count',
            'default_risk': ['mean', lambda x: sum(x >= self.high_risk_threshold)]
        }).reset_index()
        
        grouped.columns = ['date', 'time_slot', 'total_patients', 'avg_risk', 'high_risk_count']
        
        # Filter overbooked slots
        overbooked = grouped[grouped['high_risk_count'] >= 2].copy()
        overbooked['avg_risk'] = overbooked['avg_risk'].round(1)
        
        return overbooked
    
    def get_slot_recommendation(self, df, patient_risk):
        """Get recommended time slots based on risk level"""
        if patient_risk >= self.high_risk_threshold:
            # For high-risk patients, find slots with other high-risk patients
            return self._find_matching_risk_slots(df, high_risk=True)
        else:
            # For low-risk patients, find slots with available capacity
            return self._find_matching_risk_slots(df, high_risk=False)
    
    def _find_matching_risk_slots(self, df, high_risk=True):
        """Helper method to find appropriate slots"""
        slot_analysis = df.groupby(['date', 'appointment_time']).agg({
            'patient_id': 'count',
            'default_risk': 'mean'
        }).reset_index()
        
        if high_risk:
            return slot_analysis[slot_analysis['default_risk'] >= self.high_risk_threshold]
        else:
            return slot_analysis[slot_analysis['patient_id'] < 4]
''')

def main():
    st.title("🏥 Smart Medical Booking System")
    st.markdown("---")

    # Initialize session state for DataFrame if it doesn't exist
    if 'df' not in st.session_state:
        st.session_state.df = load_patient_data()

    # Initialize managers with current data
    booking_manager = BookingManager()
    st.session_state.df = booking_manager.set_data(st.session_state.df)
    risk_analyzer = RiskAnalyzer()

    # Calendar View
    st.subheader("📅 Calendar View")
    col1, col2 = st.columns([2, 3])
    
    with col1:
        selected_date = st.date_input("Select Date", datetime.now())
        time_slots = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", 
                     "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"]

    with col2:
        # Display calendar grid
        date_bookings = st.session_state.df[st.session_state.df['date'] == str(selected_date)]
        
        st.markdown("### Time Slot Availability")
        slot_data = []
        
        for slot in time_slots:
            slot_bookings = date_bookings[date_bookings['appointment_time'] == slot]
            booked_count = len(slot_bookings)
            available = 4 - booked_count  # Max 4 slots
            
            slot_data.append({
                "Time": slot,
                "Booked": booked_count,
                "Available": available,
                "Patients": ", ".join(slot_bookings['patient_id'].tolist())
            })
        
        slot_df = pd.DataFrame(slot_data)
        st.dataframe(
            slot_df,
            hide_index=True,
            column_config={
                "Time": "Time Slot",
                "Booked": st.column_config.NumberColumn(
                    "Booked Slots",
                    help="Number of booked appointments"
                ),
                "Available": st.column_config.NumberColumn(
                    "Available Slots",
                    help="Number of available slots"
                ),
                "Patients": "Booked Patients"
            }
        )

    # Booking Form
    st.subheader("📝 New Booking")
    booking_cols = st.columns(4)
    
    with booking_cols[0]:
        patient_id = st.text_input("Patient ID")
    with booking_cols[1]:
        selected_time = st.selectbox("Select Time Slot", time_slots)
    with booking_cols[2]:
        default_risk = st.slider("Default Risk (ML Prediction)", 0, 100, 50)
    with booking_cols[3]:
        if st.button("Book Appointment"):
            success, updated_df, message = booking_manager.add_booking(
                patient_id, selected_date, 
                selected_time, default_risk
            )
            
            if success:
                st.session_state.df = updated_df
                st.success(f"Appointment booked for {patient_id} at {selected_time}")
                st.rerun()
            else:
                st.error(message)

    # Analytics Section
    st.markdown("---")
    st.subheader("📊 Booking Analytics")
    
    tab1, tab2, tab3 = st.tabs(["Risk Distribution", "Time Slot Analysis", "Overbooking Analysis"])
    
    with tab1:
        # Risk Distribution
        fig = px.histogram(
            st.session_state.df, 
            x="default_risk",
            nbins=20,
            title="Distribution of Patient Default Risk"
        )
        st.plotly_chart(fig)
        
    with tab2:
        # Time Slot Analysis
        slot_analysis = booking_manager.analyze_time_slots()
        fig2 = px.bar(
            slot_analysis,
            x="time_slot",
            y="patient_count",
            title="Patients per Time Slot"
        )
        st.plotly_chart(fig2)
        
    with tab3:
        # Overbooking Analysis
        overbooked_slots = risk_analyzer.analyze_overbooking(st.session_state.df)
        if not overbooked_slots.empty:
            st.dataframe(
                overbooked_slots,
                hide_index=True,
                column_config={
                    "avg_risk": st.column_config.NumberColumn(
                        "Average Risk",
                        format="%.1f%%"
                    )
                }
            )
        else:
            st.info("No overbooked slots found")

    # View All Bookings
    st.markdown("---")
    st.subheader("📋 All Bookings")
    if not st.session_state.df.empty:
        st.dataframe(
            st.session_state.df.sort_values(['date', 'appointment_time']),
            hide_index=True,
            column_config={
                "default_risk": st.column_config.ProgressColumn(
                    "Default Risk",
                    format="%d%%",
                    min_value=0,
                    max_value=100,
                )
            }
        )
    else:
        st.info("No bookings in the system")

if __name__ == "__main__":
    main()


