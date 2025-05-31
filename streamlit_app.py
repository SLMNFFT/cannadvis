import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from duckduckgo_search import DDGS

st.set_page_config(page_title="Cannabis Strain Explorer", layout="wide")
st.title("🌇 Cannadvis BETA")

@st.cache_data
def load_data():
    df = pd.read_csv("strains.csv")
    df['thc'] = pd.to_numeric(df['thc'], errors='coerce')
    df['cbd'] = pd.to_numeric(df['cbd'], errors='coerce')
    df['effects'] = df['effects'].fillna('')
    df['image'] = df['image'].fillna('')
    df['type'] = df['type'].fillna('Unknown')
    for col in ['flavor', 'ailment', 'breeder', 'location']:
        if col not in df.columns:
            df[col] = ''
        df[col] = df[col].fillna('')
    df['description'] = df.get('description', pd.Series([''] * len(df))).fillna('')
    df['youtube'] = df.get('youtube', pd.Series([''] * len(df))).fillna('')
    return df

@st.cache_data(show_spinner=False)
def fetch_image_online(query):
    try:
        with DDGS() as ddgs:
            results = ddgs.images(query + " cannabis strain", max_results=1)
            for r in results:
                image_url = r.get("image")
                if image_url and image_url.startswith("http"):
                    return image_url
    except Exception:
        return None
    return None

try:
    df_preview = load_data()
except Exception:
    df_preview = pd.DataFrame(columns=["name", "type", "effects", "thc"])

strain_names = ["Any"] + sorted(df_preview["name"].dropna().unique().tolist())
strain_types = ["Any"] + sorted(df_preview["type"].dropna().unique().tolist())
all_effects = df_preview["effects"].str.split(", ").explode().dropna().unique()
effect_choices = ["Any"] + sorted(all_effects)

flavors = ["Any"] + sorted(df_preview["flavor"].str.split(", ").explode().dropna().unique())
ailments = ["Any"] + sorted(df_preview["ailment"].str.split(", ").explode().dropna().unique())
breeders = ["Any"] + sorted(df_preview["breeder"].dropna().unique())
locations = ["Any"] + sorted(df_preview["location"].dropna().unique())

# Sidebar filters
st.sidebar.header("🔎 Filter Strains")
selected_name = st.sidebar.selectbox("Strain Name", strain_names)
selected_type = st.sidebar.selectbox("Strain Type", strain_types)
selected_effect = st.sidebar.selectbox("Desired Effect", effect_choices)
selected_flavor = st.sidebar.selectbox("Flavor", flavors)
selected_ailment = st.sidebar.selectbox("Ailment", ailments)
selected_breeder = st.sidebar.selectbox("Breeder", breeders)
selected_location = st.sidebar.selectbox("Location", locations)
thc_range = st.sidebar.slider("THC % Range", 0.0, 40.0, (0.0, 25.0))

sort_by = st.sidebar.selectbox("Sort by Potency", ["None", "Highest THC", "Highest CBD"])
search = st.sidebar.button("🔍 Search")

# Favorites & Notes state management with session_state
if "favorites" not in st.session_state:
    st.session_state.favorites = set()
if "notes" not in st.session_state:
    st.session_state.notes = {}

def toggle_favorite(strain_name):
    if strain_name in st.session_state.favorites:
        st.session_state.favorites.remove(strain_name)
    else:
        st.session_state.favorites.add(strain_name)

def save_note(strain_name, note):
    st.session_state.notes[strain_name] = note

if search:
    df = load_data()

    filtered_df = df.copy()
    if selected_name != "Any":
        filtered_df = filtered_df[filtered_df["name"] == selected_name]
    if selected_type != "Any":
        filtered_df = filtered_df[filtered_df["type"] == selected_type]
    if selected_effect != "Any":
        filtered_df = filtered_df[filtered_df["effects"].str.contains(selected_effect, case=False, na=False)]
    if selected_flavor != "Any":
        filtered_df = filtered_df[filtered_df["flavor"].str.contains(selected_flavor, case=False, na=False)]
    if selected_ailment != "Any":
        filtered_df = filtered_df[filtered_df["ailment"].str.contains(selected_ailment, case=False, na=False)]
    if selected_breeder != "Any":
        filtered_df = filtered_df[filtered_df["breeder"] == selected_breeder]
    if selected_location != "Any":
        filtered_df = filtered_df[filtered_df["location"] == selected_location]

    filtered_df = filtered_df[
        (filtered_df["thc"].fillna(0.0) >= thc_range[0]) &
        (filtered_df["thc"].fillna(0.0) <= thc_range[1])
    ]

    if sort_by == "Highest THC":
        filtered_df = filtered_df.sort_values(by="thc", ascending=False)
    elif sort_by == "Highest CBD":
        filtered_df = filtered_df.sort_values(by="cbd", ascending=False)

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

    st.subheader("🧾 Matching Strains")
    if filtered_df.empty:
        st.warning("No matching strains found.")
    else:
        for idx, row in filtered_df.iterrows():
    st.markdown("----")
    cols = st.columns([1, 3])  # left smaller for image + metadata + favorites/notes, right bigger for text + diagrams

    with cols[0]:
        # Image
        image_url = row["image"]
        if not image_url or not image_url.startswith("http"):
            image_url = fetch_image_online(row["name"]) or ""
        if image_url:
            st.image(image_url, width=150)
        else:
            st.write("🖼️ No image available.")

        # Metadata
        st.markdown(f"**Type**: {row['type']}")
        st.markdown(f"**Effects**: {row['effects']}")
        st.markdown(f"**Flavor**: {row.get('flavor', 'N/A')}")
        st.markdown(f"**Ailments**: {row.get('ailment', 'N/A')}")
        st.markdown(f"**Breeder**: {row.get('breeder', 'N/A')}")
        st.markdown(f"**Location**: {row.get('location', 'N/A')}")

        # Favorites button
        is_fav = row['name'] in st.session_state.favorites
        if st.button(
            ("❤️ Remove from Favorites" if is_fav else "♡ Add to Favorites"),
            key=f"fav_{idx}",
        ):
            toggle_favorite(row['name'])
            st.experimental_rerun()

        # Notes
        note = st.text_area(
            "Your Notes",
            value=st.session_state.notes.get(row['name'], ""),
            key=f"note_{idx}",
            placeholder="Write your notes here...",
        )
        if st.button("Save Note", key=f"save_note_{idx}"):
            save_note(row['name'], note)
            st.success("Note saved!")

    with cols[1]:
        st.markdown(f"### {row['name']}")
        desc = row.get("description", "")
        if desc:
            st.write(desc)
        else:
            st.info("No description available.")

        # YouTube embedding (if valid URL present)
        yt_url = row.get("youtube", "")
        if yt_url.startswith("https://www.youtube.com/") or yt_url.startswith("https://youtu.be/"):
            st.video(yt_url)

        # Move THC gauge under description + YouTube
        thc_fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=row["thc"] or 0,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "THC %"},
            gauge={
                'axis': {'range': [0, 40]},
                'bar': {'color': "green"},
                'steps': [
                    {'range': [0, 10], 'color': "#e6ffe6"},
                    {'range': [10, 25], 'color': "#b3ffb3"},
                    {'range': [25, 40], 'color': "#66ff66"}
                ],
            }
        ))
        st.plotly_chart(thc_fig, use_container_width=True, key=f"thc_{idx}")

        # Move CBD gauge under THC gauge
        cbd_fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=row["cbd"] or 0,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "CBD %"},
            gauge={
                'axis': {'range': [0, 20]},
                'bar': {'color': "blue"},
                'steps': [
                    {'range': [0, 5], 'color': "#e6f0ff"},
                    {'range': [5, 15], 'color': "#99c2ff"},
                    {'range': [15, 20], 'color': "#3399ff"}
                ],
            }
        ))
        st.plotly_chart(cbd_fig, use_container_width=True, key=f"cbd_{idx}")


                # Metadata
                st.markdown(f"**Type**: {row['type']}")
                st.markdown(f"**Effects**: {row['effects']}")
                st.markdown(f"**Flavor**: {row.get('flavor', 'N/A')}")
                st.markdown(f"**Ailments**: {row.get('ailment', 'N/A')}")
                st.markdown(f"**Breeder**: {row.get('breeder', 'N/A')}")
                st.markdown(f"**Location**: {row.get('location', 'N/A')}")

                # Favorites button
                is_fav = row['name'] in st.session_state.favorites
                if st.button(
                    ("❤️ Remove from Favorites" if is_fav else "♡ Add to Favorites"),
                    key=f"fav_{idx}",
                ):
                    toggle_favorite(row['name'])
                    st.experimental_rerun()

                # Notes
                note = st.text_area(
                    "Your Notes",
                    value=st.session_state.notes.get(row['name'], ""),
                    key=f"note_{idx}",
                    placeholder="Write your notes here...",
                )
                if st.button("Save Note", key=f"save_note_{idx}"):
                    save_note(row['name'], note)
                    st.success("Note saved!")

            with cols[1]:
                st.markdown(f"### {row['name']}")
                desc = row.get("description", "")
                if desc:
                    st.write(desc)
                else:
                    st.info("No description available.")

                # YouTube embedding (if valid URL present)
                yt_url = row.get("youtube", "")
                if yt_url.startswith("https://www.youtube.com/") or yt_url.startswith("https://youtu.be/"):
                    st.video(yt_url)

    # Show favorites if any
    if st.session_state.favorites:
        st.sidebar.header("❤️ Favorites")
        for fav_name in st.session_state.favorites:
            st.sidebar.write(fav_name)
else:
    st.info("Please use the sidebar filters and click 🔍 Search to find strains.")

