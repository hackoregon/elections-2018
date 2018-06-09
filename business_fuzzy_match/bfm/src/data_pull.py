import psycopg2
import json

class DataPuller(object):
    def __init__(self, query="src/selection.sql"):
        self.login()
        with open(query, "r") as f:
            self.query = f.read()

    def login(self):
        with open("elections_login.json", "r") as f:
                login_info = json.load(f)
        self.conn = psycopg2.connect(host=login_info["ip"]
                       ,dbname=login_info["db"]
                       ,user=login_info["username"]
                       ,password=login_info["password"])

        self.cursor = self.conn.cursor()

    def get_data(self):
        self.cursor.execute(self.query)
        self.data = self.cursor.fetchall()
        self.data_dict = {}
        self.data_dict[0] = []
        self.data_dict[1] = []
        for em, prop in self.data:
            self.data_dict[prop].append(em)
