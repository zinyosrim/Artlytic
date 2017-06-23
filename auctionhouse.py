import requests
import errno
import os
import unicodedata
from abc import ABCMeta
from bs4 import BeautifulSoup
from collections import Counter
from datetime import datetime, date, time, timedelta
from lxml import html


class AbstractAuctionHouse(object):
    '''Abstract class for accessing and manipulating auction house lot data'''
    
    __metaclass__ = ABCMeta

    def __init__(self):
        self.name = ""
        self.name_simplified = self.name.lower().replace("'", "")
        self.fieldnames_for_auctions_csv = ['auction_date', 'auction_company', 'auction_id', 'auction_url']
        self.first_auction_date = datetime(2006, 1, 1)
        # lists  
        # self.auctions = []
        # URLs amd paths  
        self.base_URL = "http://" + self.name_simplified + ".com/"
        self.data_files_path = 'data/' + self.name_simplified + '/'
        self.local_html_path = self.data_files_path + 'html/'
        # self.auctions_CSV = self.data_files_path + self.name_simplified + '_auction_list.csv'
        # list of abstract parser methods
        self.parsers = [self.parse_auction_house_name,
                        self.parse_sale_id,
                        self.parse_sale_date,
                        self.parse_sale_location,
                        self.parse_lot_id,
                        self.parse_artist_name,
                        self.parse_artist_name_normalized,
                        self.parse_title,
                        self.parse_secondary_title,
                        self.parse_created_year,
                        self.parse_description,
                        self.parse_essay,
                        self.parse_provenance,
                        self.parse_provenance_estate_of,
                        self.parse_exhibited_in,
                        self.parse_exhibited_in_museums,
                        self.parse_style,
                        self.parse_height,
                        self.parse_width,
                        self.parse_currency,
                        self.parse_price,
                        self.parse_min_estimated_price,
                        self.parse_max_estimated_price,
                       ]
    
    '''
    
    Concrete methods
    
    '''
    
    def add_lot(self, lot_url_item):
        '''for a given lot_URLs entry: finds the local html file, parses it, extracts the metadata, 
        and finally adds it to the artlytic.lots list'''
        
        # build path of local html file and load file    
        url = lot_url_item['url']        
        path = self.local_html_path + str(lot_url_item['id']) + '.html'
        
        try:
            with open(path, 'rb') as html:
                # parse the html
                parsed_item = self.parse(html)
                # add some more metadata
                parsed_item['id'] = lot_url_item['id']
                parsed_item['html_file_path'] = path
                parsed_item['url'] = lot_url_item['sort_url']
                # add to list
                artlytic.lots.append(parsed_item)
                lot_url_item['scraped'] = True
                print(parsed_item['id'],': Added lot',parsed_item['title'], parsed_item['secondary_title'] )     
        except FileNotFoundError:  
            print('*** could not find file:', path) 
    
    def fetch_single_lot_html(self, lot_url_item):
        '''Get single lots html and store it in a .html file'''     
        url = lot_url_item['url']        
        path = self.local_html_path + str(lot_url_item['id']) + '.html'
        try:
            response = requests.get(url)
            response.raise_for_status() # ensure we notice bad responses
        except (requests.HTTPError, requests.ConnectionError):
            print("*** HTTPError or ConnectionError while accessing", url)

        with open(path, 'w') as fp:
            #days = fp.write(response.text)
            print(path, "saved") 
    
    def parse(self,html):
        '''Takes an HTML document (of a lot) as input. Applies the list of parsers. 
        Returns the auction lot.'''
        lot = dict()
        soup = BeautifulSoup(html, 'lxml')
        for parser in self.parsers:
            lot_key = re.match(r'parse\_(.*)$', parser.__name__)[1]
            lot[lot_key] = parser(soup)
        return lot
    
    def strip_accents(self, s):
        '''Takes a string as input. Helper function to normalize strings. 
        Returns the string with removed accents. Keeps Umlauts'''
        
        try:
            return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if not unicodedata.name(c).endswith('ACCENT')) 
        except:
            return s
        
    def number_of_exhibitions_in_major_museum(self, text):
        museum_keywords = ['museum', 'musée', 'museo', 'beyeler', 'thannhauser', 
                          'gmurzynska', 'georges petit', 'matthiesen', 'national gallery', 'tate modern',
                          'somerset house', 'wilanów palace', 'the national art center', 'Galleria degli Uffizi',
                          'National Portrait Gallery', 'Art Institute of Chicago', 'Saatchi Gallery',
                          'Wawel Royal Castle', 'Galleria dell''Accademia', 'National Galleries of Scotland',
                          'Grand Palais', 'Tretyakov', 'Tate Britain', 'Royal Academy of Arts',
                          'Minneapolis Institute of Art']
        counter = 0
        for keyword in museum_keywords:
            counter += text.lower().count(keyword)
        return counter
    
    '''
    
    Abstract methods
    
    '''
    
    def build_lotlist_from_search_url(self, search_url_list_item):
        raise NotImplementedError()
    
    def build_search_URLs_list(self, artist_list):
        raise NotImplementedError()

    '''
    
    Abstract Methods for auction-house specific parsers
    
    '''
    
    # Parser for search results page. 
    def parse_search_results_page(self, url):
        '''For a given search results page, it returns links of all listed lots on that page'''
        raise NotImplementedError()
        
    # Many parsers for lots page. Each returns specific lot details
    def parse_auction_house_name(self, soup):
        raise NotImplementedError()
    def parse_sale_id(self, soup):
        raise NotImplementedError()
    def parse_sale_date(self, soup):
        raise NotImplementedError()
    def parse_sale_location(self, soup):
        raise NotImplementedError()
    def parse_lot_id(self, soup):
        raise NotImplementedError()
    def parse_artist_name(self, soup):
        raise NotImplementedError()
    def parse_artist_name_normalized(self, soup):
        raise NotImplementedError()
    def parse_title(self, soup):
        raise NotImplementedError()
    def parse_secondary_title(self, soup):
        raise NotImplementedError()
    def parse_created_year(self, soup):
        raise NotImplementedError()
    def parse_description(self, soup):
        raise NotImplementedError()
    def parse_essay(self, soup):
        raise NotImplementedError()
    def parse_provenance(self, soup):
        raise NotImplementedError()
    def parse_provenance_estate_of(self, soup):
        raise NotImplementedError()
    def parse_exhibited_in(self, soup):
        raise NotImplementedError()
    def parse_exhibited_in_museums(self, soup):
        raise NotImplementedError()
    def parse_style(self, soup):
        raise NotImplementedError()
    def parse_height(self, soup):
        raise NotImplementedError()
    def parse_width(self, soup):
        raise NotImplementedError()
    def parse_image_url(self, soup):
        raise NotImplementedError() 
    def parse_currency(self, soup):
        raise NotImplementedError()
    def parse_price(self, soup):
        raise NotImplementedError()
    def parse_min_estimated_price(self, soup):
        raise NotImplementedError()
    def parse_max_estimated_price(self, soup):
        raise NotImplementedError()       
