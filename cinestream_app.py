import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import date

#Page Configuration
st.set_page_config(page_title="CineStream Dashboard",
    page_icon="🎬",layout="wide")

#Load Cleaned Data
@st.cache_data
def load_data():
    df = pd.read_csv("outputs/cleaned_cinestream.csv",parse_dates=['AddedDate'])
   
    df['Type'] = df['Type'].str.strip().str.title()
    df['Genre'] = df['Genre'].str.strip()
    df['Language'] = df['Language'].str.strip()
    # Derived Columns
    df['Profit_Cr'] = (df['RevenueCr'] -df['ProductionCostCr'])
    df['ROI_Pct'] = (df['Profit_Cr'] /df['ProductionCostCr']) * 100
    df['Performance_Band'] = np.where(df['Profit_Cr'] > 20,"Hit",np.where(df['Profit_Cr'] >= 0,"Break-even","Flop"))
    return df

df = load_data()

#Title and caption
st.title("🎬 CineStream Content Analytics Dashboard")

st.caption(
   "Interactive dashboard for analyzing content performance on the CineStream OTT platform."
)

st.markdown("---")

# About Dataset
st.subheader("📖 About the Dataset")

st.markdown("""
This dashboard analyzes Movies, Series, Documentaries, and Stand-up Specials
released between 2015 and 2024 and added to the CineStream platform between 2020 and 2024.
""")

#Create sidebar
with st.sidebar:

    st.header("🔍 Filters")
    st.caption("Dashboard updates automatically when filters change.")
    with st.form("filters_form"):
        genres = st.multiselect("Genre",
                                options=df['Genre'].unique(),
                                default=df['Genre'].unique())

    #Language multiselect
        languages = st.multiselect("Language",
                               options=df['Language'].unique(),
                               default=df['Language'].unique())

    #Type selectbox
        content_type = st.selectbox("Type",
                                    ["All","Movie","Series","Documentary","Stand-up"])

    #AgeRating multiselect
        age_ratings = st.multiselect("Age Rating",
                                     options=df['AgeRating'].unique(),
                                     default=df['AgeRating'].unique())
    
    #IMDb Range Slider
        imdb_range = st.slider("IMDb Score",
                               min_value=1.0,
                               max_value=10.0,
                               value=(1.0,10.0))
    
    #Runtime Slider
        runtime_range = st.slider("Runtime (Minutes)",
                                  min_value=int(df['RuntimeMinutes'].min()),
                                  max_value=int(df['RuntimeMinutes'].max()),
                                  value=(
                                      int(df['RuntimeMinutes'].min()),
                                      int(df['RuntimeMinutes'].max())))
    
    #AddedDate range picker
        date_range = st.date_input("🗓️Added Date Range",
                                   value=(df['AddedDate'].min(),
                                          df['AddedDate'].max()))

    #colour picker
        chart_color = st.color_picker("Choose Chart Color", "#1f77b4")

        apply = st.form_submit_button("✅ Apply Filters",
                                      type="primary")
        

filtered = df[
    (df['Genre'].isin(genres)) &
    (df['Language'].isin(languages)) &
    (df['AgeRating'].isin(age_ratings)) &
    (df['IMDbScore'].between(imdb_range[0], imdb_range[1])) &
    (df['RuntimeMinutes'].between(runtime_range[0], runtime_range[1]))
]

if content_type != "All":
    filtered = filtered[filtered['Type'] == content_type]

if len(date_range) == 2:
    start_date, end_date = date_range

    filtered = filtered[
        filtered['AddedDate'].dt.date.between(
            start_date,
            end_date
        )
    ]

#Download Filtered Catalog Button
st.sidebar.divider()
csv_bytes = filtered.to_csv(index=False).encode('utf-8')

today = date.today().strftime("%Y-%m-%d")

st.sidebar.download_button("📥 Download Filtered Catalog",
                           data=csv_bytes,
                           file_name=f"cinestream_{today}.csv",
                           mime="text/csv")

if filtered.empty:
    st.warning(
        "⚠️ No titles match your selected filters.\n\n"
        "Try selecting more genres, expanding the IMDb or runtime range, "
        "or widening the Added Date range."
    )
    st.stop()

#Four KPI metric cards arranged in one row
with st.container():
    total_titles = len(filtered)
    total_views = filtered["ViewsMillions"].sum()
    total_watch_hours = filtered["WatchHoursMillions"].sum()
    avg_imdb = filtered["IMDbScore"].mean()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Titles", f"{total_titles:,}")
    c2.metric("Total Views (Millions)", f"{total_views:,.2f}")
    c3.metric("Watch Hours (Millions)", f"{total_watch_hours:,.2f}")
    c4.metric("Average IMDb Score", f"{avg_imdb:.2f}")

st.markdown("---")

#Create Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview",
    "🌍 Genres & Languages",
    "💰 Money",
    "🚨 Quality Alerts"
])


with tab1:

    left, right = st.columns([2,1])
    with left:
        st.subheader("📋 Sample of the Catalog")
        st.dataframe(filtered.head(10),use_container_width=True)

    with right:
        st.subheader("🏆 Top 5 Titles by Views")
        top5 = (filtered.sort_values("ViewsMillions",ascending=False)
                [["Title","ViewsMillions"]].head(5))
        st.table(top5)

    st.subheader("🔎 Example JSON")
    st.json(filtered.iloc[0].to_dict())

    #line chart
    st.subheader("📈 Titles Added Per Month Over Time")
    monthly_titles = (filtered
                      .groupby(filtered['AddedDate']
                               .dt.to_period('M')).size())
    
    monthly_titles.index = monthly_titles.index.astype(str)
    st.line_chart(monthly_titles)

    #bar chart
    st.subheader("🎞️ Content Type Distribution")
    type_counts = filtered['Type'].value_counts()
    st.bar_chart(type_counts)


with tab2:
    left, right = st.columns(2)

    with left:
        #matplotlib horizontal bar chart
        st.subheader("🎭 Top 10 Genres by Views")
        genre_views = (filtered.groupby('Genre')['ViewsMillions'].sum()
                       .nlargest(10).sort_values())
        fig, ax = plt.subplots(figsize=(8,5))
        ax.barh(genre_views.index,genre_views.values,color=chart_color)
        ax.set_xlabel("Views (Millions)")
        ax.set_ylabel("Genre")
        ax.set_title("Top Genres by Total Views")
        st.pyplot(fig)

    with right:
        #plotly treemap
        st.subheader("🗣️ Language → Genre Treemap")
        fig = px.treemap(filtered,path=['Language','Genre'],
                         values='ViewsMillions',
                         title='Views by Language and Genre')
        st.plotly_chart(fig,use_container_width=True)

    language_views = (filtered.groupby("Language")["ViewsMillions"].mean())
    best_language = language_views.idxmax()
    worst_language = language_views.idxmin()
    st.success(
        f"🏆 Best Performing Language: {best_language}")

    st.warning(
        f"📉 Lowest Performing Language: {worst_language}")


with tab3:
    avg_roi = filtered["ROI_Pct"].mean()
    if avg_roi >= 0:
        st.info(f"📈 Average ROI is positive: {avg_roi:.2f}%")
    else:
        st.error(f"📉 Average ROI is negative: {avg_roi:.2f}%")


    left, right = st.columns(2)
    with left:
        #plotly scatter
        st.subheader("💵 Production Cost vs Revenue")
        fig = px.scatter(filtered,x='ProductionCostCr',y='RevenueCr',
                         color='Performance_Band',
                         hover_name='Title',title='Production Cost vs Revenue')
        
        st.plotly_chart(fig,use_container_width=True)

    with right:
        #matplotlib bar chart
        st.subheader("📈 Average ROI by Genre")
        roi_genre = (filtered.groupby('Genre')['ROI_Pct']
                     .mean().sort_values())
        fig, ax = plt.subplots(figsize=(8,5))
        ax.bar(roi_genre.index,roi_genre.values,color=chart_color)
        ax.set_title("Average ROI by Genre")
        ax.set_ylabel("ROI %")
        plt.xticks(rotation=45)
        st.pyplot(fig)

with tab4:
    loss_titles = filtered[filtered['Profit_Cr'] < 0]
    loss_count = len(loss_titles)

    if loss_count == 0:
        st.success("✅ Great! No titles are losing money in the current selection.")

    elif loss_count <= 5:
        st.warning(f"⚠️ {loss_count} title(s) are currently losing money.")

    else:
        st.error(f"🚨 {loss_count} titles are currently losing money. Immediate attention is recommended.")


    left,right = st.columns(2)
    with left:
        #matplotlib histogram
        st.subheader("⭐ IMDb Score Distribution")
        mean_score = filtered['IMDbScore'].mean()
        fig, ax = plt.subplots(figsize=(8,5))
        ax.hist(filtered['IMDbScore'].dropna(),bins=10)
        ax.axvline(mean_score,color='red',linestyle='--',
                   label=f"Mean = {mean_score:.2f}")
        ax.legend()
        ax.set_title("IMDb Score Distribution")
        st.pyplot(fig)

    with right:
        #matplotlib scatter plot
        st.subheader("🎯 IMDbScore vs ViewsMillions")
        fig, ax = plt.subplots(figsize=(8,5))
        ax.scatter(filtered['IMDbScore'],filtered['ViewsMillions'])
        ax.set_xlabel("IMDb Score")
        ax.set_ylabel("Views (Millions)")
        ax.set_title("IMDb Score vs Views")
        st.pyplot(fig)


with st.expander("❓ How this Dashboard Works"):

    st.markdown("""
### 🎬 About the Dataset

This dashboard analyzes the CineStream content catalog, which includes Movies, Series,
Documentaries, and Stand-up Specials released between 2015 and 2024 and added to the
platform between 2020 and 2024.

### 🔍 Filters

Use the filters in the sidebar to customize the dashboard.

Available filters:
- Genre
- Language
- Content Type
- Age Rating
- IMDb Score Range
- Runtime Range
- Added Date Range

Click **"Apply Filters"** to update all KPI cards, tables, and charts.
                
You can also download the filtered data using the **📥 Download Filtered Catalog** button.

### 📊 Overview Tab

- Catalog Sample
- Top 5 Titles by Views
- Example JSON Record
- Titles Added Per Month Over Time
- Content Distribution by Type

### 🌍 Genres & Languages Tab

- Top 10 Genres by Total Views
- Language to Genre Treemap
- Best Performing Language
- Lowest Performing Language

### 💰 Money Tab

- Production Cost vs Revenue
- Average ROI by Genre
- ℹROI Status Banner

### ⚠️ Quality Alerts Tab

- IMDb Score Distribution
- IMDb Score vs Views Analysis
- Loss-Making Titles Status

### 💡 Smart Features

- ⚡ Cached data loading for faster performance
- ✅ Filter form with Apply button
- 📥 CSV download for filtered data
- 🚦 Smart status messages based on the filtered results
""")

st.markdown("---")

st.caption(
    f"Showing {len(df):,} titles | Built by Ajeeba Farhath P.P"
)