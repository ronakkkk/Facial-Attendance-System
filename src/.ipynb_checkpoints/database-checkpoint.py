import numpy as np
import os.path as osp
import cv2
import pickle
import re

from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cosine

from .dbutils import run_query
from .messages import DB_FILE_FOR_SHARED_MEMORY_MISSING_STRING
# from .global_vars import VECTORS_TABLE, PEOPLE_TABLE
from .dbcontainers import Face_Vector_Container, Person_Person_Details_Container
from sys import exit

class FacesDatabase:

    class Identity:
        def __init__(self, label="2-2", descriptor=None):
            self.label = label
            self.id = label.split('-')[0]
            self.descriptors = descriptor
        
        @staticmethod
        def cosine_dist(x, y):
            return cosine(x, y) * 0.5
        
        def __repr__(self):
            object_name = f'Identity(label={self.label}, id={self.id}, descriptors={type(self.descriptors)})'
            return object_name

    def __init__(self):
        self.database = None

    def set_database(self, database):
        self.database = database

    def match_faces(self, descriptors):

        if self.database is None:
            raise ValueError('Face data is not set')

        return self.database.match_faces(descriptors)
    
    def __getitem__(self, idx):
        if self.database is None:
            return None

        return self.database[idx]

class Cache:

    def __init__(self, db_file=None):

        self.database = []
        self.db_file = ''
        if db_file is not None: self.db_file = db_file
    
    def _set_up_db(self, db_file=None):
        pass

class IdentityCache(Cache):

    def __init__(self, db_file=None):
        super().__init__(db_file=db_file)
    
    def _set_up_db(self, db_file=None):
        if db_file is None:
            db_file = self.db_file
        
        if db_file is None:
            print(f'{DB_FILE_FOR_SHARED_MEMORY_MISSING_STRING} : Person')
            ###### Shut down the system here. if needed
            exit(-1)
        
        query = 'SELECT * FROM person_details'
        self.database = run_query(db_file, query, 'fetch')
    
    def _find_identity(self, label):

        return_value = [''] * len(Person_Person_Details_Container.enum)

        for people in self.database:
            if str(label).upper() == str(people[Person_Person_Details_Container.enum.empid.value]):
                return_value = people
                break
        
        return return_value

    def load_people_list(self, db_file=None):
        self._set_up_db(db_file=db_file)

    def find_identity(self, label):
        return self._find_identity(label=label)

class VectorCache(Cache):

    def __init__(self, db_file=None):
        super().__init__(db_file=db_file)

    def _set_up_db(self, db_file=None):
        if db_file is None:
            db_file = self.db_file
        
        if db_file is None:
            print(f'{DB_FILE_FOR_SHARED_MEMORY_MISSING_STRING} : Face')
            ###### Shut down the system here. if needed
            exit(-1)
        
        query = 'SELECT * FROM vectors'
        rows = run_query(db_file, query, 'fetch')

        for row in rows:
            label = row[Face_Vector_Container.enum.label.value]
            descriptor = pickle.loads(row[Face_Vector_Container.enum.vector.value])
            match, _ = self.check_if_label_exists(label)

            if match == -1:
                self.database.append(FacesDatabase.Identity(label, [descriptor]))
            else:
                self.database[match].descriptors.append(descriptor)
    
    def check_if_label_exists(self, label):
        
        match = -1
        name = re.split(r'-\d+$', label)

        if not len(name):
            return -1, label
        
        name_id = name[0].upper()
        for j, identity in enumerate(self.database):
            if identity.id == name_id:
                match = j
                break

        return match, label

    def _match_faces(self, descriptors):
        
        database = self.database

        distances = np.empty((len(descriptors), len(database)))
        for i, desc in enumerate(descriptors):
            for j, identity in enumerate(database):
                dist = []
                for _, id_desc in enumerate(identity.descriptors):
                    dist.append(FacesDatabase.Identity.cosine_dist(desc, id_desc))
                distances[i][j] = min(dist)

        _, assignments = linear_sum_assignment(distances)
        matches = []

        for i in range(len(descriptors)):
            if len(assignments) <= i:
                matches.append((0, 1.0))
                continue

            _id = assignments[i]
            distance = distances[i, _id]
            matches.append((_id, distance))

        return matches
    
    def match_faces(self, descriptors):
        return self._match_faces(descriptors)
    
    def set_up_db(self, db_file=None):
        self._set_up_db(db_file=db_file)
    
    def __getitem__(self, idx):
        return self.database[idx]