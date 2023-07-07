import motor
from alita_mini.custom_types import SingletonType
from alita_mini.config import Config


class MongoClient(metaclass=SingletonType):
    @classmethod
    def instance(cls):
        return MongoClient()

    def build(self, config: Config, loop=None):
        if loop:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(config.mongo_uri, io_loop=loop)
        else:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(config.mongo_uri)

    @property
    def io_loop(self):
        loop = self.client.get_io_loop()
        return loop
