#!/usr/bin/env python

__author__ = 'stephanbuys'

# Copyright (c) 2016 Panoptix CC. All right reserved.

from jinja2 import Template as Jinja2Template, DebugUndefined, Environment, meta
from yaml import load

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import os
import logging
import sys
import argparse
import json
import re

parser = argparse.ArgumentParser(description='Mini Jinja')
parser.add_argument('--default', type=str, default='default.yml', help='The control file.')
parser.add_argument('--local', type=str, default='local.yml', help="The project file.")
parser.add_argument('--loglevel', type=str, default='WARN', help="Log level.")
parser.add_argument('--workingdir', type=str, default=os.getcwd(), help="Current working directory")
parser.add_argument('--templateext', type=str, default='.orig.tpl', help="Template pattern (orig.tpl)")
parser.add_argument('--std', type=bool, default=False, help="Use STDIN/STDOUT")
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

filename = args.default
project_filename = args.local

logging.debug("Working Directory " + args.workingdir)
logging.debug("Control File: " + filename)
logging.debug("Project File: " + project_filename)

# read the default.yml file if we can
data = {}
try:
    if '.json' in filename:
        with open(filename) as json_data:
            data = json.load(json_data)
            json_data.close()

    elif '.yml' in filename:
        stream = file(filename, 'r')
        data = load(stream, Loader=Loader)



except Exception, e:
    logging.warn("No default.yml file: " + filename + " ," + str(e))

# read the project.yml file if we can
project = {}
try:
    if '.json' in project_filename:
        with open(project_filename) as json_data:
            project = json.load(json_data)
            json_data.close()

    elif '.yml' in project_filename:
        stream = file(project_filename, 'r')
        project = load(stream, Loader=Loader)


except Exception, e:
    logging.info("No project.yml file: " + str(e) + " " + project_filename)

template_variables = {}

# Merge local with default
for key in project:
    if key in data:
        if isinstance(data[key], dict):
            data[key] = dict(data[key].items() + project[key].items())
        if isinstance(data[key], list):
            data[key] = data[key] + project[key]
    else:
        data[key] = project[key]

if 'variables' in data:
    for key in data['variables']:
        template_variables[key] = data['variables'][key]
        logging.debug("User Variable (" + str(key) + ") : " + str(template_variables[key]))
else:
    logging.warn("No variables found")

if 'evariables' in data:
    for key in data['evariables']:
        template_variables[key] = os.environ.get(key)
        logging.debug("Environment Variable (" + str(key) + ") : " + str(template_variables[key]))
else:
    logging.debug("No environment variables")

if 'split' in data:
    for var in data['split']:
        template_variables[var['var']] = template_variables[var['var']].split(var['delim'])

logging.debug("Final data: " + json.dumps(data, 2))


def findTemplates():
    templates = []

    topdir = '.'

    # The arg argument for walk, and subsequently ext for step
    # exten = '.orig.tpl'
    exten = args.templateext

    def step((ext), dirname, names):
        ext = ext.lower()

        for name in names:
            if name.lower().endswith(ext):
                # Instead of printing, open up the log file for appending
                tplate = os.path.join(dirname, name)
                destfile = tplate.replace(exten, '')
                templates.append({'src': tplate, 'dst': destfile})

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

logging.debug("Templates found: " + json.dumps(recurseTemplates))
# exit(1)

collect = {}


def jinja_parse(filedata, template_variables):
    # global var, template, filedata, e
    try:
        if filedata[-1:] != '\n':
            logging.warn(
                src + " does not contain a newline at the end of file, " + dst + " might appear mangled.")

        env = Environment()
        parsed_content = env.parse(filedata)

        for var in meta.find_undeclared_variables(parsed_content):
            if var not in template_variables:
                logging.error("Variable: " + var + " not defined")

        template = Jinja2Template(filedata, undefined=DebugUndefined)

        filedata = template.render(template_variables)
        # meta.
        return filedata

    except Exception, e:
        logging.debug("Error: ", e)
        return ""


# process the templates
if 'templates' in data:
    if project and 'templates' in project:
        for folder in project['templates']:
            if '/' not in folder['src']:
                folder['src'] = 'project/' + folder['src']
                folder['dst'] = 'project/' + folder['dst']
        data['templates'] = data['templates'] + project['templates']

    logging.debug("New template.")
    for template in data['templates']:

        src = template['src']
        dst = template['dst']
        logging.debug("Template source :" + src)
        logging.debug("Template destination :" + dst)

        filedata = ""
        with open(os.path.join(args.workingdir, src), "r") as myfile:
            filedata = myfile.read()

            logging.debug("Processing Jinja template")

            filedata = jinja_parse(filedata, template_variables)


        if 'collect' in data:
            logging.debug("Found a collect directive")
            for match in data['collect']:

                if re.search(match['regex'], src, re.MULTILINE):
                    logging.debug("Collecting " + src + " into " + match['dst'])

                    if match['dst'] in collect:
                        collect[match['dst']] = collect[match['dst']] + "\n" + filedata
                    else:
                        collect[match['dst']] = filedata

                else:

                    logging.debug("Skipping collect for " + src)
                    logging.debug("Writing " + dst)
                    f = open(os.path.join(args.workingdir, dst), 'w')
                    f.write(filedata)
                    f.close()

        else:
            logging.debug("Writing " + dst)
            f = open(os.path.join(args.workingdir, dst), 'w')
            f.write(filedata)
            f.close()

# print collect
for key in collect:
    logging.debug("Writing 'collected' file " + key)
    f = open(os.path.join(args.workingdir, key), 'w')
    f.write(collect[key])
    f.close()
