from io import BytesIO
from unittest import TestCase, mock

from freezegun import freeze_time

from libtrustbridge.websub.domain import Pattern, Id
from libtrustbridge.websub.exceptions import SubscriptionMissingExpiration
from libtrustbridge.websub.repos import SubscriptionsRepo


@freeze_time('2020-05-18 14:08:00')
class SubscriptionsRepoTest(TestCase):
    def setUp(self):
        boto3_patch = mock.patch('libtrustbridge.repos.miniorepo.boto3')
        self.boto3 = boto3_patch.start()
        self.client = self.boto3.client.return_value
        self.addCleanup(boto3_patch.stop)
        self.connection_data = {
            'access_key': 'awsAccessKeyId',
            'secret_key': 'awsSecretAccessKey',
            'host': 'some_host',
            'port': '1111',
            'use_ssl': False,
        }

    def test_subscribe_by_id__should_put_object_into_repo(self):
        repo = SubscriptionsRepo(connection_data=self.connection_data)
        id = Id('some_ref')

        repo.subscribe_by_id(id, 'http://callback.url/1', expiration_seconds=3600)
        self.client.put_object.assert_called_once()
        args, kwargs = self.client.put_object.call_args

        assert kwargs['Bucket'] == 'subscriptions'
        assert kwargs['Key'] == 'some_ref/ff0d1111f6636c354cf92c7137f1b5e6'
        assert kwargs['Body'].read() == b'{"c": "http://callback.url/1", "e": "2020-05-18T15:08:00"}'

    def test_subscribe_by_id__with_missing_expiration__should_return_error(self):
        repo = SubscriptionsRepo(connection_data=self.connection_data)
        id = Id('some_ref')
        with self.assertRaises(SubscriptionMissingExpiration):
            repo.subscribe_by_id(id, 'http://callback.url/1', expiration_seconds=0)

    def test_subscribe_by_pattern__should_put_object_into_repo(self):
        repo = SubscriptionsRepo(connection_data=self.connection_data)
        pattern = Pattern('aaa.bbb.ccc')

        repo.subscribe_by_pattern(pattern, 'http://callback.url/1', expiration_seconds=3600)
        self.client.put_object.assert_called_once()
        args, kwargs = self.client.put_object.call_args

        assert kwargs['Bucket'] == 'subscriptions'
        assert kwargs['Key'] == 'AAA/BBB/CCC/ff0d1111f6636c354cf92c7137f1b5e6'
        assert kwargs['Body'].read() == b'{"c": "http://callback.url/1", "e": "2020-05-18T15:08:00"}'

    def test_subscribe_by_pattern__with_missing_expiration__should_return_error(self):
        repo = SubscriptionsRepo(connection_data=self.connection_data)
        pattern = Pattern('aaa.bbb.ccc')
        with self.assertRaises(SubscriptionMissingExpiration):
            repo.subscribe_by_pattern(pattern, 'http://callback.url/1', expiration_seconds=0)

    def test_get_subscriptions_by_id__should_return_subscriptions(self):
        repo = SubscriptionsRepo(connection_data=self.connection_data)
        self.client.list_objects.return_value = {
            'Contents': [{'Key': 'some_ref/ff0d1111f6636c354cf92c7137f1b5e6'}]
        }
        self.client.get_object.return_value = {
            'Body': BytesIO(b'{"c": "http://callback.url/1", "e": "2020-05-18T15:08:00"}'),
            'Bucket': 'subscriptions',
            'ContentLength': 39,
            'Key': 'some_ref/ff0d1111f6636c354cf92c7137f1b5e6',
        }

        subscriptions = repo.get_subscriptions_by_id(Id('some_ref'))

        assert list(subscriptions)[0].callback_url == 'http://callback.url/1'
        self.client.list_objects.assert_called_once_with(
            Bucket='subscriptions', Prefix='some_ref', Delimiter='/'
        )
        self.client.get_object.assert_called_once_with(
            Bucket='subscriptions',
            Key='some_ref/ff0d1111f6636c354cf92c7137f1b5e6'
        )

    def test_get_subscriptions_by_pattern__should_return_subscriptions(self):
        repo = SubscriptionsRepo(connection_data=self.connection_data)
        self.client.list_objects.side_effect = [
            {'Contents': []},
            {'Contents': [{'Key': 'AA/BB/ff0d1111f6636c354cf92c7137f1b5e6'}]}
        ]
        self.client.get_object.return_value = {
            'Body': BytesIO(b'{"c": "http://callback.url/1", "e": "2020-05-18T15:08:00"}'),
            'Bucket': 'subscriptions',
            'ContentLength': 39,
            'Key': 'AA',
        }

        subscriptions = repo.get_subscriptions_by_pattern(Pattern('aa.bb'))
        assert len(list(subscriptions)) == 1
        assert list(subscriptions)[0].callback_url == 'http://callback.url/1'
        assert self.client.list_objects.mock_calls == [
            mock.call(Bucket='subscriptions', Prefix='AA/', Delimiter='/'),
            mock.call(Bucket='subscriptions', Prefix='AA/BB/', Delimiter='/')
        ]
        self.client.get_object.assert_called_once_with(Bucket='subscriptions', Key='AA/BB/ff0d1111f6636c354cf92c7137f1b5e6')

    def test_get_subscriptions_by_pattern__when_same_callback__should_return_one(self):
        repo = SubscriptionsRepo(connection_data=self.connection_data)
        self.client.list_objects.side_effect = [
            {'Contents': [{'Key': 'AA/ff0d1111f6636c354cf92c7137f1b5e6'}]},
            {'Contents': [{'Key': 'AA/BB/ff0d1111f6636c354cf92c7137f1b5e6'}]},
        ]
        self.client.get_object.side_effect = [
            {
                'Body': BytesIO(b'{"c": "http://callback.url/1", "e": "2020-05-18T15:08:00"}'),
                'Bucket': 'subscriptions',
                'ContentLength': 39,
                'Key': 'AA',
            },
            {
                'Body': BytesIO(b'{"c": "http://callback.url/1", "e": "2020-05-18T15:08:00"}'),
                'Bucket': 'subscriptions',
                'ContentLength': 39,
                'Key': 'AA/BB',
            },
        ]

        subscriptions = repo.get_subscriptions_by_pattern(Pattern('aa'))
        assert len(subscriptions) == 1
