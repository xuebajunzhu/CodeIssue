"""
redis = {
    k1: 123,
    k2: [11,22,33],
    k3: {
        k31:1,
        k32:22
    },
    k4: {1,2,3,4},
    k5: {('alex',65),('eric',60),('汪洋',99)}
}
"""


import redis
# 连接池（推荐）
pool = redis.ConnectionPool(host='192.168.16.85', port=6379)
conn = redis.Redis(connection_pool=pool)

# ########## 字符串类型 string ##########
# conn.set('k1',123)
# conn.get('k1')

# ########## 列表类型 list ##########
# conn.lpush('k2',11)
# conn.lpush('k2',22)
# conn.lpush('k2',33)
# conn.lpop('k2')

# ########## 字典类型 hash ##########
# conn.hset("k3", "k31", 1)
# conn.hset("k3", "k32", 22)
# conn.hget('k3','k32')
# conn.hgetall('k3')

# ########## 集合类型 set ##########
# conn.sadd('k4',1,2,3,4,2)

# ########## 有序集合类型 sorted set ##########
# conn.zadd








