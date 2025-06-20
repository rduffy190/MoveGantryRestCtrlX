import ctrlx_api
import pprint
from gantry import Gantry
import json
import time
import os
def read_data(event):
    pprint.pprint(event['data'])

if __name__ == '__main__':
    # Create API Object
    api = ctrlx_api.CtrlxApi(ip_addr='192.168.10.175',usr='boschrexroth', password='boschrexroth')
    # Connect to the Ctrlx Core
    ok, _  = api.connect()
    # Create A node object using the API
    dl_node = ctrlx_api.CtrXNode(api)
    # read the data layer node for the max position limit of an axis called CoeAxis
    r = dl_node.read_node('motion/axs/X/cfg/lim/pos-max')
    pprint.pprint(r.json())
    # get the meta data of a data layer node
    r = dl_node.meta_data('motion/axs/X/cmd/power')
    pprint.pprint(r.json())
    gantry1 = Gantry(api)
    gantry1.start()
    subscription_id = 'Gantry-Feedback2'
    settings = ctrlx_api.CtrlxSubscriptionSettings(subscription_id, '200', '400',
                                                   ['motion/kin/Kinematics/state/idle'],
                                                   keepaliveInterval='100000')
    ctrlx_api.create_subscription(api, settings)
    subscription = ctrlx_api.CtrlXSubscription(api)
    subscription.subscribe(subscription_id, gantry1.OnMessage)
    time.sleep(300)
    # unsubscribe to the data
    subscription.unsubscribe()
    # close subscription
    ctrlx_api.close_subscription(api, subscription_id)
    time.sleep(10)
    gantry1.stop()


