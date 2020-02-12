import redis

# 连接方式
conn = redis.Redis(host='192.168.16.85', port=6379)
conn.set('k', 'Bar')
val = conn.get('k')
print(val)

# 连接池（推荐）
pool = redis.ConnectionPool(host='192.168.16.85', port=6379)

conn = redis.Redis(connection_pool=pool)
conn.set('foo', 'Bar')
conn.get('foo')