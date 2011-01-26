#!/usr/bin/env python
# coding=utf8

import dateutil.parser
import time

from boto.s3.key import Key
from boto.s3.deletemarker import DeleteMarker

import logbook

log = logbook.Logger('S3Lock')
debug = log.debug
info = log.info

def has_versioning(bucket):
	vers = bucket.get_versioning_status()
	return 'Versioning' in vers and vers['Versioning'] == 'Enabled'


def get_ordered_versions(bucket, path):
	# check all versions, check if path matches
	# note: DeleteMarkers do not have key attribute, rather a 'name' attribute
	#       these are merged if they are next to each other and drop out on either end
	#       on the version list. however, the last delete marker is kept
	keys = [k for k in bucket.get_all_versions(prefix = path) if hasattr(k, 'key') and k.key == path or k.name == path]

	# sort by timestamp, ascending
	keys.sort(lambda a, b: cmp(dateutil.parser.parse(a.last_modified), dateutil.parser.parse(b.last_modified)))

	return keys


def filter_delete_markers(l):
	for i in l:
		if isinstance(i, DeleteMarker): continue
		yield i


class S3Lock(object):
	def __init__(self, bucket, name, interval = 0.5):
		self.bucket = bucket
		self.name = name
		self.interval = interval
		debug('New lock named %s instantiated on %r' % (self.name, self.bucket))
		assert(has_versioning(bucket))

	def __enter__(self):
		info('Trying to acquire %s' % self.name)

		self.lock_key = Key(self.bucket)
		self.lock_key.key = self.name

		self.lock_key.set_contents_from_string('')
		# version id of self.lock_key is now the one we set
		debug('Uploaded lock request, version id %s' % self.lock_key.version_id)

		while True:
			keys = list(filter_delete_markers(get_ordered_versions(self.bucket, self.lock_key.key)))
			debug('Lock-queue: *%s' % ', '.join((k.version_id for k in keys)))

			if keys[0].version_id == self.lock_key.version_id:
				info('Acquired %s' % self.name)
				break

			debug('Could not acquire lock, sleeping for %s seconds' % self.interval)
			time.sleep(self.interval)

		# we hold the lock, code runs

	def __exit__(self, type, value, traceback):
		# release the lock
		self.lock_key.delete()
		info('Released lock %s on %r' % (self.name, self.bucket))


if '__main__' == __name__:
	from secretkey import *
	from boto.s3.connection import S3Connection
	import sys

	conn = S3Connection(key_id, access_key)
	bucketname = 'mbr-locktest_2'

	# get bucket
	bucket = conn.get_bucket(bucketname)

	with S3Lock(bucket, 'my_amazing_lock'):
		print "RUNNING CRITICAL SECTION"
		print "Press enter to end critical section"
		sys.stdin.readline()
