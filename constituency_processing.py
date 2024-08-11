import pandas as pd

raw_df = pd.read_csv("data/ParliamentaryGeneralElectionResultsbyCandidate.csv")

# keep only year 2006 onwards
df = raw_df[raw_df['year'] >= 2006].copy()

# candidate names are separated by "|"; use it to count number of candidates
df['pax_number'] = df['candidates'].apply(lambda x: len(x.split('|')))

# "na" in vote_percentage becauase walkover; walkover will be assumed as 100% votes
df['vote_percentage'] = df['vote_percentage'].replace("na","1").astype(float)
df['vote_count'] = df['vote_count'].replace("na","Win by Walkover")

df_constituency = df[['year','constituency','constituency_type','pax_number','party','vote_count','vote_percentage']].copy()

# create result column to aggregate contested parties, votes and vote percentages
df_constituency['result'] = df.apply(lambda x: x['party'] + ": " + x['vote_count'] + " (" + str(round(100*x['vote_percentage'],1)) + "%)", axis=1)

final_df = df_constituency.groupby(['year', 'constituency','constituency_type','pax_number'])['result'].agg('; '.join).reset_index()
final_df = final_df.sort_values(['year','constituency'])
final_df['constituency'] = final_df['constituency'].str.upper().str.replace("-", " - ")
final_df = final_df.rename({'constituency': 'ED_DESC'}, axis=1)

final_df.to_csv("data/constituency_info_2006to2020.csv", index=False)