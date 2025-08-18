#! /usr/bin/env python3

import glob
import sys
sys.path.insert(0, glob.glob('../../')[0])

from match_server.dual_match_service import DualMatch

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

from queue import Queue
from time import sleep
from threading import Thread

from acapp.asgi import channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache

queue = Queue()  # 消息队列

class Player:
    def __init__(self, score, uuid, username, photo, channel_name):
        self.score = score
        self.uuid = uuid
        self.username = username
        self.photo = photo
        self.channel_name = channel_name
        self.waiting_time = 0  # 等待时间（秒）

class Pool:
    def __init__(self):
        self.players = []

    def add_player(self, player):
        """添加玩家到匹配池"""
        print(f"Player {player.username} added to dual match pool. Current pool size: {len(self.players) + 1}")
        self.players.append(player)

    def check_match(self, player1, player2):
        """检查两个玩家是否可以匹配"""
        score_diff = abs(player1.score - player2.score)
        
        # 基础分数差距限制
        base_diff = 200
        
        # 每等待1秒，允许的分数差距增加50分
        max_diff_p1 = base_diff + player1.waiting_time * 50
        max_diff_p2 = base_diff + player2.waiting_time * 50
        
        # 取两者的最小值作为允许的最大差距
        allowed_diff = min(max_diff_p1, max_diff_p2, 1000)  # 最大差距不超过1000分
        
        return score_diff <= allowed_diff

    def match_success(self, ps):
        """匹配成功，创建游戏房间"""
        print("Dual Match Success: %s (score: %d) vs %s (score: %d)" % 
              (ps[0].username, ps[0].score, ps[1].username, ps[1].score))
        
        # 创建房间名，使用 dual-room 前缀
        room_name = "dual-room-%s-%s" % (ps[0].uuid, ps[1].uuid)
        
        # 准备玩家数据
        players = []
        for p in ps:
            async_to_sync(channel_layer.group_add)(room_name, p.channel_name)
            players.append({
                'uuid': p.uuid,
                'username': p.username,
                'photo': p.photo,
                'hp': 100,
            })
        
        # 将房间信息存入缓存
        cache.set(room_name, players, 3600)  # 有效时间：1小时
        
        # 通知两个玩家创建对方
        for p in ps:
            async_to_sync(channel_layer.group_send)(
                room_name,
                {
                    'type': "group_send_event",
                    'event': "create_player",
                    'uuid': p.uuid,
                    'username': p.username,
                    'photo': p.photo,
                }
            )

    def increase_waiting_time(self):
        """增加所有玩家的等待时间"""
        for player in self.players:
            player.waiting_time += 1
            # 每5秒输出一次等待状态
            if player.waiting_time % 5 == 0:
                print(f"Player {player.username} has been waiting for {player.waiting_time} seconds")

    def match(self):
        """执行匹配逻辑"""
        while len(self.players) >= 2:
            # 按分数排序
            self.players = sorted(self.players, key=lambda p: p.score)
            
            matched = False
            
            # 优先匹配分数相近的玩家
            for i in range(len(self.players) - 1):
                for j in range(i + 1, len(self.players)):
                    player1 = self.players[i]
                    player2 = self.players[j]
                    
                    if self.check_match(player1, player2):
                        # 匹配成功
                        self.match_success([player1, player2])
                        
                        # 从匹配池中移除已匹配的玩家
                        remaining = []
                        for k, player in enumerate(self.players):
                            if k != i and k != j:
                                remaining.append(player)
                        self.players = remaining
                        
                        matched = True
                        break
                
                if matched:
                    break
            
            # 如果没有找到合适的匹配
            if not matched:
                # 检查是否有玩家等待时间过长（超过15秒）
                max_wait_players = [p for p in self.players if p.waiting_time > 15]
                
                if len(max_wait_players) >= 2:
                    # 如果有多个等待超时的玩家，直接匹配前两个
                    p1 = max_wait_players[0]
                    p2 = max_wait_players[1]
                    self.match_success([p1, p2])
                    self.players.remove(p1)
                    self.players.remove(p2)
                    print(f"Force match due to long waiting time: {p1.username} vs {p2.username}")
                elif len(max_wait_players) == 1 and len(self.players) >= 2:
                    # 如果只有一个等待超时的玩家，给他匹配最接近的对手
                    timeout_player = max_wait_players[0]
                    self.players.remove(timeout_player)
                    
                    # 找到分数最接近的玩家
                    closest_player = min(self.players, 
                                       key=lambda p: abs(p.score - timeout_player.score))
                    self.players.remove(closest_player)
                    
                    self.match_success([timeout_player, closest_player])
                    print(f"Priority match for timeout player: {timeout_player.username} vs {closest_player.username}")
                else:
                    # 没有合适的匹配，退出循环
                    break

        # 更新等待时间
        self.increase_waiting_time()

class DualMatchHandler:
    """Thrift服务处理器"""
    def add_player(self, score, uuid, username, photo, channel_name):
        """添加玩家到匹配队列"""
        print("Add Dual Player: %s (score: %d, uuid: %s)" % (username, score, uuid))
        player = Player(score, uuid, username, photo, channel_name)
        queue.put(player)
        return 0

def get_player_from_queue():
    """从队列中获取玩家"""
    try:
        return queue.get_nowait()
    except:
        return None

def worker():
    """后台工作线程，负责匹配逻辑"""
    pool = Pool()
    print("Dual match worker thread started")
    
    while True:
        # 从队列获取新玩家
        player = get_player_from_queue()
        if player:
            pool.add_player(player)
        else:
            # 没有新玩家，执行匹配
            if len(pool.players) > 0:
                pool.match()
            sleep(1)  # 每秒执行一次匹配

def main():
    """主函数"""
    print("=" * 50)
    print("Starting Dual Match Server")
    print("=" * 50)
    
    # 创建处理器
    handler = DualMatchHandler()
    processor = DualMatch.Processor(handler)
    
    # 设置传输层
    transport = TSocket.TServerSocket(host='127.0.0.1', port=9091)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()

    # 创建服务器
    server = TServer.TThreadedServer(
        processor, transport, tfactory, pfactory)

    # 启动后台匹配线程
    worker_thread = Thread(target=worker, daemon=True)
    worker_thread.start()
    print("Worker thread started")

    # 启动服务器
    print(f"Server listening on 127.0.0.1:9091")
    print("Waiting for dual match requests...")
    print("=" * 50)
    
    try:
        server.serve()
    except KeyboardInterrupt:
        print("\nShutting down dual match server...")
        transport.close()
        print("Dual match server stopped")
    except Exception as e:
        print(f"Error: {e}")
        transport.close()

if __name__ == '__main__':
    main()
