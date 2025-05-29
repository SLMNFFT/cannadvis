import streamlit as st
import pandas as pd
import plotly.express as px
from duckduckgo_search import ddg_images

st.set_page_config(page_title="Cannabis Strain Explorer", layout="wide")
st.title("🌿 Cannadvis BETA")

# --- Load data only when needed ---
@st.cache_data
def load_data():
    df = pd.read_csv("strains.csv")
    df['thc'] = pd.to_numeric(df['thc'], errors='coerce')
    df['cbd'] = pd.to_numeric(df['cbd'], errors='coerce')
    df['effects'] = df['effects'].fillna('')
    df['image'] = df['image'].fillna('')
    df['type'] = df['type'].fillna('Unknown')
    return df

# --- Function to search image online ---
@st.cache_data(show_spinner=False)
def fetch_image_online(query):
    try:
        results = ddg_images(query + " cannabis strain", max_results=1)
        if results:
            return results[0]["image"]
    except Exception:
        return None
    return None

# Preload data just to populate filter dropdowns
try:
    df_preview = load_data()
except:
    df_preview = pd.DataFrame(columns=["name", "type", "effects", "thc"])

strain_names = ["Any"] + sorted(df_preview["name"].dropna().unique().tolist())
strain_types = ["Any"] + sorted(df_preview["type"].dropna().unique().tolist())
all_effects = df_preview["effects"].str.split(", ").explode().dropna().unique()
effect_choices = ["Any"] + sorted(all_effects)

# --- Sidebar filters ---
st.sidebar.header("🔎 Filter Strains")
selected_name = st.sidebar.selectbox("Strain Name", strain_names, key="strain_name")
selected_type = st.sidebar.selectbox("Strain Type", strain_types, key="strain_type")
selected_effect = st.sidebar.selectbox("Desired Effect", effect_choices, key="effect")
thc_range = st.sidebar.slider("THC % Range", 0.0, 40.0, (0.0, 25.0), key="thc_slider")

search = st.sidebar.button("🔍 Search")

if search:
    df = load_data()

    # --- Apply filters ---
    filtered_df = df.copy()
    if st.session_state.strain_name != "Any":
        filtered_df = filtered_df[filtered_df["name"] == st.session_state.strain_name]
    if st.session_state.strain_type != "Any":
        filtered_df = filtered_df[filtered_df["type"] == st.session_state.strain_type]
    if st.session_state.effect != "Any":
        filtered_df = filtered_df[filtered_df["effects"].str.contains(st.session_state.effect, case=False, na=False)]
    filtered_df = filtered_df[
        (filtered_df["thc"].fillna(0.0) >= st.session_state.thc_slider[0]) &
        (filtered_df["thc"].fillna(0.0) <= st.session_state.thc_slider[1])
    ]

    # --- Effects Chart ---
    st.subheader("📊 Effects Distribution by Strain Type")
    expanded = filtered_df[["type", "effects"]].assign(effects=filtered_df["effects"].str.split(", ")).explode("effects")
    expanded = expanded.dropna()
    if not expanded.empty:
        counts = (
            expanded.groupby(["type", "effects"])
            .size()
            .reset_index(name="count")
            .sort_values(by="count", ascending=False)
        )
        fig = px.bar(
            counts,
            x="effects",
            y="count",
            color="type",
            barmode="group",
            title="Effect Counts by Strain Type",
            labels={"effects": "Effect", "count": "Count", "type": "Strain Type"},
            height=500,
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No effect data available.")

    # --- Display Strains ---
    st.subheader("🧾 Matching Strains")
    if filtered_df.empty:
        st.warning("No matching strains found.")
    else:
        for _, row in filtered_df.iterrows():
            st.markdown("----")
            cols = st.columns([1, 2])
            with cols[0]:
                # Load image from dataset or fallback to online
                image_url = row["image"]
                if not image_url.startswith("http"):
                    image_url = fetch_image_online(row["name"]) or ""

                if image_url:
                    st.image(image_url, width=200)
                else:
                    st.write("🖼️ No image available.")

                st.markdown("**THC %**")
                st.slider("THC", 0.0, 40.0, float(row["thc"] or 0), disabled=True, key=f"thc_{row['id']}")
                st.markdown("**CBD %**")
                st.slider("CBD", 0.0, 20.0, float(row["cbd"] or 0), disabled=True, key=f"cbd_{row['id']}")
                st.markdown(f"**Type**: {row['type']}")
                st.markdown(f"**Effects**: {row['effects']}")
                st.markdown(f"**Flavor**: {row.get('flavor', 'N/A')}")

            with cols[1]:
                st.markdown(f"### {row['name']}")
                st.markdown(row.get('description', 'No description available.'))

    st.caption("📄 Powered by `strains.csv` + DuckDuckGo | Built with ❤️ in Streamlit")
else:
    st.info("Use the filters in the sidebar and click **Search** to explore cannabis strains.")
