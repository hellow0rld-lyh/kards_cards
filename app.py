import json
with open('./cards.json',encoding='utf-8') as data_file:
    data = json.load(data_file) 
nodes = data['data']['cards']['edges']
imgurls = []
for node in nodes:
    imgurls.append("www.kards.com"+node['node']['imageUrl']) 
print(imgurls)