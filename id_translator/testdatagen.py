"""
Methods to generate sequential data to test ID-Translator

"""


import json
import pandas as pd


def main_data_csv():
    """
    Creates data expected from GSC intake csv as a new csv
    """
    number_of_records = 20

    df = pd.DataFrame()

    for row in range(1, number_of_records):
        df.loc[row, 'TF4CN_ID_TEST'] = ''.join(('TF4CN_TEST_', str(row).rjust(4, '0'),))
        df.loc[row, 'PROFYLE_ID_TEST'] = ''.join(('PROFYLE_TEST_', str(row).rjust(4, '0'),))
        df.loc[row, 'PIPELINE_ID'] = ''.join(('PIPELINE_ID_', str(row).rjust(4, '0'),))
        df.loc[row, 'DNA_LIBRARY_ID'] = ''.join(('DNA_DISEASE_', str(row).rjust(4, '0'),))

    df.set_index(['TF4CN_ID_TEST'], inplace=True)
    df.to_csv('{}/data/id_map_001.csv'.format("."))


def gen_bioapps_data():
    number_of_records = 15
    dt = {}
    for row in range(1, number_of_records):
        anon_id = ''.join(('LIMS_PT_', str(row).rjust(4, '0'),))
        TF4CN_ID_TEST = ''.join(('TF4CN_TEST_', str(row).rjust(4, '0'),))
        dt[TF4CN_ID_TEST] = anon_id

    return make_bioapps(dt)


def make_bioapps(data):
    pyld = {"data": data}
    with open('./tests/upload_test.json', 'w') as outfile:
        json.dump(pyld, outfile)


# print(sys.path[0])
main_data_csv()
# gen_bioapps_data()
