
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
