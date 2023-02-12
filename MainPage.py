import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import numpy as np
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
from streamlit_extras.no_default_selectbox import selectbox



def clear_text():
    st.session_state['text1'] = ""
    st.session_state['text2'] = ""
    st.session_state['text3'] = ""
    st.session_state['text4'] = ""

def table_votes(url, title,sql):

    st.text("")

    st.markdown(f'[{title}]({sql})')
    response = requests.get(url)
    
    if response.status_code == 200:
        response_json = response.json()
    else:
        response = None

    df=pd.DataFrame.from_records(response_json) 
    df["Voting Start Time"] = pd.to_datetime(df["Voting Start Time"])
    df["Voting End Time"] = pd.to_datetime(df["Voting End Time"])
    df=df.sort_values(by="Voting Start Time", ascending=False)
    df=df.reset_index(drop=True)

    col2, col3,col4,col5 = st.columns([2,4,4,1])

    # voting_status=df['Voting Eligibility Status'].drop_duplicates()
    # with col1:
    #     make_choice = selectbox('Select Voting Eligibility Status', voting_status, no_selection_label="",key='text1')
    
    with col2:
        prop_id= st.text_input("Enter Proposal ID",key='text2')

    with col3:
        prop_add = st.text_input("Enter Proposer\'s Address", key='text3')

    with col4:
        pay_wal= st.text_input("Enter Target Wallet", key='text4')

    with col5:
        st.write("")
        st.write("")
        reset = st.button("🧹", on_click=clear_text)

    if not prop_add and not prop_id and not pay_wal:
        return st.dataframe(df,use_container_width=True) 

     # st.write(" ")
    # if make_choice:
    #     df=df.loc[(df['Voting Eligibility Status']==make_choice)]
    if prop_add:
        df = df.loc[(df['Proposer']==prop_add)]
    if prop_id:
        df = df.loc[(df['Proposal ID']==int(prop_id))]
    if pay_wal:
        df = df.loc[(df['Grant Target Wallet']==pay_wal)]
    
    # df2=df1.loc[df['Proposer']==prop_add]

    st.dataframe(df,use_container_width=True)


def table_proposals(url, title,sql):

    st.text("")

    st.markdown(f'[{title}]({sql})')
    response = requests.get(url)
    
    if response.status_code == 200:
        response_json = response.json()
    else:
        response = None

    df=pd.DataFrame.from_records(response_json) 
    df["Proposal Creation Time"] = pd.to_datetime(df["Proposal Creation Time"])
    df["Deposit End Time"] = pd.to_datetime(df["Deposit End Time"])
    df=df.sort_values(by="Proposal Creation Time",ascending=False)
    df=df.reset_index(drop=True)

    col1, col2, col3,col4,col5 = st.columns([3,2,4,4,1])

    voting_status=df['Voting Eligibility Status'].drop_duplicates()
    with col1:
        make_choice = selectbox('Select Voting Eligibility Status', voting_status, no_selection_label="",key='text1')
    
    with col2:
        prop_id= st.text_input("Enter Proposal ID",key='text2')

    with col3:
        prop_add = st.text_input("Enter Proposer\'s Address", key='text3')

    with col4:
        pay_wal= st.text_input("Enter Target Wallet", key='text4')

    with col5:
        st.write("")
        st.write("")
        reset = st.button("🧹", on_click=clear_text)

    if not prop_add and not make_choice and not prop_id and not pay_wal:
        return st.dataframe(df,use_container_width=True) 

     # st.write(" ")
    if make_choice:
        df=df.loc[(df['Voting Eligibility Status']==make_choice)]
    if prop_add:
        df = df.loc[(df['Proposer']==prop_add)]
    if prop_id:
        df = df.loc[(df['Proposal ID']==int(prop_id))]
    if pay_wal:
        df = df.loc[(df['Grant Target Wallet']==pay_wal)]
    
    # df2=df1.loc[df['Proposer']==prop_add]

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

if selected == "Overview":
    np.random.seed(0)  # Seed so random arrays do not change on each rerun
    n_rows = 1000
    random_data = pd.DataFrame(
        {"A": np.random.random(size=n_rows), "B": np.random.random(size=n_rows)}
    )

    sliders = {
        "A": st.sidebar.slider(
            "Filter A", min_value=0.0, max_value=1.0, value=(0.0, 1.0), step=0.01
        ),
        "B": st.sidebar.slider(
            "Filter B", min_value=0.0, max_value=1.0, value=(0.0, 1.0), step=0.01
        ),
    }

    filter = np.full(n_rows, True)  # Initialize filter as only True

    for feature_name, slider in sliders.items():
    # Here we update the filter to take into account the value of each slider
        filter = (
            filter
            & (random_data[feature_name] >= slider[0])
            & (random_data[feature_name] <= slider[1])
        )

        st.write(random_data[filter])

if selected == "Proposals":

    table_proposals("https://api.flipsidecrypto.com/api/v2/queries/a3c67a3e-f33e-44e2-89d2-fac540bf1fd8/data/latest", 
        "Grant Proposals Explorer","https://flipsidecrypto.xyz/edit/queries/a3c67a3e-f33e-44e2-89d2-fac540bf1fd8?fileSearch=peroid")

if selected == "Votes and Grants":

    table_votes("https://api.flipsidecrypto.com/api/v2/queries/e255de62-be60-4a28-8a4d-66eaa3e668d7/data/latest", 
        "Grant Voting Explorer","https://flipsidecrypto.xyz/edit/queries/e255de62-be60-4a28-8a4d-66eaa3e668d7")