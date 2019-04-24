import requests
from bs4 import BeautifulSoup
import re,os

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


urls = [('mile-end',"https://www.kijiji.ca/b-appartement-condo/grand-montreal/mile-end/3+1+2__4+1+2__5+1+2/k0c37l80002a27949001?ad=offering&price=__1100"),
        ('plateau',"https://www.kijiji.ca/b-appartement-condo/grand-montreal/plateau/3+1+2__4+1+2__5+1+2/k0c37l80002a27949001?ad=offering&price=__1100"),
        ('outremont',"https://www.kijiji.ca/b-appartement-condo/grand-montreal/outremont/3+1+2__4+1+2__5+1+2/k0c37l80002a27949001?ad=offering&price=__1100")
]

class Apts:
  def __init__(self,title, price, url,ad_id,postalcode):
    self.title = title
    self.price = price
    self.url = url
    self.ad_id = ad_id
    self.postalcode = postalcode

    def html(self):
        html_data = ''
        html_data += '<h2>' + self.title + '</h2>'
        html_data += '<h4>' + self.price + '</h4>'
        html_data += '<a href=' + self.url + '></a>' 
        return html_data

def check_if_new_apts(urls):
    all_apts = {}

    for url in urls:
        quartier = url[0]
        print('looking for :', quartier)
        response = requests.get(url[1])
        soup = BeautifulSoup(response.text, "html.parser")
        divs = soup.findAll('div')
        apts = []

        with open(quartier,'r') as f:
            last_known_id = f.readlines()[-1][:-1]

        for div in reversed(divs):
            if div.has_attr('data-ad-id'):
                #skip les pubs
                if div.findAll('span',class_='v_ w_'):
                    pass
                title = div.findAll('div',class_="title")[0].text
                price = div.findAll('div',class_="price")[0].text
                url = "http://www.kijiji.ca" + div.find('a')['href']
                ad_id = url.split('/')[-1]
                if ad_id in last_known_id:
                    print('last apt has been seen,sorry')
                    break
                try:
                    #TODO ca donne une list
                    postalcode_raw = BeautifulSoup(requests.get(url).text, "html.parser").findAll('span',{'itemprop': 'address'})[0].text
                    postalcode = re.findall('[A-Za-z][1-9][A-Za-z]\s?[1-9][A-Za-z][1-9]',postalcode_raw)
                except:
                    postalcode = 'unknown'
                apt = Apts(title,price,url,ad_id,postalcode)
                apts.append(apt)

        
        print('done for: ', quartier)
        if len(apts) > 1:
            print('writing to file:', quartier)
            with open(quartier,'w') as f:
                try:
                    f.write(apts[0].ad_id + '\n')
                except IOError:
                    print("Could not read file:", quartier)
            print('done writing')

            all_apts[quartier] = apts
        else:
            print('nothin new has been found in ',quartier)
    return all_apts

def format_html(apts):
    html = '<html> <h1> Voici les nouveaux apartements</h1>'
    for quartier in apts:
        html += '<h2>' + quartier + '</h2>'
        for apt in apts[quartier]:
            html += '<p>' + apt.title + '</p>'
            html += '<p>' + apt.price + '</p>'
            html += '<a href=' + apt.url + '></a>'
    html += "</html>"
    return html.encode('utf-8')

def send_email(html):
    me = "recherche.kijiji.mautadine@gmail.com"
    you = "jerome.verdoni@gmail.com"
    password = os.environ['KIJIJI_PASSWORD']

    message = MIMEMultipart("alternative")
    message["Subject"] = "Des nouvelles annonces kijiji sont sorties"
    message["From"] = me
    message["To"] = you

    text = "oops, erreur avec le html"

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
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
    apts = check_if_new_apts(urls)
    if apts:
        apts_html = format_html(apts)
        send_email(apts_html)

