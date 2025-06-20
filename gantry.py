import ctrlx_api
import json
import time
class Gantry:
    def __init__(self, api: ctrlx_api.CtrlxApi):
        self.__api = api
        self.__Positions = [(400,300,0),(400,300,-50),(-100,-200,0),(-400,-400,0),(-400,-400,-50),(0,0,0)]
        self.__dlNode = ctrlx_api.CtrXNode(self.__api)
        self.__i = 0
        self.__active = False
        self.__action = self.buffered_move

    def isActive(self):
        return self.__active

    def buffered_move(self):
        while self.__Positions[self.__i][2] != -50:
            self.move()
        self.__action = self.move_down

    def move_down(self):
        self.move()
        self.__action = self.wait

    def wait(self):
        time.sleep(5)
        self.buffered_move()

    def OnMessage(self,event):
        if 'data' in event:
            if json.loads(event['data'])['value']:
                print(event['data'])
                self.__active = False
                self.__action()
            else:
                self.__active = True

    def move(self):
        pos = list()
        print(self.__i)
        pos.append(self.__Positions[self.__i][0])
        pos.append(self.__Positions[self.__i][1])
        pos.append(self.__Positions[self.__i][2])
        print(pos)
        for i in range(16-3):
            pos.append(0)
        data = dict()
        data['type'] = 'object'
        value = dict()
        value['kinPos'] = pos
        value['coordSys'] = 'WCS'
        lim  = dict()
        lim['vel'] = 200
        lim['acc'] = 1000
        lim['dec'] = 1000
        lim['jrkAcc'] = 0
        lim['jrkDec'] = 0
        value['lim'] = lim
        value['buffered'] = True
        data['value'] = value
        self.__i = (self.__i+1) % 6
        r = self.__dlNode.create_node('motion/kin/Kinematics/cmd/move-abs',json.dumps(data))
        print(r)

    def start(self):
        data = dict()
        data['type'] = 'bool8'
        data['value'] = True
        self.__dlNode.create_node('motion/axs/X/cmd/power',json.dumps(data))
        self.__dlNode.create_node('motion/axs/Y/cmd/power', json.dumps(data))
        self.__dlNode.create_node('motion/axs/Z/cmd/power', json.dumps(data))
        time.sleep(1)
        data = dict()
        data['type'] = 'object'
        value = dict()
        value["kinName"] = 'Kinematics'
        value['buffered'] = True
        data['value'] = value
        r = self.__dlNode.create_node('motion/axs/X/cmd/add-to-kin',json.dumps(data))
        self.__dlNode.create_node('motion/axs/Y/cmd/add-to-kin', json.dumps(data))
        self.__dlNode.create_node('motion/axs/Z/cmd/add-to-kin', json.dumps(data))
        self.__dlNode.create_node('motion/kin/Kinematics/cmd/group-ena', None)
        time.sleep(1)

    def stop(self):
        self.__dlNode.create_node('motion/kin/Kinematics/cmd/group-dis', None)
        time.sleep(1)
        r = self.__dlNode.create_node('motion/axs/X/cmd/rem-frm-kin', None)
        self.__dlNode.create_node('motion/axs/Y/cmd/rem-frm-kin', None)
        self.__dlNode.create_node('motion/axs/Z/cmd/rem-frm-kin', None)
        time.sleep(1)
        data = dict()
        data['type'] = 'bool8'
        data['value'] = False
        self.__dlNode.create_node('motion/axs/X/cmd/power', json.dumps(data))
        self.__dlNode.create_node('motion/axs/Y/cmd/power', json.dumps(data))
        self.__dlNode.create_node('motion/axs/Z/cmd/power', json.dumps(data))

