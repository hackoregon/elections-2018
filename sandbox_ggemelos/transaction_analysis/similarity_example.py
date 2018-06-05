import datetime
from sandbox_ggemelos.transaction_analysis.funding_similarity import SIMILARITY_GRAPH


## INSTANCIATE SIMILARITY GRAPH
START_DATE = datetime.date(2016, 11, 15)
END_DATE = datetime.date(2017, 11, 15)

graph = SIMILARITY_GRAPH(start_date=START_DATE,
                         end_data=END_DATE,
                         min_donation_amount=1000,
                         min_similarity=0.5)


## LOOK UP SIMILARLY FUNDED COMMITTEES
node_name = 'Friends of Andy Olson'
results = graph.look_up(name=node_name)

print('Similarly Funded Committees:')
print('\t' + '\n\t'.join(results['neighborhood']))

print('\nDonor Profile:')
for donor, data in results['donor_profile'].items():
    print('\t{0:s} (prct/overlap): {1:0,.1%} / {2:0,.1%}'.format(donor, data['percent'], data['overlap']))

# Print graph JSON file
print('\nGraph JSON:')
print(results['graph_json'])


## LOOK UP SIMILARLY FUNDED COMMITTEES AND LAUNCH D#
node_name = 'Friends of Andy Olson'
results = graph.look_up(name=node_name, d3_path='/Users/ggemelos/Dropbox/documents/hackoregon/data/d3graph')