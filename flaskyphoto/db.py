#!/usr/bin/env python3


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
            attr_dict[field['name']] = Column(String)
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
    def __init__(self, config):
        self.base = False
        self.tables = {}
        self.spec = {}
        self.engine = False
        self.session = False
        self.initialized = False
        self.config = config


    def init(self):
        self.create_base()
        self.create_tables_from_spec()
        self.create_engine()
        self.create_session()
        self.create_tables()
        self.commit()
        self.initialized = True

    def create_base(self):
        self.base = sqlalchemy.ext.declarative.declarative_base()

    def create_tables_from_spec(self):
        for spec in self.config['schema']:
            self.spec[spec['name']] = spec['spec']
            self.tables[spec['name']] = yaml_to_model(self.base, spec)

    def create_engine(self):
        self.engine = sqlalchemy.create_engine(
            self.config['database']['engine'],
            echo=self.config['database']['echo']
        )
        pass

    def create_session(self):
        if self.engine:
            Session = sessionmaker(bind=self.engine)
            self.session = Session()

    def create_tables(self):
        self.base.metadata.create_all(self.engine)

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
        if page:
            res, pagination = sqlalchemy_filters.apply_pagination(
                res,
                page_number=int(page),
                page_size=int(page_size)
            )
        return self.query_to_list( res.all() )


    def get_unique_field_values(self, table, field):
        res = []
        try:
            r = self.session.query(self.tables[table].__table__.c[field]).distinct()
            res = [ i[0] for i in r ]
            if not res[0]:
                res = []
        except KeyError:
            pass
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

        if page:
            res, pagination = sqlalchemy_filters.apply_pagination(
                res,
                page_number=int(page),
                page_size=int(page_size)
            )
        return self.query_to_list(res.all())


    def filter(self, table, filter_spec, page=False, page_size=False):
        try:
            res = sqlalchemy_filters.apply_filters(
                self.session.query(self.tables[table]), filter_spec).all()
            res, pagination = sqlalchemy_filters.apply_pagination(
                res,
                page_number=int(page),
                page_size=int(page_size)
            )
            return self.query_to_list(res.all())
        except:
            return []
