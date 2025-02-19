
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
