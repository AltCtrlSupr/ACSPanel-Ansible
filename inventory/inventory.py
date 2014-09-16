#!/usr/bin/env python
from ConfigParser import RawConfigParser
import MySQLdb as mdb
import sys, os, time

try:
	import json
except ImportError:
	import simplejson as json


def listhost(con):
	inventory = {}
	inventory['all']= { 'hosts': [] }
	inventory['_meta']={ 'hostvars' : {} }
	cur = con.cursor()
	cur.execute('SELECT hostname,description,ip FROM server INNER JOIN ip_address ON ip_id=ip_address.id WHERE server.enabled=1 AND ip_address.enabled=1')
	for row in cur.fetchall():
		if row[0] not in inventory['all']['hosts']:
			inventory['all']['hosts'].append(row[0])

	return inventory

def apache2(con,inventory):
	cur = con.cursor()
	cur.execute('SELECT domain.domain,GROUP_CONCAT(domain_alias.domain) AS alias,configuration,cgi,ssi,php,certificate,certificate_key,certificate_chain,certificate_authority,hostname,ip,username,value AS homedir,GROUP_CONCAT(DISTINCT(protected_dir)) AS protected FROM httpd_host INNER JOIN domain ON domain_id=domain.id LEFT JOIN domain AS domain_alias ON domain_alias.parent_domain_id=domain.id INNER JOIN service ON service_id=service.id INNER JOIN server ON server_id=server.id INNER JOIN ip_address ON service.ip_id=ip_address.id INNER JOIN fos_user ON domain.user_id=fos_user.id LEFT JOIN httpd_user ON httpd_host_id=httpd_host.id INNER JOIN config_setting WHERE ( httpd_host.enabled=1 AND domain.enabled=1 AND service.enabled=1 AND server.enabled=1 AND ip_address.enabled=1 AND fos_user.enabled=1 AND (domain_alias.enabled=1 OR domain_alias.enabled IS NULL)) AND setting_key="home_base" GROUP BY httpd_host.id')
	
	rows=cur.fetchall()
	columns=cur.description
	for row in rows:
		host=row[11]
		if not host in inventory['_meta']['hostvars']:
			inventory['_meta']['hostvars'][host]={}
		if not 'apache2' in inventory['_meta']['hostvars'][host]:
			inventory['_meta']['hostvars'][host]['apache2']=[]
		tmprow={}
		for (index, column) in enumerate(row):
			tmprow[columns[index][0]] = column
		inventory['_meta']['hostvars'][host]['apache2'].append(tmprow)

	return inventory
		

def getjson(config):
	try:
		con = mdb.connect(config.get('ansible','host'), config.get('ansible','user'), config.get('ansible','password'), config.get('ansible','db'));
	except mdb.Error, e:
		print "Error %d: %s" % (e.args[0],e.args[1])
		sys.exit(1)

	inventory=listhost(con)
	inventory=apache2(con,inventory)
	
	return inventory


def writecache(config,tmpfile):
	inventory=json.dumps(getjson(config), indent=3)
	cache=open(tmpfile, 'w')
	cache.write(inventory)
	cache.close()

def printcache(tmpfile):
	cache=open(tmpfile, 'r')
	print cache.read()


if __name__ == '__main__':
	config = RawConfigParser()
	config.read([os.path.dirname(os.path.abspath(__file__))+'/inventory_conf.ini'])
	tmpfile=config.get('ansible','tmpfile')
	
	if os.path.isfile(tmpfile):
		ago=time.time()-config.getint('ansible','cachetime')
		if os.path.getmtime(tmpfile)<ago:
			writecache(config,tmpfile)
	else:
		writecache(config,tmpfile)

	printcache(tmpfile)

