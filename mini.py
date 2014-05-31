#!/usr/bin/env python

__author__ = 'stephanbuys'

# Copyright (c) 2014 Panoptix CC. All right reserved.

from jinja2 import Template as Jinja2Template
from mako.template import Template as MakoTemplate
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import os
import logging
import sys
import argparse


parser = argparse.ArgumentParser(description='Mini Jinja')
parser.add_argument('--controlfile', type=str, default='default.yml',help='The control file.')
parser.add_argument('--loglevel', type=str, default='INFO',help="Log level.")
parser.add_argument('--workingdir', type=str, default=os.getcwd(), help="Current working directory")
args = parser.parse_args()

try:
    loglevel = str(args.loglevel).upper()
except:
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

try:
    filename = args.controlfile
except:
    filename = 'default.yml'

logging.debug("Working Directory " + args.workingdir)
logging.debug("Control File: " + filename)

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
        logging.debug("User Variable (" + str(key) + ") : " + str(template_variables[key] ))

if 'evariables' in data:
    for key in data['evariables']:
        template_variables[key] = os.environ.get(key)
        logging.debug("Environment Variable (" + str(key) + ") : " + str(template_variables[key]) )

# def split(value,seperator=None):
#     if seperator:
#         return value.strip().split(seperator)
#     else:
#         return value.strip().split()
#
# environment.filters['split'] = split

if 'split' in data:
    for var in data['split']:
        template_variables[var['var']] = template_variables[var['var']].split(var['delim'])

#process the templates
if 'templates' in data:
    logging.debug("New template.")
    for template in data['templates']:
        # try:
            engines = ['jinja2','mako']
            if 'engines' in template:
                engines = template['engines']

            src = template['src']
            dst = template['dst']
            logging.debug("Template source :" + src)
            logging.debug("Template destination :" + dst)

            filedata = ""
            with open (os.path.join(args.workingdir,src), "r") as myfile:
                filedata=myfile.read()

            for e in engines:
                if e == 'jinja2':
                    try:
                        template = Jinja2Template(filedata)
                        filedata = template.render(template_variables)
                    except Exception,e:
                        logging.debug( "Error: ", str(e) )
                elif e == 'mako':
                    try:
                        filedata = MakoTemplate(filedata).render(template_variables)
                    except Exception,e:
                        logging.debug( "Error: ", str(e) )


            f = open(os.path.join(args.workingdir,dst),'w')
            f.write(filedata) # python will convert \n to os.linesep
            f.close()


        # except Exception,e:
        #     logging.error( "Error: ", str(e) )


