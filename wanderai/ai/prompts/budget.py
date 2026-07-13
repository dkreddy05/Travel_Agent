"""
wanderai/ai/prompts/budget.py
Budget prompt templates.
"""
from wanderai.ai.prompts.registry import PromptTemplate, register

BUDGET_USER_TEMPLATE = """\
Create a detailed travel budget plan for {{ destination }}.
Duration: {{ days }} days, {{ travelers }} traveler(s)
Total budget: ${{ budget_total }} USD
Travel style: {{ travel_style }}

Provide:
1. **Daily Budget Breakdown** – Per person per day for: accommodation, food, transport, activities, shopping, misc
2. **Total Trip Cost Estimate** – Best case, expected, and worst case scenarios
3. **Money-Saving Tips** – 5 specific tips for this destination
4. **Currency & Payment Tips** – Local currency, exchange tips, card acceptance
5. **Budget vs Actual Tracker Template** – Simple table format
Include estimated costs in both USD and local currency where possible.
"""

register(PromptTemplate(
    name="budget",
    version="2.0.0",
    description="Travel budget planning",
    system="",
    user_template=BUDGET_USER_TEMPLATE,
    max_tokens=1500,
    temperature=0.5,
))
