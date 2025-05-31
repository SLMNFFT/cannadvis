import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from duckduckgo_search import DDGS

st.set_page_config(page_title="Cannabis Strain Explorer", layout="wide")

# 🌍 UI Translations
translations = {
    "en": {
        "filter": "🔎 Filter Strains",
        "strain_name": "Strain Name",
        "strain_type": "Strain Type",
        "desired_effects": "Desired Effects",
        "flavors": "Flavors",
        "ailments": "Ailments",
        "breeders": "Breeders",
        "locations": "Locations",
        "thc_range": "THC % Range",
        "sort_by": "Sort by Potency",
        "search": "🔍 Search",
        "no_results": "No matching strains found.",
        "matching_strains": "🧾 Matching Strains",
        "add_favorite": "♡ Add to Favorites",
        "remove_favorite": "❤️ Remove from Favorites",
        "your_notes": "Your Notes",
        "save_note": "Save Note",
        "note_saved": "Note saved!",
        "favorites": "❤️ Favorites",
        "no_favorites": "No favorites yet.",
        "thc_label": "THC %",
        "cbd_label": "CBD %",
        "effects_chart_title": "📊 Effects Distribution by Strain Type",
        "no_effect_data": "No effect data available.",
        "no_image": "🖼️ No image available.",
        "no_desc": "No description available.",
        "choose_lang": "🌐 Choose Language"
    },
    "fr": {
        "filter": "🔎 Filtrer les variétés",
        "strain_name": "Nom de la variété",
        "strain_type": "Type de variété",
        "desired_effects": "Effets recherchés",
        "flavors": "Saveurs",
        "ailments": "Maux soulagés",
        "breeders": "Éleveurs",
        "locations": "Origines",
        "thc_range": "Plage de THC %",
        "sort_by": "Trier par puissance",
        "search": "🔍 Rechercher",
        "no_results": "Aucune variété correspondante trouvée.",
        "matching_strains": "🧾 Variétés correspondantes",
        "add_favorite": "♡ Ajouter aux favoris",
        "remove_favorite": "❤️ Retirer des favoris",
        "your_notes": "Vos notes",
        "save_note": "Enregistrer la note",
        "note_saved": "Note enregistrée !",
        "favorites": "❤️ Favoris",
        "no_favorites": "Aucun favori pour l’instant.",
        "thc_label": "THC %",
        "cbd_label": "CBD %",
        "effects_chart_title": "📊 Répartition des effets par type de variété",
        "no_effect_data": "Aucune donnée sur les effets disponible.",
        "no_image": "🖼️ Aucune image disponible.",
        "no_desc": "Pas de description disponible.",
        "choose_lang": "🌐 Choisir la langue"
    }
}

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

def toggle_favorite(strain_name):
    if strain_name in st.session_state.favorites:
        st.session_state.favorites.remove(strain_name)
    else:
        st.session_state.favorites.add(strain_name)

def save_note(strain_name, note):
    st.session_state.notes[strain_name] = note

def main():
    # --- Initialize session state ---
    if "favorites" not in st.session_state:
        st.session_state.favorites = set()
    if "notes" not in st.session_state:
        st.session_state.notes = {}

    # Language selection at the top
    lang = st.selectbox(
        translations["en"]["choose_lang"],
        options=["en", "fr"],
        index=0
    )

    t = translations[lang]

    st.title("🌇 Cannadvis BETA")

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

    # Sidebar filters with translations
    st.sidebar.header(t["filter"])
    selected_name = st.sidebar.selectbox(t["strain_name"], strain_names)
    selected_type = st.sidebar.selectbox(t["strain_type"], strain_types)
    selected_effects = st.sidebar.multiselect(t["desired_effects"], all_effects)
    selected_flavors = st.sidebar.multiselect(t["flavors"], all_flavors)
    selected_ailments = st.sidebar.multiselect(t["ailments"], all_ailments)
    selected_breeders = st.sidebar.multiselect(t["breeders"], all_breeders)
    selected_locations = st.sidebar.multiselect(t["locations"], all_locations)
    thc_range = st.sidebar.slider(t["thc_range"], 0.0, 40.0, (0.0, 25.0))
    sort_by = st.sidebar.selectbox(t["sort_by"], ["None", "Highest THC", "Highest CBD"])
    search = st.sidebar.button(t["search"])

    if search:
        df = load_data()
        filtered_df = df.copy()

        if selected_name != "Any":
            filtered_df = filtered_df[filtered_df["name"] == selected_name]
        if selected_type != "Any":
            filtered_df = filtered_df[filtered_df["type"] == selected_type]
        if selected_effects:
            for eff in selected_effects:
                filtered_df = filtered_df[filtered_df["effects"].str.contains(eff, case=False, na=False)]
        if selected_flavors:
            for flav in selected_flavors:
                filtered_df = filtered_df[filtered_df["flavor"].str.contains(flav, case=False, na=False)]
        if selected_ailments:
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
        st.subheader(t["effects_chart_title"])
        expanded = filtered_df[["type", "effects"]].assign(effects=filtered_df["effects"].str.split(", ")).explode("effects")
        expanded = expanded.dropna()
        if not expanded.empty:
            counts = expanded.groupby(["type", "effects"]).size().reset_index(name="count").sort_values(by="count", ascending=False)
            fig = px.bar(
                counts,
                x="effects",
                y="count",
                color="type",
                barmode="group",
                title=t["effects_chart_title"],
                labels={"effects": t["desired_effects"], "count": "Count", "type": t["strain_type"]},
                height=500,
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(t["no_effect_data"])

        # Matching strains
        st.subheader(t["matching_strains"])
        if filtered_df.empty:
            st.warning(t["no_results"])
        else:
            for idx, row in filtered_df.iterrows():
                st.markdown("----")
                cols = st.columns([1, 3])

                with cols[0]:
                    img_url = row["image"]
                    if not img_url:
                        img_url = fetch_image_online(row["name"]) or ""
                    if img_url:
                        st.image(img_url, use_column_width=True, caption=row["name"])
                    else:
                        st.write(t["no_image"])

                with cols[1]:
                    st.markdown(f"### {row['name']} ({row['type']})")
                    desc = row.get("description", "")
                    if not desc:
                        desc = t["no_desc"]
                    st.write(desc)

                    st.write(f"**{t['thc_label']}:** {row['thc'] or 'N/A'}%")
                    st.write(f"**{t['cbd_label']}:** {row['cbd'] or 'N/A'}%")

                    # Favorite button
                    if row["name"] in st.session_state.favorites:
                        if st.button(t["remove_favorite"], key=f"fav_remove_{idx}"):
                            toggle_favorite(row["name"])
                    else:
                        if st.button(t["add_favorite"], key=f"fav_add_{idx}"):
                            toggle_favorite(row["name"])

                    # Notes
                    note = st.text_area(t["your_notes"], value=st.session_state.notes.get(row["name"], ""), key=f"note_{idx}")
                    if st.button(t["save_note"], key=f"save_note_{idx}"):
                        save_note(row["name"], note)
                        st.success(t["note_saved"])

        # Show favorites in sidebar
        st.sidebar.markdown("----")
        st.sidebar.subheader(t["favorites"])
        if st.session_state.favorites:
            for fav in sorted(st.session_state.favorites):
                st.sidebar.markdown(f"- {fav}")
        else:
            st.sidebar.info(t["no_favorites"])

if __name__ == "__main__":
    main()
