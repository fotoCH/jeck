#!/usr/bin/env python3


import sys

import sqlalchemy
import sqlalchemy_filters
from sqlalchemy.orm import sessionmaker
import sqlalchemy.ext.declarative

from pprint import pprint
from sqlalchemy import Column, Integer, String, Boolean, Float, Binary, Date, Text, Time



def yaml_to_model(base, yaml_spec):
    """
    this function takes a custom yaml spec and parses it to an sqlalchemy
    model. all the weird dynamic table stuff happens here
    """

    attr_dict = {
        '__tablename__': yaml_spec['name'],
	    'id': Column(Integer, primary_key=True)
    }

    # this needs to be in this loop
    # TODO: find out why cannot be implemented in own function
    for field in yaml_spec['spec']:
        spec_type = field['type']
        if spec_type == "string":
            flen = field.get('size', 255)
            attr_dict[field['name']] = Column(String(flen))
        if spec_type == "integer" or spec_type=="number":
            attr_dict[field['name']] = Column(Integer)
        if spec_type == "bool":
            attr_dict[field['name']] = Column(Boolean)
        if spec_type == "float":
            attr_dict[field['name']] = Column(Float)
        if spec_type == "binary":
            attr_dict[field['name']] = Column(Binary)
        if spec_type == "text":
            attr_dict[field['name']] = Column(Text)
        if spec_type == "date":
            attr_dict[field['name']] = Column(Date)
        if spec_type == "time":
            attr_dict[field['name']] = Column(Time)

    return type(yaml_spec['name'], (base,), attr_dict)



class Database:
    """
    the abstract db class which is the main interface for the app
    """
    def __init__(self, db, config):
        self.base = False
        self.tables = {}
        self.spec = {}

        self.db = db
        self.session = self.db.session
        self.initialized = False
        self.config = config



    def init(self):
        self.create_tables_from_spec()
        self.create_tables()
        self.commit()
        self.initialized = True


    def update_session(self, db):
        self.db = db
        self.session = db.session


    def create_tables_from_spec(self):
        for spec in self.config['schema']:
            self.spec[spec['name']] = spec['spec']
            self.tables[spec['name']] = yaml_to_model(self.db.Model, spec)


    def create_tables(self):
        self.db.create_all()


    def commit(self):
        self.session.commit()


    # query stuff
    def get_item(self, table, id):
        """ get single item from table over id
        """
        res = False
        try:
            res = self.session.query(self.tables[table]).get(id).__dict__
            del res['_sa_instance_state']
        except AttributeError:
            pass
        return res


    def add_entry_to_table(self, table, entry):
        entry = self.tables[table](**entry)
        self.session.add(entry)


    def update_entry(self, table, id, entry):
        self.session.query(self.tables[table]) \
            .filter(self.tables[table].__table__.c['id'] == id) \
            .update(entry)


    def delete_entry(self, table, id):
        self.session.query(self.tables[table]) \
         .filter(self.tables[table].__table__.c['id'] == id).delete()


    def item_to_dict(self, item):
        d = item.__dict__
        del d['_sa_instance_state']
        return d


    def query_to_list(self, query):
        res = []
        for item in query:
            res.append(self.item_to_dict(item))
        return res


    def get_whole_table(self, table, page=False, page_size=False):
        res = self.session.query(self.tables[table])
        res_len = len(res.all())
        if page:
            res, pagination = sqlalchemy_filters.apply_pagination(
                res,
                page_number=int(page),
                page_size=int(page_size)
            )
        return {
            "count": res_len,
            "results": self.query_to_list(res.all())
        }


    def get_unique_field_values(self, table, field, no_empty=True):
        res = []
        try:
            r = self.session.query(self.tables[table].__table__.c[field]).distinct()
            res = [ i[0] for i in r ]
            if not res[0]:
                res = []
        except KeyError:
            pass
        if no_empty:
            res = [x for x in res if x]

        return res



    # search stuff
    def full_search(self, table, query, page=False, page_size=False):
        filters = []
        for item in self.spec[table]:
            if item['searchable']:
                filters.append({
                    'field': item['name'],
                    'op': 'ilike',
                    'value': '%{0}%'.format(query)
                })
        filter_spec = [ { "or": filters } ]

        res = sqlalchemy_filters.apply_filters(
            self.session.query(self.tables[table]), filter_spec)

        res_len = len(res.all())

        if page:
            res, pagination = sqlalchemy_filters.apply_pagination(
                res,
                page_number=int(page),
                page_size=int(page_size)
            )
        return {
            "count": res_len,
            "results": self.query_to_list(res.all())
        }


    def filter(self, table, filter_spec, page=False, page_size=False):
        try:
            res = sqlalchemy_filters.apply_filters(
                self.session.query(self.tables[table]), filter_spec)
            res_len = len(res.all())
            if page:
                res, pagination = sqlalchemy_filters.apply_pagination(
                    res,
                    page_number=int(page),
                    page_size=int(page_size)
                )
            return {
                "count": res_len,
                "results": self.query_to_list(res.all())
            }
        except:
            return {
                "count": 0,
                "results": []
            }
