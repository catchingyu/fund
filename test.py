# !/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import datetime
import urllib2
import sys
import json
import glob

fund_info_list = ['Date', 'NetValue', 'AccuValue', 'DayIncrease', 'Bonus']


def getEveryDay(begin_date, end_date):
	date_list = []
	begin_date = datetime.datetime.strptime(begin_date, "%Y-%m-%d")
	end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
	while begin_date <= end_date:
		date_str = begin_date.strftime("%Y-%m-%d")
		date_list.append(date_str)
		begin_date += datetime.timedelta(days=1)
	return date_list

def test2():
	# 获取两个日期间的所有日期
	print(getEveryDay('2017-01-01', '2017-01-11'))




def test1():
	bonusDay = "每份派现金0.0097元"
	# process the bonustofloat
	bonusDay=bonusDay[bonusDay.find('现金') + 6:bonusDay.rfind('元')]
	print bonusDay
	bonusDay=float(bonusDay)
	print bonusDay*50


def gen_fund_insert_command(tablename, info_dict):
	"""
	fund insert command
	"""
	info_list = fund_info_list
	t = []
	for il in info_list:
		if il in info_dict:
			t.append(info_dict[il])
		else:
			t.append('')
	t = tuple(t)
	command = (r"insert into " +  tablename + " values(?,?,?,?,?)", t)
	print command
	return command

if __name__=="__main__":
	print "start..."
	info_dict = {}
	info_dict.update({fund_info_list[0]: 1})
	info_dict.update({fund_info_list[1]: 2})
	info_dict.update({fund_info_list[2]: 3})
	info_dict.update({fund_info_list[3]: 4})
	info_dict.update({fund_info_list[4]: 5})
	#gen_fund_insert_command("10000", info_dict)
	test2()
	sys.exit(0)