import logging
from pydantic import BaseModel
from alita_mini.utils import ordered_yaml_load
from alita_mini.config import MongoConfig


class DataLoadingConfig(BaseModel):
    # from crawler
    meta_file: str
    # from crawler
    data_file: str
    # for indexer
    dump_file: str
    # index file
    index_file: str
    # index meta file
    index_meta_file: str
    # index meta filed
    index_meta_fileds = ["_id"]
    index_language = "zh"
    rocket_model = "zh_dureader_de_v2"
    use_cuda = False
    batch_size = 32
    mongo_config: MongoConfig

    # Add more config for indexer config
    @classmethod
    def load(cls, file_path, load_feature_map=True):
        logging.info(f"begin load [{file_path}]")
        config_data = ordered_yaml_load(file_path)
        config = cls(**config_data)
        logging.info(f"done load [{file_path}] mongo_uri is [{config.mongo_uri}]")
        return config

    @property
    def mongo_uri(self):
        mongo_uri = f"mongodb://{self.mongo_config.user}:{self.mongo_config.password}@{self.mongo_config.host}:{self.mongo_config.port}"
        return mongo_uri

    def __hash__(self):
        return hash(self.meta_file + self.data_file + self.mongo_uri)


if __name__ == "__main__":
    yml_path = "../../scripts/config/load_data_config.yml"
    c = DataLoadingConfig.load(yml_path)
    print(c)
    print(c.mongo_uri)
