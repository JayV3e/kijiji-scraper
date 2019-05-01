# encoding=utf8
import requests
from bs4 import BeautifulSoup
import re,os

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import datetime

urls = [('mile-end',"https://www.kijiji.ca/b-appartement-condo/grand-montreal/mile-end/3+1+2__4+1+2__5+1+2/k0c37l80002a27949001?ad=offering&price=__1100"),
        ('plateau',"https://www.kijiji.ca/b-appartement-condo/grand-montreal/plateau/3+1+2__4+1+2__5+1+2/k0c37l80002a27949001?ad=offering&price=__1100"),
        ('outremont',"https://www.kijiji.ca/b-appartement-condo/grand-montreal/outremont/3+1+2__4+1+2__5+1+2/k0c37l80002a27949001?ad=offering&price=__1100")
]

dealbreakers = ['swap','echange','recherche','sublet','sous-location']

class Apts:
  def __init__(self,title, price, url,ad_id,postalcode):
    self.title = title
    self.price = price
    self.url = url
    self.ad_id = ad_id
    self.postalcode = postalcode

    def html(self):
        html_data = ''
        html_data += '<a href=' + self.url + '>' +self.tltle + '</a>' 
        html_data += '<h4>' + self.price + '</h4>'
        return html_data

def check_if_new_apts(urls):
    all_apts = {}
    path_root ='/root/kijiji/'

    for url in urls:
        quartier = url[0]
        print('On regarde dans :', quartier)
        
        path = path_root + quartier
        seen_apts = []
        with open(path,'r') as f:
            for x in f:
                seen_apts.append(x)

        response = requests.get(url[1])
        soup = BeautifulSoup(response.text, "html.parser")
        divs = soup.findAll('div')
        
        new_apts = []

        for div in reversed(divs):
            if div.has_attr('data-ad-id'):
                with open(path) as f:
                    #skip les pubs
                    if div.findAll('span',class_='v_ w_'):
                        pass
                    url = "http://www.kijiji.ca" + div.find('a')['href']
                    ad_id = url.split('/')[-1]
                    if ad_id in seen_apts:
                        pass
                    with open(path,'r+') as f:
                        f.write(ad_id + '\n')

                    title = div.findAll('div',class_="title")[0].text
                    price = div.findAll('div',class_="price")[0].text

                    try:
                        #TODO ca donne une list
                        postalcode_raw = BeautifulSoup(requests.get(url).text, "html.parser").findAll('span',{'itemprop': 'address'})[0].text
                        postalcode = re.findall('[A-Za-z][1-9][A-Za-z]\s?[1-9][A-Za-z][1-9]',postalcode_raw)
                    except:
                        postalcode = 'unknown'
                    
                    if any(x in title.lower() for x in dealbreakers):
                        pass
                    else:
                        apt = Apts(title,price,url,ad_id,postalcode)
                        new_apts.append(apt)

        print('Done : ', quartier)
        if len(new_apts) > 1:
            print('Il y a ' + str(len(apts)) + ' apts dans ' + quartier)
            all_apts[quartier] = apts
        else:
            print('Rien de nouveau dans ',quartier)
    return all_apts

def format_html(apts):
    html = '<html> <h1> Voici les nouveaux apartements</h1>'
    for quartier in apts:
        html += '<h2>' + quartier + '</h2>'
        for apt in apts[quartier]:
            html += '<a href=' + apt.url + '>' + apt.title + '</a>'
            html += '<p>' + apt.price + '</p>'
    html += "</html>"
    return html

def send_email(html):
    me = "recherche.kijiji.mautadine@gmail.com"
    #you = ["jerome.verdoni@gmail.com","perreaultmj@hotmail.com"]
    password = os.environ['KIJIJI_PASSWORD']

    message = MIMEMultipart("alternative")
    message["Subject"] = "Des nouvelles annonces kijiji sont sorties"
    message["From"] = me
    message["To"] = "jerome.verdoni@gmail.com"

    # Turn these into plain/html MIMEText objects
    part2 = MIMEText(html, "html", 'utf-8')

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part2)
    
    try:  
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(me, password)
        server.sendmail(me, you, message.as_string())
        server.close()

        print('Email sent!')
    except Exception as e:  
        print('Something went wrong...', e)
if __name__ == "__main__":
    print(datetime.datetime.now())
    apts = check_if_new_apts(urls)
    print(apts)
    if apts:
        print('theres apts')
        apts_html = format_html(apts)
        print
        print(apts_html)
        send_email(apts_html)
        print('after email')

