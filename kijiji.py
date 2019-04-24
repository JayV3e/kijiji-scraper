import requests
from bs4 import BeautifulSoup
import re

urls = [('mile-end',"https://www.kijiji.ca/b-appartement-condo/grand-montreal/mile-end/3+1+2__4+1+2__5+1+2/k0c37l80002a27949001?price=__1100"),
        ('plateau',"https://www.kijiji.ca/b-appartement-condo/grand-montreal/plateau/3+1+2__4+1+2__5+1+2/k0c37l80002a27949001?price=__1100"),
        ('outremont',"https://www.kijiji.ca/b-appartement-condo/grand-montreal/outremont/3+1+2__4+1+2__5+1+2/k0c37l80002a27949001?price=__1100")]


class Apts:
  def __init__(self,title, price, url,ad_id,postalcode):
    self.title = title
    self.price = price
    self.url = url
    self.ad_id = ad_id
    self.postalcode = postalcode

all_apts = {}

for url in urls:
    da_hood = url[0]
    print('looking for :', da_hood)
    response = requests.get(url[1])
    soup = BeautifulSoup(response.text, "html.parser")

    divs = soup.findAll('div')

    apts = []

    with open(da_hood,'r') as f:
        last_known_id = f.readlines()[-1][:-1]

    print(last_known_id)

    for div in reversed(divs):
        if div.has_attr('data-ad-id'):
            print('found one')
            if div.findAll('span',class_='v_ w_'):
                print('criss de pub')
                pass
            title = div.findAll('div',class_="title")[0].text
            price = div.findAll('div',class_="price")[0].text
            url = "http://www.kijiji.ca" + div.find('a')['href']
            ad_id = url.split('/')[-1]
            print('on compare',last_known_id, ' et ',ad_id,' et ils sont',ad_id in last_known_id )
            if ad_id in last_known_id:
                print('last apt has been seen,sorry')
                break
            try:
                postalcode_raw = BeautifulSoup(requests.get(url).text, "html.parser").findAll('span',{'itemprop': 'address'})[0].text
                postalcode = re.findall('[A-Za-z][1-9][A-Za-z]\s?[1-9][A-Za-z][1-9]',postalcode_raw)
            except:
                postalcode = 'unknown'
            apt = Apts(title,price,url,ad_id,postalcode)
            apts.append(apt)
    print('done for: ', da_hood)
    print('writing to file')

    if len(apts) > 1:
        with open(da_hood,'w') as f:
            try:
                f.write(apts[0].ad_id + '\n')
            except IOError:
                print("Could not read file:", da_hood)
        print('done writing')

        all_apts[da_hood] = apts
    else:
        print('nothin new has been found')

