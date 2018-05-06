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

#Usage need to be redefine as input of the function
def usage():
	print 'fund-rank.py usage:'
	print '\tpython fund.py start-date end-date fund-code=none\n'
	print '\tdate format ****-**-**'
	print '\t\tstart-date must before end-date'
	print '\tfund-code default none'
	print '\t\tif not input, get top 20 funds from all more than 6400 funds'
	print '\t\telse get that fund\'s rate of rise\n'
	print '\teg:\tpython fund-rank.py 2017-03-01 2017-03-25'
	print '\teg:\tpython fund-rank.py 2017-03-01 2017-03-25 377240'

#get the netvalue of a fund on a date
def get_jingzhi(strfundcode, strdate):
	try:
		url = 'http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code=' + \
		      strfundcode + '&page=1&per=20&sdate=' + strdate + '&edate=' + strdate
		#print url + '\n'
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
	#print json_fund_value

	tr_re = re.compile(r'<tr>(.*?)</tr>')
	item_re = re.compile(r'''<td>(\d{4}-\d{2}-\d{2})</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?></td>''', re.X)

	# Error -1
	jingzhi = '-1'
	for line in tr_re.findall(json_fund_value):
		#print line + '\n'
		match = item_re.match(line)
		if match:
			entry = match.groups()
			date = datetime.datetime.strptime(entry[0], '%Y-%m-%d')
			#jingzhi = entry[2]
			# result.append([date, float(entry[1]), entry[3]])
			jingzhi1 = entry[1]
			jingzhi2 = entry[2]
			#print jingzhi2
			
			if jingzhi2.strip() == '':
				# 040028
				# Date	ValuePerWan
				# 2017-01-06	1.4414
				# 2017-01-05	1.4369
				jingzhi = '-1'
			elif jingzhi2.find('%') > -1:
				# 040003
				# Date          ValuePerWan 7DayInterest
				# 2017-03-27	1.1149	3.9450%
				# 2017-03-26*	2.2240	3.8970%
				jingzhi = '-1'
			elif float(jingzhi1) > float(jingzhi2):
				# 502015
				# Date          NetValue AccuNet DayIncrease Buy Sell Bonus
				# 2017-03-27	0.6980	0.3785	-2.24%
				# 2017-03-24	0.7140	0.3945	5.15%
				jingzhi = entry[1]
			else:
				#
				# Date          NetValue AccuNet DayIncrease Buy Sell Bonus
				# 2017-03-28	1.7720	1.7720	-0.23%
				# 2017-03-27	1.7761	1.7761	-0.43%
				jingzhi = entry[2]

	return jingzhi
	
def main(argv):
	# Top 50
	gettopnum = 50
	
	# Usage Validation
	#print sys.argv
	#if len(sys.argv) != 3 and len(sys.argv) != 4:
		#usage()
		#sys.exit(1)
	
	# 1.1 Date
	#strsdate = sys.argv[1]
	#stredate = sys.argv[2]
	strsdate = '2018-04-02'
	stredate = '2018-04-03'


	#Formulate the time
	strtoday = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')
	tdatetime = datetime.datetime.strptime(strtoday, '%Y-%m-%d')
	#print tdatetime
	
	# Adjust Start Time
	#print strsdate
	sdatetime = datetime.datetime.strptime(strsdate, '%Y-%m-%d')
	sdatetime.isoweekday()
	if sdatetime.isoweekday() == 7:
		sdatetime = sdatetime + datetime.timedelta(days=-2)
	elif sdatetime.isoweekday() == 6:
		sdatetime = sdatetime + datetime.timedelta(days=-1)

	strsdate = datetime.datetime.strftime(sdatetime, '%Y-%m-%d')
	#print strsdate

	# Adjust End Time
	#print stredate
	edatetime = datetime.datetime.strptime(stredate, '%Y-%m-%d')
	edatetime.isoweekday()
	if edatetime.isoweekday() == 7:
		edatetime = edatetime + datetime.timedelta(days=-2)
	elif edatetime.isoweekday() == 6:
		edatetime = edatetime + datetime.timedelta(days=-1)

	stredate = datetime.datetime.strftime(edatetime, '%Y-%m-%d')
	#print stredate

	# Validate the Start time and End time
	if edatetime <= sdatetime or tdatetime <= sdatetime or tdatetime <= edatetime:
		print 'date input error!\n'
		usage()
		sys.exit(1)

	
	# 2 Check the fund code
	#if len(sys.argv) == 4:
		#strfundcode = sys.argv[3]
	#hard code here
	if 1:
		#hard code the fund code as GongYinHuShen
		strfundcode = '481009'
		jingzhimin = get_jingzhi(strfundcode, strsdate)
		jingzhimax = get_jingzhi(strfundcode, stredate)
		
		if jingzhimin == '-1' or jingzhimax == '-1' or jingzhimin.strip() == '' or jingzhimax.strip() == '':
			print 'maybe date input error!\n'
			usage()
			sys.exit(1)
		
		jingzhidif = float(jingzhimax) - float(jingzhimin)
		jingzhirise = float('%.2f' %(jingzhidif * 100 / float(jingzhimin)))
	
		print 'fund:' + strfundcode + '\n'
		print strsdate + '\t' + stredate + '\t������' + '\t' + '������'
		print jingzhimin + '\t\t' + jingzhimax + '\t\t' + str(jingzhidif) + '\t' + str(jingzhirise) + '%'
		sys.exit(0)
	
		
	# 3Fetch the Fundlist

	
	fundlist_files = glob.glob('fundlist-*.txt')
	if (len(fundlist_files) > 0) :
		# print fundlist_files[0]
		# read the funlist file
		file_object = open(fundlist_files[0], 'r')
		try:
			all_funds_txt = file_object.read()
			#print all_funds_txt
		finally:
			file_object.close()
	else:
		# get the funlist code from eastmoney
		response_all_funds = urllib2.urlopen('http://fund.eastmoney.com/js/fundcode_search.js')
		all_funds_txt = response_all_funds.read()
		#save the file
		file_object = open('fundlist-' + strtoday + '.txt', 'w')
		try:
			file_object.write(all_funds_txt)
			#print all_funds_txt
		finally:
			file_object.close()

	all_funds_txt = all_funds_txt[all_funds_txt.find('=')+2:all_funds_txt.rfind(';')]
	all_funds_list = json.loads(all_funds_txt.decode('utf-8'))
	 
	print 'start:'
	print datetime.datetime.now()
	print 'funds sum:' + str(len(all_funds_list))
	
	# 4 Process each fund in the list
	for fund in all_funds_list:
		print 'process fund:\t' + fund[0].encode('gb18030') + '\t' + fund[2].encode('gb18030')
		strfundcode = fund[0]
		# get the net value
		jingzhimin = get_jingzhi(strfundcode, strsdate)
		jingzhimax = get_jingzhi(strfundcode, stredate)
		
		if jingzhimin == '-1' or jingzhimax == '-1' or jingzhimin.strip() == '' or jingzhimax.strip() == '':
			# Some fund cannot be get, set it zero, such as 000002
			# 040028  maybe empty
			jingzhimin = '0'
			jingzhimax = '0'
			jingzhidif = 0
			jingzhirise = 0
			
			'''
			print 'maybe date input error!\n'
			usage()
			sys.exit(1)
			'''
		elif jingzhimin.find('%') > -1 or jingzhimax.find('%') > -1:
			# 000037
			#
			# 2016-03-01	0.7740	2.7010%	2.7010%
			jingzhidif = 0
			jingzhirise = 0
		else:
			# caculate
			jingzhidif = float('%.4f' %(float(jingzhimax) - float(jingzhimin)))
			jingzhirise = float('%.2f' %(jingzhidif * 100 / float(jingzhimin)))
		
		# add in the list
		fund.append(jingzhimin)
		fund.append(jingzhimax)
		fund.append(jingzhidif)
		fund.append(jingzhirise)
		
		# speed control
		#time.sleep(1)
				
		
	# 5 ���� д�ļ� ��ӡ���
	fileobject = open('result_' + strsdate + '_' + stredate + '.txt', 'w')
	
	# ����������������
	all_funds_list.sort(key=lambda fund: fund[8],  reverse=True)
	strhead =  '����' + '\t' + '����' + '\t\t' + '����' + '\t\t' + '����' + '\t\t' + \
	strsdate + '\t' + stredate + '\t' + '������' + '\t' + '������' + '\n'
	print strhead
	fileobject.write(strhead)
	
	# ��ӡ
	for index in range(len(all_funds_list)):
		#print all_funds_list[index]
		strcontent = str(index+1) + '\t' + all_funds_list[index][0].encode('gb18030') + '\t' + all_funds_list[index][2].encode('gb18030') + \
		'\t\t' + all_funds_list[index][3].encode('gb18030') + '\t\t' + all_funds_list[index][5].encode('gb18030') + '\t\t' + \
		all_funds_list[index][6].encode('gb18030') + '\t\t' + str(all_funds_list[index][7]) + '\t' + str(all_funds_list[index][8]) + '%\n'
		print strcontent
		fileobject.write(strcontent)
		
		if index >= gettopnum:
			break;
		
	fileobject.close()
	
	print 'end:'
	print datetime.datetime.now()
	
	sys.exit(0)
	
if __name__ == "__main__":	
	reload(sys)
	sys.setdefaultencoding('utf-8')
	
	main(sys.argv)

	
