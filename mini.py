#!/usr/bin/env python

__author__ = 'stephanbuys'

# Copyright (c) 2014 Panoptix CC. All right reserved.

from jinja2 import Template as Jinja2Template
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
parser.add_argument('--controlfile', type=str, default='default.yml', help='The control file.')
parser.add_argument('--projectfile', type=str, default='project/project.yml', help="The project file.")
parser.add_argument('--loglevel', type=str, default='INFO', help="Log level.")
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

try:
    project_filename = args.projectfile
except:
    project_filename = 'project/project.yml'


logging.debug("Working Directory " + args.workingdir)
logging.debug("Control File: " + filename)
logging.debug("Project File: " + filename)

#read the default.yml file if we can
data = {}
try:
    stream = file(filename, 'r')
    data = load(stream, Loader=Loader)
except Exception, e:
    logging.error( "Error: " + str(e))
    exit(1)


#read the project.yml file if we can
project = {}
try:
    stream = file(project_filename, 'r')
    project = load(stream, Loader=Loader)
except Exception, e:
    logging.error( "Error: " + str(e) + " " + project_filename)
    exit(1)

template_variables = {}

if 'variables' in data:
    if project and 'variables' in project:
        data['variables'] = dict(data['variables'].items() + project['variables'].items())
    for key in data['variables']:
        template_variables[key] = data['variables'][key]
        logging.debug("User Variable (" + str(key) + ") : " + str(template_variables[key]))

if 'evariables' in data:
    if 'evariables' in project:
        data['evariables'] = dict(data['evariables'].items() + project['evariables'].items())
    for key in data['evariables']:
        template_variables[key]     = os.environ.get(key)
        logging.debug("Environment Variable (" + str(key) + ") : " + str(template_variables[key]))

if 'split' in data:
    for var in data['split']:
        template_variables[var['var']] = template_variables[var['var']].split(var['delim'])

def findTemplates():
    templates = []

    topdir = '.'

    # The arg argument for walk, and subsequently ext for step
    exten = '.orig.tpl'

    def step((ext), dirname, names):
        ext = ext.lower()

        for name in names:
            if name.lower().endswith(ext):
                # Instead of printing, open up the log file for appending
                tplate = os.path.join(dirname, name)
                destfile = tplate.replace(exten, '')
                templates.append({'src': tplate, 'dst': destfile})
                # with open(logpath, 'a') as logfile:
                #     logfile.write('%s\n' % os.path.join(dirname, name))

    # Change the arg to a tuple containing the file
    # extension and the log file name. Start the walk.
    os.path.walk(topdir, step, (exten))

    return templates

recurseTemplates = findTemplates()

if len(recurseTemplates) > 0:
    if 'templates' in data:
        data['templates'] = data['templates'] + recurseTemplates
    else:
        data['templates'] = recurseTemplates


#process the templates
if 'templates' in data:
    if project and 'templates' in project:
        for folder in project['templates']:
            if '/' not in folder['src']:
                folder['src'] = 'project/' + folder['src']
                folder['dst'] = 'project/' + folder['dst']
        data['templates'] = data['templates'] + project['templates']


    logging.debug("New template.")
    for template in data['templates']:
        # try:
            engines = ['jinja2']
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
                    logging.debug("Processign Jinja template")
                    try:
                        template = Jinja2Template(filedata)
                        filedata = template.render(template_variables)
                    except Exception,e:
                        logging.debug( "Error: ", str(e) )

            f = open(os.path.join(args.workingdir,dst),'w')
            f.write(filedata) # python will convert \n to os.linesep
            f.close()

