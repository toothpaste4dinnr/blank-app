
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
