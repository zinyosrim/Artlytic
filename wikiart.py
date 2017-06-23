class Wikiart:
    '''Class to access wikiart.org Data'''
    def __init__(self):
        self.base_url = "https://www.wikiart.org/en/"
        self.base_url_api = self.base_url + "api/2/"
        self.base_url_movement = self.base_url + 'artists-by-art-movement/'
        self.artist_data_url = self.base_url_api + "UpdatedArtists"
        
    def fetch_impressionists(self):  
        url1 = self.base_url + "artists-by-art-movement/impressionism"
        url2 = self.base_url + "artists-by-art-movement/impressionism/2"
        url3 = self.base_url + "artists-by-art-movement/impressionism/3" 
        
        impressionists_list_urls = [url1, url2, url3 ]
        artist_name_list = []
        
        for url in impressionists_list_urls:        
            html = requests.get(url).text
            soup = BeautifulSoup(html, 'lxml')
            artist_name_list += [re.findall(r'>(.*?)<', str(item))[0] 
                                    for item in soup.select('.artists-list li ul li a')]
        return artist_name_list

    def fetch_artists_19th_early_20th(self):  
        
        urls = ['neoclassicism', 
                'romanticism/1', 
                'romanticism/2',
                'romanticism/3',
                'realism/1', 
                'realism/2', 
                'realism/3',
                'impressionism/1',
                'impressionism/2', 
                'impressionism/3',
                'post-impressionism/1',
                'post-impressionism/2',
                'cubism/1', 
                'cubism/2', 
                'art-nouveau/1', 
                'art-nouveau/2', 
                'expressionism/1', 
                'expressionism/1',
                'expressionism/2',
                'expressionism/3']
        
        artists_list_urls = []
        for url in urls:
            artists_list_urls.append(self.base_url_movement + url)
            
        artist_name_list = []       
        for url in artists_list_urls:        
            html = requests.get(url).text
            soup = BeautifulSoup(html, 'lxml')
            
            artist_name_list += [re.findall(r'>(.*?)<', str(item))[0] 
                                    for item in soup.select('.artists-list li ul li a')]
        
        return artist_name_list

    def write_artist_data_into_json_file(self):
        artists = requests.get(artist_data_url).json()
        all_artists = artists['data']

        with open(artlytics.data_path + 'wikiart_artist_data.json', 'w') as outfile:
            while artists['hasMore']:
                print('fetching next: pagination token',artists['paginationToken'])
                url = BASE_URL + "?paginationToken=" + artists['paginationToken']
                artists_next_page = requests.get(url).json()
                next_artists = artists_next_page['data']
                time.sleep(0.25)
                all_artists = all_artists + next_artists
                artists = artists_next_page
            
            json.dump(all_artists, outfile, indent=4)
            
