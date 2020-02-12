import redis

import redis
"""
redis = {
    "k1":123,
    'k2':456,
    name: [alex,eric]
    sb: [eric,alex]
}
"""
conn = redis.Redis(host='192.168.16.85', port=6379)

"""
conn.set('k1', '123')
conn.set('k2', '456')

val1 = conn.get('k1')
print(val1)

val2 = conn.get('k2')
print(val2)
"""

# 查看列表中所有的值
# vals = conn.lrange('sb',0,100)
# print(vals)
"""
redis中的列表可以当做栈来使用。
# conn.lpush('sb','alex')
# conn.lpush('sb','eric')
# v1 = conn.lpop('sb')
# print(v1)
"""

"""
redis中的列表可以当做队列来使用。
conn.lpush('db','alex')
conn.lpush('db','eric')
v1 = conn.rpop('db')
print(v1)
"""



