import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Cannabis Strain Explorer", layout="wide")



st.title("🌿 Cannadvis BETA")




# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("C:/Users/Scarl/Desktop/cannadv/strains.csv")
    for col in ['thc', 'cbd']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['effects'] = df['effects'].fillna('')
    df['image'] = df['image'].fillna('')  # Prevent NaN images
    df['type'] = df['type'].fillna('Unknown')  # Handle missing types
    return df

df = load_data()

# Sidebar filters
st.sidebar.header("🔎 Filter Strains")

strain_names = ["Any"] + sorted(df["name"].dropna().unique().tolist())
strain_types = ["Any"] + sorted(df["type"].dropna().unique().tolist())

# Extract unique effects
all_effects = df["effects"].str.split(", ").explode().dropna().unique()
effect_choices = ["Any"] + sorted(all_effects)

strain_name = st.sidebar.selectbox("Strain Name", strain_names)
strain_type = st.sidebar.selectbox("Strain Type", strain_types)
selected_effect = st.sidebar.selectbox("Desired Effect", effect_choices)
thc_range = st.sidebar.slider("THC % Range", 0.0, 40.0, (0.0, 25.0))

# Filter dataset
filtered_df = df.copy()

if strain_name != "Any":
    filtered_df = filtered_df[filtered_df["name"] == strain_name]

if strain_type != "Any":
    filtered_df = filtered_df[filtered_df["type"] == strain_type]

if selected_effect != "Any":
    filtered_df = filtered_df[filtered_df["effects"].str.contains(selected_effect, case=False, na=False)]

filtered_df = filtered_df[
    (filtered_df["thc"].fillna(0.0) >= thc_range[0]) &
    (filtered_df["thc"].fillna(0.0) <= thc_range[1])
]

# --- Interactive Effects by Type diagram ---
st.subheader("📊 Interactive Effects Distribution by Strain Type")

effects_expanded = (
    filtered_df[["type", "effects"]]
    .assign(effects=filtered_df["effects"].str.split(", "))
    .explode("effects")
)
effects_expanded = effects_expanded.dropna(subset=["effects"])

if effects_expanded.empty:
    st.info("No effect data available for selected filters.")
else:
    effect_counts = (
        effects_expanded.groupby(["type", "effects"])
        .size()
        .reset_index(name="count")
        .sort_values(by="count", ascending=False)
    )

    fig = px.bar(
        effect_counts,
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

# Show strains list below the diagram
st.subheader("🧾 Matching Strains")

if filtered_df.empty:
    st.warning("No matching strains found. Try adjusting your filters.")
else:
    for _, row in filtered_df.iterrows():
        st.markdown("----")
        cols = st.columns([1, 2])
        with cols[0]:
            image_url = row.get("image", "")
            if isinstance(image_url, str) and image_url.startswith("http"):
                st.image(image_url, width=200)
            else:
                st.write("🖼️ No image available.")
            st.markdown(f"**Type**: {row.get('type', 'N/A')}")
            st.markdown(f"**THC**: {row.get('thc', 'N/A')}%")
            st.markdown(f"**CBD**: {row.get('cbd', 'N/A')}%")
            st.markdown(f"**Effects**: {row.get('effects', 'N/A')}")
            st.markdown(f"**Flavor**: {row.get('flavor', 'N/A')}")
        with cols[1]:
            st.markdown(f"### {row.get('name', 'Unknown')}")
            st.markdown(row.get('description', 'No description available.'))

st.caption("📄 Powered by `strains.csv` | Built with ❤️ in Streamlit")
