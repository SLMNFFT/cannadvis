import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from duckduckgo_search import DDGS

st.set_page_config(page_title="Cannabis Strain Explorer", layout="wide")
st.title("CANNADVIS your Mood Adviser")

@st.cache_data
def load_data():
    df = pd.read_csv("strains.csv")
    df['thc'] = pd.to_numeric(df['thc'], errors='coerce')
    df['cbd'] = pd.to_numeric(df['cbd'], errors='coerce')
    df['effects'] = df['effects'].fillna('')
    df['image'] = df['image'].fillna('')
    df['type'] = df['type'].fillna('Unknown')
    for col in ['flavor', 'ailment', 'breeder', 'location']:
        df[col] = df.get(col, pd.Series([''] * len(df))).fillna('')
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

def toggle_favorite(strain_name):
    if strain_name in st.session_state.favorites:
        st.session_state.favorites.remove(strain_name)
    else:
        st.session_state.favorites.add(strain_name)

def save_note(strain_name, note):
    st.session_state.notes[strain_name] = note

def main():
    if "favorites" not in st.session_state:
        st.session_state.favorites = set()
    if "notes" not in st.session_state:
        st.session_state.notes = {}

    try:
        df_preview = load_data()
    except Exception:
        df_preview = pd.DataFrame(columns=["name", "type", "effects", "thc"])

    strain_names = ["Any"] + sorted(df_preview["name"].dropna().unique().tolist())
    strain_types = ["Any"] + sorted(df_preview["type"].dropna().unique().tolist())
    all_effects = sorted(df_preview["effects"].str.split(", ").explode().dropna().unique())
    all_flavors = sorted(df_preview["flavor"].str.split(", ").explode().dropna().unique())
    all_ailments = sorted(df_preview["ailment"].str.split(", ").explode().dropna().unique())
    all_breeders = sorted(df_preview["breeder"].dropna().unique())
    all_locations = sorted(df_preview["location"].dropna().unique())

    # Sidebar filters
    st.sidebar.header("🔎 Filter Strains")
    selected_name = st.sidebar.selectbox("Strain Name", strain_names)
    selected_type = st.sidebar.selectbox("Strain Type", strain_types)
    selected_effects = st.sidebar.multiselect("Desired Effects", all_effects)
    selected_flavors = st.sidebar.multiselect("Flavors", all_flavors)
    selected_ailments = st.sidebar.multiselect("Ailments", all_ailments)
    selected_breeders = st.sidebar.multiselect("Breeders", all_breeders)
    selected_locations = st.sidebar.multiselect("Locations", all_locations)
    thc_range = st.sidebar.slider("THC % Range", 0.0, 40.0, (0.0, 25.0))
    sort_by = st.sidebar.selectbox("Sort by Potency", ["None", "Highest THC", "Highest CBD"])
    search = st.sidebar.button("🔍 Search")

    if search:
        df = load_data()
        filtered_df = df.copy()

        if selected_name != "Any":
            filtered_df = filtered_df[filtered_df["name"] == selected_name]
        if selected_type != "Any":
            filtered_df = filtered_df[filtered_df["type"] == selected_type]
        for eff in selected_effects:
            filtered_df = filtered_df[filtered_df["effects"].str.contains(eff, case=False, na=False)]
        for flav in selected_flavors:
            filtered_df = filtered_df[filtered_df["flavor"].str.contains(flav, case=False, na=False)]
        for ail in selected_ailments:
            filtered_df = filtered_df[filtered_df["ailment"].str.contains(ail, case=False, na=False)]
        if selected_breeders:
            filtered_df = filtered_df[filtered_df["breeder"].isin(selected_breeders)]
        if selected_locations:
            filtered_df = filtered_df[filtered_df["location"].isin(selected_locations)]
        filtered_df = filtered_df[
            (filtered_df["thc"].fillna(0.0) >= thc_range[0]) &
            (filtered_df["thc"].fillna(0.0) <= thc_range[1])
        ]
        if sort_by == "Highest THC":
            filtered_df = filtered_df.sort_values(by="thc", ascending=False)
        elif sort_by == "Highest CBD":
            filtered_df = filtered_df.sort_values(by="cbd", ascending=False)

        # Effects Chart
        st.subheader("📊 Effects Distribution by Strain Type")
        expanded = filtered_df[["type", "effects"]].assign(effects=filtered_df["effects"].str.split(", ")).explode("effects").dropna()
        if not expanded.empty:
            counts = expanded.groupby(["type", "effects"]).size().reset_index(name="count").sort_values(by="count", ascending=False)
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

        # Matching strains
        st.subheader("🧾 Matching Strains")
        if filtered_df.empty:
            st.warning("No matching strains found.")
        else:
            for idx, row in filtered_df.iterrows():
                st.markdown("----")
                cols = st.columns([1, 3])

                with cols[0]:
                    image_url = row["image"]
                    if not image_url or not image_url.startswith("http"):
                        image_url = fetch_image_online(row["name"]) or ""
                    if image_url:
                        st.image(image_url, width=150)
                    else:
                        st.write("🖼️ No image available.")
                    st.markdown(f"**Type**: {row['type']}")
                    st.markdown(f"**Effects**: {row['effects']}")
                    st.markdown(f"**Flavor**: {row.get('flavor', 'N/A')}")
                    st.markdown(f"**Ailments**: {row.get('ailment', 'N/A')}")
                    st.markdown(f"**Breeder**: {row.get('breeder', 'N/A')}")
                    st.markdown(f"**Location**: {row.get('location', 'N/A')}")

                    is_fav = row['name'] in st.session_state.favorites
                    if st.button("❤️ Remove from Favorites" if is_fav else "♡ Add to Favorites", key=f"fav_{idx}"):
                        toggle_favorite(row['name'])
                        st.experimental_rerun()

                    note = st.text_area("Your Notes", value=st.session_state.notes.get(row['name'], ""), key=f"note_{idx}")
                    if st.button("Save Note", key=f"save_note_{idx}"):
                        save_note(row['name'], note)
                        st.success("Note saved!")

                with cols[1]:
                    st.markdown(f"### {row['name']}")
                    desc = row.get("description", "")
                    st.write(desc if desc else "No description available.")

                    yt_url = row.get("youtube", "")
                    if yt_url.startswith("https://www.youtube.com/") or yt_url.startswith("https://youtu.be/"):
                        st.video(yt_url)

                    thc_val = row["thc"] if pd.notna(row["thc"]) else 0
                    cbd_val = row["cbd"] if pd.notna(row["cbd"]) else 0

                    # THC Gauge
                    thc_fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=thc_val,
                        title={'text': "THC %"},
                        domain={'x': [0, 1], 'y': [0, 1]},
                        gauge={
                            'axis': {'range': [0, 40]},
                            'bar': {'color': "green"},
                            'steps': [
                                {'range': [0, 10], 'color': "#D3F9D8"},
                                {'range': [10, 20], 'color': "#A1D99B"},
                                {'range': [20, 30], 'color': "#31A354"},
                                {'range': [30, 40], 'color': "#006D2C"},
                            ],
                        }
                    ))
                    st.plotly_chart(thc_fig, use_container_width=True, key=f"thc_gauge_{idx}")

                    # CBD Gauge
                    cbd_fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=cbd_val,
                        title={'text': "CBD %"},
                        domain={'x': [0, 1], 'y': [0, 1]},
                        gauge={
                            'axis': {'range': [0, 20]},
                            'bar': {'color': "blue"},
                            'steps': [
                                {'range': [0, 5], 'color': "#D0E1F9"},
                                {'range': [5, 10], 'color': "#74A9CF"},
                                {'range': [10, 15], 'color': "#2B5788"},
                                {'range': [15, 20], 'color': "#08306B"},
                            ],
                        }
                    ))
                    st.plotly_chart(cbd_fig, use_container_width=True, key=f"cbd_gauge_{idx}")

        # Sidebar: Favorites
        st.sidebar.header("❤️ Favorites")
        if st.session_state.favorites:
            for fav_strain in sorted(st.session_state.favorites):
                st.sidebar.write(fav_strain)
        else:
            st.sidebar.write("No favorites yet.")
    else:
        st.info("Please use the sidebar filters and click 🔍 Search to find strains.")

if __name__ == "__main__":
    main()

