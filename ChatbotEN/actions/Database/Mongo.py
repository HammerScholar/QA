from typing import Any, Dict, List, Text
from pymongo import MongoClient
import traceback

class MongoDB:
    def __init__(self) -> None:
        self.url = 'mongodb://root:HammerScholarRoot0@hammerscholar-pub.mongodb.zhangbei.rds.aliyuncs.com:3717,hammerscholarsecondary-pub.mongodb.zhangbei.rds.aliyuncs.com:3717/admin?replicaSet=mgset-505729903'
    
    def find_conference(self, query, projection) -> List[Dict[Text, Any]]:
        try:
            # connect to mongodb
            client = MongoClient(self.url)
            db = client.HammerScholar
            detail = db.detail

            # find and order 1.CCF 2.Viewed 3.Begin
            result = [doc for doc in detail.find(query, projection).sort([("CCF", 1), ("Viewed", -1), ("Begin", -1)])]

            return result
        except:
            traceback.print_exc()