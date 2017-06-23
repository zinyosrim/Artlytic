import requests
import re
import unicodedata
from bs4 import BeautifulSoup
from datetime import datetime, date, time, timedelta
from dateutil import relativedelta
from lxml import html
from auctionhouse import AbstractAuctionHouse


class Christies(AbstractAuctionHouse):
    
    def __init__(self):
        super().__init__()
        self.name = "Christie's"
        
    def build_search_URLs_list(self, artists):
        '''Takes a name of artist list as input and creates 3 searchlink per artist. The links point 
        to the search results page which is returnes when on enters a keyword into the search form.
        We are building three links, for sorted by: 
            1. relevance
            2. price high to low
            3. most recent 
        to gather more auction lots by an artist'''

        new_entry_counter = 0
        search_url_templates = [
          "lotfinder/searchresults.aspx?searchfrom=header&lid=1&entry={}+{}&searchtype=p&action=sort&sortby=ehigh",
          "lotfinder/searchresults.aspx?searchfrom=header&lid=1&entry={}+{}&searchtype=p&action=sort&sortby=rel",
          "lotfinder/searchresults.aspx?searchfrom=header&lid=1&entry={}+{}&searchtype=p&action=sort&sortby=dt"
          ]     
        
        print('*** Beginning with adding new search URLs. Current list size:',len(artlytic.search_URLs))
        
        # for every artist, create 3 search URLs and append to artlytic.search_URLs list
        for artist in artists:  
            # extract artist name
            artist_name = artist['artistName']
            artist_firstname = artist_name.split()[0]
            artist_surname = artist_name.split()[-1]
            # build the URLs
            for search_url_template in search_url_templates:
                # build the search URL
                url_without_names = self.base_URL + search_url_template
                url_with_names = url_without_names.format(artist_firstname,artist_surname)
                # Build the search URL entry
                search_url_metadata = {'auction_house': self.name, 
                                       'artist_name': artist_name,
                                       'scraped': False,
                                       'timestamp': datetime.now().isoformat().replace(':', '-').replace('.', '-'),
                                       'url':url_with_names}
                # add to list
                artlytic.search_URLs.append(search_url_metadata)
                new_entry_counter += 1        
        print('*** Added to search_URLs', new_entry_counter, 'new entries. New size:', len(artlytic.search_URLs))
             
    '''
    
    Implementing abstract parsers
    
    '''
    
    # Parser for search results page 
    
    def parse_search_results_page(self, url_of_search_results_page):
        '''Scrape the search results page return lot URLs as a list '''     
        search_result_url_list = []

        try:
            # get auction list html
            html= requests.get(url_of_search_results_page, timeout=10).text
            soup = BeautifulSoup(html, 'lxml')
            
            # find search results classes
            search_results = soup.find_all("div", class_='image-overlay-box')
            # identify each URL and collect in the list search_results
            for search_result in search_results:
                try:
                    lot_link = search_result.find("a")
                    search_result_url_list.append(re.match(r'(.*)aspx', lot_link['href']).group(0))
                except:
                    pass #not a valid link for us
            return search_result_url_list
        except:
            # very likely there's a connection error
            #print('*** Timeout/Connection/corrupt html error. Could access', url_search_results_page)
            return []
        
    
    # Parsers for the lot HTML
    
    def parse_auction_house_name(self, soup):
        return self.name
    
    def parse_sale_id(self, soup):
        sale = soup.find('span', id="main_center_0_lnkSaleNumber")
        return "" if not sale else sale.get_text()
    
    def parse_sale_date(self, soup):
        sale_date = soup.find('span', id="main_center_0_lblSaleDate")
        try:
            return "" if not sale_date else datetime.strptime(re.search(r'(\d{1,2}\s[A-Z][a-z]+\s\d\d\d\d)', \
                                                        sale_date.get_text())[1], '%d %B %Y').date().isoformat() 
        except:
            return datetime(1,1,1).date().isoformat()
    
    def parse_sale_location(self, soup):
        sale_location = soup.find('span', id="main_center_0_lblSaleLocation")
        return "" if not sale_location else sale_location.get_text()
    
    def parse_lot_id(self, soup):
        lot_id = soup.find('span', id="main_center_0_lblLotNumber")
        return "" if not lot_id else lot_id.get_text()
    
    def parse_artist_name(self, soup):
        title = soup.find('h1', id="main_center_0_lblLotPrimaryTitle")
        try: 
            return re.match(r'(.*)\s\(', title.get_text())[1]
        except:
            return ''
    
    def parse_artist_name_normalized(self, soup):
        return self.strip_accents(self.parse_artist_name(soup))
    
    def parse_title(self, soup):
        title = soup.find('h1', id="main_center_0_lblLotPrimaryTitle")
        return "" if not title else title.get_text().replace('\n','').replace('\r','')
    
    def parse_secondary_title(self, soup):
        secondary_title = soup.find('h2', id="main_center_0_lblLotSecondaryTitle")
        return "" if not secondary_title else secondary_title.get_text().replace('\n','').replace('\r','')
    
    def parse_created_year(self, soup):
        description = soup.find('span', id="main_center_0_lblLotDescription")
        if description:
            pattern_for_created = re.compile(r'''\b
                                     (?:painted|signed|dated|executed|completed|painted|signed|circa)
                                     \b.{1,20}
                                     (\d{4})''',flags= re.IGNORECASE | re.VERBOSE )
            digits = pattern_for_created.findall(description.get_text())          
            try:
                return int(digits[-1])
            except IndexError:
                return 0

    def parse_description(self, soup):
        description = soup.find('span', id="main_center_0_lblLotDescription")
        return "" if not description else description.get_text().replace('\n','').replace('\r','')
    
    def parse_essay(self, soup):
        essay = soup.find('p', id="main_center_0_lblLotNotes")
        return "" if not essay else essay.get_text().replace('\n',' ').replace('\r','')
    
    def parse_provenance(self, soup):
        provenance = soup.find('p', id="main_center_0_lblLotProvenance")
        return "" if not provenance else provenance.get_text().replace('\n',' ').replace('\r','')
    
    def parse_provenance_estate_of(self, soup):
        provenance = soup.find('p', id="main_center_0_lblLotProvenance")
        if not provenance: 
            return 0
        else: 
            p = provenance.get_text()
            return (p.lower().count('estate') > 0 or p.lower().count('museum') > 0)
        
    def parse_exhibited_in(self, soup):
        exhibited_in = soup.find('p', id="main_center_0_lblExhibited")
        return "" if not exhibited_in else soup.find('p', id="main_center_0_lblExhibited").get_text().replace('\n',' ').replace('\r','')
    
    def parse_exhibited_in_museums(self, soup):
        e = self.parse_exhibited_in(soup) 
        if e == "": return 0
        else:
            exhibited_text_lower = e.lower()
            return  self.number_of_exhibitions_in_major_museum(exhibited_text_lower) 
        
    def parse_style(self, soup):
        description = soup.find('span', id="main_center_0_lblLotDescription")
        if description:
            d = description.get_text().lower()
            if 'oil on canvas' in d: return 'Oil on canvas'
            if 'drawing' in d: return 'Drawing'
            if 'water color' in d: return 'Water color'
            if 'pastel' in d: return 'Pastel'
            return ''
        
    def parse_height(self, soup):
        description = soup.find('span', id="main_center_0_lblLotDescription")
        if description:
            d = description.get_text().lower()
            if len(re.findall(r"\D(\d*\.?\d*?)\s*x\s*(\d*\.?\d*?)\s*cm",d))>0:
                try:
                    w = float(re.findall(r"\D(\d*\.?\d*?)\s*x\s*(\d*\.?\d*?)\s*cm",d)[0][1])
                    return float(re.findall(r"\D(\d*\.?\d*?)\s*x\s*(\d*\.?\d*?)\s*cm",d)[0][0])
                except ValueError:
                    return 0 
                
    def parse_width(self, soup):
        description = soup.find('span', id="main_center_0_lblLotDescription")
        if description:
            d = description.get_text().lower()
            if len(re.findall(r"\D(\d*\.?\d*?)\s*x\s*(\d*\.?\d*?)\s*cm",d))>0:
                try:
                    h = float(re.findall(r"\D(\d*\.?\d*?)\s*x\s*(\d*\.?\d*?)\s*cm",d)[0][0])
                    return float(re.findall(r"\D(\d*\.?\d*?)\s*x\s*(\d*\.?\d*?)\s*cm",d)[0][1])       
                except ValueError:
                    return 0  
                
    def parse_image_url(self, soup):
        image_url = soup.find('img', id="imgLotImage")['src']
        if image_url and 'no-image' not in image_url:
            return image_url
        else:
            return '' 
        
    def parse_currency(self, soup):
        return 'USD'
    
    def parse_price(self, soup):
        page_content_including_prices = soup.find(id='MainContentDetails')
        pattern_for_usd_prices = re.compile(r'''
            (USD)     #currency
            \s*([\d*\,]*\d*)  #number, thousands separated with commas
            ''', re.VERBOSE)
        prices =  pattern_for_usd_prices.findall(soup.text)
        if len(prices) == 3:
            return int(prices[0][1].replace(',', ''))
        else:
            return 0
        
    def parse_min_estimated_price(self, soup):
        page_content_including_prices = soup.find(id='MainContentDetails')
        pattern_for_usd_prices = re.compile(r'''
            (USD)     #currency
            \s*([\d*\,]*\d*)  #number, thousands separated with commas
            ''', re.VERBOSE)
        prices =  pattern_for_usd_prices.findall(soup.text)
        if len(prices) == 3:
            return int(prices[1][1].replace(',', ''))
        else:
            return 0
        
    def parse_max_estimated_price(self, soup):
        page_content_including_prices = soup.find(id='MainContentDetails')
        pattern_for_usd_prices = re.compile(r'''
            (USD)     #currency
            \s*([\d*\,]*\d*)  #number, thousands separated with commas
            ''', re.VERBOSE)
        prices =  pattern_for_usd_prices.findall(soup.text)
        if len(prices) == 3:
            return int(prices[2][1].replace(',', ''))
        else:
            return 0
