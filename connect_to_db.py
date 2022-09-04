import pymongo


client = pymongo.MongoClient('localhost', 27017)

db = client['client_sql_ex']
series_collection = db['client']