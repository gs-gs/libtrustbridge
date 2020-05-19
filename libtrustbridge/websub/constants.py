VALID_REQUEST_CONTENT_TYPE = 'application/x-www-form-urlencoded'

TOPIC_ATTR_KEY = 'hub.topic'
CALLBACK_ATTR_KEY = 'hub.callback'
MODE_ATTR_KEY = 'hub.mode'
LEASE_SECONDS_ATTR_KEY = 'hub.lease_seconds'
SECRET_ATTR_KEY = 'hub.secret'


__HOUR = 3600
__DAY = __HOUR * 24

LEASE_SECONDS_DEFAULT_VALUE = 5 * __DAY
LEASE_SECONDS_MIN_VALUE = __HOUR
LEASE_SECONDS_MAX_VALUE = __DAY * 365

REQUIRED_ATTRS = [
    TOPIC_ATTR_KEY,
    CALLBACK_ATTR_KEY,
    MODE_ATTR_KEY
]

OPTIONAL_ATTRS = [
    LEASE_SECONDS_ATTR_KEY
]

ATTRS_DEFAULTS = {
    LEASE_SECONDS_ATTR_KEY: LEASE_SECONDS_DEFAULT_VALUE
}

MODE_ATTR_SUBSCRIBE_VALUE = 'subscribe'
MODE_ATTR_UNSUBSCRIBE_VALUE = 'unsubscribe'

SUPPORTED_CALLBACK_URL_SCHEMES = [
    'http',
    'https'
]
