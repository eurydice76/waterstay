import os
import yaml


def load_database():

    homedir = os.path.expanduser('~')
    database_path = os.path.join(homedir, '.waterstay', 'chemical_elements.yml')

    # Load the chemical elements database
    with open(database_path, 'r') as fin:
        try:
            database = yaml.safe_load(fin)
        except yaml.YAMLError as exc:
            print(exc)

    return database


CHEMICAL_ELEMENTS = load_database()
