import os
import urllib.parse
from datetime import date, timedelta

import streamlit as st
from openai import OpenAI

# ------------------------------------------------------------
#  CONFIGURE OPENAI CLIENT
# ------------------------------------------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ------------------------------------------------------------
#  SYSTEM BEHAVIOR OF THE AGENT
# ------------------------------------------------------------
SYSTEM_PROMPT = """
You are TripTact, an AI Travel Agent.

Your job:
- Take user trip preferences and build a realistic, day-by-day itinerary.
- Keep activities logically grouped by neighborhood or area to reduce travel time.
- Respect the user's budget and travel style (relaxed, balanced, packed).
- Suggest 1–2 flight options conceptually (nonstop vs 1 stop, AM/PM departure).
- ALWAYS include at least one Google Flights URL provided by the app.
- Do NOT invent booking URLs. Only use the Google Flights link given.

Output structure:
1. Short 1–2 sentence trip summary.
2. Detailed day-by-day itinerary in markdown.
3. Section titled "Flight Options" with:
   - Written guidance (AM/PM flights, nonstop vs stops)
   - A line that says exactly: "Google Flights search link: <URL>"
"""

# ------------------------------------------------------------
#  SUPPORT: BUILD GOOGLE FLIGHTS LINK
# ------------------------------------------------------------
def build_google_flights_link(origin: str,
                              destination: str,
                              depart_date: date,
                              return_date: date | None = None) -> str:
    """
    Creates a simple Google Flights search link using a text query.
    This doesn't have to be perfect; it just gives users a real link
    they can click to refine and book their flights.
    """
    # Basic human-readable query
    query_parts = [
        f"{origin} to {destination}",
        f"depart {depart_date.isoformat()}",
    ]
    if return_date:
        query_parts.append(f"return {return_date.isoformat()}")

    query = " ".join(query_parts)
    encoded_query = urllib.parse.quote_plus(query)

    # Use Google Flights search
    url = f"https://www.google.com/travel/flights?q={encoded_query}"
    return url


# ------------------------------------------------------------
#  CORE: CALL OPENAI TO GENERATE ITINERARY
# ------------------------------------------------------------
def generate_itinerary(
    origin: str,
    destination: str,
    start_date: date,
    end_date: date,
    budget: str,
    style: str,
    preferences: str,
) -> str:
    google_flights_url = build_google_flights_link(
        origin=origin,
        destination=destination,
        depart_date=start_date,
        return_date=end_date,
    )

    user_prompt = f"""
Trip details:
- Origin: {origin}
- Destination: {destination}
- Dates: {start_date.isoformat()} to {end_date.isoformat()}
- Budget level: {budget}
- Travel style: {style}
- Preferences / must-dos: {preferences or "None specified"}

IMPORTANT:
- Use this Google Flights link in the 'Flight Options' section:
  {google_flights_url}
- In that section, include a line exactly like:
  Google Flights search link: {google_flights_url}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0.7,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    itinerary_text = response.choices[0].message.content
    return itinerary_text


# ------------------------------------------------------------
#  STREAMLIT APP UI
# ------------------------------------------------------------
st.set_page_config(
    page_title="AI Travel Agent Prototype",
    page_icon="🌍",
    layout="wide",
)

st.markdown(
    "<h1 style='font-size: 3rem; margin-bottom: 0.5rem;'>🌍 AI Travel Agent Prototype</h1>",
    unsafe_allow_html=True,
)
st.write("Generate a personalized itinerary based on your preferences.")

st.markdown("---")

# ----- ORIGIN & DESTINATION: US CITY DROPDOWNS -----
us_cities = [
    "Atlanta (ATL)",
    "Austin (AUS)",
    "Baltimore (BWI)",
    "Boston (BOS)",
    "Charlotte (CLT)",
    "Chicago O'Hare (ORD)",
    "Chicago Midway (MDW)",
    "Cincinnati (CVG)",
    "Cleveland (CLE)",
    "Dallas / Fort Worth (DFW)",
    "Dallas Love Field (DAL)",
    "Denver (DEN)",
    "Detroit (DTW)",
    "Fort Lauderdale (FLL)",
    "Honolulu (HNL)",
    "Houston Intercontinental (IAH)",
    "Houston Hobby (HOU)",
    "Las Vegas (LAS)",
    "Los Angeles (LAX)",
    "Miami (MIA)",
    "Minneapolis (MSP)",
    "Nashville (BNA)",
    "New Orleans (MSY)",
    "New York – JFK (JFK)",
    "New York – LaGuardia (LGA)",
    "Newark (EWR)",
    "Orlando (MCO)",
    "Philadelphia (PHL)",
    "Phoenix (PHX)",
    "Portland (PDX)",
    "Salt Lake City (SLC)",
    "San Antonio (SAT)",
    "San Diego (SAN)",
    "San Francisco (SFO)",
    "San Jose (SJC)",
    "Seattle (SEA)",
    "Tampa (TPA)",
    "Washington DC – Dulles (IAD)",
    "Washington DC – Reagan (DCA)",
]

col1, col2 = st.columns(2)

with col1:
    origin = st.selectbox(
        "Origin city / airport",
        options=us_cities,
        index=us_cities.index("New York – JFK (JFK)")
        if "New York – JFK (JFK)" in us_cities
        else 0,
    )

with col2:
    destination = st.selectbox(
        "Destination city / airport",
        options=us_cities,
        index=us_cities.index("Los Angeles (LAX)")
        if "Los Angeles (LAX)" in us_cities
        else 1,
    )

# ----- DATE RANGE: TODAY TO 3 YEARS OUT -----
today = date.today()
three_years_from_now = today + timedelta(days=365 * 3)

col3, col4 = st.columns(2)

with col3:
    start_date = st.date_input(
        "Start date",
        value=today,
        min_value=today,
        max_value=three_years_from_now,
    )

with col4:
    end_date = st.date_input(
        "End date",
        value=today + timedelta(days=7),
        min_value=today,
        max_value=three_years_from_now,
    )

if end_date < start_date:
    st.warning("⚠️ End date is before start date — please choose a later end date.")

# ----- BUDGET & STYLE -----
col5, col6 = st.columns(2)

with col5:
    budget = st.selectbox(
        "Budget level",
        options=["Low", "Medium", "High", "Luxury"],
        index=0,
    )

with col6:
    style = st.selectbox(
        "Travel style",
        options=["Relaxed", "Balanced", "Packed"],
        index=1,
    )

# ----- PREFERENCES TEXT AREA -----
preferences = st.text_area(
    "Tell me about your ideal trip",
    placeholder="Example: I love food, museums, night walks, and scenic photo spots.",
    height=150,
)

st.markdown("")
plan_button = st.button("Plan My Trip ✈️")

# ----- RUN THE AGENT -----
if plan_button:
    if end_date < start_date:
        st.error("Please fix the dates before generating your itinerary.")
    else:
        with st.spinner("Planning your trip..."):
            itinerary_text = generate_itinerary(
                origin=origin,
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                budget=budget,
                style=style,
                preferences=preferences,
            )

        st.markdown("---")
        st.subheader("Your AI-Generated Itinerary")
        st.markdown(itinerary_text)
