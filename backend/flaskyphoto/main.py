#!/usr/bin/env python3

import functools
import datetime

import flask
import flask_restplus

from flask_sqlalchemy import SQLAlchemy
from flask_jwt import JWT, jwt_required, current_identity


from pprint import pprint


# this is not the nicest but works for now
try:
    import db as db_base
    import helpers
    import auth
    import addfile
except ModuleNotFoundError:
    from . import db as db_base
    from . import helpers
    from . import auth
    from . import addfile


# Init app and database
config = helpers.load_config()

# Init fileadder class
fileadder = addfile.ItemFileAdder(config)

# app & API
app = flask.Flask(__name__)
api = flask_restplus.Api(
    app,
    version='1.0',
    title='flaskyphoto',
    description='A simple & dynamic api to manage photos or other documents'
)

app.config['SQLALCHEMY_DATABASE_URI'] = config['database']['engine']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

dbo = SQLAlchemy(app)

# Init Database
db = db_base.Database(dbo, config)
db.init()
#db.commit()


print("hello and welcome to flaskyphoto")


# JWT authentication
if config['auth']['enable']:
    auth.init_auth(config)
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['SECRET_KEY'] = config['auth']['secret']
    app.config['JWT_EXPIRATION_DELTA'] = datetime.timedelta(
        seconds=int(config['auth']['token_valid_for'])
    )
    jwt = JWT(app, auth.authenticate, auth.identity)
else:
    # override jwt_required if auth is disabled
    # sorry for uglyness
    def jwt_required(realm=None):
        def wrapper(fn):
            @functools.wraps(fn)
            def decorator(*args, **kwargs):
                return fn(*args, **kwargs)
            return decorator
        return wrapper


@app.before_request
def before_request():
    print("update database session")
    db.update_session(dbo)


#fix CORS stuff
@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    header['Access-Control-Allow-Headers']= 'Access-Control-Allow-Headers, Origin,Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers'
    return response


#
# The API itself
#

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
@api.doc(params={'page': 'Page number (optional)'})
@api.doc(params={'page_size': 'Page size. If page is specified and page_number empty, it will be set to 30'})
@api.doc(responses={200: 'Success'})
@api.doc(responses={404: 'Table not found'})
class TableActions(flask_restplus.Resource):
    def get(self, tablename):
        """ Get content of whole table """
        if db.spec.get(tablename):
            page = flask.request.args.get('page', False)
            page_size = flask.request.args.get('page_size', 30)
            return fileadder.list(
                tablename, db.get_whole_table(tablename, page=page, page_size=page_size)
            )
        return {"message":"cannot find table with the name provided"}, 404

    @jwt_required()
    @api.doc(responses={401: 'Not Authorized'})
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
                return fileadder.single(tablename, res)
        return {"message":"cannot find item with the id provided"}, 404

    @jwt_required()
    @api.doc(responses={401: 'Not Authorized'})
    def put(self, tablename, itemid):
        """ Update entry """
        if flask.request.is_json and db.spec.get(tablename):
            content = flask.request.get_json()
            db.update_entry(tablename, itemid, content)
            db.commit()
            return 200
        return {"message":"cannot find item with the id provided"}, 404

    @jwt_required()
    @api.doc(responses={401: 'Not Authorized'})
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
            res = db.get_unique_field_values(tablename, fieldname)
            res.sort()
            return res
        return {"message":"cannot find table with the name provided"}, 404


@api.route('/<string:tablename>/search')
@api.doc(params={'query': 'Search query'})
@api.doc(params={'page': 'Page number (optional)'})
@api.doc(params={'page_size': 'Page size. If page is specified and page_number empty, it will be set to 30'})
@api.doc(responses={404: 'Table not found'})
@api.doc(responses={200: 'Success'})
class SearchActions(flask_restplus.Resource):
    def get(self, tablename):
        """ Search an entry in given table """
        if db.spec.get(tablename):
            query = flask.request.args.get('query')
            page = flask.request.args.get('page', False)
            page_size = flask.request.args.get('page_size', 30)
            res = db.full_search(tablename, query, page=page, page_size=page_size)
            return fileadder.list(tablename, res)
        return {"message":"cannot find table with the name provided"}, 404



@api.route('/<string:tablename>/filter-spec')
@api.doc(responses={404: 'Table not found'})
@api.doc(responses={200: 'Success'})
class FilterActions(flask_restplus.Resource):
    def get(self, tablename):
        """
        Build data array for possible filters
        """
        if db.spec.get(tablename):
            res = []
            for item in db.spec.get(tablename):
                filterable = item.get("filterable", True)
                if item['searchable'] and filterable:
                    item['data'] = db.get_unique_field_values(tablename, item['name'])
                    if item['data']:
                        item['data'].sort()
                        res.append(item)
            return res
        return {"message":"cannot find table with the name provided"}, 404



@api.route('/<string:tablename>/filter')
@api.doc(responses={404: 'Table not found'})
@api.doc(responses={200: 'Success'})
@api.doc(params={'page': 'Page number (optional)'})
@api.doc(params={'page_size': 'Page size. If page is specified and page_number empty, it will be set to 30'})
class FilterActions(flask_restplus.Resource):
    def post(self, tablename):
        """
        Apply given filter on table
        Filter spec can be found here: https://github.com/juliotrigo/sqlalchemy-filters#filters-format
        Please note that you cannot specify an model, since this is controlled over tablename
        Input is JSON:
        ```json
        { filter: ["your filters here"] }
        ```
        """
        if db.spec.get(tablename) and flask.request.is_json:
            filter_spec = flask.request.get_json()['filter']
            print(filter_spec)
            page = flask.request.args.get('page', False)
            page_size = flask.request.args.get('page_size', 30)
            return fileadder.list(
                tablename,
                db.filter(tablename, filter_spec, page=page, page_size=page_size)
            )
        return {"message":"cannot find table with the name provided"}, 404









if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
