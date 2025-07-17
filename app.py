import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy.ma as ma

# Setup
st.set_page_config(layout="wide")
st.title("⚡ Hydrogen System Dashboard")

# Load all data
@st.cache_data
def load_all():
    df_pv = pd.read_csv("fPV.csv")
    df_wt = pd.read_csv("fWT.csv")
    df_demand = pd.read_csv("PD.csv")
    df_h2_demand = pd.read_csv("PEL_master.csv")
    df_bess = pd.read_csv("PBESSd_master.csv")
    df_bess_charge = pd.read_csv("PBESSc_master.csv")
    df_soc = pd.read_csv("EBESS_master.csv")
    return df_pv, df_wt, df_demand, df_h2_demand, df_bess, df_bess_charge, df_soc

df_pv, df_wt, df_demand, df_h2_demand, df_bess, df_bess_charge, df_soc = load_all()

# Pivot and align
pv_pivot = df_pv.pivot(index='hour', columns='scenario', values='value')
wt_pivot = df_wt.pivot(index='hour', columns='scenario', values='value')
demand_pivot = df_demand.pivot(index='hour', columns='scenario', values='value')
h2_pivot = df_h2_demand.pivot(index='hour', columns='scenario', values='value')
bess_pivot = df_bess.pivot(index='hour', columns='scenario', values='value')
bess_charge_pivot = df_bess_charge.pivot(index='hour', columns='scenario', values='value')
soc_pivot = df_soc.pivot(index='hour', columns='scenario', values='value')

# Align all
for other in [wt_pivot, demand_pivot, h2_pivot, bess_pivot, bess_charge_pivot, soc_pivot]:
    pv_pivot, other = pv_pivot.align(other, join='inner', axis=0)

scenarios = pv_pivot.columns.tolist()

# === GRID ===
top_left, top_right = st.columns(2)
bottom_left, bottom_right = st.columns(2)

# === TOP LEFT: POWER BALANCE ===
with top_left:
    st.markdown("### 📊 Power Balance")
    balance_scenario = st.selectbox("Select scenario:", scenarios, index=0, key="balance_scenario")
    
    fig, ax = plt.subplots(figsize=(5, 3))
    hours = pv_pivot.index

    pv = pv_pivot[balance_scenario]
    wt = wt_pivot[balance_scenario]
    bess = bess_pivot[balance_scenario]
    bess_charging = bess_charge_pivot[balance_scenario]
    base_demand = demand_pivot[balance_scenario]
    h2_demand = h2_pivot[balance_scenario]

    bess_charging_masked = ma.masked_where(bess_charging < 1e-3, bess_charging)
    h2_demand_masked = ma.masked_where(h2_demand < 1e-3, h2_demand)

    ax.bar(hours, pv, label="PV", color='gold', edgecolor='black', linewidth=0.2)
    ax.bar(hours, wt, bottom=pv, label="WT", color='#56B4E9', edgecolor='black', linewidth=0.2)
    ax.bar(hours, bess, bottom=pv + wt, label="Pdc", color='green', edgecolor='black', linewidth=0.2)
    ax.plot(hours, base_demand, label="PD", color='black', linewidth=1)
    ax.bar(hours, h2_demand_masked, bottom=base_demand, label="PEL", color='none', edgecolor='red', hatch='////')
    ax.bar(hours, bess_charging_masked, bottom=base_demand + h2_demand, label="Pch", color='none', edgecolor='blue', hatch='////')

    ax.set_ylim(0, max((pv + wt + bess).max(), (base_demand + h2_demand + bess_charging).max()) * 1.1)
    ax.set_xlabel("Time [h]")
    ax.set_ylabel("Power [MW]")
    ax.set_title(f"Scenario {balance_scenario}")
    ax.legend(fontsize=7, loc="upper left", ncol=3)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    st.pyplot(fig)

# === TOP RIGHT: PIE CHARTS ===
with top_right:
    st.markdown("### 🍕 Energy Mix by Scenario")
    pie_selected = st.multiselect("Select scenarios for pie:", scenarios, default=[balance_scenario], key="pie_selected")

    max_pies = 6
    pie_selected = pie_selected[:max_pies]  # limit to 6

    rows = 2
    cols = 3
    for row in range(rows):
        pie_cols = st.columns(cols)
        for col in range(cols):
            idx = row * cols + col
            if idx < len(pie_selected):
                scenario = pie_selected[idx]
                pv_total = pv_pivot[scenario].sum()
                wt_total = wt_pivot[scenario].sum()
                fig_pie, ax_pie = plt.subplots(figsize=(1.6, 1.6))
                ax_pie.pie(
                    [pv_total, wt_total],
                    labels=["PV", "WT"],
                    colors=["gold", "#56B4E9"],
                    autopct="%1.1f%%",
                    startangle=90,
                    textprops={'fontsize': 7}
                )
                ax_pie.axis('equal')
                ax_pie.set_title(f"{scenario}", fontsize=7)
                pie_cols[col].pyplot(fig_pie)
            else:
                pie_cols[col].empty()


# === BOTTOM LEFT: SOC ===
with bottom_left:
    st.markdown("### 🔋 SOC Evolution")
    soc_selected = st.multiselect("Select scenarios for SOC:", scenarios, default=[balance_scenario], key="soc_selected")
    fig_soc, ax_soc = plt.subplots(figsize=(5, 2.5))
    for sc in soc_selected:
        ax_soc.plot(soc_pivot.index, soc_pivot[sc], label=f"Scenario {sc}", linewidth=1)
    ax_soc.set_ylim(0, 1)
    ax_soc.set_xlabel("Time [h]")
    ax_soc.set_ylabel("SOC [0–1]")
    ax_soc.set_title("BESS SOC")
    ax_soc.legend(fontsize=7)
    ax_soc.grid(True)
    fig_soc.tight_layout()
    st.pyplot(fig_soc)

# === BOTTOM RIGHT: PLANT IMAGE ===
with bottom_right:
    st.markdown("### 🧩 Plant Layout")
    st.image("SEPOC_Plant.svg", use_container_width=True, caption="Hydrogen Plant Layout")