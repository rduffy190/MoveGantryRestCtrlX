import ctrlx_api
import json

class Gantry:
    def __init__(self, api: ctrlx_api.CtrlxApi):
        self.__api = api
        self.__Positions = [(100,100,0),(100,100,-50),(-100,100,0),(-100,-100,0),(-100,-100,-50),(0,0,0)]
        self__OnMessage = self.OnMessage
        self.__dlNode = ctrlx_api.CtrXNode(self.__api)
        i = 0
    def OnMessage(self,event):
        if event['data'].vaule:
            self.move()
    def move(self):
        pass
    def start(self):
        data = dict()
        data['type'] = 'bool8'
        data['value'] = True
        self.__dlNode.create_node('motion/axs/X/cmd/power',json.dumps(data))
        self.__dlNode.create_node('motion/axs/Y/cmd/power', json.dumps(data))
        self.__dlNode.create_node('motion/axs/Z/cmd/power', json.dumps(data))
        data = dict()
        data['type'] = 'object'
        kin_name = dict()
        kin_name['type'] = 'string'
        kin_name['value'] = 'Kinematic'
        buffered = dict()
        buffered['type'] = 'bool8'
        buffered['value'] = False
        data["kinName"] = kin_name
        data['buffered'] = buffered
        r = self.__dlNode.create_node('motion/axs/X/cmd/add-to-kin',json.dumps(data))
        self.__dlNode.create_node('motion/axs/Y/cmd/add-to-kin', json.dumps(data))
        print(self.__dlNode.create_node('motion/axs/Z/cmd/add-to-kin', json.dumps(data)))


        print(self.__dlNode.meta_data('motion/axs/X/cmd/add-to-kin').json())
