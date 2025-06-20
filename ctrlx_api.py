import requests
import json
import threading
requests.packages.urllib3.disable_warnings()

def parse_sse_event(raw_event):
    """Parse raw SSE event text block into a dict"""
    event = {}
    for line in raw_event.strip().split("\n"):
        if not line.strip() or line.startswith(":"):
            continue  # skip comments or empty lines
        if ":" not in line:
            continue  # malformed line, ignore
        field, value = line.split(":", 1)
        event[field.strip()] = value.lstrip()
    return event
class CtrlxApi:

    def __init__(self, ip_addr, usr, password, cert_path='',key_path='', api_version = 'v2'):
        """Class that handles the direct rest requests to the Ctrlx Core.

        Params:
            ip_addr (str):address of the core
            usr (str): log in user name (default is boschrexroth)
            password (str): passward for user (default is boschrexroth)
            cert_path (str): path on this computer to the certificate used with Core, if left empty will run without verification
            key_path (str): path on this computer to the key frile for the certificate
            api_version (str): core api version (same as major OS so if OS v2 then api is v2)
        """
        self.__ip_addr = ip_addr
        self.__usr = usr
        self.__password = password
        self.__api_url = '/api/' + api_version + '/'
        self.__header = json.loads(json.dumps(
            {'Content-Type': 'application/json;charset=UTF-8', 'Accept': 'application/json, text/plain, */*'}))
        self.__verify = False
        if cert_path != '' and key_path != '':
            self.__verify = cert_path
        self.__cert = (cert_path, key_path)

        self.__session = requests.Session()
        self.__session.trust_env = False


    def connect(self):
        """Makes the initial connection to the Ctrlx Core, getting authorization token for the rest of the requests.

        Returns:
            (Bool,response.status_code): (successful connection, http status code)"""

        auth_json = json.dumps({'name': self.__usr, 'password': self.__password}, separators=(',', ':'))
        url = 'https://' + self.__ip_addr + '/identity-manager'+self.__api_url+'auth/token'
        r = self.__session.post(url, data=auth_json, verify=self.__verify, headers=self.__header, cert = self.__cert)
        if not r.ok:
            return False, r.status_code

        resp = r.json()
        self.__header['Authorization'] = 'Bearer ' + resp['access_token']
        return True, r.status_code

    def read(self, ctrlx_url,stream = False):
        """Does a data layer 'read' action which is a get request.
        Params:
            ctrlx_url:Node address of core (path after ip addr)
            stream: True = data stream for subscription to be opened, False for single read

        Returns:
            requests.response: Response from the Ctrlx Core """
        url = 'https://' + self.__ip_addr + '/' + ctrlx_url
        r = self.__session.get(url, verify=self.__verify, headers=self.__header,stream = stream, cert = self.__cert)
        return r

    def write(self, ctrlx_url, data):
        """Does a data layer 'write' action, data payload as a Json String.
        args:
            ctrlx_url:Node address of core (path)
            data: data to be written, Json String

        Returns:
            requests.response: Response from the Ctrlx Core """
        url = 'https://' + self.__ip_addr + '/' + ctrlx_url
        r = self.__session.put(url, verify=self.__verify, headers=self.__header, data=data, cert = self.__cert)
        return r

    def create(self, ctrlx_url, data):
        """Does a create action on the data layer, a post request.
        Params:
            ctrlx_url:Node address of core (after ip adress)
            data: payload for the create action, see specific data layer node. Formattted as Json String

        Returns:
            requests.response: Response from the Ctrlx Core """

        url = 'https://' + self.__ip_addr + '/' + ctrlx_url
        r = self.__session.post(url, verify=self.__verify, headers=self.__header, data=data, cert = self.__cert)
        return r

    def delete(self, ctrlx_url):
        """delete action on a ctrlx node, a delete request.
         Params:
            ctrlx_url:Node address of core (after ip addr)

        Returns:
            requests.response: Response from the Ctrlx Core """
        url = 'https://' + self.__ip_addr + "/" + ctrlx_url
        r = self.__session.delete(url, verify=self.__verify, headers=self.__header, cert = self.__cert)
        return r

    def get_api_url(self):
        """returns the api version (ie v2)."""
        return self.__api_url

class CtrlxSubscriptionSettings:

    def __init__(self,id,publishiterval,error_interval,nodes:list,keepaliveInterval = 3439503088):
        """Settings to define a ctrx subscription.

        Params:
            id: subscription id
            publishiterval:the interval between publishing data to subscribers, in ms
            error_interval: the interval for connection error checking in ms
            nodes: list of data layer nodes to subscribe to
            keepaliveInterval: how long a subscription can lose connection and be able to reconnect, in ms
        """
        self.__rules = dict()
        self.__nodes = nodes
        self.__rules['id'] = id
        self.__rules['publishInterval'] = publishiterval
        self.__rules['errorInterval'] = error_interval
        self.__rules['keepaliveInterval'] = keepaliveInterval

    def dump(self):
        """Dumps the formatted settings for creation of subscription using the create method.

        Returns:
            string: Json formatted string for Ctrlx Core Subscription settings"""
        settings = dict()
        settings['properties'] = self.__rules
        settings['nodes'] = self.__nodes
        return json.dumps(settings)


def create_subscription(api:CtrlxApi,settings:CtrlxSubscriptionSettings):
    """Creates a subscription using the passed settings.

    Params:
        api: the CtrlxApi
        settings: the settings for the subscription

    Returns:
            requests.response: Response from the Ctrlx Core
    """
    return api.create('automation' + api.get_api_url() + 'events', settings.dump())


def close_subscription(api:CtrlxApi,id:str):
    """Closes a subscription.

    Params:
        api: the CtrlxApi
        id: the subscription id to close

    Returns:
            requests.response: Response from the Ctrlx Core """


    return api.delete('automation' + api.get_api_url()+'events/' + id)


class CtrlXSubscription:
    """Manages an active connection to a subscription.

    Params:
        api: the CtrlxApi"""
    def __init__(self, api:CtrlxApi):
        self.__api = api
        self.__url_preamble  = 'automation' + self.__api.get_api_url()
        self.__close = threading.Event()
        self.__worker = None
        self.__active = False

    def subscribe(self, id, fn_hdl):
        """subscribes to the already created subscription at id and calls the fn_hdl when new data arrives. fn_hdl will
        be called on a separate thread.


        Params:
            id the subscription id to subscribe to
            fn_hdl: the call back for data handling

        Returns:
            Bool : Subscription Success
            """
        if self.__active:
            return []
        r = self.__api.read(self.__url_preamble + 'events/' + id, stream=True)
        if not r.ok: return False
        self.__worker = threading.Thread(target=self.__handle_subscription, args=(r, self.__close, fn_hdl))
        self.__worker.start()
        self.__active = True
        return True

    def unsubscribe(self):
        """closes the active subscription."""
        self.__close.set()
        self.__worker.join()
        self.__active = False

    def __handle_subscription(self,r, close:threading.Event, fn_hdl):
        """checks for new data and calls the call back function."""
        try:
            while not close.is_set():
                buffer = ""
                for event in r.iter_lines(decode_unicode=True):
                    if event:  # non-empty line
                        buffer += event+ "\n"
                    else:  # empty line = event delimiter
                        # Parse event in buffer
                        event = parse_sse_event(buffer)
                        fn_hdl(event)
                        buffer = ""
                    if close.is_set():
                        break
        except Exception as e:
            # Log or handle connection errors
            print(f"Error in SSE loop: {e}")
        finally:
            if hasattr(r, "close"):
                r.close()

class CtrXNode:
    def __init__(self,api:CtrlxApi):
        """Class to handle wrapping api calls so addresses are just data layer paths

        Params:
            api: The CtrlX Api, connect must be called before use

        Returns:
            requests.response: Response from the Ctrlx Core """
        self.__api = api
        self.__url_preamble = 'automation' + self.__api.get_api_url() + "nodes/"

    def read_node(self,node_name:str):
        """Reads a node at provided path in ctrlx core

        Params:
            node_name(str): the path to the data to be read

        Returns:
            requests.response: Response from the Ctrlx Core """
        url = self.__url_preamble + node_name
        return self.__api.read(url)

    def write_node(self,node_name:str,data:str):
        """Writes a node at provided path in ctrlx core

        Params:
            node_name(str): the path to the data to be written
            data(str): a JSON string for the write payload

        Returns:
            requests.response: Response from the Ctrlx Core """

        url = self.__url_preamble + node_name
        return self.__api.write(url,data)

    def create_node(self,node_name:str,data:str):
        """Creates a node at provided path in ctrlx core

        Params:
            node_name(str): the path on the core where the create method should be invoked
            data(str): a JSON string for the create payload

        Returns:
            requests.response: Response from the Ctrlx Core """

        url = self.__url_preamble + node_name
        return self.__api.create(url,data)

    def delete_node(self,node_name:str):
        """Deletes a node at provided path in ctrlx core

        Params:
            node_name(str): the path to the data to be deleted

        Returns:
            requests.response: Response from the Ctrlx Core """
        url = self.__url_preamble + node_name
        return self.__api.delete(url)

    def browse_node(self,node_name):
        """Browses a node in the ctrx core

        Params:
            node_name(str): address in the core to browse

        Returns:
            requests.response: Response from the Ctrlx Core """


        url = self.__url_preamble + node_name + '?type=browse'
        return self.__api.read(url)

    def meta_data(self,node_name):
        """Reads node meta data

        Params:
            node_name(str): address in the core to read meta data

        Returns:
            requests.response: Response from the Ctrlx Core
        """
        url = self.__url_preamble + node_name + '?type=metadata'
        return self.__api.read(url)




