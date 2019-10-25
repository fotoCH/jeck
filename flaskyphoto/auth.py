#!/usr/bin/env python3


import flask_jwt
from flask_jwt import JWT, jwt_required, current_identity
from werkzeug.security import safe_str_cmp

class AuthUser(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password
    def __str__(self):
        return "AuthUser(id='%s')" % self.id


uid_counter = 0
username_table = {}
userid_table = {}

def init_auth(config):
    global uid_counter, username_table, userid_table
    for u in config["auth"]["users"]:
        user = AuthUser(uid_counter, u['user'], u['pass'])
        username_table[u['user']] = user
        userid_table[uid_counter] = user
        uid_counter+=1

def authenticate(username, password):
    global username_table, userid_table
    user = username_table.get(username, None)
    if user and safe_str_cmp(user.password.encode('utf-8'), password.encode('utf-8')):
        print(f"success, user {user}")
        return user

def identity(payload):
    global username_table, userid_table
    user_id = payload['identity']
    return userid_table.get(user_id, None)
