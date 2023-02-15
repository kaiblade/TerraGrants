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
from terra_sdk.client.lcd import AsyncLCDClient
import aiohttp

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

async def id_pro(id,loop):
    async with aiohttp.ClientSession(loop=loop) as client:
        asyncio.set_event_loop(loop)
        terra1 = AsyncLCDClient("https://phoenix-lcd.terra.dev", "phoenix-1")
        tally_id = await terra1.gov.tally(id)
        return tally_id
    
# loop = asyncio.new_event_loop()
# asyncio.set_event_loop(loop)

terra = LCDClient(chain_id="phoenix-1", url="https://phoenix-lcd.terra.dev")

votes_tables_url ="https://api.flipsidecrypto.com/api/v2/queries/e255de62-be60-4a28-8a4d-66eaa3e668d7/data/latest"


def status_dist():
    df2=table_votes(votes_tables_url)
    df3=df2[['Proposal ID', 'Proposal Status']]
    df4=df3.groupby('Proposal Status').agg(prop_count= ('Proposal ID', 'count'))
    df4=df4.reset_index()
    return df4

def grant_line_helper(url):
    df1=df_creator(url)
    df2=table_votes(votes_tables_url)
    df_inner =pd.merge(df1, df2, on='Proposal ID', how='inner')
    df_inner=df_inner.loc[df_inner['Proposal Status'] == 'Approved']
    df_raw=df_inner[["Voting End Time", "Grant Amount"]]
    df_raw["Weeks"] = df_raw["Voting End Time"].dt.to_period("W").dt.to_timestamp()
    df_raw.drop('Voting End Time', inplace=True, axis=1)
    df=df_raw.groupby('Weeks').agg(prop_count= ('Grant Amount', 'sum')).reset_index()
    df.rename(columns = {'prop_count':'Total Grant Disbursed in LUNA'}, inplace = True)
    df['Total Grant Disbursed in LUNA'] = df['Total Grant Disbursed in LUNA'].cumsum()
    df.rename(columns = {'Total Grant Disbursed in LUNA':'Cumulative Grant Disbursed in LUNA'}, inplace = True)
    
    return df

def grant_bar_helper(url):
    df1=df_creator(url)
    df2=table_votes(votes_tables_url)
    df_inner =pd.merge(df1, df2, on='Proposal ID', how='inner')
    df_inner=df_inner.loc[df_inner['Proposal Status'] == 'Approved']
    df_raw=df_inner[["Voting End Time", "Grant Amount"]]
    df_raw["Weeks"] = df_raw["Voting End Time"].dt.to_period("W").dt.to_timestamp()
    df_raw.drop('Voting End Time', inplace=True, axis=1)
    df=df_raw.groupby('Weeks').agg(prop_count= ('Grant Amount', 'sum')).reset_index()
    df.rename(columns = {'prop_count':'Total Grant Disbursed in LUNA'}, inplace = True)
    return df


def grant_stats(url1,url2):
    df1=df_creator(url1)
    df2=df_creator(url2)
    df3=table_votes(votes_tables_url)
    df_inner =pd.merge(df2, df3, on='Proposal ID', how='inner')

    grant_dict = dict()

    grant_dict['Total Paid Grant in LUNA']= df_inner.loc[df_inner['Proposal Status'] == 'Approved', 'Grant Amount'].sum()
    grant_dict['Total Paid Recipient Wallets']= df_inner.loc[df_inner['Proposal Status'] == 'Approved', 'Grant Target Wallet'].nunique()
    grant_dict['% Paid Grant']= (grant_dict['Total Paid Grant in LUNA']*100)/df1['Total Requested Grant in LUNA'].iat[0]
    grant_dict['% Paid Recipient Wallets']= (grant_dict['Total Paid Recipient Wallets']*100)/df1['Total Submitted Recipient Wallets'].iat[0]


    list_cols=list(df1.columns)

    for col in list_cols:
        grant_dict[col]=df1[col].iat[0]

    return grant_dict
   

def votes_stats(url1, url2):
    df1=df_creator(url1)
    df2=table_votes(votes_tables_url)
    df3=df_creator(url2)
    df_inner =pd.merge(df1, df2, on='Proposal ID', how='inner')
    votes_dict=dict()
    votes_dict['Total Approved Proposals (Voting Period)'] = df_inner.loc[df_inner['Proposal Status'] == 'Approved', 'Proposal ID'].count()
    votes_dict['Total Rejected Proposals (Voting Period)'] = df_inner.loc[df_inner['Proposal Status'] == 'Rejected', 'Proposal ID'].count()
    votes_dict['Total in-progress Proposals (Voting Period)'] = df_inner.loc[(df_inner['Proposal Status'] == 'Passing') | (df_inner['Proposal Status'] == 'Failing'), 'Proposal ID'].count()
    votes_dict['Total Votes Casted'] = df_inner['Yes Votes'].sum() + df_inner['No Votes'].sum()\
    + df_inner['Abstain Votes'].sum()+ df_inner['NoWithVeto Votes'].sum() 
    votes_dict[f"# of 'Yes' Votes"] = df_inner['Yes Votes'].sum()
    votes_dict[f"# of 'No' Votes"] = df_inner['No Votes'].sum()
    votes_dict[f"# of 'Abstain' Votes"]=df_inner['Abstain Votes'].sum()
    votes_dict[f"# of 'NoWithVeto' Votes"]=df_inner['NoWithVeto Votes'].sum()

    list_cols=list(df3.columns)
    for col in list_cols:
        votes_dict[col]=df3[col].iat[0]

    return votes_dict

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
def donuts( x,y,title,sql,datafr=None, url=None):

    st.markdown("---")
    st.text("")

    if url:
        st.markdown(f'[{title}]({sql})')

        response = requests.get(url)
        
        if response.status_code == 200:
            response_json = response.json()
        else:
            response = None

        df=pd.DataFrame.from_records(response_json)

    elif not datafr.empty:
        st.markdown(f'[{title}]({sql})')
        df= datafr
    df[x]=df[x].apply(lambda col: f'{col[0:18]}...' if len(col) > 21 else col)

  
    fig = px.pie(df[x], values = df[y], hole = 0.55,
        names = df[x],
    )

    fig.update_layout(
        autosize=True,
        width=400,
        height=400,
        showlegend=True, margin={"l":0,"r":5,"t":0,"b":0}
    )

    fig.update_traces(
        hoverinfo='label+percent',
        textinfo='percent', textfont_size=14)

    st.plotly_chart(fig, theme=None, use_container_width=True)

def line_charts(x, y,title,sql,url=None, datafr=None):
    
    st.markdown("---")
    st.text("")
    
    st.markdown(f'[{title}]({sql})')

    if url:
        response = requests.get(url)
        
        if response.status_code == 200:
            response_json = response.json()
        else:
            response = None

        df=pd.DataFrame.from_records(response_json)

    elif not datafr.empty:
        df=datafr
    df[x] = pd.to_datetime(df[x])
    # url = 'https://app.flipsidecrypto.com/velocity/queries/f8cf2192-3efc-4584-b2c4-965937f721a6'
    alt_chart = alt.Chart(df)\
    .mark_line()\
    .encode(
    x=alt.X(x, type = "temporal", axis=alt.Axis(format="%b %d, %Y")),
    y=y

    ).properties(
    width='container',
    height=400,
    ).interactive()

    # alt_chart.configure_bar(href='https://app.flipsidecrypto.com/velocity/queries/f8cf2192-3efc-4584-b2c4-965937f721a6')

    st.altair_chart(alt_chart, theme = 'streamlit', use_container_width=True)

def bar_charts(x, y,title,sql,z=None, url=None, datafr=None):
    
    if url:
        response = requests.get(url)
        
        if response.status_code == 200:
            response_json = response.json()
        else:
            response = None

        df=pd.DataFrame.from_records(response_json)

    elif not datafr.empty:
        df=datafr

    
    st.markdown("---")
    st.text("")

    st.markdown(f'[{title}]({sql})')

    df[x] = pd.to_datetime(df[x])
   

    if not z:
        alt_chart = alt.Chart(df)\
        .mark_bar()\
        .encode(
        x=alt.X(x, type = "temporal", axis=alt.Axis(format="%b %d, %Y")),
        y=y
        ).properties(
        width='container',
        height=400,
        ).interactive()
    else:
        alt_chart = alt.Chart(df)\
        .mark_bar()\
        .encode(
        x=alt.X(x, type = "temporal", axis=alt.Axis(format="%b %d, %Y")),
        y=y,
        color=z,
        ).properties(
        width='container',
        height=400,
        ).interactive()

    st.altair_chart(alt_chart, theme = 'streamlit', use_container_width=True)


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
        st.markdown("---")
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

        df = df[['Proposal Status', 'Proposal ID', 'Proposal Title','veto (V) %', 'threshold (T) %', 'quorum (Q) %', 'Proposer', 'Grant Target Wallet', 'Proposal Link', 'Voting Start Time', 'Voting End Time' ]]

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
                raw_value=(int(asyncio.run(id_pro(id))['yes'])+int(asyncio.run(id_pro(id))['no'])+int(asyncio.run(id_pro(id))['abstain'])+\
                int(asyncio.run(id_pro(id))['no_with_veto']))*100/(bonded_coins)
                quorum_dict[id]=float(millify(raw_value, precision=2))
            server_state.quorum_dict=quorum_dict

        except Exception as e:    
            print(e)
            quorum_dict=server_state.quorum_dict

        return quorum_dict

        
def table_proposals(url, title,sql):

    
    st.markdown("---")
    st.text("")
    st.markdown(f'[{title}]({sql})')



    df=df_creator(url)
    df["Proposal Submission Time"] = pd.to_datetime(df["Proposal Submission Time"])
    df["Deposit End Time"] = pd.to_datetime(df["Deposit End Time"])
    df=df.sort_values(by="Proposal Submission Time",ascending=False)
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
        options=["Overview", "Proposals & Deposits", "Votes", "Grant Disbursements"],  
        icons=["file-earmark-text-fill", "card-text", "card-checklist", "cash-coin"],  
        menu_icon="cast",  
        default_index=0, 
        orientation="horizontal",
    )


# print((terra.staking.pool().bonded_tokens))

# if selected == "Overview":
    

if selected == "Proposals & Deposits":
    stats_url='https://api.flipsidecrypto.com/api/v2/queries/b49ce1ca-f3df-4327-abe7-55da5bd74ecc/data/latest'
    deposit_amount_url = 'https://api.flipsidecrypto.com/api/v2/queries/6baf2b29-eb26-4b9e-bf13-aa2024675fef/data/latest'
    dict_data = deposits_stats(stats_url, deposit_amount_url )

    st.text("")
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
        "Proposal Submissions Explorer","https://flipsidecrypto.xyz/edit/queries/a3c67a3e-f33e-44e2-89d2-fac540bf1fd8?fileSearch=peroid")
    colu1,colu3,colu2=st.columns([8,0.5,5.5])

    with colu1:
        bar_charts("Weeks","Number of Submitted Proposals","Proposal Submissions Per Week", "https://flipsidecrypto.xyz/edit/queries/e93bd2dc-1dbe-414d-bae9-68a024ef8eb9/visualizations/4163be18-61b6-4d6b-beff-1b0f930f7359", url="https://api.flipsidecrypto.com/api/v2/queries/e93bd2dc-1dbe-414d-bae9-68a024ef8eb9/data/latest")

    with colu2:
        donuts(
        "Voting Eligibility Status", "Number of Submitted Proposals", "Proposal Voting Eligibility Status Distribution", "https://flipsidecrypto.xyz/edit/queries/496ee332-70cf-4fa7-9a67-aa7f979c029c/visualizations/0071b128-9e66-4317-80a3-6c1b62309fe4",
        url="https://api.flipsidecrypto.com/api/v2/queries/496ee332-70cf-4fa7-9a67-aa7f979c029c/data/latest")
    
    bar_charts("Weeks","Total Deposit Amount in LUNA","Total Deposit Amount Per Week", "https://flipsidecrypto.xyz/edit/queries/3e2f787f-e56c-4cb0-8d64-060821e62072/visualizations/f98b9faf-f8c8-4060-a9d3-fdb7aabe346c",url="https://api.flipsidecrypto.com/api/v2/queries/3e2f787f-e56c-4cb0-8d64-060821e62072/data/latest")

    c1,c2=st.columns(2)
    with c1:
        line_charts("Weeks", "Cumulative Proposal Submissions", "Weekly Cumulative Number of Proposal Submissions", "https://flipsidecrypto.xyz/edit/queries/23a7c6e6-15ad-480b-827c-095290ffd366/visualizations/17655c90-7f09-444d-b7e5-1484ae034cdd", url="https://api.flipsidecrypto.com/api/v2/queries/23a7c6e6-15ad-480b-827c-095290ffd366/data/latest")

    with c2:
        line_charts("Weeks", "Cumulative Deposit Amount in LUNA", "Weekly Cumulative Deposit Amount in LUNA", "https://flipsidecrypto.xyz/edit/queries/0b30377e-a914-4a9b-9b6e-2c86c43cf487", url="https://api.flipsidecrypto.com/api/v2/queries/0b30377e-a914-4a9b-9b6e-2c86c43cf487/data/latest")

    
if selected == "Votes":
    other_stats = 'https://api.flipsidecrypto.com/api/v2/queries/97988d9b-a452-4517-aab9-d14ecbde6be2/data/latest'
    votes_url= 'https://api.flipsidecrypto.com/api/v2/queries/bb06a6a7-178f-4f36-b059-5f06a2f645f6/data/latest'
    votes_dict = votes_stats(votes_url, other_stats)

    st.text("")
    colum1, colum2, colum3, colum4, colum5=st.columns(5)

    with colum1:
        st.metric("[Total Approved Proposals (Voting Period)](https://flipsidecrypto.xyz/edit/queries/bb06a6a7-178f-4f36-b059-5f06a2f645f6?fileSearch=+Grant+Votes)", millify(votes_dict['Total Approved Proposals (Voting Period)'], precision=2))
        st.metric("[Total Rejected Proposals (Voting Period)](https://flipsidecrypto.xyz/edit/queries/bb06a6a7-178f-4f36-b059-5f06a2f645f6?fileSearch=+Grant+Votes)", millify(votes_dict['Total Rejected Proposals (Voting Period)'], precision=2))

    with colum2:
        st.metric("[Total in-progress Proposals (Voting Period)](https://flipsidecrypto.xyz/edit/queries/bb06a6a7-178f-4f36-b059-5f06a2f645f6?fileSearch=+Grant+Votes)", millify(votes_dict['Total in-progress Proposals (Voting Period)'], precision=2))
        st.metric("[Total Votes Casted](https://flipsidecrypto.xyz/edit/queries/bb06a6a7-178f-4f36-b059-5f06a2f645f6?fileSearch=+Grant+Votes)", millify(votes_dict['Total Votes Casted'], precision=2))

    with colum3:
        st.metric("[# of 'Yes' Votes](https://flipsidecrypto.xyz/edit/queries/bb06a6a7-178f-4f36-b059-5f06a2f645f6?fileSearch=+Grant+Votes)", millify(votes_dict[f"# of 'Yes' Votes"], precision=2))
        st.metric("[# of 'No' Votes](https://flipsidecrypto.xyz/edit/queries/bb06a6a7-178f-4f36-b059-5f06a2f645f6?fileSearch=+Grant+Votes)", millify(votes_dict[f"# of 'No' Votes"], precision=2))

    with colum4:
        st.metric("[# of 'Abstain' Votes](https://flipsidecrypto.xyz/edit/queries/bb06a6a7-178f-4f36-b059-5f06a2f645f6?fileSearch=+Grant+Votes)", millify(votes_dict[f"# of 'Abstain' Votes"], precision=2))
        st.metric("[# of 'NoWithVeto' Votes](https://flipsidecrypto.xyz/edit/queries/bb06a6a7-178f-4f36-b059-5f06a2f645f6?fileSearch=+Grant+Votes)", millify(votes_dict[f"# of 'NoWithVeto' Votes"], precision=2))
    

    with colum5:
        st.metric("[# of Voters](https://flipsidecrypto.xyz/edit/queries/bb06a6a7-178f-4f36-b059-5f06a2f645f6?fileSearch=+Grant+Votes)", millify(votes_dict['Voters Count'], precision=2))
        st.metric("[Average Number of Votes/Proposal](https://flipsidecrypto.xyz/edit/queries/bb06a6a7-178f-4f36-b059-5f06a2f645f6?fileSearch=+Grant+Votes)", millify(votes_dict["Average Number of Votes"], precision=2))


    dataf=table_votes(votes_tables_url, 
        title="Proposal Voting Explorer",sql="https://flipsidecrypto.xyz/edit/queries/e255de62-be60-4a28-8a4d-66eaa3e668d7")
    st.dataframe(dataf,use_container_width=True)
    st.text("")
    co1,co2 = st.columns(2)
    
    with co1:
        donuts(
            "Proposal Status", "prop_count", "Proposal Status Distribution", votes_url,
            datafr=status_dist())
    with co2:
        donuts(
        "Vote Type", "Total Votes", "Vote Type Distribution", "https://flipsidecrypto.xyz/edit/queries/ad762586-822c-48fb-960d-dfd9e4bfe0d9?fileSearch=votes+category",
        url="https://api.flipsidecrypto.com/api/v2/queries/ad762586-822c-48fb-960d-dfd9e4bfe0d9/data/latest")
        
    
    cl1,cl2=st.columns([6,4])
    with cl1:
        bar_charts(
    "Weeks","Number of Votes","Number of Votes Per Week Grouped by Vote Type", "https://flipsidecrypto.xyz/edit/queries/c17a943b-9187-463d-973f-48c404ac4b32?fileSearch=Number+of+Votes+Per+Week+Grouped+By+Vote+Type", z="Vote Type", url="https://api.flipsidecrypto.com/api/v2/queries/c17a943b-9187-463d-973f-48c404ac4b32/data/latest",)
    with cl2:
        line_charts("Weeks", "Cumulative Number of Votes", "Weekly Cumulative Number of Votes", "https://flipsidecrypto.xyz/edit/queries/0e852575-4097-440c-bf5c-1af04ff69137?fileSearch=weekly+", url="https://api.flipsidecrypto.com/api/v2/queries/0e852575-4097-440c-bf5c-1af04ff69137/data/latest")


if selected == "Grant Disbursements":
    grant_dict=grant_stats( 'https://api.flipsidecrypto.com/api/v2/queries/21487e38-ebe4-4df6-9cab-2faca09cb2cb/data/latest', 'https://api.flipsidecrypto.com/api/v2/queries/3ec68f54-5889-4e27-b24a-55e2ba230724/data/latest')
    
    column1, column2, column3 = st.columns(3)
    with column1:
        st.metric("[Total Requested Grants in Luna](https://flipsidecrypto.xyz/edit/queries/21487e38-ebe4-4df6-9cab-2faca09cb2cb?fileSearch=Grant+Stat)", millify(grant_dict['Total Requested Grant in LUNA'], precision=2))
        st.metric("[Total Submitted Recipient Wallets](https://flipsidecrypto.xyz/edit/queries/21487e38-ebe4-4df6-9cab-2faca09cb2cb?fileSearch=Grant+Stat)", millify(grant_dict['Total Submitted Recipient Wallets'], precision=2))

    with column2:
        st.metric("[Total Paid Grant in LUNA](https://flipsidecrypto.xyz/edit/queries/21487e38-ebe4-4df6-9cab-2faca09cb2cb?fileSearch=Grant+Stat)", millify(grant_dict['Total Paid Grant in LUNA'], precision=2))
        st.metric("[Total Paid Recipient Wallets](https://flipsidecrypto.xyz/edit/queries/21487e38-ebe4-4df6-9cab-2faca09cb2cb?fileSearch=Grant+Stat)", millify(grant_dict['Total Paid Recipient Wallets'], precision=2))

    with column3:
        st.metric("[% Paid Grant](https://flipsidecrypto.xyz/edit/queries/21487e38-ebe4-4df6-9cab-2faca09cb2cb?fileSearch=Grant+Stat)", f'{millify(grant_dict[f"% Paid Grant"], precision=2)} %')
        st.metric("[% Paid Recipient Wallets](https://flipsidecrypto.xyz/edit/queries/21487e38-ebe4-4df6-9cab-2faca09cb2cb?fileSearch=Grant+Stat)", f'{millify(grant_dict["% Paid Recipient Wallets"], precision=2)} %')

    df=grant_bar_helper('https://api.flipsidecrypto.com/api/v2/queries/3ec68f54-5889-4e27-b24a-55e2ba230724/data/latest')
    bar_charts("Weeks", "Total Grant Disbursed in LUNA", "Weekly Total Grant Disbursed in LUNA","https://flipsidecrypto.xyz/edit/queries/3ec68f54-5889-4e27-b24a-55e2ba230724?fileSearch=Proposal", datafr=df)

    df=grant_line_helper('https://api.flipsidecrypto.com/api/v2/queries/3ec68f54-5889-4e27-b24a-55e2ba230724/data/latest')
    line_charts("Weeks", "Cumulative Grant Disbursed in LUNA", "Weekly Cumulative Total Grant Disbursed in LUNA","https://flipsidecrypto.xyz/edit/queries/3ec68f54-5889-4e27-b24a-55e2ba230724?fileSearch=Proposal", datafr=df)