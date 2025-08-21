import json
from bs4 import BeautifulSoup
from pathlib import Path

class Utl:
    
    langauges_file: Path = Path('languages.json')
    translation_file : Path = Path('episodes_titles.json')
    base_url: str = 'https://www.thetvdb.com'
    base_series_url: str = 'https://www.thetvdb.com/series/'
    translations : dict = {}
    episodes : dict = {}
    series_id : str = ''
    selected_language : str = ''
    selected_language_code : str = ''
    
    
    def __init__(self):
        if self.langauges_file.exists():
            with self.langauges_file.open('r', encoding='utf-8') as f:
                self.langauges = json.load(f)
        else:
            raise Exception(f"Languages file '{self.langauges_file}' not found. Please ensure it exists.")
        
        if self.translation_file.exists():
            with self.translation_file.open('r', encoding='utf-8') as f:
                self.translations = json.load(f)
        else:
            raise Exception(f"episodes_titles.json file '{self.translation_file}' not found. Please ensure it exists.")
        
    def check_season_url_format(self, url: str) -> bool:
        """
        Check if the provided URL matches the expected season format.
        """
        if url.startswith(self.base_series_url) and "/seasons/" in url:
            self.series_id = url.split("/series/")[1].split("/seasons/")[0]
            return True
        return False
    
    def check_lanauge_code(self, code: str) -> bool:
        """
        Check if the provided language code is valid.
        """
        if code in self.langauges.keys():
            self.selected_language = self.langauges[code]
            self.selected_language_code = code
            return True
        return False    
            
    def get_episodes_list(self, parser):
        """
        Extract the list of episodes from the parsed HTML.
        """
        
        episodes_list = {}
        
        episodes_div = parser.find('div', id="episodes")
        if not episodes_div:
            return {}
        
        episodes_data = episodes_div.find_all('tr')[1:]
        
        for episode in episodes_data:
            episode_data = episode.find_all('td')
            episode_number = episode_data[0].text.strip().split('E')[1].strip().lstrip('0')
            episode_url = self.base_url + episode_data[1].find('a')['href'].strip()
            episode_translate_url = episode_url + f"/translate/{self.selected_language_code}/0/single"
            
            episodes_list[episode_number] = {
                'url': episode_url,
                'translate_url': episode_translate_url
            }
        return episodes_list
            
    def build_episode_translate_form(self, page_parser: BeautifulSoup, title: str, description: str) -> dict:
        """
        Build the form data for episode translation.

        Args:
            page_parser (BeautifulSoup): The HTML of the episode translate page.
            title (str): The new title for the episode.
            description (str): The new description for the episode.

        Returns:
            dict: A dictionary containing all form fields, ready for a POST request.
        """
        form_data = {}
        
        # Find the specific form element on the page
        form_element = page_parser.find('form', class_='episode-translate-form')

        if not form_element:
            return {} # Return empty dict if form is not found

        # Dynamically find all input and textarea fields to build the payload
        for field in form_element.find_all(['input', 'textarea']):
            name = field.get('name')
            if name:
                # For textareas, the value is the text content; for inputs, it's the 'value' attribute.
                form_data[name] = field.string or field.get('value', '')

        # Set the title and description with the provided values, overwriting the defaults
        form_data['episode_name'] = title
        form_data['episode_overview'] = description
        
        return form_data