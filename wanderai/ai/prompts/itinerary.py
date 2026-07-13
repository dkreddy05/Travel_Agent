"""
wanderai/ai/prompts/itinerary.py
Versioned itinerary prompt templates.
"""
from wanderai.ai.prompts.registry import PromptTemplate, register

ITINERARY_USER_TEMPLATE = """\
Create a detailed {{ days }}-day travel itinerary for {{ destination }}.
Budget tier: {{ budget }}
Number of travelers: {{ travelers }}
Interests: {{ interests }}
Transport preference: {{ transport }}
Accommodation preference: {{ accommodation }}

Structure your response EXACTLY as follows:
1. **Trip Overview** – 2-sentence summary
2. **Day-by-Day Itinerary** – For each day: morning, afternoon, evening activities with estimated costs
3. **Budget Breakdown** – Categories with amounts (accommodation, food, transport, activities, misc)
4. **Top Accommodation Options** – 3 options with price range and why
5. **Getting Around** – Transport options within destination
6. **Must-Try Foods** – 5 local dishes/restaurants
7. **Packing List** – Destination-specific essentials
8. **Safety & Travel Tips** – 5 key tips
"""

register(PromptTemplate(
    name="itinerary",
    version="2.0.0",
    description="Day-by-day itinerary generation",
    system="",   # uses global system prompt
    user_template=ITINERARY_USER_TEMPLATE,
    max_tokens=2000,
    temperature=0.7,
))
