import streamlit as st
import asyncio
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
from terra_sdk.client.lcd import LCDClient

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

terra = LCDClient(chain_id="phoenix-1", url="https://phoenix-lcd.terra.dev")
votes_tables_url ="https://api.flipsidecrypto.com/api/v2/queries/e255de62-be60-4a28-8a4d-66eaa3e668d7/data/latest"

def deposits_stats(url1,url2):
    df1=df_creator(url2)
    df2=table_votes(votes_tables_url)
    df3=df_creator(url1)
    df_inner =pd.merge(df1, df2, on='Proposal ID', how='inner')
    refunded_deposit = df_inner.loc[df_inner['Proposal Status'] == 'Approved', 'Total Deposit Amount'].sum()
    burned_deposit = df_inner.loc[df_inner['Proposal Status'] == 'Rejected', 'Total Deposit Amount'].sum()
    outstanding_deposit = df_inner.loc[(df_inner['Proposal Status'] == 'Passing') | (df_inner['Proposal Status'] == 'Failing'), 'Total Deposit Amount'].sum()
    df3['Burned Deposit Amount in LUNA'] = df3['Burned Deposit Amount in LUNA'] + burned_deposit
    df3['Refunded Deposit Amount in LUNA'] = refunded_deposit
    df3['Outstanding Deposit Amount in LUNA'] = outstanding_deposit

    list_cols=list(df3.columns)
    stats_dict=dict()
    for col in list_cols:
        stats_dict[col]=df3[col].iat[0]
    
    return stats_dict

    

    
    # deposit_data =dict()
    # try:
    #     for id in id_list:
    #         print(id)
    #         deposit_amount=str(terra.gov.deposits(id)[0][0].amount)
            
    #         deposit_data[id]=int(deposit_amount.replace('uluna',''))/pow(10,6)
            
    #     server_state.deposit_data = deposit_data
    # except Exception as e:
    #     print(e)
    #     deposit_data=server_state.deposit_data
    # df2['Total Deposit Amount'] = df2["Proposal ID"].map(deposit_data)
    # return st.dataframe(df2,use_container_width=True) 




def df_creator(url):
    response = requests.get(url)
    
    if response.status_code == 200:
        response_json = response.json()
    else:
        response = None

    df=pd.DataFrame.from_records(response_json) 

    return df

def clear_text():
    st.session_state['text1'] = ""
    st.session_state['text2'] = ""
    st.session_state['text3'] = ""
    st.session_state['text4'] = ""

def table_votes(url, title=None,sql=None):
    if title and sql:
        st.text("")
        st.markdown(f'[{title}]({sql})')

    current_date=pd.to_datetime('today')
    df=df_creator(url)
    df["Voting Start Time"] = pd.to_datetime(df["Voting Start Time"])
    df["Voting End Time"] = pd.to_datetime(df["Voting End Time"])
    df=df.sort_values(by="Voting Start Time", ascending=False)
    df=df.reset_index(drop=True)
    quorum_data= terra_sdk_helper(req_url=url)
    tally_para=terra_sdk_helper()
    df['quorum (Q) %'] = df["Proposal ID"].map(quorum_data)
    df['quorum (Q) %'] = df['quorum (Q) %'].round(decimals=2)
    df['threshold (T) %'] = df['threshold (T) %'].round(decimals = 2)
    df['veto (V) %'] = df['veto (V) %'].round(decimals=2)
    

    conditions = [
    (df['quorum (Q) %'] >= tally_para['quorum']*100) & (df['veto (V) %'] <= tally_para['veto_threshold']*100) & \
    (df['threshold (T) %'] > tally_para['threshold']*100) & (df['Voting End Time'] > current_date),
    (df['quorum (Q) %'] >= tally_para['quorum']*100) & (df['veto (V) %'] <= tally_para['veto_threshold']*100) & \
    (df['threshold (T) %'] > tally_para['threshold']*100) & (df['Voting End Time'] <=current_date),
    (df['threshold (T) %'] <= tally_para['threshold']*100) & (df['Voting End Time'] > current_date),
    (df['veto (V) %'] > tally_para['veto_threshold']*100) & (df['Voting End Time'] > current_date),
    (df['quorum (Q) %'] < tally_para['quorum']*100) & (df['Voting End Time'] > current_date),
    (df['threshold (T) %'] <= tally_para['threshold']*100) & (df['Voting End Time'] <= current_date),
    (df['veto (V) %'] > tally_para['veto_threshold']*100) & (df['Voting End Time'] <= current_date),
    (df['quorum (Q) %'] < tally_para['quorum']*100) & (df['Voting End Time'] <= current_date)
    ]

    values = ['Passing', 'Approved', 'Failing', 'Failing', 'Failing', 'Rejected', 'Rejected','Rejected']

    df['Proposal Status'] = np.select(conditions, values)
    if title and sql:

        col1, col2, col3,col4,col5 = st.columns([2,2,4,4,1])

        prop_status=df['Proposal Status'].drop_duplicates()
        with col1:
            make_choice = selectbox('Select Proposal Status', prop_status, no_selection_label="",key='text1')
        
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

        if not make_choice and not prop_add and not prop_id and not pay_wal:
            return df

        # st.write(" ")
        if make_choice:
            df=df.loc[(df['Proposal Status']==make_choice)]
        if prop_add:
            df = df.loc[(df['Proposer']==prop_add)]
        if prop_id:
            df = df.loc[(df['Proposal ID']==int(prop_id))]
        if pay_wal:
            df = df.loc[(df['Grant Target Wallet']==pay_wal)]
    
    # df2=df1.loc[df['Proposer']==prop_add]

    return df

def terra_sdk_helper(req_url = None):
    if not req_url:
        try:
            tally_para = dict()
            tally_para['quorum'] = terra.gov.tally_parameters()['quorum']
            tally_para['threshold'] =terra.gov.tally_parameters()['threshold']
            tally_para['veto_threshold']= terra.gov.tally_parameters()['veto_threshold']
            server_state.tally_para=tally_para
        except Exception as e:             
            print(e)
            tally_para = server_state.tally_para
        
        return tally_para
    else:
        quorum_dict=dict()
        try:
            df=df_creator(req_url)
            id_list =df['Proposal ID'].to_list()
            bonded = str(terra.staking.pool().bonded_tokens)
            bonded_coins=int(bonded.replace('uluna', ''))
            for id in id_list:
                raw_value=(int(terra.gov.tally(id)['yes'])+int(terra.gov.tally(id)['no'])+int(terra.gov.tally(id)['abstain'])+\
                int(terra.gov.tally(id)['no_with_veto']))*100/(bonded_coins)
                quorum_dict[id]=float(millify(raw_value, precision=2))
            server_state.quorum_dict=quorum_dict

        except Exception as e:    
            print(e)
            quorum_dict=server_state.quorum_dict

        return quorum_dict

            
def table_proposals(url, title,sql):

    st.text("")

    st.markdown(f'[{title}]({sql})')

    df=df_creator(url)
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


# print((terra.staking.pool().bonded_tokens))

# if selected == "Overview":
    

if selected == "Proposals":
    stats_url='https://api.flipsidecrypto.com/api/v2/queries/b49ce1ca-f3df-4327-abe7-55da5bd74ecc/data/latest'
    deposit_amount_url = 'https://api.flipsidecrypto.com/api/v2/queries/6baf2b29-eb26-4b9e-bf13-aa2024675fef/data/latest'
    dict_data = deposits_stats(stats_url, deposit_amount_url )
    col1, col2, col3=st.columns(3)
    with col1:
        st.metric("[Total Proposers (Deposit Period)](https://flipsidecrypto.xyz/edit/queries/b49ce1ca-f3df-4327-abe7-55da5bd74ecc)", millify(dict_data['Total Proposers (Deposit Period)'], precision=2))
        st.metric("[Total Submitted Proposals](https://flipsidecrypto.xyz/edit/queries/b49ce1ca-f3df-4327-abe7-55da5bd74ecc)", millify(dict_data['Total Submitted Proposals'], precision=2))
        st.metric("[Burned Deposit Amount in LUNA](https://flipsidecrypto.xyz/edit/queries/b49ce1ca-f3df-4327-abe7-55da5bd74ecc)", millify(dict_data['Burned Deposit Amount in LUNA'], precision=2))
    with col2:
        st.metric("[# Voting Eligible Proposals](https://flipsidecrypto.xyz/edit/queries/b49ce1ca-f3df-4327-abe7-55da5bd74ecc)", millify(dict_data['# Voting Eligible Proposals '], precision=2))
        st.metric("[# Voting Ineligible Proposals](https://flipsidecrypto.xyz/edit/queries/b49ce1ca-f3df-4327-abe7-55da5bd74ecc)", millify(dict_data['# Voting Ineligible Proposals'], precision=2))
        st.metric("[Refunded Deposit Amount in LUNA](https://flipsidecrypto.xyz/edit/queries/b49ce1ca-f3df-4327-abe7-55da5bd74ecc)", millify(dict_data['Refunded Deposit Amount in LUNA'], precision=2))
    with col3:
        st.metric("[# Deposit In-progress Proposals](https://flipsidecrypto.xyz/edit/queries/b49ce1ca-f3df-4327-abe7-55da5bd74ecc)", millify(dict_data['# Deposit In-progress Proposals'], precision=2))
        st.metric("[Total Deposit Amount in LUNA](https://flipsidecrypto.xyz/edit/queries/b49ce1ca-f3df-4327-abe7-55da5bd74ecc)", millify(dict_data['Total Deposit Amount in LUNA'], precision=2))
        st.metric("[Outstanding Deposit Amount in LUNA](https://flipsidecrypto.xyz/edit/queries/b49ce1ca-f3df-4327-abe7-55da5bd74ecc)", millify(dict_data['Outstanding Deposit Amount in LUNA'], precision=2))
        
        
    table_proposals("https://api.flipsidecrypto.com/api/v2/queries/a3c67a3e-f33e-44e2-89d2-fac540bf1fd8/data/latest", 
        "Grant Proposals Explorer","https://flipsidecrypto.xyz/edit/queries/a3c67a3e-f33e-44e2-89d2-fac540bf1fd8?fileSearch=peroid")

if selected == "Votes and Grants":
    dataf=table_votes(votes_tables_url, 
        title="Grant Voting Explorer",sql="https://flipsidecrypto.xyz/edit/queries/e255de62-be60-4a28-8a4d-66eaa3e668d7")
    st.dataframe(dataf,use_container_width=True)