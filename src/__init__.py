import os
import shutil

import waterstay

# Copy the chemical elements database to $HOME/.waterstay/
homedir = os.path.expanduser('~')
database_path = os.path.join(homedir, '.waterstay', 'chemical_elements.yml')
if not os.path.exists(database_path):
    os.makedirs(os.path.dirname(database_path))
    shutil.copy(os.path.join(waterstay.__path__[0],
                             'database', 'chemical_elements.yml'), database_path)
