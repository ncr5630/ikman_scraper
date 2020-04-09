# -*- coding: utf-8 -*-
import os, shutil
import re
import requests
from urllib.parse import urljoin
import bs4
from bs4 import BeautifulSoup
import time
import json
import logging
import logging.handlers
import traceback
isNavigable = lambda s: isinstance(s, bs4.NavigableString)
IsSoup = lambda s: isinstance(s, (bs4.NavigableString, bs4.Tag))

logging.basicConfig(filename='blakswan_test_scraping.log', level=logging.DEBUG)

class IkmanFetcher:
   '''
   #--This is not important--#
   # I have created freeze text file with my python environment running this code
   # freeze file name is "blackswan_pip_freeze.txt"
   # if need to create environment please use this
   python version
   ===============
   Python 3.7.6

   1.C:\>python -m venv c:\blackswan_nihal 

   activate environment
   -------------------
   2. C:\>c:\blackswan_nihal\scripts\activate

   install library
   ------------------------------
   3.(blackswan_nihal) C:\>pip install -r blackswan_pip_freeze.txt
   '''
   def __init__(self):
      self.mainpagedata=None
      self.mainhtml=None
      self.main_file="search_result_page.html"
      self.main_search_url = "https://ikman.lk/"
      
   def clean_soup(self, soup):
      '''Convert HTML into text.'''
      re_display_none = re.compile(r"display\s*:\s*none")
      def _clean(s):
         if isNavigable(s) or isinstance(s, str):
            pass
         elif re_display_none.search(s.get('style') or ''):
            # Invisible stuff is removed.
            return ''
         elif s.find(style = re_display_none):
            s = " ".join(filter(None, map(_clean, s.contents)))
         elif s.name in ["br", "hr"]:
            # Breaks turn into spaces.
            return u' '
         else:
            s = u"".join(map(_clean, s.contents))
         '''if isinstance(s, str):
         s = s.decode('utf8')'''
         return re.sub(r"[\s\xa0]+", " ", s)
      # We should only strip at the top level.
      return _clean(soup).strip()

   def records_scraping_master(self, reqguest_url):
      soupcontent =None
      # try get request with given url
      try:
         mainpagedata = requests.get(reqguest_url) #get conatin page using requests liblary
         #read page content
         mainhtml = mainpagedata.content 
         #format content page using beautifualSoup
         time.sleep(6)
         soupcontent = BeautifulSoup(mainhtml, 'lxml')
      except requests.exceptions.RequestException as e: 
         # if get any errors then logging  
         logging.error(e)
         return False            
      return soupcontent
         
   def get_all_links_in_searchpage(self, soup):
      # matching all links in initial search grid
      vehicle_report_all_links = [] 
      # define output array as null
      # match correct div tag to get all ads more details links 
      vehicle_report = soup.select("[class^=ad-list--]")
      for record in vehicle_report:
         # match correct path to get all more details ads links
         data_list= record.select("ul>li") 
         if data_list:
            record = 0
            for link in data_list:  
               record_a = link.find('a')
               record_link = record_a['href']
               #make correct link joining "main_search_url" because scraping link is not original data link
               correct_data_url = urljoin(self.main_search_url, record_link)
               vehicle_report_all_links.append(correct_data_url)
      return vehicle_report_all_links
   
   def prase_individual_records(self, soup, clean_tags=True, match_first=None, match_second=None):
      # This html records has two diffrent GUI format there for every records
      # need to check for the both format 
      value = None
      title_data = soup.select(match_first)
      if not title_data:
         title_data = soup.select(match_second)
      if title_data:
         if clean_tags:
            value = self.clean_soup(title_data[0])
         else:
            value = title_data[0]
      else:
         logging.error("can't match any records for the given selecters (%s, %s)"%(match_first, match_second))
      return value
   
   def prase_data_page(self, record_soup, record_link):
      if not record_soup and not record_link:
         logging.error("somthing wrong with datasoup or data link")
         return False      
      title =None
      post_date =None
      details={}
      original_description=None
      image_urls = []
      price=None
      contact=[]  
      vehicle_report_dic = {}  
      first_title_matching = "h1[itemprop=name]"
      second_title_matching = "h1[class^=title--]"
      title = self.prase_individual_records(soup=record_soup,match_first=first_title_matching, match_second=second_title_matching)
                 
      # date matching    
      date_data = record_soup.select("span[class=date]")
      if not date_data:
         date_data = record_soup.select("h3[class^=sub-title--]")
         if date_data:
            date_data_conten=self.clean_soup(date_data[0])
            date_data_conten=date_data_conten.split("m,")
            post_date = "%s%s"%(date_data_conten[0],"m")
            post_date = post_date.replace("Posted on", "")
      else:
         post_date = self.clean_soup(date_data[0])
      
      # In scraping html difficult to identified it's a short description
      # or full description but web site display 6 lines for the short description.
      # it's doing javascript collapsible method but in scraping html
      # display all details without any option to split
        
      first_description_matching = "div[class=item-description]"
      second_description_matching = "div[class^=description--]"
      original_description = self.prase_individual_records(soup=record_soup,
         match_first=first_description_matching, match_second=second_description_matching)         

      # matching category paths 
      category_data= record_soup.select("div[data-testid=breadcrumb]")
      if not category_data:
         category_data= record_soup.select("ol[itemscope=itemscope]")
         category=""
         if category_data: 
            i=0
            for item in category_data[0].findAll('li'):
               if(i != 0):
                  category +="/"
               category += self.clean_soup(item)
               i=i+1
         else:
            logging.error("can't find the correct category path")
      else:
         category = self.clean_soup(category_data[0]) 
                     
      # matching images  
      # for this part I spend little bit time because some time page not loaded images 
      # but javascript json has all records at this time it's regular exposition more complex
      # if we need it or more important I can create that one as well in feature      
      data_images = record_soup.select("div.ui-gallery.sm-panel-wide")
      if not data_images:
         data_images = record_soup.select("ul[class^=thumbnail-list--]")                 
      if data_images:
         all_images_data= data_images[0].findAll('img')
         for img_item in all_images_data:
            link = img_item.get('src')
            if link:
               correct_link = "https:%s"%link
               image_urls.append(correct_link)
      else:
         logging.error("Image scraping errors ...page link : %s"%(record_link))  
      
      #matching price         
      first_price_matching = "div[class=ui-price]"
      second_price_matching = "div[class=ui-price]"
      price = self.prase_individual_records(soup=record_soup,match_first=first_price_matching, match_second=second_price_matching)
      
      #conact number some times multiple there for I have created list to add all
      data_contact= record_soup.select("div.item-contact-more.is-showable")         
      if data_contact:
         for cont in data_contact[0].select('span[class=h3]'):            
            contact.append(self.clean_soup(cont))
      else:
         for cont in record_soup.select("div[class^=phone-numbers--]"):
            contact.append(self.clean_soup(cont))            
      if not contact:
         logging.error("Contact data scraping errors ...page link : %s"%(record_link))  

      details={
      'full_description':original_description,
      'image_urls':image_urls,
      'price' :price, 
      'contact':contact        
      }

      vehicle_report_dic = {
         'title' : title,
         'date' : post_date,
         'short_description' : original_description,
         'category' : category,
         'url' : record_link,
         'details':details,
      }
      return vehicle_report_dic
      
   def prase_all_data(self, search_url):
      records_vehicle_list=[]
      if not search_url:
         logging.error("Not pass correct search url....")
         print("Please give the correct search url.")
         
      data_soup_contens=self.records_scraping_master(search_url)
      if not data_soup_contens:
         logging.error("Can't scrape data result this time ....")
         print("Can't scrape data result this Please check log...")
      get_all_records_links = self.get_all_links_in_searchpage(data_soup_contens)     
         
      if len(get_all_records_links)>1:
         record = 0
         for item in get_all_records_links:
            '''if record ==1:
               break '''
            data_page_soup=None
            data_page_soup=self.records_scraping_master(item)
            if data_page_soup:
               records_dic = self.prase_data_page(data_page_soup, item)
               records_vehicle_list.append(records_dic)
               print("Record link : %s"%item)      
               print ("Data completed-%d \n"%record) 
               record = record +1
               
      return records_vehicle_list                
               
               
dataval = IkmanFetcher()
return_list= dataval.prase_all_data("https://ikman.lk/en/ads?by_paying_member=0&sort=relevance&buy_now=0&query=bmw&page=1")    
history_file = 'vehicle_report.json'
with open(history_file, 'w') as outfile:  #open json file   
   json.dump(return_list, outfile)  #write data into json file
