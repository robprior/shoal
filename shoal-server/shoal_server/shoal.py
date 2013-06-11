import sys
import os
import web
import json
import urllib
import logging
import pika
import socket
import uuid
from time import time, sleep
from threading import Thread

import config
import utilities

"""
    Main application that will monitor RabbitMQ and ShoalUpdate threads.
    Web.py thread is handled separately.
"""
class ThreadMonitor(Thread):

    def __init__(self):
        # check if geolitecity database needs updating
        if utilities.check_geolitecity_need_update():
            utilities.download_geolitecity()

        Thread.__init__(self)
        self.threads = []

        rabbitmq_thread = RabbitMQConsumer()
        rabbitmq_thread.daemon = True
        self.threads.append(rabbitmq_thread)

        update_thread = ShoalUpdate()
        update_thread.daemon = True
        self.threads.append(update_thread)

    def run(self):
        for thread in self.threads:
            print "starting", thread
            thread.start()
        while True:
            for thread in self.threads:
                if not thread.is_alive():
                    logging.error('{0} died. Stopping application...'.format(thread))
                    sys.exit(1)
            sleep(1)

    def stop(self):
        print "\nShutting down Shoal-Server... Please wait."
        try:
            self.rabbitmq.stop()
            self.update.stop()
        except Exception as e:
            logging.error(e)
            sys.exit(1)
        finally:
            sleep(2)
        sys.exit()

"""
    ShoalUpdate is used for trimming inactive squids every set interval.
"""
class ShoalUpdate(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.inactive = config.squid_inactive_time
        self.interval = config.squid_cleanse_interval
        self.running = False

    def run(self):
        self.running = True
        self.update()
        while self.running:
            sleep(self.interval)
            self.update()

    def update(self):
        curr = time()
        shoal_list = utilities.get_shoal()
        shoal_temp = {}
        for squid in shoal_list:
            if curr - shoal_list[squid]['last_active'] < self.inactive:
                shoal_temp[squid] = shoal_list[squid]
        utilities.set_shoal(shoal_temp)

    def stop(self):
        self.running = False

"""
    Webpy webserver used to serve up active squid lists and API calls.
    Can run as either the development server or under mod_wsgi.
"""
class WebpyServer(Thread):

    def __init__(self):
        Thread.__init__(self)
        web.config.debug = False
        self.app = None
        self.urls = (
            '/nearest/?(\d+)?/?', 'shoal_server.view.nearest',
            '/wpad.dat', 'shoal_server.view.wpad',
            '/(\d+)?/?', 'shoal_server.view.index',
        )
    def run(self):
        try:
            self.app = web.application(self.urls, globals())
            self.app.run()
        except Exception as e:
            logging.error("Could not start webpy server.\n{0}".format(e))
            sys.exit(1)

    def wsgi(self):
        return web.application(self.urls, globals()).wsgifunc()

    def stop(self):
        self.app.stop()

"""
    Basic RabbitMQ async consumer.
    Consumes messages from a unique queue that is declared when Shoal server first starts.
"""
class RabbitMQConsumer(Thread):

    QUEUE = socket.gethostname() + "-" + uuid.uuid1().hex
    ROUTING_KEY = '#'

    def __init__(self):
        Thread.__init__(self)
        self.host = "{0}/{1}".format(config.amqp_server_url, urllib.quote_plus(config.amqp_virtual_host))
        self.exchange = config.amqp_exchange
        self.exchange_type = config.amqp_exchange_type
        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None

    def connect(self):
        try:
            return pika.SelectConnection(pika.URLParameters(self.host),
                                             self.on_connection_open,
                                             stop_ioloop_on_close=False)
        except pika.exceptions.AMQPConnectionError as e:
            logging.error("Could not connect to AMQP Server. Retrying in 30 seconds...")
            sleep(30)
            self.run()

    def close_connection(self):
        self._connection.close()

    def add_on_connection_close_callback(self):
        self._connection.add_on_close_callback(self.on_connection_closed)

    def on_connection_closed(self, connection, reply_code, reply_text):
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            logging.warning('Connection closed, reopening in 5 seconds: (%s) %s',
                           reply_code, reply_text)
            self._connection.add_timeout(5, self.reconnect)

    def on_connection_open(self, unused_connection):
        self.add_on_connection_close_callback()
        self.open_channel()

    def reconnect(self):
        # This is the old connection IOLoop instance, stop its ioloop
        self._connection.ioloop.stop()
        if not self._closing:
            # Create a new connection
            self._connection = self.connect()
            # There is now a new connection, needs a new ioloop to run
            self._connection.ioloop.start()

    def add_on_channel_close_callback(self):
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reply_code, reply_text):
        logging.warning('Channel was closed: (%s) %s', reply_code, reply_text)
        self._connection.close()

    def on_channel_open(self, channel):
        self._channel = channel
        self.add_on_channel_close_callback()
        self.setup_exchange(self.exchange)

    def setup_exchange(self, exchange_name):
        self._channel.exchange_declare(self.on_exchange_declareok,
                                       exchange_name,
                                       self.exchange_type)

    def on_exchange_declareok(self, unused_frame):
        self.setup_queue(self.QUEUE)

    def setup_queue(self, queue_name):
        self._channel.queue_declare(self.on_queue_declareok, queue_name, auto_delete=True)

    def on_queue_declareok(self, method_frame):
        self._channel.queue_bind(self.on_bindok, self.QUEUE,
                                 self.exchange, self.ROUTING_KEY)

    def add_on_cancel_callback(self):
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        if self._channel:
            self._channel.close()

    def acknowledge_message(self, delivery_tag):
        self._channel.basic_ack(delivery_tag)

    def on_cancelok(self, unused_frame):
        self.close_channel()

    def stop_consuming(self):
        if self._channel:
            self._channel.basic_cancel(self.on_cancelok, self._consumer_tag)

    def start_consuming(self):
        self.add_on_cancel_callback()
        self._consumer_tag = self._channel.basic_consume(self.on_message,
                                                         self.QUEUE)

    def on_bindok(self, unused_frame):
        self.start_consuming()

    def close_channel(self):
        self._channel.close()

    def open_channel(self):
        self._connection.channel(on_open_callback=self.on_channel_open)

    def run(self):
        try:
            self._connection = self.connect()
        except Exception as e:
            logging.error("Unable to connect ot RabbitMQ Server. {0}".format(e))
            sys.exit(1)
        self._connection.ioloop.start()

    def stop(self):
        self._closing = True
        self.stop_consuming()
        self._connection.ioloop.start()

    def on_message(self, unused_channel, basic_deliver, properties, body):
        try:
            data = json.loads(body)
            key = data['uuid']
        except ValueError as e:
            logging.error("Message body could not be decoded. Message: {1}".format(body))
            return
        except KeyError:
            logging.error("message body is missing a unique identifier, discarding...")
            return
        finally:
            self.acknowledge_message(basic_deliver.delivery_tag)

        shoal_list = utilities.get_shoal()

        if key in shoal_list:
            shoal_list[key]['load'] = data['load']
            shoal_list[key]['last_active'] = time()
        else:
            try:
                geo_data = utilities.get_geolocation(data['public_ip'])
            except KeyError as e:
                try:
                    geo_data = utilities.get_geolocation(data['external_ip'])
                except KeyError as f:
                    logging.error("Could not generate geo location data, discarding...")
                    return
            shoal_list[key] = data
            shoal_list[key]['geo_data'] = geo_data
            shoal_list[key]['last_active'] = shoal_list[key]['created'] = time()

        utilities.set_shoal(shoal_list)
