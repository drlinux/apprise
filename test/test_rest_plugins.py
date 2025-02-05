# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Chris Caron <lead2gold@gmail.com>
# All rights reserved.
#
# This code is licensed under the MIT License.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files(the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and / or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions :
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import six
import requests
import mock
from json import dumps
from random import choice
from string import ascii_uppercase as str_alpha
from string import digits as str_num

from apprise import plugins
from apprise import NotifyType
from apprise import NotifyBase
from apprise import Apprise
from apprise import AppriseAsset
from apprise.common import NotifyFormat
from apprise.common import OverflowMode

# Disable logging for a cleaner testing output
import logging
logging.disable(logging.CRITICAL)

# a test UUID we can use
UUID4 = '8b799edf-6f98-4d3a-9be7-2862fb4e5752'

# Some exception handling we'll use
REQUEST_EXCEPTIONS = (
    requests.ConnectionError(
        0, 'requests.ConnectionError() not handled'),
    requests.RequestException(
        0, 'requests.RequestException() not handled'),
    requests.HTTPError(
        0, 'requests.HTTPError() not handled'),
    requests.ReadTimeout(
        0, 'requests.ReadTimeout() not handled'),
    requests.TooManyRedirects(
        0, 'requests.TooManyRedirects() not handled'),
)

TEST_URLS = (
    ##################################
    # NotifyBoxcar
    ##################################
    ('boxcar://', {
        # invalid secret key
        'instance': TypeError,
    }),
    # A a bad url
    ('boxcar://:@/', {
        'instance': TypeError,
    }),
    # No secret specified
    ('boxcar://%s' % ('a' * 64), {
        'instance': TypeError,
    }),
    # An invalid access and secret key specified
    ('boxcar://access.key/secret.key/', {
        # Thrown because there were no recipients specified
        'instance': TypeError,
    }),
    # Provide both an access and a secret
    ('boxcar://%s/%s' % ('a' * 64, 'b' * 64), {
        'instance': plugins.NotifyBoxcar,
        'requests_response_code': requests.codes.created,
    }),
    # Test without image set
    ('boxcar://%s/%s?image=True' % ('a' * 64, 'b' * 64), {
        'instance': plugins.NotifyBoxcar,
        'requests_response_code': requests.codes.created,
        # don't include an image in Asset by default
        'include_image': False,
    }),
    ('boxcar://%s/%s?image=False' % ('a' * 64, 'b' * 64), {
        'instance': plugins.NotifyBoxcar,
        'requests_response_code': requests.codes.created,
    }),
    # our access, secret and device are all 64 characters
    # which is what we're doing here
    ('boxcar://%s/%s/@tag1/tag2///%s/?to=tag3' % (
        'a' * 64, 'b' * 64, 'd' * 64), {
        'instance': plugins.NotifyBoxcar,
        'requests_response_code': requests.codes.created,
    }),
    # An invalid tag
    ('boxcar://%s/%s/@%s' % ('a' * 64, 'b' * 64, 't' * 64), {
        'instance': plugins.NotifyBoxcar,
        'requests_response_code': requests.codes.created,
    }),
    ('boxcar://%s/%s/' % ('a' * 64, 'b' * 64), {
        'instance': plugins.NotifyBoxcar,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('boxcar://%s/%s/' % ('a' * 64, 'b' * 64), {
        'instance': plugins.NotifyBoxcar,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('boxcar://%s/%s/' % ('a' * 64, 'b' * 64), {
        'instance': plugins.NotifyBoxcar,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyD7Networks
    ##################################
    ('d7sms://', {
        # No target numbers
        'instance': TypeError,
    }),
    ('d7sms://:@/', {
        # invalid user/pass
        'instance': TypeError,
    }),
    ('d7sms://user:pass@{}/{}/{}'.format('1' * 10, '2' * 15, 'a' * 13), {
        # invalid target numbers
        'instance': TypeError,
    }),
    ('d7sms://user:pass@{}?batch=yes'.format('3' * 14), {
        # valid number
        'instance': plugins.NotifyD7Networks,
    }),
    ('d7sms://user:pass@{}?batch=yes'.format('7' * 14), {
        # valid number
        'instance': plugins.NotifyD7Networks,
        # Test what happens if a batch send fails to return a messageCount
        'requests_response_text': {
            'data': {
                'messageCount': 0,
            },
        },
        # Expected notify() response
        'notify_response': False,
    }),
    ('d7sms://user:pass@{}?batch=yes&to={}'.format('3' * 14, '6' * 14), {
        # valid number
        'instance': plugins.NotifyD7Networks,
    }),
    ('d7sms://user:pass@{}?batch=yes&from=apprise'.format('3' * 14), {
        # valid number, utilizing the optional from= variable
        'instance': plugins.NotifyD7Networks,
    }),
    ('d7sms://user:pass@{}?batch=yes&source=apprise'.format('3' * 14), {
        # valid number, utilizing the optional source= variable (same as from)
        'instance': plugins.NotifyD7Networks,
    }),
    ('d7sms://user:pass@{}?priority=invalid'.format('3' * 14), {
        # valid number; invalid priority
        'instance': plugins.NotifyD7Networks,
    }),
    ('d7sms://user:pass@{}?priority=3'.format('3' * 14), {
        # valid number; adjusted priority
        'instance': plugins.NotifyD7Networks,
    }),
    ('d7sms://user:pass@{}?priority=high'.format('3' * 14), {
        # valid number; adjusted priority (string supported)
        'instance': plugins.NotifyD7Networks,
    }),
    ('d7sms://user:pass@{}?batch=no'.format('3' * 14), {
        # valid number - no batch
        'instance': plugins.NotifyD7Networks,
    }),
    ('d7sms://user:pass@{}'.format('3' * 14), {
        'instance': plugins.NotifyD7Networks,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('d7sms://user:pass@{}'.format('3' * 14), {
        'instance': plugins.NotifyD7Networks,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyDiscord
    ##################################
    ('discord://', {
        'instance': None,
    }),
    # No webhook_token specified
    ('discord://%s' % ('i' * 24), {
        'instance': TypeError,
    }),
    # Provide both an webhook id and a webhook token
    ('discord://%s/%s' % ('i' * 24, 't' * 64), {
        'instance': plugins.NotifyDiscord,
        'requests_response_code': requests.codes.no_content,
    }),
    # Provide a temporary username
    ('discord://l2g@%s/%s' % ('i' * 24, 't' * 64), {
        'instance': plugins.NotifyDiscord,
        'requests_response_code': requests.codes.no_content,
    }),

    # Enable other options

    # DEPRICATED reference to Thumbnail
    ('discord://%s/%s?format=markdown&footer=Yes&thumbnail=Yes' % (
        'i' * 24, 't' * 64), {
            'instance': plugins.NotifyDiscord,
            'requests_response_code': requests.codes.no_content,
    }),
    ('discord://%s/%s?format=markdown&footer=Yes&thumbnail=No' % (
        'i' * 24, 't' * 64), {
            'instance': plugins.NotifyDiscord,
            'requests_response_code': requests.codes.no_content,
    }),

    # thumbnail= is depricated and image= is the proper entry
    ('discord://%s/%s?format=markdown&footer=Yes&image=Yes' % (
        'i' * 24, 't' * 64), {
            'instance': plugins.NotifyDiscord,
            'requests_response_code': requests.codes.no_content,
            # don't include an image by default
            'include_image': False,
    }),
    ('discord://%s/%s?format=markdown&footer=Yes&image=No' % (
        'i' * 24, 't' * 64), {
            'instance': plugins.NotifyDiscord,
            'requests_response_code': requests.codes.no_content,
            # don't include an image by default
            'include_image': True,
    }),
    ('https://discordapp.com/api/webhooks/{}/{}'.format(
        '0' * 10, 'B' * 40), {
            # Native URL Support, take the discord URL and still build from it
            'instance': plugins.NotifyDiscord,
            'requests_response_code': requests.codes.no_content,
    }),
    ('discord://%s/%s?format=markdown&avatar=No&footer=No' % (
        'i' * 24, 't' * 64), {
            'instance': plugins.NotifyDiscord,
            'requests_response_code': requests.codes.no_content,
    }),
    # different format support
    ('discord://%s/%s?format=markdown' % ('i' * 24, 't' * 64), {
        'instance': plugins.NotifyDiscord,
        'requests_response_code': requests.codes.no_content,
    }),
    ('discord://%s/%s?format=text' % ('i' * 24, 't' * 64), {
        'instance': plugins.NotifyDiscord,
        'requests_response_code': requests.codes.no_content,
    }),
    # Test without image set
    ('discord://%s/%s' % ('i' * 24, 't' * 64), {
        'instance': plugins.NotifyDiscord,
        'requests_response_code': requests.codes.no_content,
        # don't include an image by default
        'include_image': False,
    }),
    # An invalid url
    ('discord://:@/', {
        'instance': None,
    }),
    ('discord://%s/%s/' % ('a' * 24, 'b' * 64), {
        'instance': plugins.NotifyDiscord,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('discord://%s/%s/' % ('a' * 24, 'b' * 64), {
        'instance': plugins.NotifyDiscord,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('discord://%s/%s/' % ('a' * 24, 'b' * 64), {
        'instance': plugins.NotifyDiscord,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyEmby
    ##################################
    # Insecure Request; no hostname specified
    ('emby://', {
        'instance': None,
    }),
    # Secure Emby Request; no hostname specified
    ('embys://', {
        'instance': None,
    }),
    # No user specified
    ('emby://localhost', {
        # Missing a username
        'instance': TypeError,
    }),
    ('emby://:@/', {
        'instance': None,
    }),
    # Valid Authentication
    ('emby://l2g@localhost', {
        'instance': plugins.NotifyEmby,
        # our response will be False because our authentication can't be
        # tested very well using this matrix.  It will resume in
        # in test_notify_emby_plugin()
        'response': False,
    }),
    ('embys://l2g:password@localhost', {
        'instance': plugins.NotifyEmby,
        # our response will be False because our authentication can't be
        # tested very well using this matrix.  It will resume in
        # in test_notify_emby_plugin()
        'response': False,
    }),
    # The rest of the emby tests are in test_notify_emby_plugin()

    ##################################
    # NotifyFaast
    ##################################
    ('faast://', {
        'instance': None,
    }),
    # Auth Token specified
    ('faast://%s' % ('a' * 32), {
        'instance': plugins.NotifyFaast,
    }),
    ('faast://%s' % ('a' * 32), {
        'instance': plugins.NotifyFaast,
        # don't include an image by default
        'include_image': False,
    }),
    ('faast://:@/', {
        'instance': None,
    }),
    ('faast://%s' % ('a' * 32), {
        'instance': plugins.NotifyFaast,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('faast://%s' % ('a' * 32), {
        'instance': plugins.NotifyFaast,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('faast://%s' % ('a' * 32), {
        'instance': plugins.NotifyFaast,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyFlock
    ##################################
    # No token specified
    ('flock://', {
        'instance': None,
    }),
    # Provide a token
    ('flock://%s' % ('t' * 24), {
        'instance': plugins.NotifyFlock,
    }),
    # Image handling
    ('flock://%s?image=True' % ('t' * 24), {
        'instance': plugins.NotifyFlock,
    }),
    ('flock://%s?image=False' % ('t' * 24), {
        'instance': plugins.NotifyFlock,
    }),
    ('flock://%s?image=True' % ('t' * 24), {
        'instance': plugins.NotifyFlock,
        # Run test when image is set to True, but one couldn't actually be
        # loaded from the Asset Object.
        'include_image': False,
    }),
    # Test to=
    ('flock://%s?to=u:%s&format=markdown' % ('i' * 24, 'u' * 12), {
        'instance': plugins.NotifyFlock,
    }),
    # Provide markdown format
    ('flock://%s?format=markdown' % ('i' * 24), {
        'instance': plugins.NotifyFlock,
    }),
    # Provide text format
    ('flock://%s?format=text' % ('i' * 24), {
        'instance': plugins.NotifyFlock,
    }),
    # Native URL Support, take the slack URL and still build from it
    ('https://api.flock.com/hooks/sendMessage/{}/'.format('i' * 24), {
        'instance': plugins.NotifyFlock,
    }),
    # Bot API presumed if one or more targets are specified
    # Provide markdown format
    ('flock://%s/u:%s?format=markdown' % ('i' * 24, 'u' * 12), {
        'instance': plugins.NotifyFlock,
    }),
    # Bot API presumed if one or more targets are specified
    # Provide text format
    ('flock://%s/u:%s?format=html' % ('i' * 24, 'u' * 12), {
        'instance': plugins.NotifyFlock,
    }),
    # Bot API presumed if one or more targets are specified
    # u: is optional
    ('flock://%s/%s?format=text' % ('i' * 24, 'u' * 12), {
        'instance': plugins.NotifyFlock,
    }),
    # Bot API presumed if one or more targets are specified
    # Multi-entries
    ('flock://%s/g:%s/u:%s?format=text' % ('i' * 24, 'g' * 12, 'u' * 12), {
        'instance': plugins.NotifyFlock,
    }),
    # Bot API presumed if one or more targets are specified
    # Multi-entries using @ for user and # for channel
    ('flock://%s/#%s/@%s?format=text' % ('i' * 24, 'g' * 12, 'u' * 12), {
        'instance': plugins.NotifyFlock,
    }),
    # Bot API presumed if one or more targets are specified
    # has bad entry
    ('flock://%s/g:%s/u:%s?format=text' % ('i' * 24, 'g' * 12, 'u' * 10), {
        'instance': plugins.NotifyFlock,
    }),
    # Bot API presumed if one or more targets are specified
    # has all bad entries
    ('flock://%s/g:%s/u:%s?format=text' % ('i' * 24, 'g' * 14, 'u' * 10), {
        'instance': TypeError,
    }),
    # Provide invalid token
    ('flock://%s?format=text' % ('i' * 10), {
        'instance': TypeError,
    }),
    # An invalid url
    ('flock://:@/', {
        'instance': None,
    }),
    # Error Testing
    ('flock://%s/g:%s/u:%s?format=text' % ('i' * 24, 'g' * 12, 'u' * 10), {
        'instance': plugins.NotifyFlock,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('flock://%s/' % ('t' * 24), {
        'instance': plugins.NotifyFlock,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('flock://%s/' % ('t' * 24), {
        'instance': plugins.NotifyFlock,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('flock://%s/' % ('t' * 24), {
        'instance': plugins.NotifyFlock,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyGitter
    ##################################
    ('gitter://', {
        'instance': None,
    }),
    ('gitter://:@/', {
        'instance': None,
    }),
    # Token specified but it's invalid
    ('gitter://%s' % ('a' * 12), {
        'instance': TypeError,
    }),
    # Token specified but no channel - still okay
    ('gitter://%s' % ('a' * 40), {
        'instance': plugins.NotifyGitter,
        # our notify() will however return a False since it can't
        # notify anything
        'response': False,
    }),
    # Token + channel
    ('gitter://%s/apprise' % ('a' * 40), {
        'instance': plugins.NotifyGitter,
        # don't include an image by default
        'include_image': False,
        # This actually fails because the first thing we do is generate a list
        # of channel's that we are a part of, and test_rest_plugins() won't
        # be able to fulfill this task.  Hence we'll get a list of no channels
        # and having nothing to notify will give us a failed state:
        'response': False,
    }),
    # include image in post
    ('gitter://%s/apprise?image=Yes' % ('a' * 40), {
        'instance': plugins.NotifyGitter,
        'response': False,
    }),
    # Don't include image in post (this is the default anyway)
    ('gitter://%s/apprise?image=No' % ('a' * 40), {
        'instance': plugins.NotifyGitter,
        'response': False,
    }),
    ('gitter://%s' % ('a' * 40), {
        'instance': plugins.NotifyGitter,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('gitter://%s' % ('a' * 40), {
        'instance': plugins.NotifyGitter,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('gitter://%s' % ('a' * 40), {
        'instance': plugins.NotifyGitter,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyGotify
    ##################################
    ('gotify://', {
        'instance': None,
    }),
    # No token specified
    ('gotify://hostname', {
        'instance': TypeError,
    }),
    # Provide a hostname and token
    ('gotify://hostname/%s' % ('t' * 16), {
        'instance': plugins.NotifyGotify,
    }),
    # Provide a priority
    ('gotify://hostname/%s?priority=high' % ('i' * 16), {
        'instance': plugins.NotifyGotify,
    }),
    # Provide an invalid priority
    ('gotify://hostname:8008/%s?priority=invalid' % ('i' * 16), {
        'instance': plugins.NotifyGotify,
    }),
    # An invalid url
    ('gotify://:@/', {
        'instance': None,
    }),
    ('gotify://hostname/%s/' % ('t' * 16), {
        'instance': plugins.NotifyGotify,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('gotifys://localhost/%s/' % ('t' * 16), {
        'instance': plugins.NotifyGotify,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('gotify://localhost/%s/' % ('t' * 16), {
        'instance': plugins.NotifyGotify,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyIFTTT - If This Than That
    ##################################
    ('ifttt://', {
        'instance': None,
    }),
    # No User
    ('ifttt://EventID/', {
        'instance': TypeError,
    }),
    ('ifttt://:@/', {
        'instance': None,
    }),
    # A nicely formed ifttt url with 1 event and a new key/value store
    ('ifttt://WebHookID@EventID/?+TemplateKey=TemplateVal', {
        'instance': plugins.NotifyIFTTT,
    }),
    # Test to= in which case we set the host to the webhook id
    ('ifttt://WebHookID?to=EventID,EventID2', {
        'instance': plugins.NotifyIFTTT,
    }),
    # Removing certain keys:
    ('ifttt://WebHookID@EventID/?-Value1=&-Value2', {
        'instance': plugins.NotifyIFTTT,
    }),
    # A nicely formed ifttt url with 2 events defined:
    ('ifttt://WebHookID@EventID/EventID2/', {
        'instance': plugins.NotifyIFTTT,
    }),
    # Support native URL references
    ('https://maker.ifttt.com/use/WebHookID/', {
        # No EventID specified
        'instance': TypeError,
    }),
    ('https://maker.ifttt.com/use/WebHookID/EventID/', {
        'instance': plugins.NotifyIFTTT,
    }),
    # Test website connection failures
    ('ifttt://WebHookID@EventID', {
        'instance': plugins.NotifyIFTTT,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('ifttt://WebHookID@EventID', {
        'instance': plugins.NotifyIFTTT,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('ifttt://WebHookID@EventID', {
        'instance': plugins.NotifyIFTTT,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyJoin
    ##################################
    ('join://', {
        'instance': None,
    }),
    # APIkey; no device
    ('join://%s' % ('a' * 32), {
        'instance': plugins.NotifyJoin,
    }),
    # Invalid APIKey
    ('join://%s' % ('a' * 24), {
        # Missing a channel
        'instance': TypeError,
    }),
    # APIKey + device (using to=)
    ('join://%s?to=%s' % ('a' * 32, 'd' * 32), {
        'instance': plugins.NotifyJoin,
    }),
    # APIKey + device
    ('join://%s@%s?image=True' % ('a' * 32, 'd' * 32), {
        'instance': plugins.NotifyJoin,
    }),
    # No image
    ('join://%s@%s?image=False' % ('a' * 32, 'd' * 32), {
        'instance': plugins.NotifyJoin,
    }),
    # APIKey + device
    ('join://%s/%s' % ('a' * 32, 'd' * 32), {
        'instance': plugins.NotifyJoin,
        # don't include an image by default
        'include_image': False,
    }),
    # APIKey + 2 devices
    ('join://%s/%s/%s' % ('a' * 32, 'd' * 32, 'e' * 32), {
        'instance': plugins.NotifyJoin,
        # don't include an image by default
        'include_image': False,
    }),
    # APIKey + 1 device and 1 group
    ('join://%s/%s/%s' % ('a' * 32, 'd' * 32, 'group.chrome'), {
        'instance': plugins.NotifyJoin,
    }),
    # APIKey + bad device
    ('join://%s/%s' % ('a' * 32, 'd' * 10), {
        'instance': plugins.NotifyJoin,
        'response': False,
    }),
    # APIKey + bad url
    ('join://:@/', {
        'instance': None,
    }),
    ('join://%s' % ('a' * 32), {
        'instance': plugins.NotifyJoin,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('join://%s' % ('a' * 32), {
        'instance': plugins.NotifyJoin,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('join://%s' % ('a' * 32), {
        'instance': plugins.NotifyJoin,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyJSON
    ##################################
    ('json://', {
        'instance': None,
    }),
    ('jsons://', {
        'instance': None,
    }),
    ('json://localhost', {
        'instance': plugins.NotifyJSON,
    }),
    ('json://user:pass@localhost', {
        'instance': plugins.NotifyJSON,
    }),
    ('json://user@localhost', {
        'instance': plugins.NotifyJSON,
    }),
    ('json://localhost:8080', {
        'instance': plugins.NotifyJSON,
    }),
    ('json://user:pass@localhost:8080', {
        'instance': plugins.NotifyJSON,
    }),
    ('jsons://localhost', {
        'instance': plugins.NotifyJSON,
    }),
    ('jsons://user:pass@localhost', {
        'instance': plugins.NotifyJSON,
    }),
    ('jsons://localhost:8080/path/', {
        'instance': plugins.NotifyJSON,
    }),
    ('jsons://user:pass@localhost:8080', {
        'instance': plugins.NotifyJSON,
    }),
    ('json://:@/', {
        'instance': None,
    }),
    ('json://user:pass@localhost:8081', {
        'instance': plugins.NotifyJSON,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('json://user:pass@localhost:8082', {
        'instance': plugins.NotifyJSON,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('json://user:pass@localhost:8083', {
        'instance': plugins.NotifyJSON,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),
    ('json://localhost:8080/path?-HeaderKey=HeaderValue', {
        'instance': plugins.NotifyJSON,
    }),


    ##################################
    # NotifyKODI
    ##################################
    ('kodi://', {
        'instance': None,
    }),
    ('kodis://', {
        'instance': None,
    }),
    ('kodi://localhost', {
        'instance': plugins.NotifyXBMC,
    }),
    ('kodi://user:pass@localhost', {
        'instance': plugins.NotifyXBMC,
    }),
    ('kodi://localhost:8080', {
        'instance': plugins.NotifyXBMC,
    }),
    ('kodi://user:pass@localhost:8080', {
        'instance': plugins.NotifyXBMC,
    }),
    ('kodis://localhost', {
        'instance': plugins.NotifyXBMC,
    }),
    ('kodis://user:pass@localhost', {
        'instance': plugins.NotifyXBMC,
    }),
    ('kodis://localhost:8080/path/', {
        'instance': plugins.NotifyXBMC,
    }),
    ('kodis://user:pass@localhost:8080', {
        'instance': plugins.NotifyXBMC,
    }),
    ('kodi://localhost', {
        'instance': plugins.NotifyXBMC,
        # Experement with different notification types
        'notify_type': NotifyType.WARNING,
    }),
    ('kodi://localhost', {
        'instance': plugins.NotifyXBMC,
        # Experement with different notification types
        'notify_type': NotifyType.FAILURE,
    }),
    ('kodis://localhost:443', {
        'instance': plugins.NotifyXBMC,
        # don't include an image by default
        'include_image': False,
    }),
    ('kodi://:@/', {
        'instance': None,
    }),
    ('kodi://user:pass@localhost:8081', {
        'instance': plugins.NotifyXBMC,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('kodi://user:pass@localhost:8082', {
        'instance': plugins.NotifyXBMC,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('kodi://user:pass@localhost:8083', {
        'instance': plugins.NotifyXBMC,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyMailgun
    ##################################
    ('mailgun://', {
        'instance': None,
    }),
    ('mailgun://:@/', {
        'instance': None,
    }),
    # No Token specified
    ('mailgun://user@host', {
        'instance': TypeError,
    }),
    # Token is valid, but no user name specified
    ('mailgun://host/{}-{}-{}'.format('a' * 32, 'b' * 8, 'c' * 8), {
        'instance': TypeError,
    }),
    # Invalid from email address
    ('mailgun://!@host/{}-{}-{}'.format('a' * 32, 'b' * 8, 'c' * 8), {
        'instance': TypeError,
    }),
    # No To email address, but everything else is valid
    ('mailgun://user@host/{}-{}-{}'.format('a' * 32, 'b' * 8, 'c' * 8), {
        'instance': plugins.NotifyMailgun,
    }),
    # valid url with region specified (case insensitve)
    ('mailgun://user@host/{}-{}-{}?region=uS'.format(
        'a' * 32, 'b' * 8, 'c' * 8), {
            'instance': plugins.NotifyMailgun,
    }),
    # valid url with region specified (case insensitve)
    ('mailgun://user@host/{}-{}-{}?region=EU'.format(
        'a' * 32, 'b' * 8, 'c' * 8), {
            'instance': plugins.NotifyMailgun,
    }),
    # invalid url with region specified (case insensitve)
    ('mailgun://user@host/{}-{}-{}?region=invalid'.format(
        'a' * 32, 'b' * 8, 'c' * 8), {
            'instance': TypeError,
    }),
    # One To Email address
    ('mailgun://user@host/{}-{}-{}/test@example.com'.format(
        'a' * 32, 'b' * 8, 'c' * 8), {
            'instance': plugins.NotifyMailgun,
    }),
    ('mailgun://user@host/{}-{}-{}?to=test@example.com'.format(
        'a' * 32, 'b' * 8, 'c' * 8), {
            'instance': plugins.NotifyMailgun,
    }),
    # One To Email address, a from name specified too
    ('mailgun://user@host/{}-{}-{}/test@example.com?name="Frodo"'.format(
        'a' * 32, 'b' * 8, 'c' * 8), {
            'instance': plugins.NotifyMailgun,
    }),
    ('mailgun://user@host/{}-{}-{}'.format('a' * 32, 'b' * 8, 'c' * 8), {
        'instance': plugins.NotifyMailgun,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('mailgun://user@host/{}-{}-{}'.format('a' * 32, 'b' * 8, 'c' * 8), {
        'instance': plugins.NotifyMailgun,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('mailgun://user@host/{}-{}-{}'.format('a' * 32, 'b' * 8, 'c' * 8), {
        'instance': plugins.NotifyMailgun,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyMatrix
    ##################################
    ('matrix://', {
        'instance': None,
    }),
    ('matrixs://', {
        'instance': None,
    }),
    ('matrix://localhost', {
        # treats it as a anonymous user to register
        'instance': plugins.NotifyMatrix,
        # response is false because we have nothing to notify
        'response': False,
    }),
    ('matrix://user:pass@localhost/#room1/#room2/#room3', {
        'instance': plugins.NotifyMatrix,
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('matrix://user:pass@localhost/#room1/#room2/!room1', {
        'instance': plugins.NotifyMatrix,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('matrix://user:pass@localhost:1234/#room', {
        'instance': plugins.NotifyMatrix,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    # Matrix supports webhooks too; the following tests this now:
    ('matrix://user:token@localhost?mode=matrix&format=text', {
        # user and token correctly specified with webhook
        'instance': plugins.NotifyMatrix,
        'response': False,
    }),
    ('matrix://user:token@localhost?mode=matrix&format=html', {
        # user and token correctly specified with webhook
        'instance': plugins.NotifyMatrix,
    }),
    ('matrix://user:token@localhost?mode=slack&format=text', {
        # user and token correctly specified with webhook
        'instance': plugins.NotifyMatrix,
    }),
    # Legacy (depricated) webhook reference
    ('matrix://user:token@localhost?webhook=matrix&format=text', {
        # user and token correctly specified with webhook
        'instance': plugins.NotifyMatrix,
        'response': False,
    }),
    ('matrix://user:token@localhost?webhook=matrix&format=html', {
        # user and token correctly specified with webhook
        'instance': plugins.NotifyMatrix,
    }),
    ('matrix://user:token@localhost?webhook=slack&format=text', {
        # user and token correctly specified with webhook
        'instance': plugins.NotifyMatrix,
    }),
    ('matrixs://user:token@localhost?mode=SLACK&format=markdown', {
        # user and token specified; slack webhook still detected
        # despite uppercase characters
        'instance': plugins.NotifyMatrix,
    }),
    # Image Reference
    ('matrixs://user:token@localhost?mode=slack&format=markdown&image=True', {
        # user and token specified; image set to True
        'instance': plugins.NotifyMatrix,
    }),
    ('matrixs://user:token@localhost?mode=slack&format=markdown&image=False', {
        # user and token specified; image set to True
        'instance': plugins.NotifyMatrix,
    }),
    # Legacy (Depricated) image reference
    ('matrixs://user:token@localhost?mode=slack&thumbnail=False', {
        # user and token specified; image set to True
        'instance': plugins.NotifyMatrix,
    }),
    ('matrixs://user:token@localhost?mode=slack&thumbnail=True', {
        # user and token specified; image set to True
        'instance': plugins.NotifyMatrix,
    }),
    ('matrix://user:token@localhost?mode=On', {
        # invalid webhook specified (unexpected boolean)
        'instance': TypeError,
    }),
    ('matrix://token@localhost/?mode=Matrix', {
        'instance': plugins.NotifyMatrix,
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('matrix://user:token@localhost/mode=matrix', {
        'instance': plugins.NotifyMatrix,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('matrix://token@localhost:8080/?mode=slack', {
        'instance': plugins.NotifyMatrix,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),


    ##################################
    # NotifyMatterMost
    ##################################
    ('mmost://', {
        'instance': None,
    }),
    ('mmosts://', {
        'instance': None,
    }),
    ('mmost://localhost/3ccdd113474722377935511fc85d3dd4', {
        'instance': plugins.NotifyMatterMost,
    }),
    ('mmost://user@localhost/3ccdd113474722377935511fc85d3dd4?channel=test', {
        'instance': plugins.NotifyMatterMost,
    }),
    ('mmost://user@localhost/3ccdd113474722377935511fc85d3dd4?to=test', {
        'instance': plugins.NotifyMatterMost,
    }),
    ('mmost://localhost/3ccdd113474722377935511fc85d3dd4'
     '?to=test&image=True', {
         'instance': plugins.NotifyMatterMost}),
    ('mmost://localhost/3ccdd113474722377935511fc85d3dd4' \
     '?to=test&image=False', {
         'instance': plugins.NotifyMatterMost}),
    ('mmost://localhost/3ccdd113474722377935511fc85d3dd4' \
     '?to=test&image=True', {
         'instance': plugins.NotifyMatterMost,
         # don't include an image by default
         'include_image': False}),
    ('mmost://localhost:8080/3ccdd113474722377935511fc85d3dd4', {
        'instance': plugins.NotifyMatterMost,
    }),
    ('mmost://localhost:0/3ccdd113474722377935511fc85d3dd4', {
        'instance': plugins.NotifyMatterMost,
    }),
    ('mmost://localhost:invalid-port/3ccdd113474722377935511fc85d3dd4', {
        'instance': None,
    }),
    ('mmosts://localhost/3ccdd113474722377935511fc85d3dd4', {
        'instance': plugins.NotifyMatterMost,
    }),
    # Test our paths
    ('mmosts://localhost/a/path/3ccdd113474722377935511fc85d3dd4', {
        'instance': plugins.NotifyMatterMost,
    }),
    ('mmosts://localhost/////3ccdd113474722377935511fc85d3dd4///', {
        'instance': plugins.NotifyMatterMost,
    }),
    ('mmosts://localhost', {
        # Thrown because there was no webhook id specified
        'instance': TypeError,
    }),
    ('mmost://localhost/bad-web-hook', {
        # Thrown because the webhook is not in a valid format
        'instance': TypeError,
    }),
    ('mmost://:@/', {
        'instance': None,
    }),
    ('mmost://localhost/3ccdd113474722377935511fc85d3dd4', {
        'instance': plugins.NotifyMatterMost,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('mmost://localhost/3ccdd113474722377935511fc85d3dd4', {
        'instance': plugins.NotifyMatterMost,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('mmost://localhost/3ccdd113474722377935511fc85d3dd4', {
        'instance': plugins.NotifyMatterMost,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyMSTeams
    ##################################
    ('msteams://', {
        # First API Token not specified
        'instance': TypeError,
    }),
    ('msteams://:@/', {
        # We don't have strict host checking on for msteams, so this URL
        # actually becomes parseable and :@ becomes a hostname.
        # The below errors because a second token wasn't found
        'instance': TypeError,
    }),
    ('msteams://{}'.format(UUID4), {
        # Just half of one token 1 provided
        'instance': TypeError,
    }),
    ('msteams://{}@{}/'.format(UUID4, UUID4), {
        # Just 1 tokens provided
        'instance': TypeError,
    }),
    ('msteams://{}@{}/{}'.format(UUID4, UUID4, 'a' * 32), {
        # Just 2 tokens provided
        'instance': TypeError,
    }),
    ('msteams://{}@{}/{}/{}?ta'.format(UUID4, UUID4, 'a' * 20, UUID4), {
        # All tokens provided - invalid token 2
        'instance': TypeError,
    }),
    ('msteams://{}@{}/{}/{}?tb'.format(UUID4, UUID4, 'a' * 32, 'abcd'), {
        # All tokens provided - invalid token 3
        'instance': TypeError,
    }),
    ('msteams://{}@{}/{}/{}?tb'.format('garbage', UUID4, 'a' * 32, 'abcd'), {
        # All tokens provided - invalid token 1
        'instance': TypeError,
    }),
    ('msteams://{}@{}/{}/{}?t1'.format(UUID4, UUID4, 'a' * 32, UUID4), {
        # All tokens provided - we're good
        'instance': plugins.NotifyMSTeams,
    }),
    # Support native URLs
    ('https://outlook.office.com/webhook/{}@{}/IncomingWebhook/{}/{}'
     .format(UUID4, UUID4, 'a' * 32, UUID4), {
         # All tokens provided - we're good
         'instance': plugins.NotifyMSTeams}),

    ('msteams://{}@{}/{}/{}?t2'.format(UUID4, UUID4, 'a' * 32, UUID4), {
        # All tokens provided - we're good
        'instance': plugins.NotifyMSTeams,
        # don't include an image by default
        'include_image': False,
    }),
    ('msteams://{}@{}/{}/{}?image=No'.format(UUID4, UUID4, 'a' * 32, UUID4), {
        # All tokens provided - we're good  no image
        'instance': plugins.NotifyMSTeams,
    }),
    ('msteams://{}@{}/{}/{}?tx'.format(UUID4, UUID4, 'a' * 32, UUID4), {
        'instance': plugins.NotifyMSTeams,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('msteams://{}@{}/{}/{}?ty'.format(UUID4, UUID4, 'a' * 32, UUID4), {
        'instance': plugins.NotifyMSTeams,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('msteams://{}@{}/{}/{}?tz'.format(UUID4, UUID4, 'a' * 32, UUID4), {
        'instance': plugins.NotifyMSTeams,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyProwl
    ##################################
    ('prowl://', {
        'instance': None,
    }),
    # APIkey; no device
    ('prowl://%s' % ('a' * 40), {
        'instance': plugins.NotifyProwl,
    }),
    # Invalid APIKey
    ('prowl://%s' % ('a' * 24), {
        'instance': TypeError,
    }),
    # APIKey
    ('prowl://%s' % ('a' * 40), {
        'instance': plugins.NotifyProwl,
        # don't include an image by default
        'include_image': False,
    }),
    # APIKey + priority setting
    ('prowl://%s?priority=high' % ('a' * 40), {
        'instance': plugins.NotifyProwl,
    }),
    # APIKey + invalid priority setting
    ('prowl://%s?priority=invalid' % ('a' * 40), {
        'instance': plugins.NotifyProwl,
    }),
    # APIKey + priority setting (empty)
    ('prowl://%s?priority=' % ('a' * 40), {
        'instance': plugins.NotifyProwl,
    }),
    # APIKey + Invalid Provider Key
    ('prowl://%s/%s' % ('a' * 40, 'b' * 24), {
        'instance': TypeError,
    }),
    # APIKey + No Provider Key (empty)
    ('prowl://%s///' % ('a' * 40), {
        'instance': plugins.NotifyProwl,
    }),
    # APIKey + Provider Key
    ('prowl://%s/%s' % ('a' * 40, 'b' * 40), {
        'instance': plugins.NotifyProwl,
    }),
    # APIKey + with image
    ('prowl://%s' % ('a' * 40), {
        'instance': plugins.NotifyProwl,
    }),
    # bad url
    ('prowl://:@/', {
        'instance': None,
    }),
    ('prowl://%s' % ('a' * 40), {
        'instance': plugins.NotifyProwl,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('prowl://%s' % ('a' * 40), {
        'instance': plugins.NotifyProwl,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('prowl://%s' % ('a' * 40), {
        'instance': plugins.NotifyProwl,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyPushBullet
    ##################################
    ('pbul://', {
        'instance': None,
    }),
    # APIkey
    ('pbul://%s' % ('a' * 32), {
        'instance': plugins.NotifyPushBullet,
    }),
    # APIKey + channel
    ('pbul://%s/#channel/' % ('a' * 32), {
        'instance': plugins.NotifyPushBullet,
    }),
    # APIKey + channel (via to=
    ('pbul://%s/?to=#channel' % ('a' * 32), {
        'instance': plugins.NotifyPushBullet,
    }),
    # APIKey + 2 channels
    ('pbul://%s/#channel1/#channel2' % ('a' * 32), {
        'instance': plugins.NotifyPushBullet,
    }),
    # APIKey + device
    ('pbul://%s/device/' % ('a' * 32), {
        'instance': plugins.NotifyPushBullet,
    }),
    # APIKey + 2 devices
    ('pbul://%s/device1/device2/' % ('a' * 32), {
        'instance': plugins.NotifyPushBullet,
    }),
    # APIKey + email
    ('pbul://%s/user@example.com/' % ('a' * 32), {
        'instance': plugins.NotifyPushBullet,
    }),
    # APIKey + 2 emails
    ('pbul://%s/user@example.com/abc@def.com/' % ('a' * 32), {
        'instance': plugins.NotifyPushBullet,
    }),
    # APIKey + Combo
    ('pbul://%s/device/#channel/user@example.com/' % ('a' * 32), {
        'instance': plugins.NotifyPushBullet,
    }),
    # ,
    ('pbul://%s' % ('a' * 32), {
        'instance': plugins.NotifyPushBullet,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('pbul://%s' % ('a' * 32), {
        'instance': plugins.NotifyPushBullet,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('pbul://%s' % ('a' * 32), {
        'instance': plugins.NotifyPushBullet,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),
    ('pbul://:@/', {
        'instance': None,
    }),
    ('pbul://%s' % ('a' * 32), {
        'instance': plugins.NotifyPushBullet,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('pbul://%s' % ('a' * 32), {
        'instance': plugins.NotifyPushBullet,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('pbul://%s' % ('a' * 32), {
        'instance': plugins.NotifyPushBullet,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyTechulusPush
    ##################################
    ('push://', {
        # Missing APIKey
        'instance': TypeError,
    }),
    # Invalid APIKey
    ('push://%s' % ('+' * 24), {
        'instance': TypeError,
    }),
    # APIkey
    ('push://%s' % UUID4, {
        'instance': plugins.NotifyTechulusPush,
    }),
    # APIKey + bad url
    ('push://:@/', {
        'instance': TypeError,
    }),
    ('push://%s' % UUID4, {
        'instance': plugins.NotifyTechulusPush,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('push://%s' % UUID4, {
        'instance': plugins.NotifyTechulusPush,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('push://%s' % UUID4, {
        'instance': plugins.NotifyTechulusPush,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyPushed
    ##################################
    ('pushed://', {
        'instance': None,
    }),
    # Application Key Only
    ('pushed://%s' % ('a' * 32), {
        'instance': TypeError,
    }),
    # Application Key+Secret
    ('pushed://%s/%s' % ('a' * 32, 'a' * 64), {
        'instance': plugins.NotifyPushed,
    }),
    # Application Key+Secret + channel
    ('pushed://%s/%s/#channel/' % ('a' * 32, 'a' * 64), {
        'instance': plugins.NotifyPushed,
    }),
    # Application Key+Secret + channel (via to=)
    ('pushed://%s/%s?to=channel' % ('a' * 32, 'a' * 64), {
        'instance': plugins.NotifyPushed,
    }),
    # Application Key+Secret + dropped entry
    ('pushed://%s/%s/dropped/' % ('a' * 32, 'a' * 64), {
        'instance': plugins.NotifyPushed,
    }),
    # Application Key+Secret + 2 channels
    ('pushed://%s/%s/#channel1/#channel2' % ('a' * 32, 'a' * 64), {
        'instance': plugins.NotifyPushed,
    }),
    # Application Key+Secret + User Pushed ID
    ('pushed://%s/%s/@ABCD/' % ('a' * 32, 'a' * 64), {
        'instance': plugins.NotifyPushed,
    }),
    # Application Key+Secret + 2 devices
    ('pushed://%s/%s/@ABCD/@DEFG/' % ('a' * 32, 'a' * 64), {
        'instance': plugins.NotifyPushed,
    }),
    # Application Key+Secret + Combo
    ('pushed://%s/%s/@ABCD/#channel' % ('a' * 32, 'a' * 64), {
        'instance': plugins.NotifyPushed,
    }),
    # ,
    ('pushed://%s/%s' % ('a' * 32, 'a' * 64), {
        'instance': plugins.NotifyPushed,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('pushed://%s/%s' % ('a' * 32, 'a' * 64), {
        'instance': plugins.NotifyPushed,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('pushed://%s/%s' % ('a' * 32, 'a' * 64), {
        'instance': plugins.NotifyPushed,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),
    ('pushed://:@/', {
        'instance': None,
    }),
    ('pushed://%s/%s' % ('a' * 32, 'a' * 64), {
        'instance': plugins.NotifyPushed,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('pushed://%s/%s' % ('a' * 32, 'a' * 64), {
        'instance': plugins.NotifyPushed,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('pushed://%s/%s/#channel' % ('a' * 32, 'a' * 64), {
        'instance': plugins.NotifyPushed,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('pushed://%s/%s/@user' % ('a' * 32, 'a' * 64), {
        'instance': plugins.NotifyPushed,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('pushed://%s/%s' % ('a' * 32, 'a' * 64), {
        'instance': plugins.NotifyPushed,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyPushover
    ##################################
    ('pover://', {
        'instance': None,
    }),
    # APIkey; no user
    ('pover://%s' % ('a' * 30), {
        'instance': TypeError,
    }),
    # APIkey; invalid user
    ('pover://%s@%s' % ('u' * 20, 'a' * 30), {
        'instance': TypeError,
    }),
    # Invalid APIKey; valid User
    ('pover://%s@%s' % ('u' * 30, 'a' * 24), {
        'instance': TypeError,
    }),
    # APIKey + invalid sound setting
    ('pover://%s@%s?sound=invalid' % ('u' * 30, 'a' * 30), {
        'instance': TypeError,
    }),
    # APIKey + valid alternate sound picked
    ('pover://%s@%s?sound=spacealarm' % ('u' * 30, 'a' * 30), {
        'instance': plugins.NotifyPushover,
    }),
    # APIKey + Valid User
    ('pover://%s@%s' % ('u' * 30, 'a' * 30), {
        'instance': plugins.NotifyPushover,
        # don't include an image by default
        'include_image': False,
    }),
    # APIKey + Valid User + 1 Device
    ('pover://%s@%s/DEVICE' % ('u' * 30, 'a' * 30), {
        'instance': plugins.NotifyPushover,
    }),
    # APIKey + Valid User + 1 Device (via to=)
    ('pover://%s@%s?to=DEVICE' % ('u' * 30, 'a' * 30), {
        'instance': plugins.NotifyPushover,
    }),
    # APIKey + Valid User + 2 Devices
    ('pover://%s@%s/DEVICE1/DEVICE2/' % ('u' * 30, 'a' * 30), {
        'instance': plugins.NotifyPushover,
    }),
    # APIKey + Valid User + invalid device
    ('pover://%s@%s/%s/' % ('u' * 30, 'a' * 30, 'd' * 30), {
        'instance': plugins.NotifyPushover,
        # Notify will return False since there is a bad device in our list
        'response': False,
    }),
    # APIKey + Valid User + device + invalid device
    ('pover://%s@%s/DEVICE1/%s/' % ('u' * 30, 'a' * 30, 'd' * 30), {
        'instance': plugins.NotifyPushover,
        # Notify will return False since there is a bad device in our list
        'response': False,
    }),
    # APIKey + priority setting
    ('pover://%s@%s?priority=high' % ('u' * 30, 'a' * 30), {
        'instance': plugins.NotifyPushover,
    }),
    # APIKey + invalid priority setting
    ('pover://%s@%s?priority=invalid' % ('u' * 30, 'a' * 30), {
        'instance': plugins.NotifyPushover,
    }),
    # APIKey + emergency(2) priority setting
    ('pover://%s@%s?priority=emergency' % ('u' * 30, 'a' * 30), {
        'instance': plugins.NotifyPushover,
    }),
    # APIKey + emergency priority setting with retry and expire
    ('pover://%s@%s?priority=emergency&%s&%s' % ('u' * 30,
                                                 'a' * 30,
                                                 'retry=30',
                                                 'expire=300'), {
        'instance': plugins.NotifyPushover,
    }),
    # APIKey + emergency priority setting with text retry
    ('pover://%s@%s?priority=emergency&%s&%s' % ('u' * 30,
                                                 'a' * 30,
                                                 'retry=invalid',
                                                 'expire=300'), {
        'instance': plugins.NotifyPushover,
    }),
    # APIKey + emergency priority setting with text expire
    ('pover://%s@%s?priority=emergency&%s&%s' % ('u' * 30,
                                                 'a' * 30,
                                                 'retry=30',
                                                 'expire=invalid'), {
        'instance': plugins.NotifyPushover,
    }),
    # APIKey + emergency priority setting with invalid expire
    ('pover://%s@%s?priority=emergency&%s' % ('u' * 30,
                                              'a' * 30,
                                              'expire=100000'), {
        'instance': TypeError,
    }),
    # APIKey + emergency priority setting with invalid retry
    ('pover://%s@%s?priority=emergency&%s' % ('u' * 30,
                                              'a' * 30,
                                              'retry=15'), {
        'instance': TypeError,
    }),
    # APIKey + priority setting (empty)
    ('pover://%s@%s?priority=' % ('u' * 30, 'a' * 30), {
        'instance': plugins.NotifyPushover,
    }),
    # bad url
    ('pover://:@/', {
        'instance': None,
    }),
    ('pover://%s@%s' % ('u' * 30, 'a' * 30), {
        'instance': plugins.NotifyPushover,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('pover://%s@%s' % ('u' * 30, 'a' * 30), {
        'instance': plugins.NotifyPushover,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('pover://%s@%s' % ('u' * 30, 'a' * 30), {
        'instance': plugins.NotifyPushover,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyRocketChat
    ##################################
    ('rocket://', {
        'instance': None,
    }),
    ('rockets://', {
        'instance': None,
    }),
    ('rocket://:@/', {
        'instance': None,
    }),
    # No username or pass
    ('rocket://localhost', {
        'instance': TypeError,
    }),
    # No room or channel
    ('rocket://user:pass@localhost', {
        'instance': TypeError,
    }),
    # No valid rooms or channels
    ('rocket://user:pass@localhost/#/!/@', {
        'instance': TypeError,
    }),
    # No user/pass combo
    ('rocket://user@localhost/room/', {
        'instance': TypeError,
    }),
    # No user/pass combo
    ('rocket://localhost/room/', {
        'instance': TypeError,
    }),
    # A room and port identifier
    ('rocket://user:pass@localhost:8080/room/', {
        'instance': plugins.NotifyRocketChat,
        # The response text is expected to be the following on a success
        'requests_response_text': {
            'status': 'success',
            'data': {
                'authToken': 'abcd',
                'userId': 'user',
            },
        },
    }),
    # A channel (using the to=)
    ('rockets://user:pass@localhost?to=#channel', {
        'instance': plugins.NotifyRocketChat,
        # The response text is expected to be the following on a success
        'requests_response_text': {
            'status': 'success',
            'data': {
                'authToken': 'abcd',
                'userId': 'user',
            },
        },
    }),
    # A channel
    ('rockets://user:pass@localhost/#channel', {
        'instance': plugins.NotifyRocketChat,
        # The response text is expected to be the following on a success
        'requests_response_text': {
            'status': 'success',
            'data': {
                'authToken': 'abcd',
                'userId': 'user',
            },
        },
    }),
    # Several channels
    ('rocket://user:pass@localhost/#channel1/#channel2/?avatar=No', {
        'instance': plugins.NotifyRocketChat,
        # The response text is expected to be the following on a success
        'requests_response_text': {
            'status': 'success',
            'data': {
                'authToken': 'abcd',
                'userId': 'user',
            },
        },
    }),
    # Several Rooms
    ('rocket://user:pass@localhost/room1/room2', {
        'instance': plugins.NotifyRocketChat,
        # The response text is expected to be the following on a success
        'requests_response_text': {
            'status': 'success',
            'data': {
                'authToken': 'abcd',
                'userId': 'user',
            },
        },
    }),
    # A room and channel
    ('rocket://user:pass@localhost/room/#channel?mode=basic', {
        'instance': plugins.NotifyRocketChat,
        # The response text is expected to be the following on a success
        'requests_response_text': {
            'status': 'success',
            'data': {
                'authToken': 'abcd',
                'userId': 'user',
            },
        },
    }),
    # A user/pass where the pass matches a webtoken
    # to ensure we get the right mode, we enforce basic mode
    # so that web/token gets interpreted as a password
    ('rockets://user:pass%2Fwithslash@localhost/#channel/?mode=basic', {
        'instance': plugins.NotifyRocketChat,
        # The response text is expected to be the following on a success
        'requests_response_text': {
            'status': 'success',
            'data': {
                'authToken': 'abcd',
                'userId': 'user',
            },
        },
    }),
    # A room and channel
    ('rockets://user:pass@localhost/rooma/#channela', {
        # The response text is expected to be the following on a success
        'requests_response_code': requests.codes.ok,
        'requests_response_text': {
            # return something other then a success message type
            'status': 'failure',
        },
        # Exception is thrown in this case
        'instance': plugins.NotifyRocketChat,
        # Notifications will fail in this event
        'response': False,
    }),
    # A web token
    ('rockets://web/token@localhost/@user/#channel/roomid', {
        'instance': plugins.NotifyRocketChat,
    }),
    ('rockets://user:web/token@localhost/@user/?mode=webhook', {
        'instance': plugins.NotifyRocketChat,
    }),
    ('rockets://user:web/token@localhost?to=@user2,#channel2', {
        'instance': plugins.NotifyRocketChat,
    }),
    ('rockets://web/token@localhost/?avatar=No', {
        # a simple webhook token with default values
        'instance': plugins.NotifyRocketChat,
    }),
    ('rockets://localhost/@user/?mode=webhook&webhook=web/token', {
        'instance': plugins.NotifyRocketChat,
    }),
    ('rockets://user:web/token@localhost/@user/?mode=invalid', {
        # invalid mode
        'instance': TypeError,
    }),
    ('rocket://user:pass@localhost:8081/room1/room2', {
        'instance': plugins.NotifyRocketChat,
        # force a failure using basic mode
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('rockets://user:web/token@localhost?to=@user3,#channel3', {
        'instance': plugins.NotifyRocketChat,
        # force a failure using webhook mode
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('rocket://user:pass@localhost:8082/#channel', {
        'instance': plugins.NotifyRocketChat,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('rocket://user:pass@localhost:8083/#chan1/#chan2/room', {
        'instance': plugins.NotifyRocketChat,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyRyver
    ##################################
    ('ryver://', {
        'instance': None,
    }),
    ('ryver://:@/', {
        'instance': None,
    }),
    ('ryver://apprise', {
        # Just org provided (no token)
        'instance': TypeError,
    }),
    ('ryver://abc,#/ckhrjW8w672m6HG', {
        # Invalid org provided (this isn't actually even a value url)
        # because the hostname has ,# in it
        'instance': None,
    }),
    ('ryver://a/ckhrjW8w672m6HG', {
        # org is too short
        'instance': TypeError,
    }),
    ('ryver://apprise/ckhrjW8w67HG', {
        # Invalid token specified
        'instance': TypeError,
    }),
    ('ryver://apprise/ckhrjW8w672m6HG?webhook=invalid', {
        # Invalid webhook provided
        'instance': TypeError,
    }),
    ('ryver://apprise/ckhrjW8w672m6HG?mode=slack', {
        # No username specified; this is still okay as we use whatever
        # the user told the webhook to use; set our slack mode
        'instance': plugins.NotifyRyver,
    }),
    ('ryver://apprise/ckhrjW8w672m6HG?mode=ryver', {
        # No username specified; this is still okay as we use whatever
        # the user told the webhook to use; set our ryver mode
        'instance': plugins.NotifyRyver,
    }),
    # Legacy webhook mode setting:
    # Legacy webhook mode setting:
    ('ryver://apprise/ckhrjW8w672m6HG?webhook=slack', {
        # No username specified; this is still okay as we use whatever
        # the user told the webhook to use; set our slack mode
        'instance': plugins.NotifyRyver,
    }),
    ('ryver://apprise/ckhrjW8w672m6HG?webhook=ryver', {
        # No username specified; this is still okay as we use whatever
        # the user told the webhook to use; set our ryver mode
        'instance': plugins.NotifyRyver,
    }),
    # Support Native URLs
    ('https://apprise.ryver.com/application/webhook/ckhrjW8w672m6HG', {
        'instance': plugins.NotifyRyver,
    }),
    ('ryver://caronc@apprise/ckhrjW8w672m6HG', {
        'instance': plugins.NotifyRyver,
        # don't include an image by default
        'include_image': False,
    }),
    ('ryver://apprise/ckhrjW8w672m6HG', {
        'instance': plugins.NotifyRyver,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('ryver://apprise/ckhrjW8w672m6HG', {
        'instance': plugins.NotifyRyver,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('ryver://apprise/ckhrjW8w672m6HG', {
        'instance': plugins.NotifyRyver,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifySlack
    ##################################
    ('slack://', {
        'instance': None,
    }),
    ('slack://:@/', {
        'instance': None,
    }),
    ('slack://T1JJ3T3L2', {
        # Just Token 1 provided
        'instance': TypeError,
    }),
    ('slack://T1JJ3T3L2/A1BRTD4JD/', {
        # Just 2 tokens provided
        'instance': TypeError,
    }),
    ('slack://T1JJ3T3L2/A1BRTD4JD/TIiajkdnlazkcOXrIdevi7FQ/#hmm/#-invalid-', {
        # No username specified; this is still okay as we sub in
        # default; The one invalid channel is skipped when sending a message
        'instance': plugins.NotifySlack,
        # There is an invalid channel that we will fail to deliver to
        # as a result the response type will be false
        'response': False,
    }),
    ('slack://T1JJ3T3L2/A1BRTD4JD/TIiajkdnlazkcOXrIdevi7FQ/#channel', {
        # No username specified; this is still okay as we sub in
        # default; The one invalid channel is skipped when sending a message
        'instance': plugins.NotifySlack,
        # don't include an image by default
        'include_image': False,
    }),
    ('slack://T1JJ3T3L2/A1BRTD4JD/TIiajkdnlazkcOXrIdevi7FQ/+id/@id/', {
        # + encoded id,
        # @ userid
        'instance': plugins.NotifySlack,
    }),
    ('slack://username@T1JJ3T3L2/A1BRTD4JD/TIiajkdnlazkcOXrIdevi7FQ/' \
        '?to=#nuxref', {
            'instance': plugins.NotifySlack,
        }),
    ('slack://username@T1JJ3T3L2/A1BRTD4JD/TIiajkdnlazkcOXrIdevi7FQ/#nuxref', {
        'instance': plugins.NotifySlack,
    }),
    ('slack://username@T1JJ3T3L2/A1BRTD4JD/TIiajkdnlazkcOXrIdevi7FQ', {
        # Missing a channel, falls back to webhook channel bindings
        'instance': plugins.NotifySlack,
    }),
    # Native URL Support, take the slack URL and still build from it
    ('https://hooks.slack.com/services/{}/{}/{}'.format(
        'A' * 9, 'B' * 9, 'c' * 24), {
        'instance': plugins.NotifySlack,
    }),
    ('slack://username@INVALID/A1BRTD4JD/TIiajkdnlazkcOXrIdevi7FQ/#cool', {
        # invalid 1st Token
        'instance': TypeError,
    }),
    ('slack://username@T1JJ3T3L2/INVALID/TIiajkdnlazkcOXrIdevi7FQ/#great', {
        # invalid 2rd Token
        'instance': TypeError,
    }),
    ('slack://username@T1JJ3T3L2/A1BRTD4JD/INVALID/#channel', {
        # invalid 3rd Token
        'instance': TypeError,
    }),
    ('slack://l2g@T1JJ3T3L2/A1BRTD4JD/TIiajkdnlazkcOXrIdevi7FQ/#usenet', {
        'instance': plugins.NotifySlack,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('slack://respect@T1JJ3T3L2/A1BRTD4JD/TIiajkdnlazkcOXrIdevi7FQ/#a', {
        'instance': plugins.NotifySlack,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('slack://notify@T1JJ3T3L2/A1BRTD4JD/TIiajkdnlazkcOXrIdevi7FQ/#b', {
        'instance': plugins.NotifySlack,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifySNS (AWS)
    ##################################
    ('sns://', {
        'instance': None,
    }),
    ('sns://:@/', {
        'instance': None,
    }),
    ('sns://T1JJ3T3L2', {
        # Just Token 1 provided
        'instance': TypeError,
    }),
    ('sns://T1JJ3TD4JD/TIiajkdnlazk7FQ/', {
        # Missing a region
        'instance': TypeError,
    }),
    ('sns://T1JJ3T3L2/A1BRTD4JD/TIiajkdnlazkcevi7FQ/us-west-2/12223334444', {
        # we have a valid URL here
        'instance': plugins.NotifySNS,
    }),
    ('sns://T1JJ3TD4JD/TIiajkdnlazk7FQ/us-west-2/12223334444/12223334445', {
        # Multi SNS Suppport
        'instance': plugins.NotifySNS,
    }),
    ('sns://T1JJ3T3L2/A1BRTD4JD/TIiajkdnlazkcOXrIdevi7FQ/us-east-1', {
        # Missing a topic and/or phone No
        'instance': plugins.NotifySNS,
    }),
    ('sns://T1JJ3T3L2/A1BRTD4JD/TIiajkdnlazkcOXrIdevi7FQ/us-east-1' \
        '?to=12223334444', {
            # Missing a topic and/or phone No
            'instance': plugins.NotifySNS,
        }),
    ('sns://T1JJ3T3L2/A1BRTD4JD/TIiajkdnlazkcevi7FQ/us-west-2/12223334444', {
        'instance': plugins.NotifySNS,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('sns://T1JJ3T3L2/A1BRTD4JD/TIiajkdnlazkcevi7FQ/us-west-2/15556667777', {
        'instance': plugins.NotifySNS,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyTelegram
    ##################################
    ('tgram://', {
        'instance': None,
    }),
    # Simple Message
    ('tgram://123456789:abcdefg_hijklmnop/lead2gold/', {
        'instance': plugins.NotifyTelegram,
    }),
    # Simple Message (no images)
    ('tgram://123456789:abcdefg_hijklmnop/lead2gold/', {
        'instance': plugins.NotifyTelegram,
        # don't include an image by default
        'include_image': False,
    }),
    # Simple Message with multiple chat names
    ('tgram://123456789:abcdefg_hijklmnop/id1/id2/', {
        'instance': plugins.NotifyTelegram,
    }),
    # Simple Message with multiple chat names
    ('tgram://123456789:abcdefg_hijklmnop/?to=id1,id2', {
        'instance': plugins.NotifyTelegram,
    }),
    # Simple Message with an invalid chat ID
    ('tgram://123456789:abcdefg_hijklmnop/%$/', {
        'instance': plugins.NotifyTelegram,
        # Notify will fail
        'response': False,
    }),
    # Simple Message with multiple chat ids
    ('tgram://123456789:abcdefg_hijklmnop/id1/id2/23423/-30/', {
        'instance': plugins.NotifyTelegram,
    }),
    # Simple Message with multiple chat ids (no images)
    ('tgram://123456789:abcdefg_hijklmnop/id1/id2/23423/-30/', {
        'instance': plugins.NotifyTelegram,
        # don't include an image by default
        'include_image': False,
    }),
    # Support bot keyword prefix
    ('tgram://bottest@123456789:abcdefg_hijklmnop/lead2gold/', {
        'instance': plugins.NotifyTelegram,
    }),
    # Testing image
    ('tgram://123456789:abcdefg_hijklmnop/lead2gold/?image=Yes', {
        'instance': plugins.NotifyTelegram,
    }),
    # Testing invalid format (fall's back to html)
    ('tgram://123456789:abcdefg_hijklmnop/lead2gold/?format=invalid', {
        'instance': plugins.NotifyTelegram,
    }),
    # Testing empty format (falls back to html)
    ('tgram://123456789:abcdefg_hijklmnop/lead2gold/?format=', {
        'instance': plugins.NotifyTelegram,
    }),
    # Testing valid formats
    ('tgram://123456789:abcdefg_hijklmnop/lead2gold/?format=markdown', {
        'instance': plugins.NotifyTelegram,
    }),
    ('tgram://123456789:abcdefg_hijklmnop/lead2gold/?format=html', {
        'instance': plugins.NotifyTelegram,
    }),
    ('tgram://123456789:abcdefg_hijklmnop/lead2gold/?format=text', {
        'instance': plugins.NotifyTelegram,
    }),
    # Simple Message without image
    ('tgram://123456789:abcdefg_hijklmnop/lead2gold/', {
        'instance': plugins.NotifyTelegram,
        # don't include an image by default
        'include_image': False,
    }),
    # Invalid Bot Token
    ('tgram://alpha:abcdefg_hijklmnop/lead2gold/', {
        'instance': None,
    }),
    # AuthToken + bad url
    ('tgram://:@/', {
        'instance': None,
    }),
    ('tgram://123456789:abcdefg_hijklmnop/lead2gold/', {
        'instance': plugins.NotifyTelegram,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('tgram://123456789:abcdefg_hijklmnop/lead2gold/?image=Yes', {
        'instance': plugins.NotifyTelegram,
        # force a failure without an image specified
        'include_image': False,
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('tgram://123456789:abcdefg_hijklmnop/id1/id2/', {
        'instance': plugins.NotifyTelegram,
        # force a failure with multiple chat_ids
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('tgram://123456789:abcdefg_hijklmnop/id1/id2/', {
        'instance': plugins.NotifyTelegram,
        # force a failure without an image specified
        'include_image': False,
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('tgram://123456789:abcdefg_hijklmnop/lead2gold/', {
        'instance': plugins.NotifyTelegram,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('tgram://123456789:abcdefg_hijklmnop/lead2gold/', {
        'instance': plugins.NotifyTelegram,
        # throw a bizzare code forcing us to fail to look it up without
        # having an image included
        'include_image': False,
        'response': False,
        'requests_response_code': 999,
    }),
    # Test with image set
    ('tgram://123456789:abcdefg_hijklmnop/lead2gold/?image=Yes', {
        'instance': plugins.NotifyTelegram,
        # throw a bizzare code forcing us to fail to look it up without
        # having an image included
        'include_image': True,
        'response': False,
        'requests_response_code': 999,
    }),
    ('tgram://123456789:abcdefg_hijklmnop/lead2gold/', {
        'instance': plugins.NotifyTelegram,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),
    ('tgram://123456789:abcdefg_hijklmnop/lead2gold/?image=Yes', {
        'instance': plugins.NotifyTelegram,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them without images set
        'include_image': True,
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyTwilio
    ##################################
    ('twilio://', {
        # No Account SID specified
        'instance': TypeError,
    }),
    ('twilio://:@/', {
        # invalid Auth token
        'instance': TypeError,
    }),
    ('twilio://AC{}@12345678'.format('a' * 32), {
        # Just sid provided
        'instance': TypeError,
    }),
    ('twilio://AC{}:{}@_'.format('a' * 32, 'b' * 32), {
        # sid and token provided but invalid from
        'instance': TypeError,
    }),
    ('twilio://AC{}:{}@{}'.format('a' * 23, 'b' * 32, '1' * 11), {
        # sid invalid and token
        'instance': TypeError,
    }),
    ('twilio://AC{}:{}@{}'.format('a' * 32, 'b' * 23, '2' * 11), {
        # sid and invalid token
        'instance': TypeError,
    }),
    ('twilio://AC{}:{}@{}'.format('a' * 32, 'b' * 32, '3' * 5), {
        # using short-code (5 characters) without a target
        'instance': TypeError,
    }),
    ('twilio://AC{}:{}@{}'.format('a' * 32, 'b' * 32, '3' * 9), {
        # sid and token provided and from but invalid from no
        'instance': TypeError,
    }),
    ('twilio://AC{}:{}@{}/123/{}/abcd/'.format(
        'a' * 32, 'b' * 32, '3' * 11, '9' * 15), {
        # valid everything but target numbers
        'instance': plugins.NotifyTwilio,
    }),
    ('twilio://AC{}:{}@12345/{}'.format('a' * 32, 'b' * 32, '4' * 11), {
        # using short-code (5 characters)
        'instance': plugins.NotifyTwilio,
    }),
    ('twilio://AC{}:{}@123456/{}'.format('a' * 32, 'b' * 32, '4' * 11), {
        # using short-code (6 characters)
        'instance': plugins.NotifyTwilio,
    }),
    ('twilio://AC{}:{}@{}'.format('a' * 32, 'b' * 32, '5' * 11), {
        # using phone no with no target - we text ourselves in
        # this case
        'instance': plugins.NotifyTwilio,
    }),
    ('twilio://_?sid=AC{}&token={}&from={}'.format(
        'a' * 32, 'b' * 32, '5' * 11), {
        # use get args to acomplish the same thing
        'instance': plugins.NotifyTwilio,
    }),
    ('twilio://_?sid=AC{}&token={}&source={}'.format(
        'a' * 32, 'b' * 32, '5' * 11), {
        # use get args to acomplish the same thing (use source instead of from)
        'instance': plugins.NotifyTwilio,
    }),
    ('twilio://_?sid=AC{}&token={}&from={}&to={}'.format(
        'a' * 32, 'b' * 32, '5' * 11, '7' * 13), {
        # use to=
        'instance': plugins.NotifyTwilio,
    }),
    ('twilio://AC{}:{}@{}'.format('a' * 32, 'b' * 32, '6' * 11), {
        'instance': plugins.NotifyTwilio,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('twilio://AC{}:{}@{}'.format('a' * 32, 'b' * 32, '6' * 11), {
        'instance': plugins.NotifyTwilio,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyTwist
    ##################################
    ('twist://', {
        # Missing Email and Login
        'instance': None,
    }),
    ('twist://:@/', {
        'instance': None,
    }),
    ('twist://user@example.com/', {
        # No password
        'instance': None,
    }),
    ('twist://user@example.com/password', {
        # Password acceptable as first entry in path
        'instance': plugins.NotifyTwist,
        # Expected notify() response is False because internally we would
        # have failed to login
        'notify_response': False,
    }),
    ('twist://password:user1@example.com', {
        # password:login acceptable
        'instance': plugins.NotifyTwist,
        # Expected notify() response is False because internally we would
        # have failed to login
        'notify_response': False,
    }),
    ('twist://password:user2@example.com', {
        # password:login acceptable
        'instance': plugins.NotifyTwist,
        # Expected notify() response is False because internally we would
        # have logged in, but we would have failed to look up the #General
        # channel and workspace.
        'requests_response_text': {
            # Login expected response
            'id': 1234,
            'default_workspace': 9876,
        },
        'notify_response': False,
    }),
    ('twist://password:user2@example.com', {
        'instance': plugins.NotifyTwist,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('twist://password:user2@example.com', {
        'instance': plugins.NotifyTwist,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),
    ##################################
    # NotifyTwitter
    ##################################
    ('twitter://', {
        # Missing Consumer API Key
        'instance': TypeError,
    }),
    ('twitter://:@/', {
        'instance': TypeError,
    }),
    ('twitter://consumer_key', {
        # Missing Keys
        'instance': TypeError,
    }),
    ('twitter://consumer_key/consumer_secret/', {
        # Missing Keys
        'instance': TypeError,
    }),
    ('twitter://consumer_key/consumer_secret/access_token/', {
        # Missing Access Secret
        'instance': TypeError,
    }),
    ('twitter://consumer_key/consumer_secret/access_token/access_secret', {
        # No user mean's we message ourselves
        'instance': plugins.NotifyTwitter,
        # Expected notify() response False (because we won't be able
        # to detect our user)
        'notify_response': False,
    }),
    ('twitter://consumer_key/consumer_secret/access_token/access_secret'
        '?cache=no', {
            # No user mean's we message ourselves
            'instance': plugins.NotifyTwitter,
            # However we'll be okay if we return a proper response
            'requests_response_text': {
                'id': 12345,
                'screen_name': 'test'
            },
        }),
    ('twitter://consumer_key/consumer_secret/access_token/access_secret', {
        # No user mean's we message ourselves
        'instance': plugins.NotifyTwitter,
        # However we'll be okay if we return a proper response
        'requests_response_text': {
            'id': 12345,
            'screen_name': 'test'
        },
    }),
    # A duplicate of the entry above, this will cause cache to be referenced
    ('twitter://consumer_key/consumer_secret/access_token/access_secret', {
        # No user mean's we message ourselves
        'instance': plugins.NotifyTwitter,
        # However we'll be okay if we return a proper response
        'requests_response_text': {
            'id': 12345,
            'screen_name': 'test'
        },
    }),
    # handle cases where the screen_name is missing from the response causing
    # an exception during parsing
    ('twitter://consumer_key/consumer_secret2/access_token/access_secret', {
        # No user mean's we message ourselves
        'instance': plugins.NotifyTwitter,
        # However we'll be okay if we return a proper response
        'requests_response_text': {
            'id': 12345,
        },
        # due to a mangled response_text we'll fail
        'notify_response': False,
    }),
    ('twitter://user@consumer_key/csecret2/access_token/access_secret/-/%/', {
        # One Invalid User
        'instance': plugins.NotifyTwitter,
        # Expected notify() response False (because we won't be able
        # to detect our user)
        'notify_response': False,
    }),
    ('twitter://user@consumer_key/csecret/access_token/access_secret'
        '?cache=No', {
            # No Cache
            'instance': plugins.NotifyTwitter,
            'requests_response_text': [{
                'id': 12345,
                'screen_name': 'user'
            }],
        }),
    ('twitter://user@consumer_key/csecret/access_token/access_secret', {
        # We're good!
        'instance': plugins.NotifyTwitter,
        'requests_response_text': [{
            'id': 12345,
            'screen_name': 'user'
        }],
    }),
    # A duplicate of the entry above, this will cause cache to be referenced
    # for this reason, we don't even need to return a valid response
    ('twitter://user@consumer_key/csecret/access_token/access_secret', {
        # We're identifying the same user we already sent to
        'instance': plugins.NotifyTwitter,
    }),
    ('twitter://ckey/csecret/access_token/access_secret?mode=tweet', {
        # A Public Tweet
        'instance': plugins.NotifyTwitter,
    }),
    ('tweet://consumer_key/consumer_secret/access_token/access_secret', {
        # tweet:// is to be depricated; but we will support for purposes of
        # generating a warning to the user; the above matches an above
        # twitter:// reference so that it can use what was cached
        'instance': plugins.NotifyTwitter,
    }),
    ('twitter://user@ckey/csecret/access_token/access_secret?mode=invalid', {
        # An invalid mode
        'instance': TypeError,
    }),
    ('twitter://usera@consumer_key/consumer_secret/access_token/'
        'access_secret/user/?to=userb', {
            # We're good!
            'instance': plugins.NotifyTwitter,
            'requests_response_text': [{
                'id': 12345,
                'screen_name': 'usera'
            }, {
                'id': 12346,
                'screen_name': 'userb'
            }, {
                # A garbage entry we can test exception handling on
                'id': 123,
            }],
        }),
    ('twitter://ckey/csecret/access_token/access_secret', {
        'instance': plugins.NotifyTwitter,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('twitter://ckey/csecret/access_token/access_secret', {
        'instance': plugins.NotifyTwitter,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),
    ('twitter://ckey/csecret/access_token/access_secret?mode=tweet', {
        'instance': plugins.NotifyTwitter,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),
    ##################################
    # NotifyNexmo
    ##################################
    ('nexmo://', {
        # No API Key specified
        'instance': TypeError,
    }),
    ('nexmo://:@/', {
        # invalid Auth key
        'instance': TypeError,
    }),
    ('nexmo://{}@12345678'.format('a' * 8), {
        # Just a key provided
        'instance': TypeError,
    }),
    ('nexmo://{}:{}@_'.format('a' * 8, 'b' * 16), {
        # key and secret provided but invalid from
        'instance': TypeError,
    }),
    ('nexmo://{}:{}@{}'.format('a' * 23, 'b' * 16, '1' * 11), {
        # key invalid and secret
        'instance': TypeError,
    }),
    ('nexmo://{}:{}@{}'.format('a' * 8, 'b' * 2, '2' * 11), {
        # key and invalid secret
        'instance': TypeError,
    }),
    ('nexmo://{}:{}@{}'.format('a' * 8, 'b' * 16, '3' * 9), {
        # key and secret provided and from but invalid from no
        'instance': TypeError,
    }),
    ('nexmo://{}:{}@{}/?ttl=0'.format('a' * 8, 'b' * 16, '3' * 11), {
        # Invalid ttl defined
        'instance': TypeError,
    }),
    ('nexmo://{}:{}@{}/123/{}/abcd/'.format(
        'a' * 8, 'b' * 16, '3' * 11, '9' * 15), {
        # valid everything but target numbers
        'instance': plugins.NotifyNexmo,
    }),
    ('nexmo://{}:{}@{}'.format('a' * 8, 'b' * 16, '5' * 11), {
        # using phone no with no target - we text ourselves in
        # this case
        'instance': plugins.NotifyNexmo,
    }),
    ('nexmo://_?key={}&secret={}&from={}'.format(
        'a' * 8, 'b' * 16, '5' * 11), {
        # use get args to acomplish the same thing
        'instance': plugins.NotifyNexmo,
    }),
    ('nexmo://_?key={}&secret={}&source={}'.format(
        'a' * 8, 'b' * 16, '5' * 11), {
        # use get args to acomplish the same thing (use source instead of from)
        'instance': plugins.NotifyNexmo,
    }),
    ('nexmo://_?key={}&secret={}&from={}&to={}'.format(
        'a' * 8, 'b' * 16, '5' * 11, '7' * 13), {
        # use to=
        'instance': plugins.NotifyNexmo,
    }),
    ('nexmo://{}:{}@{}'.format('a' * 8, 'b' * 16, '6' * 11), {
        'instance': plugins.NotifyNexmo,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('nexmo://{}:{}@{}'.format('a' * 8, 'b' * 16, '6' * 11), {
        'instance': plugins.NotifyNexmo,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyWebexTeams
    ##################################
    ('wxteams://', {
        # Teams Token missing
        'instance': TypeError,
    }),
    ('wxteams://:@/', {
        # We don't have strict host checking on for wxteams, so this URL
        # actually becomes parseable and :@ becomes a hostname.
        # The below errors because a second token wasn't found
        'instance': TypeError,
    }),
    ('wxteams://{}'.format('a' * 40), {
        # Just half of one token 1 provided
        'instance': TypeError,
    }),
    ('wxteams://{}'.format('a' * 80), {
        # token provided - we're good
        'instance': plugins.NotifyWebexTeams,
    }),
    # Support Native URLs
    ('https://api.ciscospark.com/v1/webhooks/incoming/{}'.format('a' * 80), {
        # token provided - we're good
        'instance': plugins.NotifyWebexTeams,
    }),
    ('wxteams://{}'.format('a' * 80), {
        'instance': plugins.NotifyWebexTeams,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('wxteams://{}'.format('a' * 80), {
        'instance': plugins.NotifyWebexTeams,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('wxteams://{}'.format('a' * 80), {
        'instance': plugins.NotifyWebexTeams,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyKODI
    ##################################
    ('xbmc://', {
        'instance': None,
    }),
    ('xbmc://localhost', {
        'instance': plugins.NotifyXBMC,
    }),
    ('xbmc://localhost?duration=14', {
        'instance': plugins.NotifyXBMC,
    }),
    ('xbmc://localhost?duration=invalid', {
        'instance': plugins.NotifyXBMC,
    }),
    ('xbmc://localhost?duration=-1', {
        'instance': plugins.NotifyXBMC,
    }),
    ('xbmc://user:pass@localhost', {
        'instance': plugins.NotifyXBMC,
    }),
    ('xbmc://localhost:8080', {
        'instance': plugins.NotifyXBMC,
    }),
    ('xbmc://user:pass@localhost:8080', {
        'instance': plugins.NotifyXBMC,
    }),
    ('xbmc://user@localhost', {
        'instance': plugins.NotifyXBMC,
        # don't include an image by default
        'include_image': False,
    }),
    ('xbmc://localhost', {
        'instance': plugins.NotifyXBMC,
        # Experement with different notification types
        'notify_type': NotifyType.WARNING,
    }),
    ('xbmc://localhost', {
        'instance': plugins.NotifyXBMC,
        # Experement with different notification types
        'notify_type': NotifyType.FAILURE,
    }),
    ('xbmc://:@/', {
        'instance': None,
    }),
    ('xbmc://user:pass@localhost:8081', {
        'instance': plugins.NotifyXBMC,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('xbmc://user:pass@localhost:8082', {
        'instance': plugins.NotifyXBMC,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('xbmc://user:pass@localhost:8083', {
        'instance': plugins.NotifyXBMC,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),

    ##################################
    # NotifyXML
    ##################################
    ('xml://', {
        'instance': None,
    }),
    ('xmls://', {
        'instance': None,
    }),
    ('xml://localhost', {
        'instance': plugins.NotifyXML,
    }),
    ('xml://user@localhost', {
        'instance': plugins.NotifyXML,
    }),
    ('xml://user:pass@localhost', {
        'instance': plugins.NotifyXML,
    }),
    ('xml://localhost:8080', {
        'instance': plugins.NotifyXML,
    }),
    ('xml://user:pass@localhost:8080', {
        'instance': plugins.NotifyXML,
    }),
    ('xmls://localhost', {
        'instance': plugins.NotifyXML,
    }),
    ('xmls://user:pass@localhost', {
        'instance': plugins.NotifyXML,
    }),
    ('xmls://localhost:8080/path/', {
        'instance': plugins.NotifyXML,
    }),
    ('xmls://user:pass@localhost:8080', {
        'instance': plugins.NotifyXML,
    }),
    ('xml://:@/', {
        'instance': None,
    }),
    ('xml://user:pass@localhost:8081', {
        'instance': plugins.NotifyXML,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('xml://user:pass@localhost:8082', {
        'instance': plugins.NotifyXML,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('xml://user:pass@localhost:8083', {
        'instance': plugins.NotifyXML,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),
    ('xml://localhost:8080/path?-HeaderKey=HeaderValue', {
        'instance': plugins.NotifyXML,
    }),

    ##################################
    # NotifyZulip
    ##################################
    ('zulip://', {
        'instance': None,
    }),
    ('zulip://:@/', {
        'instance': None,
    }),
    ('zulip://apprise', {
        # Just org provided (no token or botname)
        'instance': TypeError,
    }),
    ('zulip://botname@apprise', {
        # Just org and botname provided (no token)
        'instance': TypeError,
    }),
    # invalid token
    ('zulip://botname@apprise/{}'.format('a' * 24), {
        'instance': TypeError,
    }),
    # invalid botname
    ('zulip://....@apprise/{}'.format('a' * 32), {
        'instance': TypeError,
    }),
    # Valid everything - no target so default is used
    ('zulip://botname@apprise/{}'.format('a' * 32), {
        'instance': plugins.NotifyZulip,
    }),
    # Valid everything - organization as hostname
    ('zulip://botname@apprise.zulipchat.com/{}'.format('a' * 32), {
        'instance': plugins.NotifyZulip,
    }),
    # Valid everything - 2 channels specified
    ('zulip://botname@apprise/{}/channel1/channel2'.format('a' * 32), {
        'instance': plugins.NotifyZulip,
    }),
    # Valid everything - 2 channels specified (using to=)
    ('zulip://botname@apprise/{}/?to=channel1/channel2'.format('a' * 32), {
        'instance': plugins.NotifyZulip,
    }),
    # Valid everything - 2 emails specified
    ('zulip://botname@apprise/{}/user@example.com/user2@example.com'.format(
        'a' * 32), {
        'instance': plugins.NotifyZulip,
    }),
    ('zulip://botname@apprise/{}'.format('a' * 32), {
        'instance': plugins.NotifyZulip,
        # don't include an image by default
        'include_image': False,
    }),
    ('zulip://botname@apprise/{}'.format('a' * 32), {
        'instance': plugins.NotifyZulip,
        # force a failure
        'response': False,
        'requests_response_code': requests.codes.internal_server_error,
    }),
    ('zulip://botname@apprise/{}'.format('a' * 32), {
        'instance': plugins.NotifyZulip,
        # throw a bizzare code forcing us to fail to look it up
        'response': False,
        'requests_response_code': 999,
    }),
    ('zulip://botname@apprise/{}'.format('a' * 32), {
        'instance': plugins.NotifyZulip,
        # Throws a series of connection and transfer exceptions when this flag
        # is set and tests that we gracfully handle them
        'test_requests_exceptions': True,
    }),
)


@mock.patch('requests.get')
@mock.patch('requests.post')
def test_rest_plugins(mock_post, mock_get):
    """
    API: REST Based Plugins()

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # Define how many characters exist per line
    row = 80

    # Some variables we use to control the data we work with
    body_len = 1024
    title_len = 1024

    # Create a large body and title with random data
    body = ''.join(choice(str_alpha + str_num + ' ') for _ in range(body_len))
    body = '\r\n'.join([body[i: i + row] for i in range(0, len(body), row)])

    # Create our title using random data
    title = ''.join(choice(str_alpha + str_num) for _ in range(title_len))

    # iterate over our dictionary and test it out
    for (url, meta) in TEST_URLS:
        # Our expected instance
        instance = meta.get('instance', None)

        # Our expected server objects
        self = meta.get('self', None)

        # Our expected Query response (True, False, or exception type)
        response = meta.get('response', True)

        # Our expected Notify response (True or False)
        notify_response = meta.get('notify_response', response)

        # Allow us to force the server response code to be something other then
        # the defaults
        requests_response_code = meta.get(
            'requests_response_code',
            requests.codes.ok if response else requests.codes.not_found,
        )

        # Allow us to force the server response text to be something other then
        # the defaults
        requests_response_text = meta.get('requests_response_text')
        if not isinstance(requests_response_text, six.string_types):
            # Convert to string
            requests_response_text = dumps(requests_response_text)

        # Allow notification type override, otherwise default to INFO
        notify_type = meta.get('notify_type', NotifyType.INFO)

        # Whether or not we should include an image with our request; unless
        # otherwise specified, we assume that images are to be included
        include_image = meta.get('include_image', True)
        if include_image:
            # a default asset
            asset = AppriseAsset()

        else:
            # Disable images
            asset = AppriseAsset(image_path_mask=False, image_url_mask=False)
            asset.image_url_logo = None

        test_requests_exceptions = meta.get(
            'test_requests_exceptions', False)

        # A request
        robj = mock.Mock()
        robj.content = u''
        mock_get.return_value = robj
        mock_post.return_value = robj

        if test_requests_exceptions is False:
            # Handle our default response
            mock_post.return_value.status_code = requests_response_code
            mock_get.return_value.status_code = requests_response_code

            # Handle our default text response
            mock_get.return_value.content = requests_response_text
            mock_post.return_value.content = requests_response_text

            # Ensure there is no side effect set
            mock_post.side_effect = None
            mock_get.side_effect = None

        else:
            # Handle exception testing; first we turn the boolean flag ito
            # a list of exceptions
            test_requests_exceptions = REQUEST_EXCEPTIONS

        try:
            obj = Apprise.instantiate(
                url, asset=asset, suppress_exceptions=False)

            if obj is None:
                if instance is not None:
                    # We're done (assuming this is what we were expecting)
                    print("{} didn't instantiate itself "
                          "(we expected it to be a {})".format(url, instance))
                    assert False
                continue

            if instance is None:
                # Expected None but didn't get it
                print('%s instantiated %s (but expected None)' % (
                    url, str(obj)))
                assert False

            assert isinstance(obj, instance) is True

            if isinstance(obj, plugins.NotifyBase):
                # We loaded okay; now lets make sure we can reverse this url
                assert isinstance(obj.url(), six.string_types) is True

                # Some Simple Invalid Instance Testing
                assert instance.parse_url(None) is None
                assert instance.parse_url(object) is None
                assert instance.parse_url(42) is None

                # Instantiate the exact same object again using the URL from
                # the one that was already created properly
                obj_cmp = Apprise.instantiate(obj.url())

                # Our object should be the same instance as what we had
                # originally expected above.
                if not isinstance(obj_cmp, plugins.NotifyBase):
                    # Assert messages are hard to trace back with the way
                    # these tests work. Just printing before throwing our
                    # assertion failure makes things easier to debug later on
                    print('TEST FAIL: {} regenerated as {}'.format(
                        url, obj.url()))
                    assert False

                # Tidy our object
                del obj_cmp

            if self:
                # Iterate over our expected entries inside of our object
                for key, val in self.items():
                    # Test that our object has the desired key
                    assert hasattr(key, obj) is True
                    assert getattr(key, obj) == val

            #
            # Stage 1: with title defined
            #
            try:
                if test_requests_exceptions is False:
                    # Disable throttling
                    obj.request_rate_per_sec = 0

                    # check that we're as expected
                    assert obj.notify(
                        body=body, title=title,
                        notify_type=notify_type) == notify_response

                    # check that this doesn't change using different overflow
                    # methods
                    assert obj.notify(
                        body=body, title=title,
                        notify_type=notify_type,
                        overflow=OverflowMode.UPSTREAM) == notify_response
                    assert obj.notify(
                        body=body, title=title,
                        notify_type=notify_type,
                        overflow=OverflowMode.TRUNCATE) == notify_response
                    assert obj.notify(
                        body=body, title=title,
                        notify_type=notify_type,
                        overflow=OverflowMode.SPLIT) == notify_response

                else:
                    # Disable throttling
                    obj.request_rate_per_sec = 0

                    for _exception in REQUEST_EXCEPTIONS:
                        mock_post.side_effect = _exception
                        mock_get.side_effect = _exception

                        try:
                            assert obj.notify(
                                body=body, title=title,
                                notify_type=NotifyType.INFO) is False

                        except AssertionError:
                            # Don't mess with these entries
                            raise

                        except Exception:
                            # We can't handle this exception type
                            raise

            except AssertionError:
                # Don't mess with these entries
                raise

            except Exception as e:
                # Check that we were expecting this exception to happen
                try:
                    if not isinstance(e, response):
                        raise

                except TypeError:
                    print('%s Unhandled response %s' % (url, type(e)))
                    raise

            #
            # Stage 2: without title defined
            #
            try:
                if test_requests_exceptions is False:
                    # check that we're as expected
                    assert obj.notify(body='body', notify_type=notify_type) \
                        == notify_response

                else:
                    for _exception in REQUEST_EXCEPTIONS:
                        mock_post.side_effect = _exception
                        mock_get.side_effect = _exception

                        try:
                            assert obj.notify(
                                body=body,
                                notify_type=NotifyType.INFO) is False

                        except AssertionError:
                            # Don't mess with these entries
                            raise

                        except Exception:
                            # We can't handle this exception type
                            raise

            except AssertionError:
                # Don't mess with these entries
                raise

            except Exception as e:
                # Check that we were expecting this exception to happen
                if not isinstance(e, response):
                    raise

            # Tidy our object and allow any possible defined deconstructors to
            # be executed.
            del obj

        except AssertionError:
            # Don't mess with these entries
            print('%s AssertionError' % url)
            raise

        except Exception as e:
            # Handle our exception
            if(instance is None):
                print('%s %s' % (url, str(e)))
                raise

            if not isinstance(e, instance):
                print('%s %s' % (url, str(e)))
                raise


@mock.patch('requests.get')
@mock.patch('requests.post')
def test_notify_boxcar_plugin(mock_post, mock_get):
    """
    API: NotifyBoxcar() Extra Checks

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # Generate some generic message types
    device = 'A' * 64
    tag = '@B' * 63

    access = '-' * 64
    secret = '_' * 64

    # Initializes the plugin with recipients set to None
    plugins.NotifyBoxcar(access=access, secret=secret, targets=None)

    # Initializes the plugin with a valid access, but invalid access key
    try:
        plugins.NotifyBoxcar(access=None, secret=secret, targets=None)
        assert False

    except TypeError:
        # We should throw an exception for knowingly having an invalid
        assert True

    # Initializes the plugin with a valid access, but invalid secret key
    try:
        plugins.NotifyBoxcar(access=access, secret='invalid', targets=None)
        assert False

    except TypeError:
        # We should throw an exception for knowingly having an invalid key
        assert True

    # Initializes the plugin with a valid access, but invalid secret
    try:
        plugins.NotifyBoxcar(access=access, secret=None, targets=None)
        assert False

    except TypeError:
        # We should throw an exception for knowingly having an invalid
        assert True

    # Initializes the plugin with recipients list
    # the below also tests our the variation of recipient types
    plugins.NotifyBoxcar(
        access=access, secret=secret, targets=[device, tag])

    mock_get.return_value = requests.Request()
    mock_post.return_value = requests.Request()
    mock_post.return_value.status_code = requests.codes.created
    mock_get.return_value.status_code = requests.codes.created

    # Test notifications without a body or a title
    p = plugins.NotifyBoxcar(access=access, secret=secret, targets=None)

    assert p.notify(body=None, title=None, notify_type=NotifyType.INFO) is True

    # Test comma, separate values
    device = 'a' * 64

    p = plugins.NotifyBoxcar(
        access=access, secret=secret,
        targets=','.join([device, device, device]))
    assert len(p.device_tokens) == 3


@mock.patch('requests.get')
@mock.patch('requests.post')
def test_notify_discord_plugin(mock_post, mock_get):
    """
    API: NotifyDiscord() Extra Checks

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # Initialize some generic (but valid) tokens
    webhook_id = 'A' * 24
    webhook_token = 'B' * 64

    # Prepare Mock
    mock_get.return_value = requests.Request()
    mock_post.return_value = requests.Request()
    mock_post.return_value.status_code = requests.codes.ok
    mock_get.return_value.status_code = requests.codes.ok

    # Empty Channel list
    try:
        plugins.NotifyDiscord(webhook_id=None, webhook_token=webhook_token)
        assert False

    except TypeError:
        # we'll thrown because no webhook_id was specified
        assert True

    obj = plugins.NotifyDiscord(
        webhook_id=webhook_id,
        webhook_token=webhook_token,
        footer=True, thumbnail=False)

    # This call includes an image with it's payload:
    assert obj.notify(
        body='body', title='title', notify_type=NotifyType.INFO) is True

    # Test our header parsing
    test_markdown = "## Heading one\nbody body\n\n" + \
        "# Heading 2 ##\n\nTest\n\n" + \
        "more content\n" + \
        "even more content  \t\r\n\n\n" + \
        "# Heading 3 ##\n\n\n" + \
        "normal content\n" + \
        "# heading 4\n" + \
        "#### Heading 5"

    results = obj.extract_markdown_sections(test_markdown)
    assert isinstance(results, list) is True
    # We should have 5 sections (since there are 5 headers identified above)
    assert len(results) == 5

    # Use our test markdown string during a notification
    assert obj.notify(
        body=test_markdown, title='title', notify_type=NotifyType.INFO) is True

    # Create an apprise instance
    a = Apprise()

    # Our processing is slightly different when we aren't using markdown
    # as we do not pre-parse content during our notifications
    assert a.add(
        'discord://{webhook_id}/{webhook_token}/'
        '?format=markdown&footer=Yes'.format(
            webhook_id=webhook_id,
            webhook_token=webhook_token)) is True

    # This call includes an image with it's payload:
    assert a.notify(body=test_markdown, title='title',
                    notify_type=NotifyType.INFO,
                    body_format=NotifyFormat.TEXT) is True

    assert a.notify(body=test_markdown, title='title',
                    notify_type=NotifyType.INFO,
                    body_format=NotifyFormat.MARKDOWN) is True

    # Toggle our logo availability
    a.asset.image_url_logo = None
    assert a.notify(
        body='body', title='title', notify_type=NotifyType.INFO) is True


@mock.patch('requests.get')
@mock.patch('requests.post')
def test_notify_emby_plugin_login(mock_post, mock_get):
    """
    API: NotifyEmby.login()

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # Prepare Mock
    mock_get.return_value = requests.Request()
    mock_post.return_value = requests.Request()

    obj = Apprise.instantiate('emby://l2g:l2gpass@localhost')
    assert isinstance(obj, plugins.NotifyEmby)

    # Test our exception handling
    for _exception in REQUEST_EXCEPTIONS:
        mock_post.side_effect = _exception
        mock_get.side_effect = _exception
        # We'll fail to log in each time
        assert obj.login() is False

    # Disable Exceptions
    mock_post.side_effect = None
    mock_get.side_effect = None

    # Our login flat out fails if we don't have proper parseable content
    mock_post.return_value.content = u''
    mock_get.return_value.content = mock_post.return_value.content

    # KeyError handling
    mock_post.return_value.status_code = 999
    mock_get.return_value.status_code = 999
    assert obj.login() is False

    # General Internal Server Error
    mock_post.return_value.status_code = requests.codes.internal_server_error
    mock_get.return_value.status_code = requests.codes.internal_server_error
    assert obj.login() is False

    mock_post.return_value.status_code = requests.codes.ok
    mock_get.return_value.status_code = requests.codes.ok

    obj = Apprise.instantiate('emby://l2g:l2gpass@localhost:%d' % (
        # Increment our port so it will always be something different than
        # the default
        plugins.NotifyEmby.emby_default_port + 1))
    assert isinstance(obj, plugins.NotifyEmby)
    assert obj.port == (plugins.NotifyEmby.emby_default_port + 1)

    # The login will fail because '' is not a parseable JSON response
    assert obj.login() is False

    # Disable the port completely
    obj.port = None
    assert obj.login() is False

    # Default port assigments
    obj = Apprise.instantiate('emby://l2g:l2gpass@localhost')
    assert isinstance(obj, plugins.NotifyEmby)
    assert obj.port == plugins.NotifyEmby.emby_default_port

    # The login will (still) fail because '' is not a parseable JSON response
    assert obj.login() is False

    # Our login flat out fails if we don't have proper parseable content
    mock_post.return_value.content = dumps({
        u'AccessToken': u'0000-0000-0000-0000',
    })
    mock_get.return_value.content = mock_post.return_value.content

    obj = Apprise.instantiate('emby://l2g:l2gpass@localhost')
    assert isinstance(obj, plugins.NotifyEmby)

    # The login will fail because the 'User' or 'Id' field wasn't parsed
    assert obj.login() is False

    # Our text content (we intentionally reverse the 2 locations
    # that store the same thing; we do this so we can test which
    # one it defaults to if both are present
    mock_post.return_value.content = dumps({
        u'User': {
            u'Id': u'abcd123',
        },
        u'Id': u'123abc',
        u'AccessToken': u'0000-0000-0000-0000',
    })
    mock_get.return_value.content = mock_post.return_value.content

    obj = Apprise.instantiate('emby://l2g:l2gpass@localhost')
    assert isinstance(obj, plugins.NotifyEmby)

    # Login
    assert obj.login() is True
    assert obj.user_id == '123abc'
    assert obj.access_token == '0000-0000-0000-0000'

    # We're going to log in a second time which checks that we logout
    # first before logging in again. But this time we'll scrap the
    # 'Id' area and use the one found in the User area if detected
    mock_post.return_value.content = dumps({
        u'User': {
            u'Id': u'abcd123',
        },
        u'AccessToken': u'0000-0000-0000-0000',
    })
    mock_get.return_value.content = mock_post.return_value.content

    # Login
    assert obj.login() is True
    assert obj.user_id == 'abcd123'
    assert obj.access_token == '0000-0000-0000-0000'


@mock.patch('apprise.plugins.NotifyEmby.login')
@mock.patch('apprise.plugins.NotifyEmby.logout')
@mock.patch('requests.get')
@mock.patch('requests.post')
def test_notify_emby_plugin_sessions(mock_post, mock_get, mock_logout,
                                     mock_login):
    """
    API: NotifyEmby.sessions()

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # Prepare Mock
    mock_get.return_value = requests.Request()
    mock_post.return_value = requests.Request()

    # This is done so we don't obstruct our access_token and user_id values
    mock_login.return_value = True
    mock_logout.return_value = True

    obj = Apprise.instantiate('emby://l2g:l2gpass@localhost')
    assert isinstance(obj, plugins.NotifyEmby)
    obj.access_token = 'abc'
    obj.user_id = '123'

    # Test our exception handling
    for _exception in REQUEST_EXCEPTIONS:
        mock_post.side_effect = _exception
        mock_get.side_effect = _exception
        # We'll fail to log in each time
        sessions = obj.sessions()
        assert isinstance(sessions, dict) is True
        assert len(sessions) == 0

    # Disable Exceptions
    mock_post.side_effect = None
    mock_get.side_effect = None

    # Our login flat out fails if we don't have proper parseable content
    mock_post.return_value.content = u''
    mock_get.return_value.content = mock_post.return_value.content

    # KeyError handling
    mock_post.return_value.status_code = 999
    mock_get.return_value.status_code = 999
    sessions = obj.sessions()
    assert isinstance(sessions, dict) is True
    assert len(sessions) == 0

    # General Internal Server Error
    mock_post.return_value.status_code = requests.codes.internal_server_error
    mock_get.return_value.status_code = requests.codes.internal_server_error
    sessions = obj.sessions()
    assert isinstance(sessions, dict) is True
    assert len(sessions) == 0

    mock_post.return_value.status_code = requests.codes.ok
    mock_get.return_value.status_code = requests.codes.ok
    mock_get.return_value.content = mock_post.return_value.content

    # Disable the port completely
    obj.port = None

    sessions = obj.sessions()
    assert isinstance(sessions, dict) is True
    assert len(sessions) == 0

    # Let's get some results
    mock_post.return_value.content = dumps([
        {
            u'Id': u'abc123',
        },
        {
            u'Id': u'def456',
        },
        {
            u'InvalidEntry': None,
        },
    ])
    mock_get.return_value.content = mock_post.return_value.content

    sessions = obj.sessions(user_controlled=True)
    assert isinstance(sessions, dict) is True
    assert len(sessions) == 2

    # Test it without setting user-controlled sessions
    sessions = obj.sessions(user_controlled=False)
    assert isinstance(sessions, dict) is True
    assert len(sessions) == 2

    # Triggers an authentication failure
    obj.user_id = None
    mock_login.return_value = False
    sessions = obj.sessions()
    assert isinstance(sessions, dict) is True
    assert len(sessions) == 0


@mock.patch('requests.post')
def test_notify_twilio_plugin(mock_post):
    """
    API: NotifyTwilio() Extra Checks

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # Prepare our response
    response = requests.Request()
    response.status_code = requests.codes.ok

    # Prepare Mock
    mock_post.return_value = response

    # Initialize some generic (but valid) tokens
    account_sid = 'AC{}'.format('b' * 32)
    auth_token = '{}'.format('b' * 32)
    source = '+1 (555) 123-3456'

    try:
        plugins.NotifyTwilio(
            account_sid=None, auth_token=auth_token, source=source)
        # No account_sid specified
        assert False

    except TypeError:
        # Exception should be thrown about the fact account_sid was not
        # specified
        assert True

    try:
        plugins.NotifyTwilio(
            account_sid=account_sid, auth_token=None, source=source)
        # No account_sid specified
        assert False

    except TypeError:
        # Exception should be thrown about the fact account_sid was not
        # specified
        assert True

    # a error response
    response.status_code = 400
    response.content = dumps({
        'code': 21211,
        'message': "The 'To' number +1234567 is not a valid phone number.",
    })
    mock_post.return_value = response

    # Initialize our object
    obj = plugins.NotifyTwilio(
        account_sid=account_sid, auth_token=auth_token, source=source)

    # We will fail with the above error code
    assert obj.notify('title', 'body', 'info') is False


@mock.patch('requests.post')
def test_notify_nexmo_plugin(mock_post):
    """
    API: NotifyNexmo() Extra Checks

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # Prepare our response
    response = requests.Request()
    response.status_code = requests.codes.ok

    # Prepare Mock
    mock_post.return_value = response

    # Initialize some generic (but valid) tokens
    apikey = '{}'.format('b' * 8)
    secret = '{}'.format('b' * 16)
    source = '+1 (555) 123-3456'

    try:
        plugins.NotifyNexmo(
            apikey=None, secret=secret, source=source)
        # No apikey specified
        assert False

    except TypeError:
        # Exception should be thrown about the fact apikey was not
        # specified
        assert True

    try:
        plugins.NotifyNexmo(
            apikey=apikey, secret=None, source=source)
        # No secret specified
        assert False

    except TypeError:
        # Exception should be thrown about the fact apikey was not
        # specified
        assert True

    # a error response
    response.status_code = 400
    response.content = dumps({
        'code': 21211,
        'message': "The 'To' number +1234567 is not a valid phone number.",
    })
    mock_post.return_value = response

    # Initialize our object
    obj = plugins.NotifyNexmo(
        apikey=apikey, secret=secret, source=source)

    # We will fail with the above error code
    assert obj.notify('title', 'body', 'info') is False


@mock.patch('apprise.plugins.NotifyEmby.login')
@mock.patch('requests.get')
@mock.patch('requests.post')
def test_notify_emby_plugin_logout(mock_post, mock_get, mock_login):
    """
    API: NotifyEmby.sessions()

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # Prepare Mock
    mock_get.return_value = requests.Request()
    mock_post.return_value = requests.Request()

    # This is done so we don't obstruct our access_token and user_id values
    mock_login.return_value = True

    obj = Apprise.instantiate('emby://l2g:l2gpass@localhost')
    assert isinstance(obj, plugins.NotifyEmby)
    obj.access_token = 'abc'
    obj.user_id = '123'

    # Test our exception handling
    for _exception in REQUEST_EXCEPTIONS:
        mock_post.side_effect = _exception
        mock_get.side_effect = _exception
        # We'll fail to log in each time
        obj.logout()
        obj.access_token = 'abc'
        obj.user_id = '123'

    # Disable Exceptions
    mock_post.side_effect = None
    mock_get.side_effect = None

    # Our login flat out fails if we don't have proper parseable content
    mock_post.return_value.content = u''
    mock_get.return_value.content = mock_post.return_value.content

    # KeyError handling
    mock_post.return_value.status_code = 999
    mock_get.return_value.status_code = 999
    obj.logout()
    obj.access_token = 'abc'
    obj.user_id = '123'

    # General Internal Server Error
    mock_post.return_value.status_code = requests.codes.internal_server_error
    mock_get.return_value.status_code = requests.codes.internal_server_error
    obj.logout()
    obj.access_token = 'abc'
    obj.user_id = '123'

    mock_post.return_value.status_code = requests.codes.ok
    mock_get.return_value.status_code = requests.codes.ok
    mock_get.return_value.content = mock_post.return_value.content

    # Disable the port completely
    obj.port = None

    # Perform logout
    obj.logout()

    # Calling logout on an object already logged out
    obj.logout()

    # Test Python v3.5 LookupError Bug: https://bugs.python.org/issue29288
    mock_post.side_effect = LookupError()
    mock_get.side_effect = LookupError()
    obj.access_token = 'abc'
    obj.user_id = '123'

    # Tidy object
    del obj


@mock.patch('apprise.plugins.NotifyEmby.sessions')
@mock.patch('apprise.plugins.NotifyEmby.login')
@mock.patch('apprise.plugins.NotifyEmby.logout')
@mock.patch('requests.get')
@mock.patch('requests.post')
def test_notify_emby_plugin_notify(mock_post, mock_get, mock_logout,
                                   mock_login, mock_sessions):
    """
    API: NotifyEmby.notify()

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    req = requests.Request()
    req.status_code = requests.codes.ok
    req.content = ''
    mock_get.return_value = req
    mock_post.return_value = req

    # This is done so we don't obstruct our access_token and user_id values
    mock_login.return_value = True
    mock_logout.return_value = True
    mock_sessions.return_value = {'abcd': {}}

    obj = Apprise.instantiate('emby://l2g:l2gpass@localhost?modal=False')
    assert isinstance(obj, plugins.NotifyEmby)
    assert obj.notify('title', 'body', 'info') is True
    obj.access_token = 'abc'
    obj.user_id = '123'

    # Test Modal support
    obj = Apprise.instantiate('emby://l2g:l2gpass@localhost?modal=True')
    assert isinstance(obj, plugins.NotifyEmby)
    assert obj.notify('title', 'body', 'info') is True
    obj.access_token = 'abc'
    obj.user_id = '123'

    # Test our exception handling
    for _exception in REQUEST_EXCEPTIONS:
        mock_post.side_effect = _exception
        mock_get.side_effect = _exception
        # We'll fail to log in each time
        assert obj.notify('title', 'body', 'info') is False

    # Disable Exceptions
    mock_post.side_effect = None
    mock_get.side_effect = None

    # Our login flat out fails if we don't have proper parseable content
    mock_post.return_value.content = u''
    mock_get.return_value.content = mock_post.return_value.content

    # KeyError handling
    mock_post.return_value.status_code = 999
    mock_get.return_value.status_code = 999
    assert obj.notify('title', 'body', 'info') is False

    # General Internal Server Error
    mock_post.return_value.status_code = requests.codes.internal_server_error
    mock_get.return_value.status_code = requests.codes.internal_server_error
    assert obj.notify('title', 'body', 'info') is False

    mock_post.return_value.status_code = requests.codes.ok
    mock_get.return_value.status_code = requests.codes.ok
    mock_get.return_value.content = mock_post.return_value.content

    # Disable the port completely
    obj.port = None
    assert obj.notify('title', 'body', 'info') is True

    # An Empty return set (no query is made, but notification will still
    # succeed
    mock_sessions.return_value = {}
    assert obj.notify('title', 'body', 'info') is True

    # Tidy our object
    del obj


@mock.patch('requests.get')
@mock.patch('requests.post')
def test_notify_ifttt_plugin(mock_post, mock_get):
    """
    API: NotifyIFTTT() Extra Checks

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # Initialize some generic (but valid) tokens
    webhook_id = 'webhook_id'
    events = ['event1', 'event2']

    # Prepare Mock
    mock_get.return_value = requests.Request()
    mock_post.return_value = requests.Request()
    mock_post.return_value.status_code = requests.codes.ok
    mock_get.return_value.status_code = requests.codes.ok
    mock_get.return_value.content = '{}'
    mock_post.return_value.content = '{}'

    try:
        obj = plugins.NotifyIFTTT(webhook_id=None, events=None)
        # No webhook_id specified
        assert False

    except TypeError:
        # Exception should be thrown about the fact webhook_id was specified
        assert True

    try:
        obj = plugins.NotifyIFTTT(webhook_id=webhook_id, events=None)
        # No events specified
        assert False

    except TypeError:
        # Exception should be thrown about the fact no token was specified
        assert True

    obj = plugins.NotifyIFTTT(webhook_id=webhook_id, events=events)
    assert isinstance(obj, plugins.NotifyIFTTT) is True

    assert obj.notify(
        body='body', title='title', notify_type=NotifyType.INFO) is True

    # Test the addition of tokens
    obj = plugins.NotifyIFTTT(
        webhook_id=webhook_id, events=events,
        add_tokens={'Test': 'ValueA', 'Test2': 'ValueB'})

    assert isinstance(obj, plugins.NotifyIFTTT) is True

    assert obj.notify(
        body='body', title='title', notify_type=NotifyType.INFO) is True

    try:
        # Invalid del_tokens entry
        obj = plugins.NotifyIFTTT(
            webhook_id=webhook_id, events=events,
            del_tokens=plugins.NotifyIFTTT.ifttt_default_title_key)

        # we shouldn't reach here
        assert False

    except TypeError:
        # del_tokens must be a list, so passing a string will throw
        # an exception.
        assert True

    assert isinstance(obj, plugins.NotifyIFTTT) is True

    assert obj.notify(
        body='body', title='title', notify_type=NotifyType.INFO) is True

    # Test removal of tokens by a list
    obj = plugins.NotifyIFTTT(
        webhook_id=webhook_id, events=events,
        add_tokens={
            'MyKey': 'MyValue'
        },
        del_tokens=(
            plugins.NotifyIFTTT.ifttt_default_title_key,
            plugins.NotifyIFTTT.ifttt_default_body_key,
            plugins.NotifyIFTTT.ifttt_default_type_key))

    assert isinstance(obj, plugins.NotifyIFTTT) is True

    assert obj.notify(
        body='body', title='title', notify_type=NotifyType.INFO) is True

    # Test removal of tokens as dict
    obj = plugins.NotifyIFTTT(
        webhook_id=webhook_id, events=events,
        add_tokens={
            'MyKey': 'MyValue'
        },
        del_tokens={
            plugins.NotifyIFTTT.ifttt_default_title_key: None,
            plugins.NotifyIFTTT.ifttt_default_body_key: None,
            plugins.NotifyIFTTT.ifttt_default_type_key: None})

    assert isinstance(obj, plugins.NotifyIFTTT) is True


@mock.patch('requests.get')
@mock.patch('requests.post')
def test_notify_join_plugin(mock_post, mock_get):
    """
    API: NotifyJoin() Extra Checks

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # Generate some generic message types
    device = 'A' * 32
    group = 'group.chrome'
    apikey = 'a' * 32

    # Initializes the plugin with devices set to a string
    plugins.NotifyJoin(apikey=apikey, targets=group)

    # Initializes the plugin with devices set to None
    plugins.NotifyJoin(apikey=apikey, targets=None)

    # Initializes the plugin with devices set to a set
    p = plugins.NotifyJoin(apikey=apikey, targets=[group, device])

    # Prepare our mock responses
    req = requests.Request()
    req.status_code = requests.codes.created
    req.content = ''
    mock_get.return_value = req
    mock_post.return_value = req

    # Test notifications without a body or a title; nothing to send
    # so we return False
    p.notify(body=None, title=None, notify_type=NotifyType.INFO) is False


def test_notify_pover_plugin():
    """
    API: NotifyPushover() Extra Checks

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # No token
    try:
        plugins.NotifyPushover(token=None)
        assert False

    except TypeError:
        # we'll thrown because we provided no token
        assert True


def test_notify_ryver_plugin():
    """
    API: NotifyRyver() Extra Checks

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # must be 15 characters long
    token = 'a' * 15

    # No organization
    try:
        plugins.NotifyRyver(organization=None, token=token)
        assert False

    except TypeError:
        # we'll thrown because an empty list of channels was provided
        assert True


def test_notify_zulip_plugin():
    """
    API: NotifyZulip() Extra Checks

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # must be 32 characters long
    token = 'a' * 32

    # Invalid organization
    try:
        plugins.NotifyZulip(
            botname='test', organization='#', token=token)
        assert False

    except TypeError:
        # we'll thrown because an empty list of channels was provided
        assert True


@mock.patch('requests.get')
@mock.patch('requests.post')
def test_notify_slack_plugin(mock_post, mock_get):
    """
    API: NotifySlack() Extra Checks

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # Initialize some generic (but valid) tokens
    token_a = 'A' * 9
    token_b = 'B' * 9
    token_c = 'c' * 24

    # Support strings
    channels = 'chan1,#chan2,+id,@user,,,'

    obj = plugins.NotifySlack(
        token_a=token_a, token_b=token_b, token_c=token_c, targets=channels)
    assert len(obj.channels) == 4

    # Prepare Mock
    mock_get.return_value = requests.Request()
    mock_post.return_value = requests.Request()
    mock_post.return_value.status_code = requests.codes.ok
    mock_get.return_value.status_code = requests.codes.ok

    # Missing first Token
    try:
        plugins.NotifySlack(
            token_a=None, token_b=token_b, token_c=token_c,
            targets=channels)
        assert False

    except TypeError:
        # we'll thrown because an empty list of channels was provided
        assert True

    # Test include_image
    obj = plugins.NotifySlack(
        token_a=token_a, token_b=token_b, token_c=token_c, targets=channels,
        include_image=True)

    # This call includes an image with it's payload:
    assert obj.notify(
        body='body', title='title', notify_type=NotifyType.INFO) is True


@mock.patch('requests.get')
@mock.patch('requests.post')
def test_notify_pushbullet_plugin(mock_post, mock_get):
    """
    API: NotifyPushBullet() Extra Checks

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # Initialize some generic (but valid) tokens
    accesstoken = 'a' * 32

    # Support strings
    recipients = '#chan1,#chan2,device,user@example.com,,,'

    # Prepare Mock
    mock_get.return_value = requests.Request()
    mock_post.return_value = requests.Request()
    mock_post.return_value.status_code = requests.codes.ok
    mock_get.return_value.status_code = requests.codes.ok

    obj = plugins.NotifyPushBullet(
        accesstoken=accesstoken, targets=recipients)
    assert isinstance(obj, plugins.NotifyPushBullet) is True
    assert len(obj.targets) == 4

    obj = plugins.NotifyPushBullet(accesstoken=accesstoken)
    assert isinstance(obj, plugins.NotifyPushBullet) is True
    # Default is to send to all devices, so there will be a
    # recipient here
    assert len(obj.targets) == 1

    obj = plugins.NotifyPushBullet(accesstoken=accesstoken, targets=set())
    assert isinstance(obj, plugins.NotifyPushBullet) is True
    # Default is to send to all devices, so there will be a
    # recipient here
    assert len(obj.targets) == 1


@mock.patch('requests.get')
@mock.patch('requests.post')
def test_notify_pushed_plugin(mock_post, mock_get):
    """
    API: NotifyPushed() Extra Checks

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # Chat ID
    recipients = '@ABCDEFG, @DEFGHIJ, #channel, #channel2'

    # Some required input
    app_key = 'ABCDEFG'
    app_secret = 'ABCDEFG'

    # Prepare Mock
    mock_get.return_value = requests.Request()
    mock_post.return_value = requests.Request()
    mock_post.return_value.status_code = requests.codes.ok
    mock_get.return_value.status_code = requests.codes.ok

    try:
        obj = plugins.NotifyPushed(
            app_key=app_key,
            app_secret=None,
            recipients=None,
        )
        assert False

    except TypeError:
        # No application Secret was specified; it's a good thing if
        # this exception was thrown
        assert True

    try:
        obj = plugins.NotifyPushed(
            app_key=app_key,
            app_secret=app_secret,
            recipients=None,
        )
        # recipients list set to (None) is perfectly fine; in this
        # case it will notify the App
        assert True

    except TypeError:
        # Exception should never be thrown!
        assert False

    obj = plugins.NotifyPushed(
        app_key=app_key,
        app_secret=app_secret,
        targets=recipients,
    )
    assert isinstance(obj, plugins.NotifyPushed) is True
    assert len(obj.channels) == 2
    assert len(obj.users) == 2

    # Prepare Mock to fail
    mock_post.return_value.status_code = requests.codes.internal_server_error
    mock_get.return_value.status_code = requests.codes.internal_server_error


@mock.patch('requests.get')
@mock.patch('requests.post')
def test_notify_pushover_plugin(mock_post, mock_get):
    """
    API: NotifyPushover() Extra Checks

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # Initialize some generic (but valid) tokens
    token = 'a' * 30
    user = 'u' * 30

    invalid_device = 'd' * 35

    # Support strings
    devices = 'device1,device2,,,,%s' % invalid_device

    # Prepare Mock
    mock_get.return_value = requests.Request()
    mock_post.return_value = requests.Request()
    mock_post.return_value.status_code = requests.codes.ok
    mock_get.return_value.status_code = requests.codes.ok

    try:
        obj = plugins.NotifyPushover(user=user, webhook_id=None)
        # No token specified
        assert False

    except TypeError:
        # Exception should be thrown about the fact no token was specified
        assert True

    obj = plugins.NotifyPushover(user=user, token=token, targets=devices)
    assert isinstance(obj, plugins.NotifyPushover) is True
    assert len(obj.targets) == 3

    # This call fails because there is 1 invalid device
    assert obj.notify(
        body='body', title='title', notify_type=NotifyType.INFO) is False

    obj = plugins.NotifyPushover(user=user, token=token)
    assert isinstance(obj, plugins.NotifyPushover) is True
    # Default is to send to all devices, so there will be a
    # device defined here
    assert len(obj.targets) == 1

    # This call succeeds because all of the devices are valid
    assert obj.notify(
        body='body', title='title', notify_type=NotifyType.INFO) is True

    obj = plugins.NotifyPushover(user=user, token=token, targets=set())
    assert isinstance(obj, plugins.NotifyPushover) is True
    # Default is to send to all devices, so there will be a
    # device defined here
    assert len(obj.targets) == 1


@mock.patch('requests.get')
@mock.patch('requests.post')
def test_notify_rocketchat_plugin(mock_post, mock_get):
    """
    API: NotifyRocketChat() Extra Checks

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # Chat ID
    recipients = 'AbcD1245, @l2g, @lead2gold, #channel, #channel2'

    # Authentication
    user = 'myuser'
    password = 'mypass'

    # Prepare Mock
    mock_get.return_value = requests.Request()
    mock_post.return_value = requests.Request()
    mock_post.return_value.status_code = requests.codes.ok
    mock_get.return_value.status_code = requests.codes.ok
    mock_post.return_value.content = ''
    mock_get.return_value.content = ''

    obj = plugins.NotifyRocketChat(
        user=user, password=password, targets=recipients)
    assert isinstance(obj, plugins.NotifyRocketChat) is True
    assert len(obj.channels) == 2
    assert len(obj.users) == 2
    assert len(obj.rooms) == 1

    # No Webhook specified
    try:
        obj = plugins.NotifyRocketChat(webhook=None, mode='webhook')
        # We should have thrown an exception before we get to the next
        # assert line:
        assert False
    except TypeError:
        # We're in good shape if we reach here as we got the expected error
        assert True

    #
    # Logout
    #
    assert obj.logout() is True

    # Prepare Mock to fail
    mock_post.return_value.status_code = requests.codes.internal_server_error
    mock_get.return_value.status_code = requests.codes.internal_server_error

    #
    # Send Notification
    #
    assert obj.notify(
        body='body', title='title', notify_type=NotifyType.INFO) is False
    assert obj._send(payload='test', notify_type=NotifyType.INFO) is False

    #
    # Logout
    #
    assert obj.logout() is False

    # KeyError handling
    mock_post.return_value.status_code = 999
    mock_get.return_value.status_code = 999

    #
    # Send Notification
    #
    assert obj.notify(
        body='body', title='title', notify_type=NotifyType.INFO) is False
    assert obj._send(payload='test', notify_type=NotifyType.INFO) is False

    #
    # Logout
    #
    assert obj.logout() is False

    # Generate exceptions
    mock_get.side_effect = requests.ConnectionError(
        0, 'requests.ConnectionError() not handled')
    mock_post.side_effect = mock_get.side_effect

    #
    # Send Notification
    #
    assert obj._send(payload='test', notify_type=NotifyType.INFO) is False

    # Attempt the check again but fake a successful login
    obj.login = mock.Mock()
    obj.login.return_value = True
    assert obj.notify(
        body='body', title='title', notify_type=NotifyType.INFO) is False
    #
    # Logout
    #
    assert obj.logout() is False


@mock.patch('requests.get')
@mock.patch('requests.post')
def test_notify_telegram_plugin(mock_post, mock_get):
    """
    API: NotifyTelegram() Extra Checks

    """
    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # Bot Token
    bot_token = '123456789:abcdefg_hijklmnop'
    invalid_bot_token = 'abcd:123'

    # Chat ID
    chat_ids = 'l2g, lead2gold'

    # Prepare Mock
    mock_get.return_value = requests.Request()
    mock_post.return_value = requests.Request()
    mock_post.return_value.status_code = requests.codes.ok
    mock_get.return_value.status_code = requests.codes.ok
    mock_get.return_value.content = '{}'
    mock_post.return_value.content = '{}'

    try:
        obj = plugins.NotifyTelegram(bot_token=None, targets=chat_ids)
        # invalid bot token (None)
        assert False

    except TypeError:
        # Exception should be thrown about the fact no token was specified
        assert True

    try:
        obj = plugins.NotifyTelegram(
            bot_token=invalid_bot_token, targets=chat_ids)
        # invalid bot token
        assert False

    except TypeError:
        # Exception should be thrown about the fact an invalid token was
        # specified
        assert True

    obj = plugins.NotifyTelegram(
        bot_token=bot_token, targets=chat_ids, include_image=True)
    assert isinstance(obj, plugins.NotifyTelegram) is True
    assert len(obj.targets) == 2

    # Test Image Sending Exceptions
    mock_get.side_effect = IOError()
    mock_post.side_effect = IOError()
    obj.send_image(obj.targets[0], NotifyType.INFO)

    # Restore their entries
    mock_get.side_effect = None
    mock_post.side_effect = None
    mock_get.return_value.content = '{}'
    mock_post.return_value.content = '{}'

    # test url call
    assert isinstance(obj.url(), six.string_types) is True
    # Test that we can load the string we generate back:
    obj = plugins.NotifyTelegram(**plugins.NotifyTelegram.parse_url(obj.url()))
    assert isinstance(obj, plugins.NotifyTelegram) is True

    # Prepare Mock to fail
    response = mock.Mock()
    response.status_code = requests.codes.internal_server_error

    # a error response
    response.content = dumps({
        'description': 'test',
    })
    mock_get.return_value = response
    mock_post.return_value = response

    # No image asset
    nimg_obj = plugins.NotifyTelegram(bot_token=bot_token, targets=chat_ids)
    nimg_obj.asset = AppriseAsset(image_path_mask=False, image_url_mask=False)

    # Test that our default settings over-ride base settings since they are
    # not the same as the one specified in the base; this check merely
    # ensures our plugin inheritance is working properly
    assert obj.body_maxlen == plugins.NotifyTelegram.body_maxlen

    # We don't override the title maxlen so we should be set to the same
    # as our parent class in this case
    assert obj.title_maxlen == plugins.NotifyBase.title_maxlen

    # This tests erroneous messages involving multiple chat ids
    assert obj.notify(
        body='body', title='title', notify_type=NotifyType.INFO) is False
    assert obj.notify(
        body='body', title='title', notify_type=NotifyType.INFO) is False
    assert nimg_obj.notify(
        body='body', title='title', notify_type=NotifyType.INFO) is False

    # This tests erroneous messages involving a single chat id
    obj = plugins.NotifyTelegram(bot_token=bot_token, targets='l2g')
    nimg_obj = plugins.NotifyTelegram(bot_token=bot_token, targets='l2g')
    nimg_obj.asset = AppriseAsset(image_path_mask=False, image_url_mask=False)

    assert obj.notify(
        body='body', title='title', notify_type=NotifyType.INFO) is False
    assert nimg_obj.notify(
        body='body', title='title', notify_type=NotifyType.INFO) is False

    # Bot Token Detection
    # Just to make it clear to people reading this code and trying to learn
    # what is going on.  Apprise tries to detect the bot owner if you don't
    # specify a user to message.  The idea is to just default to messaging
    # the bot owner himself (it makes it easier for people).  So we're testing
    # the creating of a Telegram Notification without providing a chat ID.
    # We're testing the error handling of this bot detection section of the
    # code
    mock_post.return_value.content = dumps({
        "ok": True,
        "result": [{
            "update_id": 645421321,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 532389719,
                    "is_bot": False,
                    "first_name": "Chris",
                    "language_code": "en-US"
                },
                "chat": {
                    "id": 532389719,
                    "first_name": "Chris",
                    "type": "private"
                },
                "date": 1519694394,
                "text": "/start",
                "entities": [{
                    "offset": 0,
                    "length": 6,
                    "type": "bot_command",
                }],
            }},
        ],
    })
    mock_post.return_value.status_code = requests.codes.ok

    obj = plugins.NotifyTelegram(bot_token=bot_token, targets=None)
    assert len(obj.targets) == 1
    assert obj.targets[0] == '532389719'

    # Do the test again, but without the expected (parsed response)
    mock_post.return_value.content = dumps({
        "ok": True,
        "result": [{
            "message": {
                "text": "/ignored.entry",
            }},
        ],
    })
    try:
        obj = plugins.NotifyTelegram(bot_token=bot_token, targets=None)
        # No chat_ids specified
        assert False

    except TypeError:
        # Exception should be thrown about the fact no token was specified
        assert True

    # Detect the bot with a bad response
    mock_post.return_value.content = dumps({})
    obj.detect_bot_owner()

    # Test our bot detection with a internal server error
    mock_post.return_value.status_code = requests.codes.internal_server_error
    try:
        obj = plugins.NotifyTelegram(bot_token=bot_token, targets=None)
        # No chat_ids specified
        assert False

    except TypeError:
        # Exception should be thrown about the fact no token was specified
        assert True

    # Test our bot detection with an unmappable html error
    mock_post.return_value.status_code = 999
    try:
        obj = plugins.NotifyTelegram(bot_token=bot_token, targets=None)
        # No chat_ids specified
        assert False

    except TypeError:
        # Exception should be thrown about the fact no token was specified
        assert True

    # Do it again but this time provide a failure message
    mock_post.return_value.content = dumps({'description': 'Failure Message'})
    try:
        obj = plugins.NotifyTelegram(bot_token=bot_token, targets=None)
        # No chat_ids specified
        assert False

    except TypeError:
        # Exception should be thrown about the fact no token was specified
        assert True

    # Do it again but this time provide a failure message and perform a
    # notification without a bot detection by providing at least 1 chat id
    obj = plugins.NotifyTelegram(bot_token=bot_token, targets=['@abcd'])
    assert nimg_obj.notify(
        body='body', title='title', notify_type=NotifyType.INFO) is False

    # iterate over our exceptions and test them
    for _exception in REQUEST_EXCEPTIONS:
        mock_post.side_effect = _exception
        try:
            obj = plugins.NotifyTelegram(bot_token=bot_token, targets=None)
            # No chat_ids specified
            assert False

        except TypeError:
            # Exception should be thrown about the fact no token was specified
            assert True


def test_notify_overflow_truncate():
    """
    API: Overflow Truncate Functionality Testing

    """
    #
    # A little preparation
    #

    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # Number of characters per line
    row = 24

    # Some variables we use to control the data we work with
    body_len = 1024
    title_len = 1024

    # Create a large body and title with random data
    body = ''.join(choice(str_alpha + str_num + ' ') for _ in range(body_len))
    body = '\r\n'.join([body[i: i + row] for i in range(0, len(body), row)])

    # the new lines add a large amount to our body; lets force the content
    # back to being 1024 characters.
    body = body[0:1024]

    # Create our title using random data
    title = ''.join(choice(str_alpha + str_num) for _ in range(title_len))

    #
    # First Test: Truncated Title
    #
    class TestNotification(NotifyBase):

        # Test title max length
        title_maxlen = 10

        def __init__(self, *args, **kwargs):
            super(TestNotification, self).__init__(**kwargs)

        def notify(self, *args, **kwargs):
            # Pretend everything is okay
            return True

    try:
        # Load our object
        obj = TestNotification(overflow='invalid')

        # We should have thrown an exception because our specified overflow
        # is wrong.
        assert False

    except TypeError:
        # Expected to be here
        assert True

    # Load our object
    obj = TestNotification(overflow=OverflowMode.TRUNCATE)
    assert obj is not None

    # Verify that we break the title to a max length of our title_max
    # and that the body remains untouched
    chunks = obj._apply_overflow(body=body, title=title, overflow=None)
    chunks = obj._apply_overflow(
        body=body, title=title, overflow=OverflowMode.SPLIT)
    assert len(chunks) == 1
    assert body.rstrip() == chunks[0].get('body')
    assert title[0:TestNotification.title_maxlen] == chunks[0].get('title')

    #
    # Next Test: Line Count Control
    #

    class TestNotification(NotifyBase):

        # Test title max length
        title_maxlen = 5

        # Maximum number of lines
        body_max_line_count = 5

        def __init__(self, *args, **kwargs):
            super(TestNotification, self).__init__(**kwargs)

        def notify(self, *args, **kwargs):
            # Pretend everything is okay
            return True

    # Load our object
    obj = TestNotification(overflow=OverflowMode.TRUNCATE)
    assert obj is not None

    # Verify that we break the title to a max length of our title_max
    # and that the body remains untouched
    chunks = obj._apply_overflow(body=body, title=title)
    assert len(chunks) == 1
    assert len(chunks[0].get('body').split('\n')) == \
        TestNotification.body_max_line_count
    assert title[0:TestNotification.title_maxlen] == chunks[0].get('title')

    #
    # Next Test: Truncated body
    #

    class TestNotification(NotifyBase):

        # Test title max length
        title_maxlen = title_len

        # Enforce a body length of just 10
        body_maxlen = 10

        def __init__(self, *args, **kwargs):
            super(TestNotification, self).__init__(**kwargs)

        def notify(self, *args, **kwargs):
            # Pretend everything is okay
            return True

    # Load our object
    obj = TestNotification(overflow=OverflowMode.TRUNCATE)
    assert obj is not None

    # Verify that we break the title to a max length of our title_max
    # and that the body remains untouched
    chunks = obj._apply_overflow(body=body, title=title)
    assert len(chunks) == 1
    assert body[0:TestNotification.body_maxlen] == chunks[0].get('body')
    assert title == chunks[0].get('title')

    #
    # Next Test: Append title to body + Truncated body
    #

    class TestNotification(NotifyBase):

        # Enforce no title
        title_maxlen = 0

        # Enforce a body length of just 100
        body_maxlen = 100

        def __init__(self, *args, **kwargs):
            super(TestNotification, self).__init__(**kwargs)

        def notify(self, *args, **kwargs):
            # Pretend everything is okay
            return True

    # Load our object
    obj = TestNotification(overflow=OverflowMode.TRUNCATE)
    assert obj is not None

    # Verify that we break the title to a max length of our title_max
    # and that the body remains untouched

    obj.notify_format = NotifyFormat.HTML
    chunks = obj._apply_overflow(body=body, title=title)
    assert len(chunks) == 1

    obj.notify_format = NotifyFormat.MARKDOWN
    chunks = obj._apply_overflow(body=body, title=title)
    assert len(chunks) == 1

    obj.notify_format = NotifyFormat.TEXT
    chunks = obj._apply_overflow(body=body, title=title)
    assert len(chunks) == 1

    # The below line should be read carefully... We're actually testing to see
    # that our title is matched against our body. Behind the scenes, the title
    # was appended to the body. The body was then truncated to the maxlen.
    # The thing is, since the title is so large, all of the body was lost
    # and a good chunk of the title was too.  The message sent will just be a
    # small portion of the title
    assert len(chunks[0].get('body')) == TestNotification.body_maxlen
    assert title[0:TestNotification.body_maxlen] == chunks[0].get('body')


def test_notify_overflow_split():
    """
    API: Overflow Split Functionality Testing

    """

    #
    # A little preparation
    #

    # Disable Throttling to speed testing
    plugins.NotifyBase.request_rate_per_sec = 0

    # Number of characters per line
    row = 24

    # Some variables we use to control the data we work with
    body_len = 1024
    title_len = 1024

    # Create a large body and title with random data
    body = ''.join(choice(str_alpha + str_num) for _ in range(body_len))
    body = '\r\n'.join([body[i: i + row] for i in range(0, len(body), row)])

    # the new lines add a large amount to our body; lets force the content
    # back to being 1024 characters.
    body = body[0:1024]

    # Create our title using random data
    title = ''.join(choice(str_alpha + str_num) for _ in range(title_len))

    #
    # First Test: Truncated Title
    #
    class TestNotification(NotifyBase):

        # Test title max length
        title_maxlen = 10

        def __init__(self, *args, **kwargs):
            super(TestNotification, self).__init__(**kwargs)

        def notify(self, *args, **kwargs):
            # Pretend everything is okay
            return True

    # Load our object
    obj = TestNotification(overflow=OverflowMode.SPLIT)
    assert obj is not None

    # Verify that we break the title to a max length of our title_max
    # and that the body remains untouched
    chunks = obj._apply_overflow(body=body, title=title)
    assert len(chunks) == 1
    assert body == chunks[0].get('body')
    assert title[0:TestNotification.title_maxlen] == chunks[0].get('title')

    #
    # Next Test: Line Count Control
    #

    class TestNotification(NotifyBase):

        # Test title max length
        title_maxlen = 5

        # Maximum number of lines
        body_max_line_count = 5

        def __init__(self, *args, **kwargs):
            super(TestNotification, self).__init__(**kwargs)

        def notify(self, *args, **kwargs):
            # Pretend everything is okay
            return True

    # Load our object
    obj = TestNotification(overflow=OverflowMode.SPLIT)
    assert obj is not None

    # Verify that we break the title to a max length of our title_max
    # and that the body remains untouched
    chunks = obj._apply_overflow(body=body, title=title)
    assert len(chunks) == 1
    assert len(chunks[0].get('body').split('\n')) == \
        TestNotification.body_max_line_count
    assert title[0:TestNotification.title_maxlen] == chunks[0].get('title')

    #
    # Next Test: Split body
    #

    class TestNotification(NotifyBase):

        # Test title max length
        title_maxlen = title_len

        # Enforce a body length
        # Wrap in int() so Python v3 doesn't convert the response into a float
        body_maxlen = int(body_len / 4)

        def __init__(self, *args, **kwargs):
            super(TestNotification, self).__init__(**kwargs)

        def notify(self, *args, **kwargs):
            # Pretend everything is okay
            return True

    # Load our object
    obj = TestNotification(overflow=OverflowMode.SPLIT)
    assert obj is not None

    # Verify that we break the title to a max length of our title_max
    # and that the body remains untouched
    chunks = obj._apply_overflow(body=body, title=title)
    offset = 0
    assert len(chunks) == 4
    for chunk in chunks:
        # Our title never changes
        assert title == chunk.get('title')

        # Our body is only broken up; not lost
        _body = chunk.get('body')
        assert body[offset: len(_body) + offset].rstrip() == _body
        offset += len(_body)

    #
    # Next Test: Append title to body + split body
    #

    class TestNotification(NotifyBase):

        # Enforce no title
        title_maxlen = 0

        # Enforce a body length based on the title
        # Wrap in int() so Python v3 doesn't convert the response into a float
        body_maxlen = int(title_len / 4)

        def __init__(self, *args, **kwargs):
            super(TestNotification, self).__init__(**kwargs)

        def notify(self, *args, **kwargs):
            # Pretend everything is okay
            return True

    # Load our object
    obj = TestNotification(overflow=OverflowMode.SPLIT)
    assert obj is not None

    # Verify that we break the title to a max length of our title_max
    # and that the body remains untouched
    chunks = obj._apply_overflow(body=body, title=title)

    # Our final product is that our title has been appended to our body to
    # create one great big body. As a result we'll get quite a few lines back
    # now.
    offset = 0

    # Our body will look like this in small chunks at the end of the day
    bulk = title + '\r\n' + body

    # Due to the new line added to the end
    assert len(chunks) == (
        # wrap division in int() so Python 3 doesn't convert it to a float on
        # us
        int(len(bulk) / TestNotification.body_maxlen) +
        (1 if len(bulk) % TestNotification.body_maxlen else 0))

    for chunk in chunks:
        # Our title is empty every time
        assert chunk.get('title') == ''

        _body = chunk.get('body')
        assert bulk[offset: len(_body) + offset] == _body
        offset += len(_body)
