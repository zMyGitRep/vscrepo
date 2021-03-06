#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
//////////////////////////////////////////////////////////////////////////////////////////
 ^----^
  *  * 
   ~
//////////////////////////////////////////////////////////////////////////////////////////
"""

#from http import client
import paho.mqtt.client as mqtt     # MQTTのライブラリをインポート
#from time import sleep              # 3秒間のウェイトのために使う
import dlogger as dlog
import json
#from dronekit import Command
import os

##################################################################
### Class as singleton
##################################################################
class Mqtt_Singleton(object):
    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        #    cls._instance = cls(input)
        # else:
        #     cls._instance.input = input
        return cls._instance

##################################################################
### Drone control class
##################################################################
class MqttCtrl(Mqtt_Singleton):

    host = "localhost"
    port = 1883
    # Publisher 座標等のドローン情報
    topic_dinfo = "drone/dinfo"
    # Subscriber コマンド、Simple Goto
    topic_dctrl = "drone/dctrl"
    # Subscriber ミッション
    topic_mission = "drone/mission"
    client = ""
    client_m = ""
    #msg = ""

    ### =================================================================================== 
    ### MQTTで受信するドローン操作コマンド:クライアントから受信
    ###     コマンドおよび移動先の「緯度、経度、高度」情報
    ### =================================================================================== 
    drone_command = {
        "operation":"None",
        "d_lat":"0",
        "d_lon":"0",
        "d_alt":"0"
    }    

    drone_mission = {
        "operation":"None",
        "index":"0",
        "cntwp":"0",
        "frame":"0",
        "command":"0",
        "para1":"0",
        "para2":"0",
        "para3":"0",
        "para4":"0",
        "d_lat":"0",
        "d_lon":"0",
        "d_alt":"0",
        "acnt":"0"
    }   

    ### =================================================================================== 
    ### コンストラクタ
    ### =================================================================================== 
    def __init__(self):
        dlog.LOG("INFO", "START")
        # クラスのインスタンス(実体)の作成
        self.client = mqtt.Client() 
        self.client_m = mqtt.Client() 
        # 接続時のコールバック関数を登録
        self.client.on_connect = self.on_connect              
        self.client_m.on_connect = self.on_connect_m             
        # 切断時のコールバックを登録
        self.client.on_disconnect = self.on_disconnect        
        self.client_m.on_disconnect = self.on_disconnect_m        
        # メッセージ送信時のコールバック
        #self.client.on_publish = self.on_publish              
        #self.client_m.on_publish = self.on_publish_m              
        # 接続先は自分自身
        self.client.connect(self.host, self.port, 60)     
        self.client_m.connect(self.host, self.port, 60)     
        # メッセージ到着時のコールバック        
        self.client.on_message = self.on_message
        self.client_m.on_message = self.on_message_m
        # subはloop_forever()だが，pubはloop_start()で起動だけさせる
        self.client.loop_start()                                   
        self.client_m.loop_start()                                   
        # 永久ループして待ち続ける
        #mqttClass.client.loop_forever()
        #mqttClass.client_m.loop_forever()

    ### =================================================================================== 
    ### ブローカーに接続できたときの処理：コールバック
    ### =================================================================================== 
    def on_connect(self, client, userdata, flag, rc):
        dlog.LOG("DEBUG", "Connected with result code " + str(rc))  # 接続できた旨表示
        client.subscribe(self.topic_dctrl)  # subするトピックを設定 

    def on_connect_m(self, client_m, userdata, flag, rc):
        dlog.LOG("DEBUG", "Connected with result code " + str(rc))  # 接続できた旨表示
        client_m.subscribe(self.topic_mission)  # subするトピックを設定 

    ### =================================================================================== 
    ### ブローカーから切断されたときの処理：コールバック
    ### =================================================================================== 
    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            dlog.LOG("DEBUG", "Unexpected disconnection.")

    def on_disconnect_m(self, client, userdata, rc):
        if rc != 0:
            dlog.LOG("DEBUG", "Unexpected disconnection.")

    ### =================================================================================== 
    ### publishが完了したときの処理：コールバック
    ### =================================================================================== 
    # def on_publish(self, client, userdata, mid):
    #     dlog.LOG("DEBUG", "publish: {0}".format(mid))

    # def on_publish_m(self, client, userdata, mid):
    #     dlog.LOG("DEBUG", "publish: {0}".format(mid))

    ### =================================================================================== 
    ### メッセージが届いたときの処理：コールバック
    ### =================================================================================== 
    ### コマンド: Simple Goto
    def on_message(self, client, userdata, msg):
        dlog.LOG("DEBUG","START");
        # msg.topicにトピック名が，msg.payloadに届いたデータ本体が入っている
        recvData = json.loads(msg.payload)
        if msg.topic==self.topic_dctrl:
            # 受信メッセージをコマンド辞書にコピー、その際に変更フラグを付加
            # 届いた際にtrueにし，コマンドを処理したらfalseにする
            self.drone_command["operation"] = recvData["operation"]
            if self.drone_command["operation"] == "GOTO":
                self.drone_command["d_lat"] = recvData["d_lat"]
                self.drone_command["d_lon"] = recvData["d_lon"]
                self.drone_command["d_alt"] = recvData["d_alt"]

            # print("Received command '" 
            #     + self.drone_command["operation"] + ","
            #     + str(self.drone_command["d_lat"]) + ","
            #     + str(self.drone_command["d_lon"]) + ","
            #     + str(self.drone_command["d_alt"]) 
            # )
    ### コマンド: Mission
    def on_message_m(self, client, userdata, msg):
        dlog.LOG("DEBUG","START");

        path = '../mission/mpmission.txt'
        f = open(path, 'w')
        #f.write(self.drone_mission2["sfx"]) # これは送られていない、要チェック！
        f.write('QGC WPL 110'+'\r\n')

        # msg.topicにトピック名が，msg.payloadに届いたデータ本体が入っている
        recvData = json.loads(msg.payload)

        # ミッションデータをファイルに保存
        if msg.topic==self.topic_mission:
          for num in range(len(recvData)):
            f.write(recvData[num])
          self.drone_mission["operation"] = "MISSION";
        f.close()        

    ### =================================================================================== 
    ### topicをpublish
    ### =================================================================================== 
    def publish_topic(self, topic):
        self.client.publish(topic)

    def publish_topic_m(self, topic):
        self.client_m.publish(topic)

