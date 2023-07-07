import logging
from pydantic import BaseModel
from alita_mini.utils import ordered_yaml_load


class MongoConfig(BaseModel):
    user: str
    password: str
    host: str
    port: str

    def __hash__(self):
        return hash(self.host + self.user + self.password)


class SSLConfig(BaseModel):
    chinese_key: str = "/home/test/.ssl/memorylib.cloud/memorylib.cloud.key"
    chinese_csr: str = "/home/test/.ssl/memorylib.cloud/memorylib.cloud.csr"
    us_key: str = "/home/test/https_keys/chat.memorylib.me/privkey.pem"
    us_csr: str = "/home/test/https_keys/chat.memorylib.me/fullchain.pem"


class Config(BaseModel):
    config_tag: str = "default"
    mongo_config: MongoConfig
    ssl_config: SSLConfig

    @classmethod
    def load(cls, file_path, load_feature_map=True):
        logging.info(f"begin load [{file_path}]")
        config_data = ordered_yaml_load(file_path)
        config = cls(**config_data)
        logging.info(f"done load [{file_path}] mongo_uri is [{config.mongo_uri}]")
        return config

    def __hash__(self):
        return hash(self.config_tag)

    @property
    def mongo_uri(self):
        mongo_uri = f"mongodb://{self.mongo_config.user}:{self.mongo_config.password}@{self.mongo_config.host}:{self.mongo_config.port}"
        return mongo_uri


if __name__ == "__main__":
    yml_path = "../scripts/config/config.yml"
    c = Config.load(yml_path)
    print(c)
    print(c.mongo_uri)
