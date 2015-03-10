import json
import os.path
import random
import re
import sys
import string
import subprocess
import time

from flask import Flask, request, url_for, render_template

webapp = Flask(__name__)
webapp.config["DEBUG"] = True

projects = ["fraudlinks", "industry-classifier", "transaction-classification"]

file_config = json.loads(open("file_config.json").read())
projects = [key for key in file_config]

def find_defs(path):
    lines = open(path).readlines()
    # Push the line numbers of all defs into a list
    line_nos = []
    i = 0
    for line in lines:
        i += 1
        if re.match("^\s*def ", line):
            line_nos.append((i, path))
    return line_nos
    

def extract_def(path, starting_line_num):
    # Could have a nested def, so can't just read until next def or EOF
    last_line = ""
    lines = open(path).readlines()
    def_text = ""
    def_length_leading_space = None
    # Line we are on
    i = 0
    # Lines since we hit our def
    j = 0
    in_def = False
    for line in lines:
        i += 1
        blank_line = line.strip() == ""
        matches = re.search("(^\s*)[^\s]", line)
        if matches is not None:
            leading_space = matches.group(1)
        else:
            leading_space = ""
        leading_space = leading_space.replace("\t", " " * 4)
        length_leading_space = len(leading_space)
        if i == starting_line_num:
            in_def = True
            # Want to append stuff like @app.route annotations for my Flask apps
            if re.search("^\s*@.*route", last_line):
                def_text = last_line
            def_length_leading_space = length_leading_space
        leading_space_match = length_leading_space == def_length_leading_space
        if j > 0 and leading_space_match and not blank_line:
            in_def = False
        if in_def:
            j += 1
            def_text += line
        last_line = line
    return def_text 


@webapp.route("/code_driller/random/<project>", methods=["GET"])
def show_random_def(project):
    if project not in projects:
        return "No project with that name!"
    
    project_parent = file_config[project]["parent"]
    project_parent = re.sub("/$", "", project_parent)
    results = subprocess.check_output(
        ["find", str(project_parent + "/"  + project), "-name", "*.py"]
    )
    splitup = results.split("\n")
    all_defs = []
    for path in splitup:
        if not os.path.isfile(path):
            continue
        defs = find_defs(path)
        all_defs += defs

    starting_line_num, random_path = random.choice(all_defs) 
    def_text = extract_def(random_path, starting_line_num)

    return render_template("defs.html", def_text=def_text, path=random_path, projects=projects)


webapp.run("0.0.0.0", port=5454)


