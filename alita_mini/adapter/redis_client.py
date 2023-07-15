import redis
from alita_mini.custom_types import SingletonType
from alita_mini.config import RedisConfig


class RedisClient(metaclass=SingletonType):
    @classmethod
    def instance(cls):
        return RedisClient()

    def build(self, config: RedisConfig):
        self.redis_pool = redis.ConnectionPool(
            host=config.host,
            port=config.port,
            password=config.password,
            db=config.db,
        )

    def get_db(self):
        return self.redis_pool


class RedisCache(metaclass=SingletonType):
    @classmethod
    def instance(cls):
        return RedisCache()

    def build(self, config: RedisConfig, redis_client: RedisClient):
        self.expiration = config.expire_time
        self.redis_client: RedisClient = redis_client
        self.latest_key = config.latest_key
        self.max_queue_size = config.max_history_size

    def cache_item(self, key: str, item: str):
        redis_client = redis.Redis(connection_pool=self.redis_client.redis_pool)
        # If the queue is already at maximum size, remove the oldest item before adding the new item
        redis_client.set(key, item, ex=self.expiration)
        if redis_client.llen(self.latest_key) >= self.max_queue_size:
            redis_client.lpop(self.latest_key)
        redis_client.rpush(self.latest_key, key)
        # Set the expiration time for the queue
        redis_client.expire(self.latest_key, self.expiration)

    def get_latest_keys(self):
        # Get a connection from the Redis connection pool
        redis_client = redis.Redis(connection_pool=self.redis_client.redis_pool)
        keys = redis_client.lrange(self.latest_key, 0, -1)
        keys_new = [key.decode("utf-8") for key in keys if type(key) == bytes]
        return keys_new

    def get_item_from_cache(self, key: str):
        # Get a connection from the Redis connection pool
        redis_client = redis.Redis(connection_pool=self.redis_client.redis_pool)
        value = redis_client.get(key)
        return value
