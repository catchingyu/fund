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
import getallfund

returnvalue_info_list = ['Date', 'InvestRate', 'SellDate', 'SellNetValue', 'SellCost', 'SellTotalMoney', 'TotalInvestMoney']
sellcost = 0.015
buycost = 0.0012
global_fundcode = '481009'


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





def trans_sdate2datetime(strdate):
	sdatetime = datetime.datetime.strptime(strdate, '%Y-%m-%d')
	return sdatetime

def trans_datetime2str(dt):
	return dt.strftime("%Y-%m-%d")

def time_cmp(first_time, second_time):
	print(first_time)
	print(second_time)
	return int(first_time) - int(second_time)


def init_DB(fundcode):
	dbname = fundcode + '.sqlite'
	command = "create table if not exists fundvalue ( Date TEXT primary key UNIQUE, NetValue FLOAT, AccuValue FLOAT, DayIncrease TEXT, Bonus FLOAT)"
	db_fundcode = SQLiteWraper(dbname, command)
	#print "DB init"
	return db_fundcode

#returnvalue_info_list = ['Date', 'InvestRate', 'SellDate', 'SellNetValue', 'SellCost', 'SellTotalMoney', 'TotalInvestMoney']
def get_resulttablename(fundcode):
	return 'returnrate'

def init_ResultDB(fundcode, period):
	dbname = fundcode + '-' + str(period) + 'returnrate.sqlite'
	#if os.path.isfile(dbname):
		#os.remove(dbname)
	command = "create table if not exists returnrate ( Date TEXT primary key UNIQUE, InvestRate FLOAT, SellDate TEXT, SellNetValue FLOAT, " \
			  "SellCost FLOAT, SellTotalMoney FLOAT,  TotalInvestMoney FLOAT)"
	db_fundcode = SQLiteWraper(dbname, command)
	#print "init_ResultDB init"
	return db_fundcode

def gen_resultdb_insert_command(tablename, info_dict):
	"""
	fund insert command
	"""
	info_list=returnvalue_info_list
	t=[]
	for il in info_list:
		if il in info_dict:
			t.append(info_dict[il])
		else:
			t.append('')
	t=tuple(t)
	command = (r"insert into " +  tablename + " values(?,?,?,?,?,?,?)", t)
	return command

def cal_interest(fundcode, startdate, enddate, freq, money):
	db = init_DB(fundcode)
	netvalue = db.fetchall()
	#print len(netvalue)
	#startdate = '2017-01-12'
	#sdatetime = trans_sdate2datetime(startdate)
	#sdatetime = sdatetime + datetime.timedelta(days=2)
	#sdatetime = trans_datetime2str(sdatetime)
	#print sdatetime
	numoffund = 0
	sellnetvalue = 0
	selldate = 0
	totalinvestmoney = 0
	interest = 0
	returnstartdate = trans_datetime2str(startdate)

	#list is from the enddate to the startdate
	#print netvalue
	netvalue = sorted(netvalue, key=lambda x: x[0])
	#print netvalue
	"""
	fetch the netvalue of specified day, caculate the numoffunds
	fetch the next day = day + freq
	sum the numoffunds at the end of enddate
	cal interest by adding the cost(buy and sell) and the possible interest
	the possible interest is the numoffunds on the interest day * interest rate (get all the interest day since it is few)
	"""

	for itemnetvalue in netvalue:
		#print trans_datetime2str(itemnetvalue[0])
		#tranfer the date to datetime object and set it back to seconds to compare
		itemdate = trans_sdate2datetime(itemnetvalue[0])
		if startdate == itemdate:
			#get the netvalue of the day
			#do not consider the money buy the fund
			#print startdate
			numoffund += money / itemnetvalue[1]
			totalinvestmoney += money
			#print 'netvalue of the date is %f, numoffund is %f ' % (itemnetvalue[1], money/itemnetvalue[1])

			startdate = startdate + datetime.timedelta(days=freq)

			selldate = startdate
			sellnetvalue = itemnetvalue[1]
		if itemdate > startdate:
			#should not be here , if here due to the holiday
			#print itemdate
			#skip the invest at the day
			startdate = startdate + datetime.timedelta(days=freq)
		if itemdate >= enddate:
			break

		if itemnetvalue[4] != 0:
			interest += numoffund * itemnetvalue[4]
	#print netvalue
	#print numoffund
	#print selldate
	selldate = trans_datetime2str(selldate)
	#print 'sellnetvalue is %f' % (sellnetvalue)
	returnofmoney = numoffund * sellnetvalue
	#adjust money
	#print 'rough cost of buy and sell is %f' % (returnofmoney * (sellcost + buycost))
	returnofmoney = returnofmoney * (1 - sellcost - buycost)
	#interest by the money
	#print 'final interest is %f' % (interest)
	returnofmoney = returnofmoney + interest
	investrate = returnofmoney / totalinvestmoney
	returnlist = []
	returnlist.append(returnstartdate)
	returnlist.append(investrate)

	returnlist.append(selldate)
	returnlist.append(sellnetvalue)
	returnlist.append((returnofmoney * (sellcost + buycost)))
	returnlist.append(returnofmoney)
	returnlist.append(totalinvestmoney)
	#print returnlist
	return returnlist

def cal_periodtimereturnrate(fundcode, startdate, money, periodtime,freq = 7):
	startdate = trans_sdate2datetime(startdate)
	enddate = startdate + datetime.timedelta(days=periodtime)
	list = cal_interest(fundcode, startdate, enddate, freq, money=1000)
	return list

def construct_startdatelist(fundcode):
	db = init_DB(fundcode)
	netvalue = db.fetchall()
	netvalue = sorted(netvalue, key=lambda x: x[0])
	startdatelist = []
	for item in netvalue:
		startdatelist.append(item[0])
	return startdatelist

def cal_returnvalue(fundcode = '481009', startdate = '2017-01-03', money = 1000, periodtime = 365, freq = 7):
	print "cal_turenvalue " + ' ' + fundcode + ' ' + startdate + ' ' + str(periodtime) + ' ' + str(money) + ' ' + str(freq)
	resultDB = init_ResultDB(fundcode, periodtime)
	liststartdate = construct_startdatelist(fundcode)
	for startdate in liststartdate:
		print startdate
		list = cal_periodtimereturnrate(fundcode, startdate, money, periodtime,freq)
		# construct the db data
		info_dict = {}
		#len(list) == 7 , but range is [) contains 7
		for i in range(0, len(list)):
			info_dict.update({returnvalue_info_list[i]: list[i]})
		#print info_dict
		tablename = get_resulttablename(fundcode)
		command = gen_resultdb_insert_command(tablename, info_dict)
		#print command
		resultDB.execute(command, 1)
	return

def cal_possibility(fundcode,periodtime):
	resultDB = init_ResultDB(fundcode, periodtime)
	alldata = resultDB.fetchall("select * from returnrate")
	numofalldata = len(alldata)
	numofprofit = 0
	numofmax3 = 0
	numofmax7 = 0
	for item in alldata:
		#print item[1]
		if item[1] > 1 :
			numofprofit += 1
		if item[1] > 1.3 :
			numofmax3 += 1
		if item[1] > 1.7 :
			numofmax7 += 1
	#print numofprofit
	print (periodtime/365)
	print float(numofprofit)/numofalldata
	print float(numofmax3)/numofalldata
	print float(numofmax7) / numofalldata
	#print profitrate


def batch_cal(fundcode):
	#start date is no use, since start date is the date in the history net table
	cal_returnvalue(fundcode, '2017-01-03', 1000, 365,     7)
	cal_returnvalue(fundcode, '2017-01-03', 1000, 365 * 2, 7)
	cal_returnvalue(fundcode, '2017-01-03', 1000, 365 * 3, 7)
	cal_returnvalue(fundcode, '2017-01-03', 1000, 365 * 4, 7)
	cal_returnvalue(fundcode, '2017-01-03', 1000, 365 * 5, 7)
	cal_returnvalue(fundcode, '2017-01-03', 1000, 365 * 6, 7)
	cal_returnvalue(fundcode, '2017-01-03', 1000, 365 * 7, 7)
	cal_returnvalue(fundcode, '2017-01-03', 1000, 365 * 8, 7)
	cal_returnvalue(fundcode, '2017-01-03', 1000, 365 * 9, 7)
	cal_returnvalue(fundcode, '2017-01-03', 1000, 365 * 10, 7)

def batch_cal_possibility(fundcode):
	cal_possibility(fundcode, 365*2)
	cal_possibility(fundcode, 365*3)
	cal_possibility(fundcode, 365*4)
	cal_possibility(fundcode, 365*5)
	cal_possibility(fundcode, 365*6)
	cal_possibility(fundcode, 365*7)
	cal_possibility(fundcode, 365*8)
	cal_possibility(fundcode, 365*9)
	cal_possibility(fundcode, 365*10)

#after import getallfund.py
def main(argv):
	getallfund.getallfund(global_fundcode)
	batch_cal(global_fundcode)
	#cal_possibility('481009', 365*2)
	batch_cal_possibility(global_fundcode)
	sys.exit(0)

if __name__ == "__main__":
	reload(sys)
	sys.setdefaultencoding('utf-8')
	main(sys.argv)


