import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from datetime import datetime
from simulation.ai_inference import AIInferenceEngine
# Initialize AI Engine
ai_engine = AIInferenceEngine()


# --- CONFIG ---
st.set_page_config(
    page_title="EcoSync | Dynamic",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS ---
def local_css(file_name):
    # specify utf-8 to handle any non-ASCII characters in CSS
    try:
        with open(file_name, encoding="utf-8") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except UnicodeDecodeError:
        # fallback: read with latin-1 which maps bytes directly to first 256 unicode points
        with open(file_name, encoding="latin-1") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("assets/compact.css")


@st.cache_data
def load_historical_weather():
    try:
        df = pd.read_csv("historical_weather_6mo.csv")
        df['time'] = pd.to_datetime(df['time'])
        return df
    except:
        return None

@st.cache_data(ttl=3600)  # cache each date for 1 hour
def fetch_weather_for_date(date_str):
    """
    Fetch real hourly weather data for a specific date from Open-Meteo Archive API.
    Returns dict with 24-element lists for solar (W/m²), wind (km/h), temp (°C),
    or None if the date is unavailable (future / API error).
    """
    import requests as _req
    from datetime import date as _date, timedelta as _td

    # Open-Meteo archive lags by ~2 days — don't attempt future or very recent dates
    today = _date.today()
    try:
        target = _date.fromisoformat(date_str)
    except ValueError:
        return None
    if target >= today - _td(days=2):
        return None  # data not yet available

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude":   39.0438,       # Northern Virginia (major US data center hub)
        "longitude":  -77.4874,
        "start_date": date_str,
        "end_date":   date_str,
        "hourly":     "direct_radiation,wind_speed_10m,temperature_2m",
        "timezone":   "America/New_York"
    }
    try:
        resp = _req.get(url, params=params, timeout=10)
        resp.raise_for_status()
        hourly = resp.json()["hourly"]
        if len(hourly["time"]) < 24:
            return None
        return {
            "solar": hourly["direct_radiation"][:24],   # W/m²
            "wind":  hourly["wind_speed_10m"][:24],     # km/h
            "temp":  hourly["temperature_2m"][:24],     # °C
        }
    except Exception:
        return None

# --- DATA AGENT ---
@st.cache_data
def get_dynamic_model(user_mult, solar_cap, wind_cap, weather_type):
    hours = np.linspace(0, 23, 24)
    
    # 1. Weather Impact Logic
    # Define how weather shapes the curve, not just a flat multiplier
    if weather_type == "Sunny":
        weather_factor = np.ones(24) # 100% efficient
        cloud_noise = 0
    elif weather_type == "Partly Cloudy":
        # Random passing clouds (drops in efficiency)
        weather_factor = np.random.uniform(0.6, 1.0, 24) 
        cloud_noise = 20
    elif weather_type == "Overcast":
        # Consistently low flat curve
        weather_factor = np.full(24, 0.4) 
        cloud_noise = 10
    else: # Rainy
        # Very low, fluctuating
        weather_factor = np.random.uniform(0.1, 0.3, 24)
        cloud_noise = 5

    # 2. Solar Generation (24h Forecast)
    # Bell curve * Weather Factor
    base_solar = solar_cap * np.exp(-0.15 * (hours - 12)**2)
    solar_gen = base_solar * weather_factor
    solar_gen = np.maximum(solar_gen, 0) # No negative energy

    # 2b. Wind Generation (24h Forecast)
    # Unlike solar, wind is NOT constrained to daylight hours.
    # It follows a gentle sine variation (slightly higher at night) scaled by weather.
    # Storm/rain = strong wind; sunny/calm = weak wind.
    wind_speed_factors = {
        "Sunny":         0.25,   # Calm day, light breeze
        "Partly Cloudy": 0.45,   # Moderate breeze
        "Overcast":      0.65,   # Stronger winds accompanying cloud systems
        "Rainy":         0.80,   # Stormy conditions, high wind
    }
    wind_factor = wind_speed_factors.get(weather_type, 0.45)
    # Sine wave: peaks around hour 3-4 (night offshore winds) and hour 15-16 (afternoon sea breeze)
    wind_base = wind_cap * wind_factor * (0.5 + 0.2 * np.sin(hours / 4.0))
    wind_noise = np.random.normal(0, wind_cap * 0.03, 24)
    wind_gen = np.maximum(0, wind_base + wind_noise)
    
    # 3. Load Profiles (Dynamic Reaction)
    # If solar is low (Rainy), AI delays batch jobs -> Flattening the load curve
    base_load = 300 + (user_mult * 50) * np.sin((hours+2)/4)
    
    if weather_type in ["Rainy", "Overcast"]:
        # AI Reaction: Load Shedding / shifting
        # Reduced peak, higher night load (shifted)
        base_load[10:16] *= 0.8 # Cut peak
        base_load[0:6] += 50 # Moved to night
    
    # Add category components
    load_compute = base_load + np.random.normal(0, 10, 24)
    load_storage = 100 + (user_mult * 10)
    load_network = 50 + (user_mult * 20) * np.random.uniform(0.9, 1.1, 24)
    
    total_load = load_compute + load_storage + load_network

    # 4. Energy Cleanliness Heatmap (Dynamic)
    # If Solar is High -> Grid is clean (Green)
    # If Solar is Low -> Grid relies on Coal (Red)
    avg_sol = solar_gen.mean()
    if avg_sol > 400: # Sunny
        heatmap = np.random.randint(60, 100, size=(4, 12)) # Greenish
    elif avg_sol > 150: # Cloudy
        heatmap = np.random.randint(40, 80, size=(4, 12)) # Yellow/Green
    else: # Rainy
        heatmap = np.random.randint(10, 50, size=(4, 12)) # Red/Orange
        

    # 5. Tech Scaling (Make it distinct per weather)
    if weather_type == "Sunny":
        tech_scale = 1.0
    elif weather_type == "Rainy":
        tech_scale = 1.45 # Significant jump to make visual obvious
    else:
        tech_scale = 1.2


    # 6. AI Decision Logic (Hybrid: Real PPO Model + Heuristic Explainer)
    decision_log = []

    # Use actual current hour so the decision reflects time-of-day conditions
    current_hour = datetime.now().hour

    # Solar at the current hour (not a flat 24h average)
    sim_solar_now = float(solar_gen[current_hour])

    # Realistic carbon intensity based on weather + time-of-day peak periods.
    # Base values mirror the energy model's duck-curve pattern (400 g/kWh base).
    base_carbon_by_weather = {
        "Sunny":        350,   # Solar feeding the grid lowers carbon
        "Partly Cloudy": 430,
        "Overcast":     490,
        "Rainy":        580,   # Full grid reliance, no solar offset
    }
    sim_carbon = base_carbon_by_weather.get(weather_type, 420)
    # Morning (8-10) and evening (18-21) are peak demand hours — carbon spikes
    if 8 <= current_hour <= 10 or 18 <= current_hour <= 21:
        sim_carbon += 80
    # At night (no solar window), grid runs on fossil fuels regardless of weather forecast
    if current_hour < 6 or current_hour > 18:
        sim_carbon = max(sim_carbon, 430)

    sim_queue = user_mult * 10

    # Define Battery State based on Weather
    if weather_type == "Sunny":
        bat_pct = 94
    elif weather_type == "Rainy":
        bat_pct = 35
    elif weather_type == "Partly Cloudy":
        bat_pct = 78
    else: # Overcast
        bat_pct = 55

    # Wind at current hour (not a flat average)
    sim_wind_now = float(wind_gen[current_hour])

    # LIVE INFERENCE — correct hour, real solar + wind, calibrated carbon, both capacities passed
    action_str, action_id = ai_engine.infer_action(
        current_hour, sim_solar_now, sim_wind_now, sim_carbon, sim_queue, bat_pct,
        solar_capacity=solar_cap, wind_capacity=wind_cap
    )

    # 1. Traffic Analysis
    if user_mult > 35:
        decision_log.append(f"⚠️ **High Traffic:** Queue depth {int(sim_queue)}. Policy: **{action_str}**")
    elif user_mult < 10:
        decision_log.append("💤 **Low Traffic:** Consolidated workloads. Efficiency Mode.")
    else:
        decision_log.append(f"✅ **Traffic Nominal:** Policy: **{action_str}** active.")

    # 2. Energy Status — based on actual fractions of each farm's rated capacity
    solar_fraction_pct = int((sim_solar_now / max(1, solar_cap)) * 100)
    wind_fraction_pct  = int((sim_wind_now  / max(1, wind_cap))  * 100)
    combined_pct       = int(((sim_solar_now + sim_wind_now) / max(1, solar_cap + wind_cap)) * 100)

    # Solar label
    if solar_fraction_pct >= 40:
        solar_label = f"☀️ Solar {solar_fraction_pct}% (strong)"
    elif solar_fraction_pct >= 15:
        solar_label = f"⛅ Solar {solar_fraction_pct}% (moderate)"
    else:
        solar_label = f"🌑 Solar {solar_fraction_pct}% (low)"

    # Wind label
    if wind_fraction_pct >= 50:
        wind_label = f"💨 Wind {wind_fraction_pct}% (strong)"
    elif wind_fraction_pct >= 20:
        wind_label = f"🌬️ Wind {wind_fraction_pct}% (moderate)"
    else:
        wind_label = f"🍃 Wind {wind_fraction_pct}% (low)"

    decision_log.append(f"{solar_label} | {wind_label} | Combined renewables: **{combined_pct}%** | Grid carbon: {sim_carbon}g CO₂/kWh.")

    # 3. AI Decision explanation — honest about energy source and reason
    if action_id == 0:  # PROCESS_ALL
        if combined_pct >= 40:
            decision_log.append(f"🚀 **AI Decision:** BOOST MODE — {combined_pct}% combined renewables available, processing full backlog on clean energy.")
        elif sim_queue > 400:
            decision_log.append(f"🚀 **AI Decision:** BACKLOG CRITICAL ({int(sim_queue)} tasks) — clearing queue; renewables at {combined_pct}%, grid supplement active.")
        else:
            decision_log.append(f"🚀 **AI Decision:** PROCESS ALL — renewables low ({combined_pct}%), running on grid. Consider deferring non-urgent tasks.")
    elif action_id == 1:  # ECO
        decision_log.append(f"🌱 **AI Decision:** ECO MODE — running on {combined_pct}% combined renewables (☀️{solar_fraction_pct}% + 💨{wind_fraction_pct}%). Excess tasks queued for next clean window.")
    elif action_id == 2:  # HOLD
        decision_log.append(f"🛑 **AI Decision:** DEFER LOADS — combined renewables only {combined_pct}%, grid carbon {sim_carbon}g. Holding non-critical tasks until cleaner window.")

    ai_msg = " ".join([f"<div style='margin-bottom:4px;'>{x}</div>" for x in decision_log])
    
    df_live = pd.DataFrame({
        "Hour": hours,
        "Compute": load_compute, "Storage": load_storage, "Network": load_network,
        "Total": total_load, "Solar": solar_gen, "Wind": wind_gen
    })

    return df_live, heatmap, tech_scale, ai_msg, bat_pct

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='font-size: 2.2rem; font-weight: 800; margin-bottom: 20px;'>Eco-Compute</h1>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Simulation Controls")
    user_mult = st.slider("Active User Traffic", 1, 50, 15)
    solar_cap = st.slider("Solar Farm Capacity (kW)", 0, 2000, 850)
    wind_cap  = st.slider("Wind Farm Capacity (kW)",  0, 1000, 200)
    
    st.markdown("---")
    st.markdown("### Weather Condition")
    # This trigger is key - it drives the entire model
    w_select = st.selectbox("Current", ["Sunny", "Partly Cloudy", "Overcast", "Rainy"], index=0, label_visibility="collapsed")
    

    st.markdown("---")



df, heatmap, tech_scale, ai_decision, bat_pct = get_dynamic_model(user_mult, solar_cap, wind_cap, w_select)


# --- ROW 1: MINI METRICS ---
c1, c2, c3, c4, c5, c6 = st.columns(6)
def mini(label, val, sub):
    return f"""<div class="dashboard-card" style="padding:10px;"><div class="metric-title">{label}</div><div class="metric-value" style="font-size:1.4rem;">{val}</div><div class="metric-sub sub-neutral" style="font-size:0.6rem;">{sub}</div></div>"""

total     = int(df['Total'].sum())
solar_sum = int(df['Solar'].sum())
wind_sum  = int(df['Wind'].sum())
renewable_sum = solar_sum + wind_sum
# Wind fraction at current hour — used in battery panel
_current_hour = datetime.now().hour
wind_fraction_pct = int((df['Wind'].iloc[_current_hour] / max(1, wind_cap)) * 100)
# CO2 avoided: renewables displaced grid at ~0.5 kg CO2/kWh
saved_kg  = int(renewable_sum * 0.5)

with c1: st.markdown(mini("Total Demand",   f"{total} kWh",       "24h Forecast"),                    unsafe_allow_html=True)
with c2: st.markdown(mini("Avoided CO2",    f"{saved_kg} kg",     "Solar + Wind"),                    unsafe_allow_html=True)
with c3: st.markdown(mini("Solar Input",    f"{solar_sum} kWh",   w_select),                          unsafe_allow_html=True)
with c4: st.markdown(mini("Wind Input",     f"{wind_sum} kWh",    w_select),                          unsafe_allow_html=True)
# Cost based on grid import only (total minus what renewables covered)
grid_import = max(0, total - renewable_sum)
est_cost = int(grid_import * 0.15)
with c5: st.markdown(mini("Est. Cost",      f"${est_cost}",       "Grid Import"),                     unsafe_allow_html=True)
with c6: st.markdown(mini("Grid Relief",    f"{int(min(renewable_sum, total)/total*100)}%", "Self-Sufficiency"), unsafe_allow_html=True)

# --- ROW 2: LIVE LOAD + BATTERY (Split 2 cols) ---
r2_1, r2_2 = st.columns([1, 2]) 


with r2_1:
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-title">Resource Split</div>', unsafe_allow_html=True)
    sums = df[['Compute', 'Storage', 'Network']].sum()
    fig_p = px.pie(names=sums.index, values=sums.values, hole=0.65, color_discrete_sequence=['#5E63D8', '#818CF8', '#C7D2FE'])
    fig_p.update_traces(textposition='inside', textinfo='percent+label')
    fig_p.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
    fig_p.add_annotation(text=f"{int(sums.sum())}", font_size=14, showarrow=False)
    st.plotly_chart(fig_p, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r2_2:
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    sub_c1, sub_c2 = st.columns([3, 1])
    
    with sub_c1:
        st.markdown('<div class="metric-title">Live Load Profile (AI Reacting)</div>', unsafe_allow_html=True)
        fig_l = go.Figure()
        fig_l.add_trace(go.Scatter(x=df['Hour'], y=df['Total'], fill='tozeroy', line=dict(color='#5E63D8', width=2), name='Demand'))
        fig_l.add_trace(go.Scatter(x=df['Hour'], y=df['Solar'], line=dict(color='#F59E0B', width=2, dash='dot'), name=f'Solar ({w_select})'))
        fig_l.add_trace(go.Scatter(x=df['Hour'], y=df['Wind'],  line=dict(color='#06B6D4', width=2, dash='dash'), name=f'Wind ({w_select})'))

        y_max = max(df['Total'].max(), df['Solar'].max(), df['Wind'].max()) * 1.25
        fig_l.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), template="plotly_white", 
                            legend=dict(orientation="h", y=1.1),
                            yaxis=dict(range=[0, y_max]))
        st.plotly_chart(fig_l, use_container_width=True)

        

    with sub_c2:
        st.markdown('<div class="metric-title" style="margin-bottom:5px; text-align:center;">Battery Status</div>', unsafe_allow_html=True)
        bat_cap = int(solar_cap * 0.8)
        
        # Weather-based parameters (Logic moved to start of function)
        if w_select == "Sunny":
            solar_in = 98 
            health_pct = 98
            health_text = "Good"
            color = "#10B981" # Green
        elif w_select == "Rainy":
            solar_in = 15
            health_pct = 94
            health_text = "Fair"
            color = "#EF4444" # Red
        elif w_select == "Partly Cloudy":
            solar_in = 65
            health_pct = 97
            health_text = "Good"
            color = "#F59E0B" # Orange
        else: # Overcast
            solar_in = 30
            health_pct = 96
            health_text = "Good"
            color = "#F59E0B" # Orange
            
        def mini_bar(val, max_v=100, col="#5E63D8"):
            pct = (val / max_v) * 100
            return f"""<div style="background:#E2E8F0; width:100%; height:6px; border-radius:3px; margin-top:2px;"><div style="background:{col}; width:{pct}%; height:100%; border-radius:3px;"></div></div>"""

        st.markdown(f"""
        <div style="display:flex; justify-content:center; margin-bottom:10px;">
             <!-- Main Battery Visual -->
            <div style="border:2px solid #E2E8F0; border-radius:8px; padding:2px; width:40px; height:70px; position:relative; margin-right:15px;">
                <div style="background:{color}; width:100%; height:{bat_pct}%; position:absolute; bottom:0; border-radius:4px; transition: height 0.5s;"></div>
            </div>
            <!-- Large % Text -->
            <div style="display:flex; flex-direction:column; justify-content:center; align-items:flex-start;">
                <div style="font-size:1.5rem; font-weight:bold; color:{color};">{bat_pct}%</div>
                <div style="font-size:0.75rem; color:#64748B;">Charge Level</div>
            </div>
        </div>
        
        <div style="font-size:0.75rem; color:#475569; padding-top:5px; border-top:1px solid #F1F5F9;">
            <div style="margin-bottom:6px;">
                <div style="display:flex; justify-content:space-between;"><span>☀️ <strong>Solar Input</strong></span> <span>{solar_in}%</span></div>
                {mini_bar(solar_in, 100, "#F59E0B")}
            </div>
            <div style="margin-bottom:6px;">
                <div style="display:flex; justify-content:space-between;"><span>💨 <strong>Wind Input</strong></span> <span>{int(wind_fraction_pct)}%</span></div>
                {mini_bar(wind_fraction_pct, 100, "#06B6D4")}
            </div>
            <div style="margin-bottom:6px;">
                <div style="display:flex; justify-content:space-between;"><span>❤️ <strong>Health</strong></span> <span>{health_pct}%</span></div>
                {mini_bar(health_pct, 100, "#10B981")}
            </div>
            <div style="font-size:0.7rem; color:#94A3B8; margin-top:5px;">Est. Replace: <strong>{8 if health_pct>95 else 6} Years</strong></div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)



# --- ROW 3: CUMULATIVE IMPACT (Full Screen Width) ---
st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
st.markdown('<div class="metric-title">Cumulative Impact Projection (Yearly Scenario Analysis)</div>', unsafe_allow_html=True)

ci_1, ci_2 = st.columns([1, 4])

with ci_1:
    st.markdown("<br>", unsafe_allow_html=True)
    mode = st.radio("Select Scenario", ["Hybrid", "100% Green", "100% Dirty"], label_visibility="visible")
    st.markdown("<br>", unsafe_allow_html=True)
    

    if "Green" in mode:
        impact_curve = np.cumsum(np.full(12, 5000)) + np.random.normal(0, 500, 12)
        perf_curve = 90 - (np.arange(12) * 2) # Degrading perf
        
        impact_text = "🌿 <strong>12,500 Trees</strong> planted eqv."
        profit_text = "⚠️ Performance: <strong>Dropping (-20%)</strong>"
        car_text = "🚗 <strong>352 Cars</strong> removed from road"
        l_col = "#10B981"
        
    elif "Dirty" in mode:
        impact_curve = np.zeros(12) - 100 # Flatline/Negative
        perf_curve = np.full(12, 100) # Max perf
        
        impact_text = "🔥 <strong>50 tons Coal</strong> burned"
        profit_text = "✅ Performance: <strong>Maximum (100%)</strong>"
        car_text = "🚗 <strong>152 Cars</strong> added to road"
        l_col = "#EF4444"

    else:
        impact_curve = np.cumsum(np.full(12, saved_kg * 30))
        perf_curve = np.full(12, 95) + np.random.normal(0, 2, 12)
        
        impact_text = "✨ <strong>2,400 Trees</strong> saved"
        profit_text = "✅ Performance: <strong>Stable (95%)</strong>"
        cars = int(impact_curve[-1] / 4600)
        car_text = f"🚗 <strong>{cars} Cars</strong> removed from road"
        l_col = "#5E63D8"
    
    st.markdown(f"<div style='font-size:0.85rem; line-height:1.6;'>{impact_text}<br>{car_text}<br><span style='font-size:0.75rem; color:#6B7280;'>{profit_text}</span></div>", unsafe_allow_html=True)

with ci_2:
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    fig_y = go.Figure()
    
    # Dual Axis to show Productivity separately from Carbon
    fig_y.add_trace(go.Scatter(x=months, y=impact_curve, mode='lines', name='Carbon Saved (kg)', line=dict(color=l_col, width=4)))
    fig_y.add_trace(go.Scatter(x=months, y=perf_curve, mode='lines+markers', name='System Productivity', yaxis='y2', line=dict(color='#64748B', width=2, dash='dot')))
    
    fig_y.update_layout(
        height=250, margin=dict(l=0,r=0,t=10,b=0), template="plotly_white", 
        showlegend=True, legend=dict(orientation="h", y=1.1),
        yaxis=dict(title="Carbon Impact"),
        yaxis2=dict(title="Productivity Score", overlaying='y', side='right', range=[0, 110])
    )
    st.plotly_chart(fig_y, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)



# --- ROW 3: INFRASTRUCTURE ---
r3_1, r3_2 = st.columns([2, 1])

with r3_1:
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("### 📊 Tech Stack Analysis")
    c_tech_l, c_tech_r = st.columns([1, 2])
    with c_tech_l:
        st.caption("Real-time emission factors.")
        cat = st.radio("Select Layer", ["Compute Engines", "Cloud Storage", "Serverless", "Networking"], label_visibility="collapsed")
    with c_tech_r:
        # Data scales with weather impact (Dirty Grid = More savings from efficiency)
        if cat == "Compute Engines": v1, v2 = 4500*tech_scale, 3500*tech_scale
        elif cat == "Cloud Storage": v1, v2 = 1200*tech_scale, 1020*tech_scale
        elif cat == "Networking": v1, v2 = 800*tech_scale, 720*tech_scale
        else: v1, v2 = 2000*tech_scale, 1400*tech_scale
        
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(y=['Co2'], x=[v1], orientation='h', name='Std', marker_color='#9CA3AF'))
        fig_b.add_trace(go.Bar(y=['Co2'], x=[v2], orientation='h', name='Eco', marker_color='#10B981'))
        fig_b.update_layout(height=120, margin=dict(l=0,r=0,t=0,b=0), template="plotly_white", showlegend=False)
        st.plotly_chart(fig_b, use_container_width=True)
        st.caption(f"Net Savings: {int(v1-v2)} kgCO2")
    st.markdown('</div>', unsafe_allow_html=True)

with r3_2:
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-title">Energy Cleanliness Map (Clean vs Dirty)</div>', unsafe_allow_html=True)
    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
    # Heatmap is now Dynamic!
    fig_h = px.imshow(heatmap, color_continuous_scale="RdYlGn", aspect="auto", zmin=0, zmax=100)
    fig_h.update_layout(height=130, margin=dict(l=0,r=0,t=0,b=0), coloraxis_showscale=False)
    st.plotly_chart(fig_h, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- ROW 4: WEATHER FORECAST (SINGLE DAY FOCUS) ---
st.markdown("### 🌤️ Real-Time 24h Solar Forecast")

w1, w2 = st.columns([1, 2])

with w1:
    st.markdown('<div class="dashboard-card" style="text-align:center;">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-title">Current Conditions</div>', unsafe_allow_html=True)
    icons = {"Sunny": "☀️", "Partly Cloudy": "⛅", "Overcast": "☁️", "Rainy": "🌧️"}
    st.markdown(f"<div style='font-size:3.5rem;'>{icons[w_select]}</div>", unsafe_allow_html=True)
    
    if w_select == "Rainy" or w_select == "Overcast":
        st.warning("⚠️ Solar Critical Low")
        eff = "20-40%"
    elif w_select == "Partly Cloudy":
        st.info("☁️ Variable Output")
        eff = "60-80%"
    else:
        st.success("✅ Peak Generation")
        eff = "95-100%"
        
    st.caption(f"Efficiency: {eff}")
    st.markdown('</div>', unsafe_allow_html=True)

with w2:
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-title">24-Hour Solar Generation Curve</div>', unsafe_allow_html=True)
    
    # Detailed 24h Forecast Chart
    fig_f = go.Figure()
    
    # 1. Theoretical Max (Dot)
    fig_f.add_trace(go.Scatter(x=df['Hour'], y=850 * np.exp(-0.15 * (df['Hour'] - 12)**2), 
                               name='Potential', line=dict(color='gray', width=1, dash='dot')))
    
    # 2. Actual Forecast (Solid Color, Fill)
    # Color changes with weather
    color_map = {"Sunny": "#F59E0B", "Partly Cloudy": "#FBBF24", "Overcast": "#9CA3AF", "Rainy": "#6B7280"}
    
    fig_f.add_trace(go.Scatter(x=df['Hour'], y=df['Solar'], 
                               name='Forecast', fill='tozeroy', 
                               line=dict(color=color_map[w_select], width=3)))
    

    fig_f.update_layout(height=200, margin=dict(l=0,r=0,t=10,b=0), template="plotly_white", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig_f, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- ROW 5: AI NEURAL ENGINE ---
st.markdown('<div class="dashboard-card" style="border-left: 4px solid #5E63D8;">', unsafe_allow_html=True)
st.markdown('<div class="metric-title" style="color:#5E63D8;">🧠 EcoSync Neural Engine (Live Decision Stream)</div>', unsafe_allow_html=True)

c_ai_1, c_ai_2 = st.columns([4, 1])
with c_ai_1:
    st.markdown(f"""
    <div style="font-family:'Consolas', 'Courier New', monospace; font-size:0.85rem; color:#1E293B; background:#F1F5F9; padding:10px; border-radius:4px;">
    {ai_decision}
    </div>
    """, unsafe_allow_html=True)
with c_ai_2:
    st.markdown("**Model State**")
    st.caption("PPO-RL Agent v4.2")
    if w_select == "Rainy":
        st.error("Hard Constraints")
    else:
        st.success("Optimal Policy")
    

st.markdown('</div>', unsafe_allow_html=True)


import random 






# --- ROW 6: MONTHLY ECO-AUDIT (Redesigned with Solar + Wind) ---
st.markdown('<div id="audit-trigger-area">', unsafe_allow_html=True)
st.markdown("""
<div class="dashboard-card" style="margin-top:20px; border-left:4px solid #10B981;">
    <div class="metric-title" style="color:#10B981; font-size:1rem; margin-bottom:12px;">
        📅 Monthly Eco-Audit — Solar & Wind Breakdown
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="dashboard-card" style="margin-top:0px;">', unsafe_allow_html=True)

if 'audit_active' not in st.session_state:
    st.session_state['audit_active'] = False
if 'last_date' not in st.session_state:
    st.session_state['last_date'] = datetime.now().date()

if st.button("RESET", key="btn_reset_audit", help="Hidden master reset"):
    st.session_state['audit_active'] = False
    st.session_state['last_date'] = datetime.now().date()
    st.rerun()

# Date picker row with instruction
col_dp1, col_dp2, col_dp3 = st.columns([1, 1.5, 1])
with col_dp2:
    st.caption("📆 Pick a date to run the audit")
    audit_picker = st.date_input("Audit Date", datetime.now(), label_visibility="collapsed", key="audit_picker_trigger")

if audit_picker != st.session_state['last_date']:
    st.session_state['audit_active'] = True
    st.session_state['last_date'] = audit_picker
    st.rerun()

if st.session_state['audit_active']:
    st.markdown("""
    <style>
    @keyframes slideInUp {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .audit-reveal { animation: slideInUp 0.5s ease-out forwards; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="audit-reveal">', unsafe_allow_html=True)
    st.markdown("---")

    hours_arr  = np.arange(24)
    hours_list = [f"{h:02d}:00" for h in hours_arr]

    # ── Build per-hour arrays: 3-tier data pipeline ───────────────────────────
    # Tier 1: Live Open-Meteo API  →  Tier 2: Local CSV cache  →  Tier 3: Simulation
    found_data  = False
    data_source = "simulated"   # updated as we find better data

    def _raw_to_kw(rad_arr, wspd_arr):
        """Convert raw radiation (W/m²) and wind speed (km/h) to kW generation."""
        sol = np.clip((np.array(rad_arr)  / 1000.0) * solar_cap, 0, solar_cap)
        wnd_frac = np.clip((np.array(wspd_arr) - 10.0) / (50.0 - 10.0), 0.0, 1.0) ** 1.5
        wnd = wnd_frac * wind_cap
        return sol, wnd

    # Tier 1 — live API fetch (cached per date for 1 h)
    date_str = audit_picker.strftime("%Y-%m-%d")
    with st.spinner("Fetching real weather data from Open-Meteo…"):
        live = fetch_weather_for_date(date_str)

    if live is not None:
        found_data  = True
        data_source = "api"
        solar_kw, wind_kw = _raw_to_kw(live["solar"], live["wind"])

    # Tier 2 — local CSV (covers Aug 2025 – Feb 2026 for Northern Virginia)
    if not found_data:
        weather_df = load_historical_weather()
        if weather_df is not None:
            day_data = weather_df[weather_df['time'].dt.date == audit_picker]
            if len(day_data) >= 24:
                found_data  = True
                data_source = "csv"
                solar_kw, wind_kw = _raw_to_kw(
                    day_data['solar_radiation_w_m2'].values[:24],
                    day_data['wind_speed_kmh'].values[:24]
                )

    # Tier 3 — deterministic simulation (seeded by date so same date = same result)
    if not found_data:
        random.seed(int(audit_picker.strftime("%Y%m%d")))
        day_type    = random.choice(["Sunny", "Rainy", "Cloudy"])
        cloud_cover = {"Sunny": 0.05, "Cloudy": 0.5, "Rainy": 0.85}[day_type]
        solar_kw    = np.maximum(solar_cap * np.exp(-0.15*(hours_arr-12.0)**2) * (1-cloud_cover), 0)
        wind_factor = {"Sunny": 0.25, "Cloudy": 0.55, "Rainy": 0.80}[day_type]
        wind_kw     = np.maximum(wind_cap * wind_factor * (0.5 + 0.2*np.sin(hours_arr/4.0)), 0)

    # Demand curve: business-hours shaped sine + base load
    demand_kw = 300 + (user_mult * 40) * np.clip(np.sin((hours_arr - 2) / 4.0), 0, 1)
    renewable_kw  = solar_kw + wind_kw
    grid_kw       = np.maximum(demand_kw - renewable_kw, 0)
    curtailed_kw  = np.maximum(renewable_kw - demand_kw, 0)  # surplus not used

    # ── KPI summary values ────────────────────────────────────────────────────
    total_demand    = demand_kw.sum()
    total_solar     = solar_kw.sum()
    total_wind      = wind_kw.sum()
    total_renewable = min(total_solar + total_wind, total_demand)
    total_grid      = grid_kw.sum()
    renewable_pct   = int(min(total_renewable / max(1, total_demand) * 100, 100))
    co2_avoided_kg  = int(total_renewable * 0.5)   # 0.5 kg CO2/kWh displaced
    grid_import_kwh = int(total_grid)
    # "Clean hour" = renewable covers ≥ 60 % of demand that hour
    clean_hours     = int(np.sum((renewable_kw / np.maximum(demand_kw, 1)) >= 0.6))

    # ── ROW A: KPI Cards ──────────────────────────────────────────────────────
    badge_map = {
        "api":       ("<span style='color:#10B981;'>●</span> Live — Open-Meteo API",  "#ECFDF5", "#10B981"),
        "csv":       ("<span style='color:#5E63D8;'>●</span> Cached — Open-Meteo",   "#EEF2FF", "#5E63D8"),
        "simulated": ("<span style='color:#94A3B8;'>●</span> Simulated",              "#F8FAFC", "#94A3B8"),
    }
    badge_text, badge_bg, badge_col = badge_map[data_source]

    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
        <div style="font-size:1.05rem; font-weight:700; color:#1E293B;">
            🕒 {audit_picker.strftime('%B %d, %Y')}
            <span style="font-size:0.7rem; font-weight:400; color:#64748B; margin-left:8px;">
                Northern Virginia · Data Center Region
            </span>
        </div>
        <div style="font-size:0.72rem; font-weight:600; color:{badge_col};
                    background:{badge_bg}; padding:3px 12px; border-radius:12px;
                    border:1px solid {badge_col}30;">
            {badge_text}
        </div>
    </div>
    """, unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    def kpi(label, value, sub, color):
        return f"""<div style="background:#F8FAFC; border-radius:10px; padding:12px 10px;
                               border-top:3px solid {color}; text-align:center;">
                     <div style="font-size:1.35rem; font-weight:800; color:{color};">{value}</div>
                     <div style="font-size:0.7rem; font-weight:600; color:#1E293B; margin:2px 0;">{label}</div>
                     <div style="font-size:0.62rem; color:#94A3B8;">{sub}</div>
                   </div>"""
    with k1: st.markdown(kpi("Renewable Coverage", f"{renewable_pct}%",   "Solar + Wind vs Demand", "#10B981"), unsafe_allow_html=True)
    with k2: st.markdown(kpi("CO₂ Avoided",        f"{co2_avoided_kg} kg","vs Full-Grid Equivalent", "#5E63D8"), unsafe_allow_html=True)
    with k3: st.markdown(kpi("Grid Import",         f"{grid_import_kwh} kWh","Fossil supplement",    "#F59E0B"), unsafe_allow_html=True)
    with k4: st.markdown(kpi("Clean Hours",         f"{clean_hours}/24",  "≥60% renewable coverage", "#06B6D4"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── ROW B: Main Stacked Area Chart ────────────────────────────────────────
    st.markdown('<div style="font-size:0.8rem; font-weight:600; color:#475569; margin-bottom:6px;">⚡ 24-Hour Generation vs Demand</div>', unsafe_allow_html=True)

    fig_main = go.Figure()
    # Grid area (bottom of stack)
    fig_main.add_trace(go.Bar(
        x=hours_list, y=grid_kw,
        name="Grid (Fossil)", marker_color="#CBD5E1",
        hovertemplate='%{x}<br>Grid: %{y:.0f} kW<extra></extra>'
    ))
    # Wind area (middle)
    fig_main.add_trace(go.Bar(
        x=hours_list, y=np.minimum(wind_kw, demand_kw - np.maximum(demand_kw - wind_kw - solar_kw, 0) - grid_kw + wind_kw),
        name="Wind", marker_color="#06B6D4",
        hovertemplate='%{x}<br>Wind: %{y:.0f} kW<extra></extra>'
    ))
    # Solar area (top)
    fig_main.add_trace(go.Bar(
        x=hours_list, y=np.minimum(solar_kw, demand_kw),
        name="Solar", marker_color="#F59E0B",
        hovertemplate='%{x}<br>Solar: %{y:.0f} kW<extra></extra>'
    ))
    # Demand line overlay
    fig_main.add_trace(go.Scatter(
        x=hours_list, y=demand_kw,
        name="Demand", mode='lines',
        line=dict(color='#1E293B', width=2.5, dash='dot'),
        hovertemplate='%{x}<br>Demand: %{y:.0f} kW<extra></extra>'
    ))
    fig_main.update_layout(
        barmode='stack', height=230,
        margin=dict(l=0, r=0, t=10, b=0),
        template="plotly_white",
        legend=dict(orientation="h", y=1.12, x=0),
        yaxis=dict(title="kW", gridcolor="#F1F5F9"),
        xaxis=dict(tickangle=-45, tickfont=dict(size=10))
    )
    st.plotly_chart(fig_main, use_container_width=True)

    # ── ROW C: Donut + AI Decision Timeline ───────────────────────────────────
    col_donut, col_timeline = st.columns([1, 2])

    with col_donut:
        st.markdown('<div style="font-size:0.8rem; font-weight:600; color:#475569; margin-bottom:6px;">🍩 Daily Energy Mix</div>', unsafe_allow_html=True)
        solar_used = float(np.minimum(solar_kw, demand_kw).sum())
        wind_used  = float(np.minimum(wind_kw,  np.maximum(demand_kw - solar_kw, 0)).sum())
        grid_used_total = float(total_grid)
        fig_donut = go.Figure(go.Pie(
            labels=["Solar", "Wind", "Grid"],
            values=[solar_used, wind_used, grid_used_total],
            hole=0.55,
            marker=dict(colors=["#F59E0B", "#06B6D4", "#CBD5E1"]),
            textinfo='percent',
            hovertemplate='%{label}: %{value:.0f} kWh (%{percent})<extra></extra>'
        ))
        fig_donut.update_layout(
            height=220, margin=dict(l=0, r=0, t=10, b=0),
            showlegend=True,
            legend=dict(orientation="h", y=-0.1, x=0.1, font=dict(size=10)),
            annotations=[dict(text=f"<b>{renewable_pct}%</b><br>clean", x=0.5, y=0.5,
                              font=dict(size=13, color="#10B981"), showarrow=False)]
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_timeline:
        st.markdown('<div style="font-size:0.8rem; font-weight:600; color:#475569; margin-bottom:6px;">🤖 AI Decision Timeline (per hour)</div>', unsafe_allow_html=True)

        # Derive per-hour AI action using the same guardrail logic
        audit_actions = []
        audit_colors  = []
        audit_labels  = []
        total_cap = max(1, solar_cap + wind_cap)
        for h in range(24):
            s_frac = (solar_kw[h] + wind_kw[h]) / total_cap
            carbon_h = 400 + 100 * np.exp(-0.5 * ((h - 9) / 1.5) ** 2) + \
                             150 * np.exp(-0.5 * ((h - 19) / 2.0) ** 2)
            q = user_mult * 10  # queue depth from current traffic slider

            if carbon_h > 500 and s_frac < 0.15:
                act, col, lbl = 2, "#EF4444", "Defer"
            elif q > 400 and s_frac > 0.15:
                act, col, lbl = 0, "#5E63D8", "Boost"
            elif s_frac > 0.55:
                act, col, lbl = 0, "#5E63D8", "Boost"
            elif s_frac > 0.25 and carbon_h < 450:
                act, col, lbl = 1, "#10B981", "Eco"
            else:
                act, col, lbl = 2, "#EF4444", "Defer"

            audit_actions.append(act)
            audit_colors.append(col)
            audit_labels.append(lbl)

        fig_timeline = go.Figure()
        fig_timeline.add_trace(go.Bar(
            x=hours_list,
            y=[1] * 24,
            marker_color=audit_colors,
            text=audit_labels,
            textposition='inside',
            textfont=dict(color='white', size=9),
            hovertemplate='%{x}<br>Decision: %{text}<extra></extra>',
            showlegend=False
        ))
        # Legend annotations
        for label, color in [("🚀 Boost", "#5E63D8"), ("🌱 Eco", "#10B981"), ("🛑 Defer", "#EF4444")]:
            fig_timeline.add_trace(go.Bar(x=[None], y=[None], name=label, marker_color=color))
        fig_timeline.update_layout(
            height=220, margin=dict(l=0, r=0, t=10, b=0),
            template="plotly_white",
            barmode='stack',
            legend=dict(orientation="h", y=1.15, x=0, font=dict(size=10)),
            yaxis=dict(visible=False),
            xaxis=dict(tickangle=-45, tickfont=dict(size=9))
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

    # ── Attribution footer ────────────────────────────────────────────────────
    if data_source == "api":
        st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; margin-top:10px;
                    padding:8px 14px; background:#F0FDF4; border-radius:8px;
                    border:1px solid #BBF7D0;">
            <div style="font-size:1.4rem;">🌍</div>
            <div>
                <div style="font-size:0.75rem; font-weight:700; color:#15803D;">
                    Powered by Open-Meteo
                </div>
                <div style="font-size:0.65rem; color:#64748B;">
                    Free open-source weather API · Historical archive data ·
                    <a href="https://open-meteo.com" target="_blank"
                       style="color:#5E63D8; text-decoration:none;">open-meteo.com</a>
                    · Location: Northern Virginia (39.04°N, 77.49°W)
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif data_source == "csv":
        st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; margin-top:10px;
                    padding:8px 14px; background:#EEF2FF; border-radius:8px;
                    border:1px solid #C7D2FE;">
            <div style="font-size:1.4rem;">💾</div>
            <div>
                <div style="font-size:0.75rem; font-weight:700; color:#4338CA;">
                    Data: Open-Meteo (Cached)
                </div>
                <div style="font-size:0.65rem; color:#64748B;">
                    Served from local archive · Source:
                    <a href="https://open-meteo.com" target="_blank"
                       style="color:#5E63D8; text-decoration:none;">open-meteo.com</a>
                    · Northern Virginia
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; margin-top:10px;
                    padding:8px 14px; background:#F8FAFC; border-radius:8px;
                    border:1px solid #E2E8F0;">
            <div style="font-size:1.4rem;">🔵</div>
            <div>
                <div style="font-size:0.75rem; font-weight:700; color:#475569;">
                    Simulated Data
                </div>
                <div style="font-size:0.65rem; color:#94A3B8;">
                    No real data available for this date (future date or outside archive range).
                    Showing physics-based deterministic simulation seeded by date.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # audit-reveal

st.markdown('</div></div>', unsafe_allow_html=True)

# JAVASCRIPT: click-outside reset + calendar weekday header colour fix
st.components.v1.html(
    """
    <script>
    const doc = window.parent.document;

    // --- 1. Inject a <style> tag into the parent <head> ---
    // This is the only approach guaranteed to reach the calendar popup,
    // because it becomes part of the page's own stylesheet cascade.
    (function() {
        const styleId = 'eco-calendar-fix';
        if (doc.getElementById(styleId)) return; // already injected
        const style = doc.createElement('style');
        style.id = styleId;
        style.textContent = `
            /* Weekday header row: Sun Mon Tue Wed Thu Fri Sat */
            [role="columnheader"],
            [role="columnheader"] abbr,
            [role="columnheader"] span,
            [role="columnheader"] div {
                color: #ffffff !important;
                text-decoration: none !important;
                font-weight: 600 !important;
            }
            /* Month / year label and nav arrow buttons */
            [data-baseweb="calendar"] [role="heading"],
            [data-baseweb="calendar"] button svg,
            [data-baseweb="calendar"] button {
                color: #ffffff !important;
                fill:  #ffffff !important;
            }
        `;
        doc.head.appendChild(style);
    })();

    // --- 2. Click-outside reset for audit card ---
    doc.addEventListener('click', function(e) {
        const area = doc.getElementById('audit-trigger-area');
        const resetBtn = doc.querySelector('button[key="btn_reset_audit"]');
        if (area && !area.contains(e.target)) {
            if (resetBtn) resetBtn.click();
        }
    }, true);
    </script>
    """,
    height=0
)

