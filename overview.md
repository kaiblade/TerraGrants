# Introduction
In a bid to grow the new Terra ecosystem after the demise of the former one, a [proposal](https://agora.terra.money/discussion/7257-terra-expedition-an-ecosystem-expansion-program) was passed by  some Terra developers on the 17th of November, 2022. This proposal allocates 95 million LUNA for the Terra ecosystem expansion program, of which 20 million LUNA will be set aside for developer grants. This grant allocation hopes to incentivize developments of innovative dapps and smart contracts. 
This dashboard aims to track the grant funding process from proposal submissions to proposal voting and finally to grant disbursements. This dashboard will consist of the following sections:
 1. Proposals & Deposits
 2. Votes
 3. Grant Disbursements

Kindly note that analysis of the current data wouldn't be done on this dashboard as it's only required to track the grant funding process.

# Methodology
The data required for the visualizations on the dashboard were obtained through the following sources:

1.  Most were obtained from Flipside's Terra core tables e.g. `terra.core.fact_transactions`,`terra.core.fact_msgs`, `terra.core.fact_governance_votes` e.t.c.
2.  Some of the data was obtained using Terra's Python SDK i.e. [Terra SDK](https://pypi.org/project/terra-sdk/)
3. The above 2 sources were used in combination with data found on various Terra block explorers, Terra documentations and the [Terra Station](https://station.terra.money/gov#PROPOSAL_STATUS_VOTING_PERIOD)
