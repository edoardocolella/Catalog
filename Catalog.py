import json
import time
import uuid
import datetime
import cherrypy
import paho.mqtt.client as PahoMQTT


class Presentation(object):
    exposed = True

    def GET(self, *uri):
        if len(uri) == 0:
            index = '{"subscriptions": { ' \
               '"REST": {                   ' \
               '  "device": "http://127.0.0.1:8080/devices/subscription",' \
               '  "service": "http://127.0.0.1:8080/services/subscription",' \
               '  "user": "http://127.0.0.1:8080/users/subscription"' \
               ' },' \
               ' "MQTT": {' \
               '    "device": {' \
               '       "hostname": "mqtt.eclipseprojects.io",' \
               '        "port": 1883,' \
               '        "topic": "tiot/7/catalog/devices/subscription"' \
               '     }' \
               '  }' \
               '  }' \
               '}'
            return index
        else:
            return "ERROR"

    def POST(self, *uri, **params):
        return "ERROR 405 Method Not Allowed"

    def PUT(self, *uri, **params):
        return "ERROR 405 Method Not Allowed"
    def DELETE(self, *uri, **params):
        return "ERROR 405 Method Not Allowed"

class Device(object):
    exposed = True

    def GET(self, *uri):
        if len(uri) == 0:
            output = str(devices)
            output = output.replace("'", '"')
            return output
        else:
            if uri[0] in devices:
                output = str(devices[uri[0]])
                output = output.replace("'", '"')
                return output  # aggiungere check
            else:
                return "ERROR"

    def POST(self, *uri, **params):
        if len(uri) > 1 and uri[0] == "subscription":
            print(devices[uri[1]]["timestamp"])
            devices[uri[1]]["timestamp"] = str(datetime.datetime.now())
            print(devices[uri[1]]["timestamp"])
            # fare check
        else:
            return "ERROR"

    def PUT(self, *uri, **params):
        if uri[0] == "subscription":
            rawbody = cherrypy.request.body.read()
            x = json.loads(rawbody)
            mac_address = x["MAC_ADDRESS"]
            devices[mac_address] = x
            devices[mac_address]["timestamp"] = str(datetime.datetime.now())
            print(devices)
            return str(mac_address)
        else:
            return "ERROR"

    def DELETE(self, *uri, **params):
        return "ERROR 405 Method Not Allowed"

class User(object):
    exposed = True

    def GET(self, *uri):
        if len(uri) == 0:
            output = str(users)
            output = output.replace("'", '"')
            return output
        else:
            if uri[0] in users:
                output = str(users[uri[0]])
                output = output.replace("'", '"')
                return output
            else:
                return "ERROR"

    def POST(self, *uri, **params):
        return "ERROR 405 Method Not Allowed"

    def PUT(self, *uri, **params):
        if uri[0] == "subscription":
            rawbody = cherrypy.request.body.read()
            x = json.loads(rawbody)
            a = str(uuid.uuid1())
            users[a] = x

            # print(users)
            # print(users[a])
            return str(a)
        else:
            return "ERROR"

    def DELETE(self, *uri, **params):
        return "ERROR 405 Method Not Allowed"

class Service(object):
    exposed = True

    def GET(self, *uri):
        if len(uri) == 0:
            output = str(services)
            output = output.replace("'", '"')
            return output
        else:
            if uri[0] in users:
                 output = str(services[uri[0]])
                 output = output.replace("'", '"')
                 return output  
            else:
                return "ERROR"

    def POST(self, *uri, **params):
        return "ERROR 405 Method Not Allowed"

    def PUT(self, *uri, **params):

        if uri[0] == "subscription":
            rawbody = cherrypy.request.body.read()
            x = json.loads(rawbody)
            a = str(uuid.uuid1())
            services[a] = x
            services[a]["timestamp"] = str(datetime.datetime.now())
            print(services)
            print(services[a])
            return str(a)
        else:
            return "ERROR"

    def DELETE(self, *uri, **params):
        return "ERROR 405 Method Not Allowed"


def myOnConnect(client, userdata, flags, rc):
    print("Connected to %s with result code: %d" % (messageBroker, rc))


def myOnMessageReceived(paho_mqtt, userdata, msg):
    # A new message is received
    print("Topic:'" + msg.topic + "', QoS: '" + str(msg.qos) + "' Message: '" + str(msg.payload) + "'")
    output = msg.payload
    output = output.decode('utf-8')
    #output = output.replace("'", '"')
    x = json.loads(output)

    mac_address = x["MAC_Address"]

    if mac_address in devices:
        devices[mac_address]["timestamp"] = str(datetime.datetime.now())
    else:
        devices[mac_address] = x
        devices[mac_address]["timestamp"] = str(datetime.datetime.now())
        print("registrato dispositivo %s" % mac_address)
        clientMqtt.publish("tiot/7/catalog/devices/subscription/aa_aa_aa", "all fine")


if __name__ == "__main__":
    # Standard configuration to serve the url "localhost:8080"
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
        }
    }

    devices = {}
    users = {}
    services = {}

    topic = "tiot/7/catalog/devices/subscription"
    messageBroker = "mqtt.eclipseprojects.io"
    port = 1883

    # create an instance of paho.mqtt.client
    clientMqtt = PahoMQTT.Client("CatalogClient", False)

    # register the callback
    clientMqtt.on_connect = myOnConnect
    clientMqtt.on_message = myOnMessageReceived

    # manage connection to broker
    clientMqtt.connect(messageBroker, port)
    clientMqtt.loop_start()
    clientMqtt.subscribe(topic, 2)

    cherrypy.tree.mount(Service(), '/services', conf)
    cherrypy.tree.mount(Device(), '/devices', conf)
    cherrypy.tree.mount(User(), '/users', conf)
    cherrypy.tree.mount(Presentation(), '/', conf)

    # cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    # cherrypy.config.update({'server.socket_port': 8080})
    cherrypy.engine.start()
    cherrypy.engine.block()

    clientMqtt.unsubscribe(topic)
    clientMqtt.loop_stop()
    clientMqtt.disconnect()
