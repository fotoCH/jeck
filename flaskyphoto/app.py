#!/usr/bin/env python3


import flask
import flask_restplus

from flask_jwt import JWT, jwt_required, current_identity

from . import db as db_base
from . import helpers


from pprint import pprint

# init app and database
config = helpers.load_config()

#
# def authenticate(username, password):
#     print(username, password)
#     pass
#
# def identity(payload):
#     print(payload)
#     pass


db = db_base.Database(config)
db.init()
db.commit()
app = flask.Flask(__name__)


api = flask_restplus.Api(
    app,
    version='1.0',
    title='flaskyphoto',
    description='A simple & dynamic api to manage photos or other documents'
)


#jwt = JWT(app, authenticate, identity)


@api.route('/list')
class ListTables(flask_restplus.Resource):
    def get(self):
        """ List all existing tables """
        return list(db.tables.keys())


@api.route('/<string:tablename>/spec')
@api.doc(responses={404: 'Table not found'})
class ListSchema(flask_restplus.Resource):
    def get(self, tablename):
        """ List schema/spec for given table """
        if db.spec.get(tablename):
            return db.spec[tablename]
        return {"message":"cannot find table with the name provided"}, 404


@api.route('/<string:tablename>')
@api.doc(responses={200: 'Success'})
@api.doc(responses={404: 'Table not found'})
class TableActions(flask_restplus.Resource):
    def get(self, tablename):
        """ Get content of whole table """
        if db.spec.get(tablename):
            return db.get_whole_table(tablename)
        return {"message":"cannot find table with the name provided"}, 404

    @api.doc(responses={403: 'Not Authorized'})
    def post(self, tablename):
        """
        Create new entry
        Input is JSON with field values. Valid fields can be get by
        API /tablename/spec
        """
        if flask.request.is_json and db.spec.get(tablename):
            content = flask.request.get_json()
            db.add_entry_to_table(tablename, content)
            db.commit()
            return 200
        return {"message":"cannot find table with the name provided"}, 404


@api.route('/<string:tablename>/<int:itemid>')
@api.doc(responses={404: 'Table or item not found'})
@api.doc(responses={200: 'Success'})
class EntryActions(flask_restplus.Resource):

    def get(self, tablename, itemid):
        """ Get entry by ID"""
        if db.spec.get(tablename):
            res = db.get_item(tablename, itemid)
            if res:
                return res
        return {"message":"cannot find item with the id provided"}, 404

    @api.doc(responses={403: 'Not Authorized'})
    def put(self, tablename, itemid):
        """ Update entry """
        if flask.request.is_json and db.spec.get(tablename):
            content = flask.request.get_json()
            db.update_entry(tablename, itemid, content)
            db.commit()
            return 200
        return {"message":"cannot find item with the id provided"}, 404

    @api.doc(responses={403: 'Not Authorized'})
    def delete(self, tablename, itemid):
        """ Delete entry """
        if db.spec.get(tablename):
            db.delete_entry(tablename, itemid)
            db.commit()
            return 200
        return {"message":"cannot find item with the id provided"}, 404


@api.route('/<string:tablename>/<int:itemid>/image.jpg')
class ImageServer(flask_restplus.Resource):
    pass


# get list of unique values from a field
@api.route('/<string:tablename>/field/<string:fieldname>')
@api.doc(responses={404: 'Table not found'})
@api.doc(responses={200: 'Success'})
class FieldActions(flask_restplus.Resource):
    def get(self, tablename, fieldname):
        """ Get unique field values for a given field """
        if db.spec.get(tablename):
            return db.get_unique_field_values(tablename, fieldname)
        return {"message":"cannot find table with the name provided"}, 404


@api.route('/<string:tablename>/search')
@api.doc(params={'query': 'Search query'})
@api.doc(responses={404: 'Table not found'})
@api.doc(responses={200: 'Success'})
class SearchActions(flask_restplus.Resource):
    def get(self, tablename):
        """ Search an entry in given table """
        if db.spec.get(tablename):
            query = flask.request.args.get('query')
            res = db.full_search(tablename, query)
            return res
        return {"message":"cannot find table with the name provided"}, 404


@api.route('/<string:tablename>/filter')
@api.doc(responses={404: 'Table not found'})
@api.doc(responses={200: 'Success'})
class FilterActions(flask_restplus.Resource):
    def post(self, tablename):
        """
        Apply given filter on table
        Filter spec can be found here: https://pypi.org/project/sqlalchemy-filters
        Input is JSON:
        ```json
        { filter: ["your filters here"] }
        ```
        """
        if db.spec.get(tablename) and flask.request.is_json:
            filter_spec = flask.request.get_json()['filter']
            return db.filter(tablename, filter_spec)
        return {"message":"cannot find table with the name provided"}, 404
