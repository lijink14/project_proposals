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

# --- DATA AGENT ---
@st.cache_data
def get_dynamic_model(user_mult, solar_cap, weather_type):
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
    
    # Construct simulated observation for the PPO agent
    sim_solar = solar_gen.mean()
    sim_carbon = 800 if weather_type == "Rainy" else 200
    sim_queue = user_mult * 10
    
    # Define Battery State based on Weather (moved from UI section)
    if weather_type == "Sunny":
        bat_pct = 94
    elif weather_type == "Rainy":
        bat_pct = 35
    elif weather_type == "Partly Cloudy":
        bat_pct = 78
    else: # Overcast
        bat_pct = 55

    # 🔥 LIVE INFERENCE CALL 🔥
    # Passed bat_pct instead of hardcoded 100
    action_str, action_id = ai_engine.infer_action(12, sim_solar, 150, sim_carbon, sim_queue, bat_pct)
    
    # 1. Traffic Analysis
    if user_mult > 35:
        decision_log.append(f"⚠️ **High Traffic:** Queue depth {int(sim_queue)}. Policy: **{action_str}**")
    elif user_mult < 10:
        decision_log.append("💤 **Low Traffic:** Consolidated workloads. Efficiency Mode.")
    else:
        decision_log.append(f"✅ **Traffic Nominal:** Policy: **{action_str}** active.")
        
    # 2. Weather/Energy Analysis
    if weather_type == "Rainy":
        decision_log.append(f"🌧️ **Solar Critical:** Logic detects High Carbon Grid ({sim_carbon}g/kWh).")
        if action_id == 2: # HOLD
            decision_log.append("🛑 **AI Decision:** DEFER LOADS. Holding non-critical tasks.")
        else: 
             decision_log.append("📉 **AI Decision:** Shedding 60% load to Night cycle.")
             
    elif weather_type == "Sunny":
        decision_log.append("☀️ **Solar Peak:** Grid Carbon Negative.")
        if action_id == 0: # PROCESS ALL
             decision_log.append("🚀 **AI Decision:** BOOST MODE. Processing all backlog.")
        else:
             decision_log.append("🚀 **AI Decision:** Max Throughput allowed.")
    else:
        decision_log.append(f"☁️ **Variable Gen:** AI Action: {action_str} to balance grid.")

    ai_msg = " ".join([f"<div style='margin-bottom:4px;'>{x}</div>" for x in decision_log])
    
    df_live = pd.DataFrame({
        "Hour": hours, 
        "Compute": load_compute, "Storage": load_storage, "Network": load_network,
        "Total": total_load, "Solar": solar_gen
    })

    return df_live, heatmap, tech_scale, ai_msg, bat_pct

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='font-size: 2.2rem; font-weight: 800; margin-bottom: 20px;'>Eco-Compute</h1>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Simulation Controls")
    user_mult = st.slider("Active User Traffic", 1, 50, 15)
    solar_cap = st.slider("Solar Farm Capacity (kW)", 0, 2000, 850)
    
    st.markdown("---")
    st.markdown("### Weather Condition")
    # This trigger is key - it drives the entire model
    w_select = st.selectbox("Current", ["Sunny", "Partly Cloudy", "Overcast", "Rainy"], index=0, label_visibility="collapsed")
    

    st.markdown("---")
    st.caption("Status: **LOCKED FINAL**")



df, heatmap, tech_scale, ai_decision, bat_pct = get_dynamic_model(user_mult, solar_cap, w_select)


# --- ROW 1: MINI METRICS ---
c1, c2, c3, c4, c5, c6 = st.columns(6)
def mini(label, val, sub):
    return f"""<div class="dashboard-card" style="padding:10px;"><div class="metric-title">{label}</div><div class="metric-value" style="font-size:1.4rem;">{val}</div><div class="metric-sub sub-neutral" style="font-size:0.6rem;">{sub}</div></div>"""

total = int(df['Total'].sum())
solar_sum = int(df['Solar'].sum())
# Carbon Saved depends on weather (if Rainy, grid is dirty, so avoiding it saves MORE carbon per kWh, but we used less solar...)
# Let's simplify: Saved = Solar Gen * 0.5kg
saved_kg = int(solar_sum * 0.5) 

with c1: st.markdown(mini("Total Demand", f"{total} kWh", "24h Forecast"), unsafe_allow_html=True)
with c2: st.markdown(mini("Avoided CO2", f"{saved_kg} kg", "Via Solar"), unsafe_allow_html=True)
with c3: st.markdown(mini("Solar Input", f"{solar_sum} kWh", w_select), unsafe_allow_html=True)
with c4: st.markdown(mini("Active Threads", f"{int(user_mult*120)}", "AI Scaled"), unsafe_allow_html=True)
# Cost increases if solar is low
est_cost = int((total - solar_sum) * 0.15) 
with c5: st.markdown(mini("Est. Cost", f"${est_cost}", "Grid Import"), unsafe_allow_html=True)
with c6: st.markdown(mini("Grid Relief", f"{int(solar_sum/total*100)}%", "Self-Sufficiency"), unsafe_allow_html=True)

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
        
        y_max = max(df['Total'].max(), df['Solar'].max()) * 1.25
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






# --- ROW 6: HISTORICAL IMPACT AUDIT (Auto-Vanish & Animation) ---
# We use an ID here so our Javascript can identify the 'Safe Zone'
st.markdown('<div id="audit-trigger-area">', unsafe_allow_html=True)
st.markdown('<div class="dashboard-card" style="margin-top:20px; text-align:center;">', unsafe_allow_html=True)
st.markdown('<div class="metric-title">📅 Monthly Eco-Audit</div>', unsafe_allow_html=True)

if 'audit_active' not in st.session_state:
    st.session_state['audit_active'] = False
if 'last_date' not in st.session_state:
    st.session_state['last_date'] = datetime.now().date()

# 🧪 Hidden Reset Bridge
# This button is clicked by our JS script when you click outside the card
if st.button("RESET", key="btn_reset_audit", help="Hidden master reset"):
    st.session_state['audit_active'] = False
    st.session_state['last_date'] = datetime.now().date() # Reset date too
    st.rerun()

# 1. Centered Date Picker
c_a1, c_a2, c_a3 = st.columns([1, 1.5, 1])
with c_a2:
    st.caption("Select Date to Reveal Analysis")
    audit_picker = st.date_input("Audit Date", datetime.now(), label_visibility="collapsed", key="audit_picker_trigger")

# 2. Logic: Auto-Reveal on Change
if audit_picker != st.session_state['last_date']:
    st.session_state['audit_active'] = True
    st.session_state['last_date'] = audit_picker
    st.rerun()

# 3. Animated Analysis Reveal
if st.session_state['audit_active']:
    st.markdown("""
    <style>
    @keyframes slideInUp {
        0% { opacity: 0; transform: translateY(30px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .analysis-reveal {
        animation: slideInUp 0.6s ease-out forwards;
        margin-top: 20px;
        padding-top: 20px;
        border-top: 1px dashed #E2E8F0;
    }
    /* Hide the master reset button visually */
    div[data-testid="stButton"] button[key="btn_reset_audit"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="analysis-reveal">', unsafe_allow_html=True)
    
    # Chart Logic
    hours_list = [f"{h:02d}:00" for h in range(24)]
    
    # Try to load real data
    weather_df = load_historical_weather()
    found_data = False
    mix_data = []
    desc_text = ""

    if weather_df is not None:
        mask = weather_df['time'].dt.date == audit_picker
        day_data = weather_df[mask]
        
        if len(day_data) >= 24:
            found_data = True
            # Use real solar radiation to simulate energy mix
            # Map 0-1000 W/m2 to 0-100 scale (with a base grid mix of 20%)
            solar_vals = day_data['solar_radiation_w_m2'].values[:24]
            mix_data = np.clip(20 + (solar_vals / 900 * 80), 0, 100).astype(int)
            
            avg_sol = solar_vals.mean()
            if avg_sol > 200:
                desc_text = f"☀️ **Real Historical Data:** High Solar Output detected ({int(avg_sol)} W/m² avg)."
            elif avg_sol > 50:
                 desc_text = f"☁️ **Real Historical Data:** Variable Cloud Cover ({int(avg_sol)} W/m² avg)."
            else:
                 desc_text = f"🌧️ **Real Historical Data:** Low Solar Generation ({int(avg_sol)} W/m² avg)."
            
            # Clean text without HTML
            desc_text += "\n\nHistorical weather data sourced from **Open-Meteo** API."

    if not found_data:
        random.seed(int(audit_picker.strftime("%Y%m%d")))
        day_type = random.choice(["Sunny", "Rainy", "Cloudy"])
        
        if day_type == "Sunny":
            mix_data = [20, 20, 20, 30, 50, 75, 95, 100, 100, 95, 80, 60, 40, 30, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20]
            desc_text = "✨ **Solar Peak:** 100% Green penetration achieved during daylight hours."
        elif day_type == "Rainy":
            mix_data = [random.randint(5, 15) for _ in range(24)]
            desc_text = "🌧️ **Grid Strain:** High reliance on non-renewable sources."
        else:
            mix_data = [random.randint(30, 70) for _ in range(24)]
            desc_text = "☁️ **Variable Load:** AI balanced mixed energy inputs."
        
        desc_text += "\n\n*(Simulated Data)*"

    # --- Header Layout ---
    # Logo moves to top right
    c_head_1, c_head_2 = st.columns([0.85, 0.15])
    with c_head_1:
         st.markdown(f"### 🕒 Hourly Energy Mix: {audit_picker.strftime('%B %d, %Y')}")
         st.caption("Live Audit Stream. Click anywhere outside this card to reset.")
    
    if found_data:
        with c_head_2:
            # use a relative path inside the repository so it works on any machine
            import os
            base = os.path.dirname(__file__)
            logo_path = os.path.join(base, "..", "image_reference", "OIP.jpeg")
            logo_path = os.path.normpath(logo_path)
            if os.path.exists(logo_path):
                st.image(logo_path, width=50)
            else:
                # fallback: small placeholder (transparent pixel) to avoid crash
                st.image("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAQAAAEAAelq7NEAAAAASUVORK5CYII=", width=50)
                st.warning(f"Logo not found at {logo_path}")

    # --- Chart ---
    fig_deep = go.Figure(data=go.Heatmap(
        z=np.array(mix_data).reshape(1, 24),
        x=hours_list, y=['Mix'],
        colorscale='RdYlGn', zmin=0, zmax=100,
        xgap=2, hovertemplate='Hour: %{x}<br>Efficiency: %{z}%<extra></extra>'
    ))
    fig_deep.update_layout(height=150, margin=dict(l=0,r=0,t=0,b=0), template="plotly_white", yaxis=dict(visible=False))
    st.plotly_chart(fig_deep, use_container_width=True)
    
    # --- Description (Single Column for proper alignment) ---
    st.info(desc_text)
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div></div>', unsafe_allow_html=True)

# 🧪 JAVASCRIPT CLICK-OUTSIDE BRIDGE
# This script detects clicks. If click is NOT on our audit card, it triggers the hidden reset.
st.components.v1.html(
    """
    <script>
    const doc = window.parent.document;
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

