import os
import shutil

import waterstay

# Copy the chemical elements database to $HOME/.waterstay/
homedir = os.path.expanduser('~')

databases = ['chemical_elements.yml', 'residues.yml']

for db in databases:
    database_path = os.path.join(homedir, '.waterstay', db)
    if not os.path.exists(database_path):
        try:
            os.makedirs(os.path.dirname(database_path))
        except FileExistsError:
            pass
        shutil.copy(os.path.join(waterstay.__path__[0],
                                 'database', db), database_path)
