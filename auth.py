import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

class Auth:
    
    account_file = Path('config/account.json')
    base_url : str = "https://www.thetvdb.com"
    login_url : str = base_url + "/auth/login"
    translate_url : str = base_url + "/episodes/translatestore"

    session : requests.Session = requests.Session()
    
    def __init__(self):
        self.account = self._validate_and_load_account_file()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0'
        })

        self._load_cookies()
        
    def _validate_and_load_account_file(self):
        """
        Validates account.json. If missing or corrupt, creates a new template
        and exits, instructing the user to fill it.
        """
        if not self.account_file.exists():
            print(f"Account file '{self.account_file}' not found. Creating a new one.")
            self.account_file.parent.mkdir(parents=True, exist_ok=True)
            self._create_account_template()
            raise Exception(f"Please fill in your credentials in '{self.account_file}' and run the script again.")

        try:
            with self.account_file.open('r') as f:
                account_data = json.load(f)
        except json.JSONDecodeError:
            print(f"Error: '{self.account_file}' is corrupt. Deleting and creating a new template.")
            self.account_file.unlink()  # Delete the corrupt file
            self._create_account_template()
            raise Exception(f"Please fill in your credentials in '{self.account_file}' and run the script again.")

        # Normalize "Cookies" key to "cookies" if it exists
        if "Cookies" in account_data and "cookies" not in account_data:
            account_data["cookies"] = account_data.pop("Cookies")

        if not account_data.get("username") or not account_data.get("password"):
            print(f"Error: 'username' or 'password' is missing or empty in '{self.account_file}'.")
            raise Exception(f"Please update '{self.account_file}' with your credentials and run the script again.")

        return account_data

    def _create_account_template(self):
        """Creates a template account.json file."""
        template = {"username": "", "password": "", "cookies": {}}
        with self.account_file.open('w') as f:
            json.dump(template, f, indent=4)

    def _load_cookies(self):
        """Loads cookies from the account file into the session."""
        cookies = self.account.get('cookies')
        if cookies and isinstance(cookies, dict):
            print("Found existing cookies, loading into session.")
            self.session.cookies = requests.utils.cookiejar_from_dict(cookies)
        else:
            print("No existing session cookies found.")

    def _save_cookies(self):
        """Saves the current session cookies to the account file."""
        print("Saving session cookies to file...")
        cookies_dict = requests.utils.dict_from_cookiejar(self.session.cookies)
        self.account['cookies'] = cookies_dict
        
        with self.account_file.open('w') as file:
            json.dump(self.account, file, indent=4)
        print("Session cookies saved.")
    
    def request(self, url, method="GET", data=None, headers=None):
        # allow_redirects=True is the default, but we make it explicit.
        response = self.session.request(method, url, data=data, headers=headers, allow_redirects=True)

        # If we were redirected to the login page, our session is likely expired or invalid.
        if response.url.startswith(self.login_url) and response.history:
            print("Session seems to have expired. Attempting to log in again.")
            if self.login():
                print("Login successful. Retrying original request.")
                # Retry the original request with the new authenticated session
                response = self.session.request(method, url, data=data, headers=headers)
            else:
                raise Exception("Cannot proceed without login.")
        return response

    def login(self):
        # 1. Get the login page to acquire a CSRF token (_token)
        try:
            get_response = self.session.get(self.login_url)
            get_response.raise_for_status() # Raise an exception for bad status codes
            soup = BeautifulSoup(get_response.content, 'html.parser')
            token = soup.find('input', {'name': '_token'})['value']
        except (requests.exceptions.RequestException, AttributeError, KeyError) as e:
            print(f"Failed to retrieve login token: {e}")
            return False

        # 2. Prepare the login payload with your credentials and the token
        # I see your account.json uses "username", so we'll use that key.
        login_data = {
            '_token': token,
            'email': self.account['username'],
            'password': self.account['password'],
            'remember': 'on'
        }

        # 3. Send the POST request to log in. The session will store the auth cookies.
        try:
            post_response = self.session.post(self.login_url, data=login_data, headers={'Referer': self.login_url})
            post_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Login POST request failed: {e}")
            return False

        # 4. Verify login was successful. A successful login sets a specific cookie and redirects.
        if 'TVDB_AUTHENTICATED' in self.session.cookies and post_response.url != self.login_url:
            print("Successfully logged in and session cookies are stored.")
            self._save_cookies() # <-- This is the new step to save cookies
            return True
        else:
            print("Login failed. Please check your credentials or site changes.")
            return False

    def update_episode(self, form_data):
        return self.request(self.translate_url, method="POST", data=form_data)