import streamlit as st
import modules

from modules import utils

###
st.set_page_config(layout="wide",page_title="Release Date Analysis Tool")

st.markdown("# Release Date Analysis - Google Trend version")
st.markdown("## Intro")

st.markdown("The goal of this tool is to estimate consumer demand for two subjects: \n - piracy services \n - OTT/DTH content (Gangs of Londons S2, e.g.)")
st.markdown("The data source of this tool is retrived from Google Trend. Update on 17/11/22")

st.markdown("## User Input")

check = st.selectbox("What keywords do you want to use to perform the analysis? (Manual version not yet tested, use Default)",("Default","Manual"))

if check == "Default":
    cat = ['123movies','torrent','stream','online free','gangs of london season 2']
    st.write("Default has these keywords: ",cat)
else:
    cat = []
    for i in range(0,5):
        word = st.text_input(label="Inser keywords {} (max 5)".format(i),key=i)
        cat.append(word)

check2 = st.selectbox("On which week do you want to do the analysis (related to the Gangs release)?",("Week 1", "Week 2", "Week 3", "Week 4"))

if check2 == "Week 1":
    release_date = "20-10-2022"
elif check2 == "Week 2":
    release_date = "27-10-2022"
elif check2 == "Week 3":
    release_date = "03-11-2022"
else:
    release_date = "10-11-2022"

st.write("The release date of the ", check2, "is: ",release_date)

###
st.markdown("## Data Retrieval")

if st.button("Click to retrieve data from Google Trend"):
    start_date, end_date = utils.range_date(release_date)
    df_raw = utils.download_data(cat,'Hourly',start_date,end_date)
    df = df_raw.copy()
    st.write("Check dimension dataframe (should be 168*5): ",df.shape)
    

    st.markdown("## Data preparation")
    st.markdown("Compute Pirate Demand Index and other Score backend.")
    ## PDI
    weights = [0.25,0.25,0.25,0.25]
    df['Piracy Demand Index'] = df.drop(columns='gangs of london season 2').apply(lambda x: x.dot(weights),axis=1)
    ## Z-SCORE
    df['Piracy Score'] = utils.zscore(df['Piracy Demand Index'])
    df['Gangs Score'] = utils.zscore(df['gangs of london season 2'])
    df['Final Score'] = df['Piracy Score']*0.3 + df['Gangs Score']*0.7
    df['Final Score Scaled'] = utils.scaler.fit_transform(df['Final Score'].values.reshape(-1,1))
    ## Date time info
    df['Day'] = df.index.date
    df['Hour'] = df.index.hour
    df['Hour Range'] = 'Night'
    df['Hour Range'] = df['Hour Range'].mask((df['Hour']>=5) & (df['Hour']<=12),'Morning')
    df['Hour Range'] = df['Hour Range'].mask((df['Hour']>12) & (df['Hour']<=17),'Afternoon')
    df['Hour Range'] = df['Hour Range'].mask((df['Hour']>17) & (df['Hour']<=21),'Evening')
    df = df.reset_index()

    st.markdown("## Modeling")
    gr = df.groupby('Day')['Piracy Score','Gangs Score','Final Score'].mean()
    st.markdown("### 1) Bar Chart")
    fig = utils.px.bar(gr,x=gr.index,y=gr.columns,title="When did consumer demand increase (or decrease) during the week selected?<br><sup>Final Score: weighted average of Piracy and Gangs Score - Score related to the week under examination - Weekly mean centered at Zero</sup>")
    fig.update_layout(title_x=0.5)
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Score")
    fig.update_layout(barmode='group')
    st.plotly_chart(fig, use_container_width=True)
    
    df['date_str'] = df['Day'].apply(lambda x: str(x))
    
    st.markdown("### 2) Multicriteria - Animation Day by Day")
    st.markdown("Each quadrant of the graph below describe how consumer demand behaved simultaneously for the subjects under consideration. Legend and tooltip interactive.")
    fig =utils.px.scatter(df, x='Piracy Score', y='Gangs Score',color='Hour Range',custom_data=['date'],size='Final Score Scaled',animation_frame='date_str',
                 range_x=[df['Piracy Score'].min()-0.5,df['Piracy Score'].max()+0.5],
                 range_y=[df['Gangs Score'].min()-0.5,df['Gangs Score'].max()+0.5],
                 title="How did consumer demand behave during the selected time periods?<br><sup>Day by day animation - Every circle represents one hour of data gruped into four day parts (hour range).</sup>")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    # fig.update_layout(showlegend=False)
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1000
    fig.add_hrect(y0=0, y1=df['Gangs Score'].max()+0.5, line_width=0, fillcolor="red", opacity=0.1)
    fig.add_vrect(x0=0, x1=df['Piracy Score'].max()+0.5, line_width=0, fillcolor="red", opacity=0.1)
    fig.add_hrect(y0=0, y1=df['Gangs Score'].min()-0.5, line_width=0, fillcolor="green", opacity=0.1)
    fig.add_vrect(x0=0, x1=df['Piracy Score'].min()-0.5, line_width=0, fillcolor="green", opacity=0.1)
    fig.add_hline(y=0)
    fig.add_vline(x=0)
    fig.add_vrect(x0=0, x1=round(df['Piracy Score'].max()+0.5,5), annotation_text="Piracy increase, Gangs increase", annotation_position="top left", annotation=dict(font_size=10))
    fig.add_vrect(x0=0, x1=round(df['Piracy Score'].min()-0.5,5), annotation_text="Piracy decrease, Gangs increase", annotation_position="top right", annotation=dict(font_size=10))
    fig.add_vrect(x0=0, x1=round(df['Piracy Score'].max()+0.5,5), annotation_text="Piracy increase, Gangs decrease", annotation_position="bottom left", annotation=dict(font_size=10))
    fig.add_vrect(x0=0, x1=round(df['Piracy Score'].min()-0.5,5), annotation_text="Piracy decrease, Gangs decrease", annotation_position="bottom right", annotation=dict(font_size=10))
    fig.update_traces(marker=dict(line=dict(width=2,color='DarkSlateGrey')),selector=dict(mode='markers'))
    fig.update_layout(title_x=0.5)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### 3) Multicriteria - All days together")
    st.markdown("Each quadrant of the graphs below describe how consumer demand behaved simultaneously for the subjects under consideration. Legend and tooltip interactive.")
    fig = utils.px.scatter(df, x='Piracy Score', y='Gangs Score',color='date_str',custom_data=['date'],size='Final Score Scaled',
                 range_x=[df['Piracy Score'].min()-0.5,df['Piracy Score'].max()+0.5],
                 range_y=[df['Gangs Score'].min()-0.5,df['Gangs Score'].max()+0.5],
                 title="How did consumer demand behave during the selected time periods?<br><sup>Overall days - Every circle represents one hour of data - Legend interactive</sup>")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    fig.add_hrect(y0=0, y1=df['Gangs Score'].max()+0.5, line_width=0, fillcolor="red", opacity=0.1)
    fig.add_vrect(x0=0, x1=df['Piracy Score'].max()+0.5, line_width=0, fillcolor="red", opacity=0.1)
    fig.add_hrect(y0=0, y1=df['Gangs Score'].min()-0.5, line_width=0, fillcolor="green", opacity=0.1)
    fig.add_vrect(x0=0, x1=df['Piracy Score'].min()-0.5, line_width=0, fillcolor="green", opacity=0.1)
    fig.add_hline(y=0)
    fig.add_vline(x=0)
    fig.add_vrect(x0=0, x1=round(df['Piracy Score'].max()+0.5,5), annotation_text="Piracy increase, Gangs increase", annotation_position="top left", annotation=dict(font_size=10))
    fig.add_vrect(x0=0, x1=round(df['Piracy Score'].min()-0.5,5), annotation_text="Piracy decrease, Gangs increase", annotation_position="top right", annotation=dict(font_size=10))
    fig.add_vrect(x0=0, x1=round(df['Piracy Score'].max()+0.5,5), annotation_text="Piracy increase, Gangs decrease", annotation_position="bottom left", annotation=dict(font_size=10))
    fig.add_vrect(x0=0, x1=round(df['Piracy Score'].min()-0.5,5), annotation_text="Piracy decrease, Gangs decrease", annotation_position="bottom right", annotation=dict(font_size=10))
    fig.update_traces(marker=dict(line=dict(width=2,color='DarkSlateGrey')),selector=dict(mode='markers'))
    fig.update_layout(title_x=0.5)
    fig.update_traces(hovertemplate="<br>".join([
            "Pirate Score: %{x}",
            "Gangs Score: %{y}",
            "Date & Hour: %{customdata[0]}"]))
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### 4) Keywords importance")
    st.markdown("This data can be useful for estimating how much each keyword is able to explain the current analysis. The scores represented indicated a kind of 'boosted' correlation between the keywords present. This allows us to identify how the other variables relate to our subject of interest (Gangs, in this case). If we had high values of concordant sign for Gangs and 123movies/torrent, for example, we might conclude that Gangs has generated some movement in the cyberlocker world. This might help answer the question of distribution choice: weekly or boxset? From the analysis there seems to be on average more 'movement' on keywords related to the boxset world (those of cyberlockers, as also revealed by Texcipio), than those of the weekly world.")
    var1, sv1 = utils.principal_component_analysis(df)
    st.markdown("The following are just for a 'tech-check': ")
    st.write("Variance explained by first component: ",var1)
    st.write("Eigenvalues (should be > 1): ",sv1)
    
    st.markdown("### 5) Consumer Demand Score (ex PDS)")
    st.markdown("The higher the score, the higher the consumer demand for the week selected. The score exists in [0,100]")
    ris = utils.pds_static(df)
    st.write("Score for Gangs is: ",ris[0])
    st.write("Score for Piracy is: ",ris[1])