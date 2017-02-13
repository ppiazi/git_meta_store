#!/usr/bin/python
#coding:utf-8
#===============================================================================
# name    : get_meta_store.py
# version : v1.0.0
# initial creator : Kwanghyun Yoo
# maintainer : Joohyun Lee (ppiazi@gmail.com)
#===============================================================================

import datetime
import fileinput
import git
import os
import shutil
import sys
import tempfile
import win32con
import win32file

from optparse import OptionParser

class ReadFileDate:
	STORE_FILE_NAME = ".git_meta_file"
	ALL_FILE_LIST = []
	SEPARATE_CHARACTER = "|"

	def __getDate(self, file_name):
		creation_date = access_date = modify_date = datetime.datetime.now()

		try:
			handle = win32file.CreateFile(file_name, 0, 0, None, win32con.OPEN_EXISTING, win32con.FILE_FLAG_BACKUP_SEMANTICS, None)

			creation_time, access_time, modify_time = win32file.GetFileTime(handle)

			creation_date = datetime.datetime.fromtimestamp(int(creation_time)) + datetime.timedelta(hours=9)
			access_date = datetime.datetime.fromtimestamp(int(access_time)) + datetime.timedelta(hours=9)
			modify_date = datetime.datetime.fromtimestamp(int(modify_time)) + datetime.timedelta(hours=9)

			handle.close()

		except Exception as e:
			print("[GetDate]", file_name, "=>", e)

		return creation_date, access_date, modify_date
		
	def __writeDate(self, file_name, creation_date, access_date, modify_date):
		try:
			handle = win32file.CreateFile(file_name, win32con.GENERIC_WRITE, 0, None, win32con.OPEN_EXISTING, win32con.FILE_FLAG_BACKUP_SEMANTICS, None)
			creation_time = datetime.datetime.strptime(creation_date, '%Y-%m-%d %H:%M:%S')
			access_time = datetime.datetime.strptime(access_date, '%Y-%m-%d %H:%M:%S')
			modify_time = datetime.datetime.strptime(modify_date, '%Y-%m-%d %H:%M:%S')

			win32file.SetFileTime(handle, creation_time, access_time, modify_time)

			handle.close()

		except Exception as e:
			print("[SetDate]", file_name, "=>", e)

	def __getGitStagedList(self):
		array_stage = []

		repo = git.Repo()

		staged_list = repo.index.diff("HEAD")   # staged file list
		if (len(staged_list) > 0):
			for x in staged_list:
				added_file = x.a_path
				removed_file = x.b_path
				if x.new_file is not True:  # staged file 의 경우, 삭제된 파일은 new_file flag True 로 표시됨
					array_stage.append(os.path.join('.', added_file).encode('euc-kr'))

		return array_stage
		
	def __getGitStagedUpdatedList(self):
		array_deleted = []
		array_added = []
		array_updated = []

		repo = git.Repo()

		staged_list = repo.index.diff("HEAD")   # staged file list
		if (len(staged_list) > 0):
			for x in staged_list:
				modified_file = x.a_path
				if x.new_file is True:  # staged file 의 경우, 삭제된 파일은 new_file flag True 로 표시됨
					array_deleted.append(os.path.join('.', modified_file).encode('euc-kr'))
				elif x.deleted_file is True:  # staged file 의 경우, 추가된 파일은 deleted_file flag True 로 표시됨
					array_added.append(os.path.join('.', modified_file).encode('euc-kr'))
				else:
					array_updated.append(os.path.join('.', modified_file).encode('euc-kr'))

		return array_deleted, array_added, array_updated

	def __getGitModifiedList(self):
		array_modified = []

		repo = git.Repo()

		modified_list = repo.index.diff(None)   # modified file list
		if (len(modified_list) > 0):
			for x in modified_list:
				added_file = x.a_path
				removed_file = x.b_path
				if x.deleted_file is not True:  # modified file 의 경우, 삭제된 파일은 deleted_file flag True 로 표시됨
					array_modified.append(added_file.encode('euc-kr'))

		return array_modified

	def __getGitUntrackedList(self):
		array_untracked = []

		repo = git.Repo()

		untracked_list = repo.untracked_files   # untracked file list
		if (len(untracked_list) > 0):
			for x in untracked_list:
				array_untracked.append(x)

		return array_untracked
		
	def __makeFileDateList(self, file_list):
		file = open(self.STORE_FILE_NAME, "w")

		for file_name in file_list:
			if file_name != self.STORE_FILE_NAME:
				creation_date, access_date, modify_date = self.__getDate(file_name);
				line = file_name + self.SEPARATE_CHARACTER + str(creation_date) + self.SEPARATE_CHARACTER + str(access_date) + self.SEPARATE_CHARACTER + str(modify_date) + "\n"
				file.write(line)

		file.close()

	def restoreFromMetaFile(self):
		file = open(self.STORE_FILE_NAME, "r")

		file_lines = file.readlines()
		for file_line in file_lines:
			file_name, creation_date, access_date, modify_date = file_line.replace("\n", "").split(self.SEPARATE_CHARACTER)
			if file_name != self.STORE_FILE_NAME:
				self.__writeDate(file_name, creation_date, access_date, modify_date)

		file.close()

	def __search(self, path):
		try:
			file_names = os.listdir(path)
			for file_name in file_names:
				if file_name != self.STORE_FILE_NAME:
					full_name = os.path.join(path, file_name)
					if file_name != '.git':
						self.ALL_FILE_LIST.append(full_name)
						if os.path.isdir(full_name):
							self.__search(full_name)

		except Exception as e:
			pass
			
	def realPathFiles(self, path):
		self.__search(path)
		self.__makeFileDateList(self.ALL_FILE_LIST)

	def storeMetaFile(self):
		self.realPathFiles('.')

	def updateMetaFiles(self):
		file_deleted, file_added, file_modified = self.__getGitStagedUpdatedList()

		temp_file = self.STORE_FILE_NAME + ".bak"

		file = open(self.STORE_FILE_NAME, "r")
		temp_file_handler = open(temp_file, "w")

		file_lines = file.readlines()
		for file_line in file_lines:
			file_name, creation_date, access_date, modify_date = file_line.replace("\n", "").split(self.SEPARATE_CHARACTER)
			if file_name not in file_deleted:
				if file_name in file_modified:
					cr_date, ac_date, md_date = self.__getDate(file_name);
					line = file_name + self.SEPARATE_CHARACTER + str(creation_date) + self.SEPARATE_CHARACTER + str(ac_date) + self.SEPARATE_CHARACTER + str(md_date) + "\n"
					temp_file_handler.write(line)
				elif file_name not in file_added:
					line = file_name + self.SEPARATE_CHARACTER + str(creation_date) + self.SEPARATE_CHARACTER + str(access_date) + self.SEPARATE_CHARACTER + str(modify_date) + "\n"
					temp_file_handler.write(line)

		file.close()

		os.remove(self.STORE_FILE_NAME)

		for file_name in file_added:
			cr_date, ac_date, md_date = self.__getDate(file_name);
			line = file_name + self.SEPARATE_CHARACTER + str(cr_date) + self.SEPARATE_CHARACTER + str(ac_date) + self.SEPARATE_CHARACTER + str(md_date) + "\n"
			temp_file_handler.write(line)

		temp_file_handler.close()

		shutil.move(temp_file, self.STORE_FILE_NAME)
		
if __name__ == "__main__":
	usage = """Usage: %prog [option]
	ex1) %prog -s or %prog --store : store file status into metadata(.git_meta_file)
	ex2) %prog -u or %prog --update : update metadata(.git_meta_file)
	ex3) %prog -r or %prog --restore : restore file status from metadata(.git_meta_file)
	ex4) %prog -p c:\ or %prog --path c:\ : make metadata(.git_meta_file) from specified path
	"""
	parser = OptionParser(usage=usage)
	parser.add_option("-s", "--store", dest="store", action="store_true", help="store file status into metadata(.git_meta_file)", default=False)
	parser.add_option("-r", "--restore", dest="restore", action="store_true", help="restore file status from metadata(.git_meta_file)", default=False)
	parser.add_option("-u", "--update", dest="update", action="store_true", help="update metadata(.git_meta_file) based according to current file status ", default=False)
	parser.add_option("-p", "--path", dest="path", help="make metadata(.git_meta_file) from specified path", default=False)

	(options, args) = parser.parse_args()

	runner = ReadFileDate()

	if (options.path):
		runner.realPathFiles(options.path)
	elif (options.store):
		runner.storeMetaFile()
	elif (options.update):
		runner.updateMetaFiles()
	elif (options.restore):
		runner.restoreFromMetaFile()
	else:
		parser.print_help()
