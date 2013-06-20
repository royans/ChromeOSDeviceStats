#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = 'royans@google.com (Royans K Tharakan)'

from datetime import datetime
import logging
import os
import sys
from time import mktime
from time import gmtime

from apiclient.discovery import build
import gflags
import httplib2
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run

FLAGS = gflags.FLAGS
CLIENT_SECRETS = 'client_secrets.json'
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the APIs Console <https://code.google.com/apis/console>.

""" % os.path.join(os.path.dirname(__file__), CLIENT_SECRETS)

# Set up a Flow object to be used if we need to authenticate.
FLOW = flow_from_clientsecrets(
    CLIENT_SECRETS,
    scope="""https://www.googleapis.com/auth/admin.directory.device.chromeos.readonly""",
    message=MISSING_CLIENT_SECRETS_MESSAGE)

gflags.DEFINE_enum('logging_level', 'ERROR',
                   ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                   'Set the level of logging detail.')

gflags.DEFINE_bool('csv', False, 'Print CSV dump of devices')

# The currently used keys in chromeosdevices
keys = ['serialNumber', 'status', 'lastSync', 'lastEnrollmentTime',
        'orgUnitPath', 'bootMode', 'platformVersion', 'osVersion',
        'firmwareVersion', 'status']

def printDeviceList(devices):
  print ','.join(keys)
  for device in devices:
    temp = []
    for key in keys:
      if key in device:
        temp.append(device[key])
      else:
        temp.append('')
    print ','.join(temp)


def getStats(devices):
  stats = {}
  stats['active'] = 0
  stats['dev'] = 0
  stats['total'] = len(devices)
  stats['versions'] = {}
  stats['platforms'] = {}
  stats['orgUnitPath'] = {}
  stats['enrolled_in_2_days'] = 0
  stats['enrolled_in_7_days'] = 0
  stats['enrolled_in_1_month'] = 0
  stats['enrolled_in_1_year'] = 0

  for device in devices:
    if 'status' in device and device['status'] == 'ACTIVE':
      stats['active']+=1
    if 'bootMode' in device and device['bootMode'] == 'Dev':
      stats['dev']=1

    if 'osVersion' in device:
      version = device['osVersion'].split('.')[0]
      if version in stats['versions']:
        stats['versions'][version]+=1
      else:
        stats['versions'][version]=1

    if 'firmwareVersion' in device:
      platform = device['firmwareVersion'].split('.')[0]
      if platform in stats['platforms']:
        stats['platforms'][platform]+=1
      else:
        stats['platforms'][platform]=1

    if 'orgUnitPath' in device:
      org = device['orgUnitPath'].split('.')[0]
      if org in stats['orgUnitPath']:
        stats['orgUnitPath'][org]+=1
      else:
        stats['orgUnitPath'][org]=1

    if 'lastEnrollmentTime' in device:
      lastEnrollmentTime = mktime(
          datetime.strptime(
              device['lastEnrollmentTime'][0:10],
              '%Y-%m-%d').timetuple())
      now = mktime(gmtime())
      if lastEnrollmentTime > now - 3600*24*2:
        stats['enrolled_in_2_days']+=1
      if lastEnrollmentTime > now - 3600*24*7:
        stats['enrolled_in_7_days']+=1
      if lastEnrollmentTime > now - 3600*24*30:
        stats['enrolled_in_1_month']+=1
      if lastEnrollmentTime > now - 3600*24*365:
        stats['enrolled_in_1_year']+=1
  return stats


def report(devices):
  stats = getStats(devices)
  print "---------------------------------------------------------------------------"
  print "Total devices : %d" % stats['total']
  print "Total active : %d" % stats['active']
  print "Total in Dev mode : %d" % stats['dev']
  print "Total devices enrolled in last 2 days : %d" % stats['enrolled_in_2_days']
  print "Total devices enrolled in last 7 days : %d" % stats['enrolled_in_7_days']
  print "Total devices enrolled in last 1 month : %d" % stats['enrolled_in_1_month']
  print "Total devices enrolled in last 1 year : %d" % stats['enrolled_in_1_year']
  print "Distribution of devices across models: "
  for platform in stats['platforms']:
    print "                          %s : %s " % (platform,
                                                  stats['platforms'][platform])
  print "Distribution of devices across versions: "
  for version in stats['versions']:
    print "                          %s : %s " % (version,
                                                  stats['versions'][version])
  print "Distribution of devices across orgUnits: "
  for org in stats['orgUnitPath']:
    print "                          %s : %s " % (org,
                                                  stats['orgUnitPath'][org])
  print "---------------------------------------------------------------------------"

def main(argv):
  try:
    argv = FLAGS(argv)
  except gflags.FlagsError, e:
    print '%s\\nUsage: %s ARGS\\n%s' % (e, argv[0], FLAGS)
    sys.exit(1)

  logging.getLogger().setLevel(getattr(logging, FLAGS.logging_level))
  storage = Storage('plus.dat')
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run(FLOW, storage)

  http = httplib2.Http()
  http = credentials.authorize(http)
  service = build('admin', 'directory_v1', http=http)
  try:
    result = service.chromeosdevices().list(customerId='my_customer').execute()
    devices = result['chromeosdevices']
    while 'nextPageToken' in result:
      result = service.chromeosdevices().list(customerId='my_customer',
                                              pageToken=result['nextPageToken']).execute()
      devices.append(result['chromeosdevices'])
    if FLAGS.csv:
      printDeviceList(devices)
    else:
      report(devices)

  except AccessTokenRefreshError:
    print ('The credentials have been revoked or expired, please re-run'
      'the application to re-authorize')

if __name__ == '__main__':
  main(sys.argv)
