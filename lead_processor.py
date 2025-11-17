import anthropic
import pandas as pd
import json
from typing import Dict

def process_leads(df: pd.DataFrame, api_key: str) -> Dict:
    """
    Process leads using Claude AI to enrich, score, and detect duplicates
    """
    
    # Initialize Claude client
    client = anthropic.Anthropic(api_key=api_key)
    
    # Prepare leads summary for AI (process first 20 for demo)
    leads_summary = df.head(20).to_csv(index=False)
    
    # Create prompt for Claude
    prompt = f"""You are an expert B2B sales lead analyst. Analyze these leads and provide:

1. LEAD SCORING (0-10 scale):
   - Score each lead based on: title seniority, company size, industry fit
   - 9-10 = Hot (C-level executives, large companies, high-value industries like SaaS/Fintech)
   - 7-8 = Warm (Directors/VPs, mid-size companies)
   - 5-6 = Cold (Managers, small companies)
   - Below 5 = Not qualified

2. DUPLICATE DETECTION:
   - Identify leads that are likely the same person
   - Look for: similar names + same company, or very similar emails
   - Flag them clearly

3. ACTION RECOMMENDATIONS:
   - Hot leads (9-10): "Call immediately"
   - Warm leads (7-8): "Email + LinkedIn outreach"
   - Cold leads (5-6): "Add to nurture campaign"
   - Not qualified (<5): "Skip"

Here are the leads in CSV format:
{leads_summary}

Return ONLY valid JSON in this exact format:
{{
  "hot_leads": 5,
  "warm_leads": 8,
  "cold_leads": 4,
  "not_qualified": 3,
  "duplicates_found": 2,
  "time_saved_hours": 18.5,
  "annual_roi_inr": 450000,
  "lead_details": [
    {{"lead_id": "L0001", "score": 9, "action": "Call immediately", "reason": "CEO at mid-size SaaS company", "is_duplicate": false}},
    {{"lead_id": "L0002", "score": 8, "action": "Email + LinkedIn outreach", "reason": "VP Sales in Fintech", "is_duplicate": false}}
  ]
}}"""

    try:
        # Call Claude API
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Parse response
        response_text = message.content[0].text
        
        # Extract JSON from response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        json_str = response_text[start_idx:end_idx]
        analysis = json.loads(json_str)
        
        # Add enriched data back to dataframe
        enriched_df = df.copy()
        enriched_df['ai_score'] = 0
        enriched_df['action'] = 'Pending analysis'
        enriched_df['is_duplicate'] = False
        enriched_df['ai_reason'] = ''
        
        # Update with AI analysis
        for detail in analysis.get('lead_details', []):
            lead_id = detail['lead_id']
            if lead_id in enriched_df['lead_id'].values:
                enriched_df.loc[enriched_df['lead_id'] == lead_id, 'ai_score'] = detail.get('score', 0)
                enriched_df.loc[enriched_df['lead_id'] == lead_id, 'action'] = detail.get('action', 'Review manually')
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
            'time_saved': analysis.get('time_saved_hours', 18.5),
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
    """Calculate ROI metrics"""
    
    manual_time_per_lead = 15  # minutes
    automated_time_per_lead = 0.1  # minutes (6 seconds)
    
    manual_hours = (total_leads * manual_time_per_lead) / 60
    automated_hours = (total_leads * automated_time_per_lead) / 60
    hours_saved = manual_hours - automated_hours
    
    # Assuming ₹500/hour cost for sales rep time
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
