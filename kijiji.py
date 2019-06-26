# encoding=utf8
import requests
from bs4 import BeautifulSoup
import re,os,json

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import datetime

urls = [('mile-end',"https://www.kijiji.ca/b-appartement-condo/grand-montreal/mile-end/k0c37l80002a27949001?ad=offering&price=__1900"),
        ('plateau',"https://www.kijiji.ca/b-appartement-condo/grand-montreal/plateau/k0c37l80002a27949001?ad=offering&price=__1900"),
        ('outremont',"https://www.kijiji.ca/b-appartement-condo/grand-montreal/outremont/k0c37l80002a27949001?ad=offering&price=__1900")
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
    
# def send_sms(username,password):
#     to_number = os.environ['PHONE']
#     try:  
#         server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
#         server.ehlo()
#         server.login(username, password)
#         server.sendmail(username, to_number, 'nouveaux apts disponibles')
#         server.close()

#         print('sms sent!')
#     except Exception as e:  
#         print('Something went wrong...', e)
def get_walking_distance(postalcode):
    if postalcode =='unknown':
        return 'inconnu'
    url = 'https://maps.googleapis.com/maps/api/distancematrix/json?mode=walking&origins=' + postalcode + '&destinations=h2v3r6&key=' + os.environ['GOOGLE_API_KEY']
    r = requests.get(url)
    r = json.loads(r.text)
    if r['status'] == 'OK':
        return r['rows'][0]["elements"][0]["duration"]['text']
    else:
        print(postalcode)
        print(r.text)
        return 'erreur lors du calcul'


def get_apt_details(div):
    url = "http://www.kijiji.ca" + div.find('a')['href']
    ad_id = url.split('/')[-1] + '\n'
    title = div.findAll('div',class_="title")[0].text
    price = div.findAll('div',class_="price")[0].text
    try:
        #TODO ca donne une list
        postalcode_raw = BeautifulSoup(requests.get(url).text, "html.parser").findAll('span',{'itemprop': 'address'})[0].text
        postalcode = re.findall('[A-Za-z][1-9][A-Za-z]\s?[1-9][A-Za-z][1-9]',postalcode_raw)[0]
    except:
        postalcode = 'unknown'
    return Apts(title, price, url,ad_id,postalcode)

def get_list_of_apts(url):
    response = requests.get(url)
    print(response.status_code)
    print(response.text[:100])
    soup = BeautifulSoup(response.text, "html.parser")
    divs = soup.findAll('div')
    return reversed(divs)

def apt_is_wanted(apt,seen_apts):
    if apt.ad_id in seen_apts:
        return False
    if any(x in apt.title.lower() for x in dealbreakers):
        return False
    return True

def check_if_new_apts(urls):
    all_apts = {}
    #path_root = '/Users/jerome/Desktop/kijiji/'
    path_root = '/root/kijiji/'
    for url in urls:
        quartier = url[0]
        print('On regarde dans :', quartier)
        
        path = path_root + quartier
        seen_apts = []
        with open(path,'r') as f:
            for x in f:
                seen_apts.append(x)
        print('Il y a deja ' + str(len(seen_apts)) + ' dans ' + quartier)
        divs = get_list_of_apts(url[1])
        new_apts = []
        for div in divs:
            if div.has_attr('data-ad-id'):
                apt = get_apt_details(div)
                if not apt_is_wanted(apt,seen_apts):
                    continue
                
                with open(path,'a') as f:
                    f.write(apt.ad_id)

                apt.distance = get_walking_distance(apt.postalcode)

                new_apts.append(apt)
        print('Done : ', quartier)

        if len(new_apts) > 1:
            print('Il y a maintenant ' + str(len(new_apts)) + ' apts dans ' + quartier)
            all_apts[quartier] = new_apts
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
            html += '<p>' + apt.distance + '</p>'
    html += "</html>"
    return html

def send_email(html):
    me = "recherche.kijiji.mautadine@gmail.com"
    #you = ["jerome.verdoni@gmail.com","perreaultmj@hotmail.com"]
    you = ["jerome.verdoni@gmail.com"]
    password = os.environ['KIJIJI_PASSWORD']
    # send_sms(me,password)

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
    print('Debut du script a : ' + str(datetime.datetime.now()))
    apts = check_if_new_apts(urls)
    if apts:
        print('Sending email...')
        apts_html = format_html(apts)
        send_email(apts_html)
    else:
        print('Rien de nouveau a envoyer')
    print('Fin du script a : ' + str(datetime.datetime.now()))
    print('-=-=-=-=-=-=-')
    print('\n')

