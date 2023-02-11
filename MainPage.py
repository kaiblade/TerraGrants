import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import requests
from requests import Session
import plotly.express as px
import altair as alt
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects,ReadTimeout
import json
import os
from millify import millify
from PIL import Image
from streamlit_server_state import server_state, server_state_lock
from st_aggrid import *


def tables(url, title,sql):

    st.text("")
    st.markdown("---")
    st.text("")

    st.markdown(f'[{title}]({sql})')
    response = requests.get(url)
    
    if response.status_code == 200:
        response_json = response.json()
    else:
        response = None

    df=pd.DataFrame.from_records(response_json)  
    # df.set_index('#', inplace=True, drop=True) 
    st.dataframe(df,use_container_width=True)




st.set_page_config(page_title=None, page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([5.5,10,1.2])

with col2:
    st.title("Terra Grants Funding")

st.text("")
st.markdown("- Dashboard Github link: https://github.com/kaiblade/TerraGrants")
st.text("")
selected = option_menu(
        menu_title=None,  
        options=["Overview", "Proposals", "Votes and Grants", "Funds Disbursements"],  
        icons=["file-earmark-text-fill", "card-text", "card-checklist", "cash-coin"],  
        menu_icon="cast",  
        default_index=0, 
        orientation="horizontal",
    )

if selected == "Proposals":
    # df = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
    # AgGrid(
    # df,
    # columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW
    # )
    tables("https://api.flipsidecrypto.com/api/v2/queries/a3c67a3e-f33e-44e2-89d2-fac540bf1fd8/data/latest", 
        "Grant Proposals Explorer","https://flipsidecrypto.xyz/edit/queries/a3c67a3e-f33e-44e2-89d2-fac540bf1fd8?fileSearch=peroid")
