__author__ = 'stephanbuys'

# Copyright (c) 2014 Panoptix CC. All right reserved.

from jinja2 import Template
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import os
import logging
import sys

loglevel = 'DEBUG'

def setup_logging():
    global lg, ch, formatter
    lg = logging.getLogger()
    lg.setLevel(loglevel)
    ch = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    lg.addHandler(ch)

setup_logging()

filename = 'default.yml'

#read the default.yml file if we can
data = {}
try:
    stream = file(filename, 'r')
    data = load(stream, Loader=Loader)
except Exception, e:
    logging.error( "Error: ", e )
    exit(1)


template_variables = {}

if 'variables' in data:
    for key in data['variables']:
        template_variables[key] = data['variables'][key]
        logging.debug("User Variable (" + key + ") : " + template_variables[key] )

if 'evariables' in data:
    for key in data['evariables']:
        template_variables[key] = os.environ.get(key)
        logging.debug("Environment Variable (" + key + ") : " + template_variables[key] )

#process the templates
if 'templates' in data:
    logging.debug("New template.")
    for template in data['templates']:
        try:

            src = template['src']
            dst = template['dst']
            logging.debug("Template source :" + src)
            logging.debug("Template destination :" + dst)

            cwd = os.getcwd()


            filedata = ""
            with open (os.path.join(cwd,src), "r") as myfile:
                filedata=myfile.read()

            template = Template(filedata)
            rendereddata = template.render(template_variables)

            f = open(os.path.join(cwd,dst),'w')
            f.write(rendereddata) # python will convert \n to os.linesep
            f.close()


        except Exception,e:
            logging.error( "Error: ", e )


