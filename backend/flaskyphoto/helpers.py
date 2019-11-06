#!/usr/bin/env python3

import os
import sys
import yaml

def load_config():
    conf_file = os.environ.get("APP_CONFIG")
    if not conf_file:
        print("please define environ variable APP_CONFIG")
        sys.exit(1)
    with open(conf_file) as f:
        config = yaml.safe_load(f)
    return config
