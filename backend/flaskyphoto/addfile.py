#!/usr/bin/env python3


import os
import glob


"""
this class adds file to database entrys
"""
class ItemFileAdder:

    def __init__(self, config):
        self.tables = {}
        self.config = config
        for table in config['schema']:
            self.tables[table['name']] = table

    def single(self, tablename, entry):
        """
        Add files to single entry
        """
        glob_str = os.path.join(
            os.path.realpath( self.config['storage']['path'] ),
            self.tables[tablename]['settings']['fileregex'].format(**entry)
        )
        glob_res = glob.glob(glob_str)
        files = []
        for file in glob_res:
            dpath = os.path.relpath(
                file,
                self.config['storage']['path']
            )
            files.append("{0}{1}".format(
                self.config['storage']['storage-url'],
                dpath
            ))
        entry['files'] = files
        return entry


    def list(self, tablename, entrys):
        """
        Add files to list of entrys
        """
        res = {
            "count": entrys['count'],
            "results": []
        }
        for entry in entrys['results']:
            res['results'].append(
                self.single(tablename, entry)
            )
        return res
