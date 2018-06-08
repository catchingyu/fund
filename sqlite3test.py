# !/usr/bin/python 
# -*- coding: utf-8 -*-
# -*- coding: gdb -*-

import time
import datetime
import glob
import urllib2
import json
import sys
import re
import sqlite3
import random
import threading
import os

fund_info_list = ['Date', 'NetValue', 'AccuValue', 'DayIncrease', 'Bonus']

lock = threading.Lock()
class SQLiteWraper(object):
	"""
	数据库的一个小封装，更好的处理多线程写入
	"""

	def __init__(self, path, command='', *args, **kwargs):
		self.lock = threading.RLock()  # 锁
		self.path = path  # 数据库连接参数

		if command != '':
			conn = self.get_conn()
			cu = conn.cursor()
			cu.execute(command)

	def get_conn(self):
		conn = sqlite3.connect(self.path)  # ,check_same_thread=False)
		conn.text_factory = str
		return conn

	def conn_close(self, conn=None):
		conn.close()

	def conn_trans(func):
		def connection(self, *args, **kwargs):
			self.lock.acquire()
			conn = self.get_conn()
			kwargs['conn'] = conn
			rs = func(self, *args, **kwargs)
			self.conn_close(conn)
			self.lock.release()
			return rs

		return connection

	@conn_trans
	def execute(self, command, method_flag=0, conn=None):
		cu = conn.cursor()
		try:
			if not method_flag:
				cu.execute(command)
			else:
				cu.execute(command[0], command[1])
			conn.commit()
		except sqlite3.IntegrityError, e:
			print e
			return -1
		except Exception, e:
			print e
			return -2
		return 0

	@conn_trans
	def fetchall(self, command="select * from fundvalue", conn=None):
		cu = conn.cursor()
		lists = []
		try:
			cu.execute(command)
			lists = cu.fetchall()
		except Exception, e:
			print e
			pass
		return lists

	@conn_trans
	def fetchallfun(self, command="select name from ", tablename="", conn=None):
		cu = conn.cursor()
		command = command + tablename
		lists = []
		try:
			cu.execute(command)
			lists = cu.fetchall()
		except Exception, e:
			print e
			pass
		return lists




def gen_fund_insert_command(tablename, info_dict):
	"""
	fund insert command
	"""
	tablename = "fundvalue"
	info_list=fund_info_list
	t=[]
	for il in info_list:
		if il in info_dict:
			t.append(info_dict[il])
		else:
			t.append('')
	t=tuple(t)
	command = (r"insert into " +  tablename + " values(?,?,?,?,?)", t)
	print command
	return command

#get the netvalue of a fund on a date
def process_fundInfo(db_fundcode, fundcode, json_fund_value):
	# Error -1
	tr_re = re.compile(r'<tr>(.*?)</tr>')
	item_re = re.compile(r'''<td>(\d{4}-\d{2}-\d{2})</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td>''', re.X)


	jingzhi = '-1'
	for line in tr_re.findall(json_fund_value):
		#print line + '\n'
		match = item_re.match(line)
		if match:
			entry = match.groups()
			#print entry
			date = datetime.datetime.strptime(entry[0], '%Y-%m-%d')
			date = date.strftime("%Y-%m-%d")
			#date = entry[0]
			netValue = float(entry[1])
			netValueAll = float(entry[2])
			dayIncrease = (entry[3])
			buy = entry[4]
			sell = entry[5]
			bonusDay = entry[6]
			if bonusDay != "":
				bonusDay = entry[6]
				#process the bonustofloat
				#webside is unicode for the chinese character
				bonusDay = bonusDay[bonusDay.find(u'现金') + 2:bonusDay.rfind(u'元')]
				print bonusDay
				bonusDay = float(bonusDay)
			else:
				bonusDay = 0.0
			#print date
			#print bonusDay
			jingzhi1 = entry[1]
			jingzhi2 = entry[2]

			#construct the db data
			info_dict = {}
			info_dict.update({fund_info_list[0]: date})
			info_dict.update({fund_info_list[1]: netValue})
			info_dict.update({fund_info_list[2]: netValueAll})
			info_dict.update({fund_info_list[3]: dayIncrease})
			info_dict.update({fund_info_list[4]: bonusDay})

			command = gen_fund_insert_command(fundcode,info_dict)
			#print command
			db_fundcode.execute(command, 1)

def get_pagenum(strfundcode = "000001", strsdate = "1970-1-1", stredate="2020-1-1"):
	url = 'http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code=' + \
		  strfundcode + '&page=' + "1" + '&per=20&sdate=' + strsdate + '&edate=' + stredate
	try:
		print url + '\n'
		response = urllib2.urlopen(url)
	except urllib2.HTTPError, e:
		print e
		urllib_error_tag = True
	except StandardError, e:
		print e
		urllib_error_tag = True
	else:
		urllib_error_tag = False

	if urllib_error_tag == True:
		return '-1'

	json_fund_value = response.read().decode('utf-8')
	records = json_fund_value[
			  json_fund_value.find('records') + 8:json_fund_value.find(',', json_fund_value.find('records'))]
	#print records
	pages = json_fund_value[
			json_fund_value.find('pages') + 6:json_fund_value.find(',', json_fund_value.find('pages'))]
	#print pages
	curpage = json_fund_value[
			json_fund_value.find('curpage') + 8:json_fund_value.find('}', json_fund_value.find('curpage'))]
	#print curpage
	return int(pages)

def get_fundpage(db_fundcode,strfundcode = "000001",pagenum = 0, strsdate = "1970-1-1", stredate="2020-1-1"):

	url = 'http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code=' + \
		  strfundcode + '&page=' + str(pagenum) + '&per=20&sdate=' + strsdate + '&edate=' + stredate
	try:
		print url + '\n'
		response = urllib2.urlopen(url)
	except urllib2.HTTPError, e:
		print e
		urllib_error_tag = True
	except StandardError, e:
		print e
		urllib_error_tag = True
	else:
		urllib_error_tag = False

	if urllib_error_tag == True:
		return '-1'

	json_fund_value = response.read().decode('utf-8')
	# print json_fund_value
	process_fundInfo(db_fundcode,strfundcode,json_fund_value)
	records = json_fund_value[
			  json_fund_value.find('records') + 8:json_fund_value.find(',', json_fund_value.find('records'))]
	print records
	pages = json_fund_value[
			json_fund_value.find('pages') + 6:json_fund_value.find(',', json_fund_value.find('pages'))]
	print pages
	curpage = json_fund_value[
			json_fund_value.find('curpage') + 8:json_fund_value.find('}', json_fund_value.find('curpage'))]
	print curpage
	return '-1'

def get_funInfo(db_fundcode):
	#hardcode test number
	strfundcode = '481009'
	strsdate = '2017-01-01'
	stredate = '2017-01-28'
	pagenum = get_pagenum(strfundcode, strsdate, stredate)
	while(pagenum > 0):
		get_fundpage(db_fundcode,strfundcode,pagenum,strsdate,stredate)
		pagenum = pagenum - 1
	return '-1'

def init_DB():
	print "start..."
	if os.path.isfile("481009.sqlite"):
		os.remove("481009.sqlite")
	command = "create table if not exists fundvalue ( Date TEXT primary key UNIQUE, NetValue FLOAT, AccuValue FLOAT, DayIncrease TEXT, Bonus FLOAT)"
	db_fundcode = SQLiteWraper('481009.sqlite', command)
	print "DB created"
	return db_fundcode

def trans_sdate2datetime(strdate):
	sdatetime = datetime.datetime.strptime(strdate, '%Y-%m-%d')
	return sdatetime
def trans_datetime2str(dt):
	return dt.strftime("%Y-%m-%d")

def test_DB(db):
	print "TEST"
	netvalue = db.fetchall()
	for itemnetvalue in netvalue:
		print trans_datetime2str(itemnetvalue[0])
		if itemnetvalue[0] == '2017-01-03':
			print 'OK'

def main(argv):
	db_fundcode = init_DB()

	get_funInfo(db_fundcode)

	test_DB(db_fundcode)
	sys.exit(0)

if __name__ == "__main__":
	reload(sys)
	sys.setdefaultencoding('utf-8')
	main(sys.argv)


