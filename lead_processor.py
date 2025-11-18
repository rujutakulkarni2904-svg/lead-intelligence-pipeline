from openai import OpenAI
import pandas as pd
import json
from typing import Dict

def process_leads(df: pd.DataFrame, api_key: str) -> Dict:
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        
        leads_summary = df.head(20).to_csv(index=False)
        
        prompt = "You are an expert B2B sales lead analyst. Analyze these leads and provide: 1. LEAD SCORING (0-10 scale): 9-10 = Hot (C-level executives), 7-8 = Warm (Directors/VPs), 5-6 = Cold (Managers), Below 5 = Not qualified. 2. DUPLICATE DETECTION: Identify duplicate contacts. 3. ACTION RECOMMENDATIONS. Return ONLY valid JSON with keys: hot_leads, warm_leads, cold_leads, not_qualified, duplicates_found, time_saved_hours, annual_roi_inr, lead_details (array with lead_id, score, action, reason, is_duplicate). Here are the leads: " + leads_summary
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        
        response_text = response.choices[0].message.content
        
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        json_str = response_text[start_idx:end_idx]
        analysis = json.loads(json_str)
        
        enriched_df = df.copy()
        enriched_df['ai_score'] = 0
        enriched_df['action'] = 'Pending'
        enriched_df['is_duplicate'] = False
        enriched_df['ai_reason'] = ''
        
        for detail in analysis.get('lead_details', []):
            lead_id = detail['lead_id']
            if lead_id in enriched_df['lead_id'].values:
                enriched_df.loc[enriched_df['lead_id'] == lead_id, 'ai_score'] = detail.get('score', 0)
                enriched_df.loc[enriched_df['lead_id'] == lead_id, 'action'] = detail.get('action', 'Review')
                enriched_df.loc[enriched_df['lead_id'] == lead_id, 'is_duplicate'] = detail.get('is_duplicate', False)
                enriched_df.loc[enriched_df['lead_id'] == lead_id, 'ai_reason'] = detail.get('reason', '')
        
        return {
            'success': True,
            'processed_df': enriched_df,
            'hot_count': analysis.get('hot_leads', 0),
            'warm_count': analysis.get('warm_leads', 0),
            'cold_count': analysis.get('cold_leads', 0),
            'not_qualified': analysis.get('not_qualified', 0),
            'duplicates': analysis.get('duplicates_found', 0),
            'time_saved': analysis.get('time_saved_hours', 18),
            'annual_roi': analysis.get('annual_roi_inr', 450000)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'processed_df': df,
            'hot_count': 0,
            'warm_count': 0,
            'cold_count': 0,
            'not_qualified': 0,
            'duplicates': 0,
            'time_saved': 0,
            'annual_roi': 0
        }

def get_metrics_summary(total_leads: int) -> Dict:
    manual_time_per_lead = 15
    automated_time_per_lead = 0.1
    manual_hours = (total_leads * manual_time_per_lead) / 60
    automated_hours = (total_leads * automated_time_per_lead) / 60
    hours_saved = manual_hours - automated_hours
    cost_per_hour = 500
    weekly_batches = 4
    annual_savings = hours_saved * cost_per_hour * weekly_batches * 52
    return {
        'manual_hours': round(manual_hours, 1),
        'automated_hours': round(automated_hours, 2),
        'hours_saved': round(hours_saved, 1),
        'annual_savings': int(annual_savings),
        'speed_improvement': '150x faster'
    }
