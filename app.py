import os
import urllib.parse
import streamlit as st
from datetime import date
from openai import OpenAI

# ---------------------------------------------------------
#  CONFIGURE OPENAI CLIENT
# ---------------------------------------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------------------------------------------------
#  SYSTEM BEHAVIOR OF THE AGENT
# ---------------------------------------------------------
SYSTEM_PROMPT = """
You are TripTact, an AI Travel Agent.

Your job:
- Take user trip preferences and build a realistic, day-by-day itinerary.
- Keep activities logically grouped by neighborhood or area to reduce travel time.
- Respect the user's budget and travel style (relaxed, balanced, packed).
- Suggest 1–2 flight options conceptually (nonstop vs 1 stop, AM/PM departure)
- ALWAYS include at least one Google Flights URL provided by the app.
- Do NOT invent booking URLs. Only use the Google Flights link given.

Output structure:
1. Short 1–2 sentence trip summary.
2. Detailed day-by-day itinerary in markdown.
3. Section titled "Flight Options" with:
   - Written guidance (AM/PM flights, nonstop vs stops)
   - A line that says: "Google Flights search link: <URL>"
"""

# ---------------------------------------------------------
#  SUPPORT: BUILD GOOGLE FLIGHTS LINK
# ---------------------------------------------------------
def build_google_flights_link(origin, destination, depart_date, return_date=None):
    """
    Creates a simple Google Flights search link using a text query.
    """
    base = "https://www.google.com/travel/flights"
    q = f"Flights from {origin} to {destination} on {depart_date}"
    if return_date:
        q += f" returning on {return_date}"
    params = urllib.parse.urlencode({"q": q})
    return f"{base}?{params}"


# ---------------------------------------------------------
#  CORE FUNCTION: GENERATE ITINERARY
# ---------------------------------------------------------
def generate_itinerary(origin, destination, start_date, end_date,
                       budget_level, travel_style, preferences):
    
    user_prompt = f"""
The user wants to plan a trip. Here are the details:

- Origin: {origin}
- Destination: {destination}
- Start date: {start_date}
- End date: {end_date}
- Budget level: {budget_level}
- Travel style: {travel_style}
- Preferences: {preferences}

Please follow the exact output structure requested in the system prompt.
Remember: DO NOT create your own flight URLs. The app will insert one.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",    "content": user_prompt},
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content


# ---------------------------------------------------------
#  STREAMLIT UI
# ---------------------------------------------------------
st.set_page_config(page_title="AI Travel Agent", page_icon="🌍")
st.title("🌍 AI Travel Agent Prototype")
st.write("Generate a personalized itinerary based on your preferences.")

with st.form("trip_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        origin = st.text_input("Origin city / airport", placeholder="New York (JFK)")
        start = st.date_input("Start date", value=date(2025, 6, 1))
        budget = st.selectbox("Budget level", ["Low", "Medium", "High"])

    with col2:
        destination = st.text_input("Destination city / airport", placeholder="Rome (FCO)")
        end = st.date_input("End date", value=date(2025, 6, 7))
        style = st.selectbox("Travel style", ["Relaxed", "Balanced", "Packed"])

    preferences = st.text_area(
        "Tell me about your ideal trip:",
        placeholder="Example: I love food, museums, night walks, and scenic photo spots.",
        height=120,
    )

    submitted = st.form_submit_button("Plan My Trip ✈️")

# ---------------------------------------------------------
#  ON SUBMIT: GENERATE ITINERARY
# ---------------------------------------------------------
if submitted:
    if not origin or not destination:
        st.error("Please enter both origin and destination.")
    else:
        with st.spinner("Crafting your itinerary..."):
            itinerary_text = generate_itinerary(
                origin=origin,
                destination=destination,
                start_date=start.isoformat(),
                end_date=end.isoformat(),
                budget_level=budget,
                travel_style=style,
                preferences=preferences,
            )

        # Create Google Flights link
        gf_link = build_google_flights_link(
            origin=origin,
            destination=destination,
            depart_date=start.isoformat(),
            return_date=end.isoformat(),
        )

        # ---------------------------------------------------------
        #  OUTPUT
        # ---------------------------------------------------------
        st.markdown("## ✨ Your Custom Itinerary")
        st.markdown(itinerary_text)

        st.markdown("## ✈️ Book Flights")
        st.write("Here is your Google Flights search link:")
        st.markdown(f"[Click to view flights]({gf_link})")