import os


class Config:
    SECRET_KEY = "1883eb9a04f787018d99ff7dceb4ade9af17cf91d70593336e13a40630dd18c5"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 18 * 60

    DB_CONNECTION_STRING = "mysql+mysqldb://hdsg:password@127.0.0.1/hdsg"
    if "HDSG_DB_CONNECTION_STRING" in os.environ:
        DB_CONNECTION_STRING = os.environ["HDSG_DB_CONNECTION_STRING"]

