
#################################
##### Name: Gamila Elshobary
##### Uniqname: Gamila
#################################

from bs4 import BeautifulSoup
import requests
import time
import json
import secrets


CACHE_FILE_NAME = "nps_cache.json"
CACHE_DICT = {}

url = "https://www.nps.gov"
r = requests.get(url)
soup = BeautifulSoup(r.text, 'html.parser')

key = secrets.mapquest_key


def load_cache():
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache


def save_cache(cache):

    contents_to_write = json.dumps(cache)
    cache_file = open(CACHE_FILE_NAME, 'w')
    cache_file.write(contents_to_write)
    cache_file.close()


def make_request_using_cache(url):
    cache = load_cache()
    if url in cache.keys(): # the url is our unique key
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        time.sleep(1)
        response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]

class NationalSite:
    '''a national site
    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')
    address: string
        the city and state of a national site (e.g. 'Houghton, MI')
    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')
    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        '''
        Returns
        -------
        An instance of itself
        '''
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"
    Parameters
    ----------
    None
    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    state_name_link = {}
    states = soup.find('ul', class_='dropdown-menu SearchBar-keywordSearch')
    states_links = states.find_all('li', recursive=False)

    for link in states_links:
        #link_tag = (link.find('a').contents[0]).lower()
        state_tag = link.find('a')
        #print(link_tag['href'])
        #state_tag = link_tag.find('a')
        path = state_tag['href']
        state_url = url + path
        state_name_link[state_tag.text.lower()] = state_url
        #print(state_tag.text.lower())
        #print(state_url)

    return state_name_link

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    response = requests.get(site_url)
    soupDetail = BeautifulSoup(response.text, 'html.parser' )
    all_park_elements = soupDetail.find(class_='Hero-titleContainer clearfix')
    # print(all_park_elements)

    name = all_park_elements.find(class_='Hero-title').text

    category_site = all_park_elements.find(class_='Hero-designationContainer')
    category = category_site.find(class_='Hero-designation').text
    # print(category)

    address_listing = soupDetail.find(class_='vcard')
    full_address = address_listing.find(class_='adr')
    city_address = full_address.find(itemprop='addressLocality').text
    state_address = full_address.find(itemprop='addressRegion').text
    address = city_address + ', ' + state_address
    #print(address)
    
    zip_address = full_address.find(itemprop='postalCode').text
    
    phone_num = address_listing.find(itemprop='telephone').text
    #print(phone_num)
    var = NationalSite(category, name, address, zip_address.strip(), phone_num.strip())

    return var


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    cache_dict_response = make_request_using_cache(state_url)
    site_urls = []
    soup = BeautifulSoup(cache_dict_response, 'html.parser')
    state_parks = soup.find(id='parkListResultsArea')
    state_park = state_parks.find_all('li', class_='clearfix')

    for item in state_park:
        header = item.find('h3')
        park_url_tag = header.find('a')
        park_url = park_url_tag['href']
        full_url = url + park_url
        site_urls.append(full_url)

    national_sites_instances = []
    for each_url in site_urls:
        i = get_site_instance(each_url)
        national_sites_instances.append(i)

    return national_sites_instances

def make_zipcode_request_with_cache(site_object, params=None, base_url=None):
    '''Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.

    Parameters
    ----------
    site_object

    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''

    CACHE_DICT = load_cache()

    if site_object in CACHE_DICT.keys():
        print("using cache")
        return CACHE_DICT[site_object]
    else:
        print("fetching")
        response = requests.get(base_url, params)
        CACHE_DICT[site_object] = response.json()
        save_cache(CACHE_DICT)
        return CACHE_DICT[site_object]

def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    base_url = 'http://www.mapquestapi.com/search/v2/radius'
    params = {'key' : key,
                'origin': site_object.zipcode ,
                'radius': 10,
                'maxMatches' : 10,
                'ambiguities' : 'ignore',
                'outFormat' : 'json'
    }
    cache_response_dict = make_zipcode_request_with_cache(site_object.info(), params, base_url)

    distance_info = cache_response_dict
    results = distance_info['searchResults']
    for result in results:
        name = result['name']
        address = result['fields']['address']
        if address == '':
            address = 'no address'
        category = result['fields']['group_sic_code_name_ext']
        if category == '':
            category = 'no category'
        city = result['fields']['city']
        if city == '':
            city = 'no city'
        string_rep = f"{name} ({category}) : {address}, {city}\n"
    #print(string_rep)

    return string_rep

if __name__ == "__main__":

    def get_userInput():
        '''
        Parameters: No parameters

        This function prompts users to enter a search term or to exit the program.
        Users can enter exit to leave the program or
        Users can enter a search term state info. An organized list is returned to the screen.
        
        When exit is entered, the program quits.

        '''
        while True:
            state = input("Please enter a state name of your interest or type exit: ")
            if state != 'exit':
                if state.isalpha():
                    state_links = build_state_url_dict()
                    if state.lower() in state_links.keys():
                        print(f'List of National Sites in {state.title()}')
                        state_website = state_links[state.lower()]
                        print(state_website)
                        site_instances = get_sites_for_state(state_website)

                        for i, site_instance in enumerate(site_instances):
                            i = i + 1
                            print(f'[{i}] {site_instance.info()}')

                    while True:
                        user_input = input("Select a number for more details or type 'back' or 'exit': ")
                        if user_input.isnumeric() == True:
                            user_input = int(user_input)
                            if user_input <= len(site_instances):
                                user_input = user_input -1
                                x = get_nearby_places(site_instances[user_input])
                                print(f'Places near {site_instances[user_input].name} >>>> {x}')
                            else:
                                print("Invalid entry. Number is out of range")

                        elif user_input.lower() == 'back':
                            print('Returning to previous page...')

                        elif user_input.lower() =='exit':
                            print('See you later!')
                        break
            else:
                break

    get_userInput()

