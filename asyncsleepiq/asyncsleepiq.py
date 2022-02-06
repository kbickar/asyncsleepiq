import aiohttp
import asyncio
import random
from .consts import *
from .sleeper import *
from .bed import *

class SleepIQLoginException(Exception):
    pass
class SleepIQTimeoutException(Exception):
    pass
class SleepIQAPIException(Exception):
    pass

# Return a randomly generated sorta valid User Agent string
def random_user_agent():
    uas = {
        "Edge": ("AppleWebKit/537.36 (KHTML, like Gecko) "
                 "Chrome/98.0.4758.80 Safari/537.36 Edg/98.0.1108.43"),
        "Chrome": ("AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/97.0.4692.99 Safari/537.36"),
        "Firefox": "Gecko/20100101 Firefox/96.0",
        "iphone": ("AppleWebKit/605.1.15 (KHTML, like Gecko) "
                   "Version/15.2 Mobile/15E148 Safari/604.1"),
        "Safari": ("AppleWebKit/605.1.15 (KHTML, like Gecko) "
                   "Version/11.1.2 Safari/605.1.15"),
    }
    os = {
        "windows": "Windows NT 10.0; Win64; x64",
        "iphone": "iPhone; CPU iPhone OS 15_2_1 like Mac OS X",
        "mac": "Macintosh; Intel Mac OS X 10_11_6",
    }
    template = "Mozilla/5.0 ({os}) {ua}"

    return template.format(
        os=random.choice(list(os.values())),
        ua=random.choice(list(uas.values()))
    )

class AsyncSleepIQ:
    def __init__(self, email=None, password=None, login_method=LOGIN_KEY, client_session=None):
        self._email = email
        self._password = password
        self._session = client_session or aiohttp.ClientSession()
        self._headers = {'User-Agent': random_user_agent()}
        self._key = ""
        self._login_method = login_method
        
        self.beds = []

    async def login(self, email="", password=""):            
        if not email: email = self._email
        if not password: password = self._password
        if not email or not password:
            raise SleepIQLoginException("username/password not set")
            
        try:
            if self._login_method == LOGIN_KEY:
                await self.login_key(email, password)
            else:
                await self.login_cookie(email, password)

        except asyncio.TimeoutError as ex:
            # timed out
            raise SleepIQTimeoutException("API call timed out") from ex
        except SleepIQTimeoutException as ex:
            raise ex
        except Exception as ex:
            raise SleepIQLoginException(f"Connection failure: {ex}") from ex
            
        # store in case we need to login again  
        self._email = email
        self._password = password    

    async def login_key(self, email="", password=""):
        self._key = ""
        auth_data = {'login': email, 'password': password}
            
            
        async with self._session.put(
            API_URL+'/login', headers=self._headers, timeout=TIMEOUT, json=auth_data
        ) as resp:

            if resp.status == 401:
                raise SleepIQLoginException("Incorect username or password")
            if resp.status == 403:
                raise SleepIQLoginException("User Agent is blocked. May need to update GenUserAgent data?")
            if resp.status not in (200, 201):
                raise SleepIQLoginException("Unexpected response code: {code}\n{body}".format(
                    code=resp.status,
                    body=resp.text,
                ))
                
            json = await resp.json()
            self._key = json['key']          

    async def login_cookie(self, email="", password=""):
        auth_data = {'Email': email, 'Password': password, 'ClientID': "2oa5825venq9kek1dnrhfp7rdh"}
        async with self._session.post(
            "https://l06it26kuh.execute-api.us-east-1.amazonaws.com/Prod/v1/token", 
            headers=self._headers, timeout=TIMEOUT, json=auth_data
        ) as resp:

            if resp.status == 401:
                raise SleepIQLoginException("Incorect username or password")
            if resp.status == 403:
                raise SleepIQLoginException("User Agent is blocked. May need to update GenUserAgent data?")
            if resp.status not in (200, 201):
                raise SleepIQLoginException("Unexpected response code: {code}\n{body}".format(
                    code=resp.status,
                    body=resp.text,
                ))
            json = await resp.json()
            token = json['data']['AccessToken']
            self._headers["Authorization"] = token
            
        async with self._session.get(
            API_URL+'/user/jwt', headers=self._headers, timeout=TIMEOUT
        ) as resp:
            if resp.status not in (200, 201):
                raise SleepIQLoginException("Unexpected response code: {code}\n{body}".format(
                    code=resp.status,
                    body=resp.text,
                ))           

    async def put(self, url, data="", params={}):
        await self.__make_request(self._session.put, url, data, params)
        
    async def get(self, url, data="", params={}):
        return await self.__make_request(self._session.get, url, data, params)
        
    async def check(self, url, data="", params={}):
        return await self.__make_request(self._session.get, url, data, params, check=True)
    
    async def __make_request(self, make_request, url, data="", params={}, retry=True, check=False):
        timeout = aiohttp.ClientTimeout(total=TIMEOUT)
        params['_k'] = self._key
        try:
            async with make_request(
                API_URL + "/" + url, headers=self._headers, timeout=timeout, data=data, params=params
            ) as resp:
                if resp.status != 200:
                    if resp.status == 404 and check:
                        return False
                        
                    if retry and resp.status in (401, 404):
                        # login and try again
                        await self.login()
                        return await self.__make_request(make_request, url, data, params, False)
                    raise SleepIQAPIException(f"API call error response {resp.status}\n{resp.text}")
                if check:
                    return True
                return await resp.json()
        except asyncio.TimeoutError as ex:
            # timed out
            raise SleepIQTimeoutException("API call timed out") from ex
        
    # initialize beds and sleepers from API
    async def init_beds(self):             
        data = await self.get('bed')
        
        # get beds
        self.beds = {bed['bedId']: SleepIQBed(self, bed) for bed in data['beds']}
        
        # get sleepers and assign to beds
        data = await self.get('sleeper')
        for sleeper_data in data['sleepers']:
            if sleeper_data['bedId'] not in self.beds: continue
            sleeper = self.beds[sleeper_data['bedId']].sleepers[sleeper_data['side']]
            sleeper.name = sleeper_data['firstName']
            sleeper.active = sleeper_data['active']
            
        # init foundations
        for bed in self.beds.values():
            await bed.foundation.fetch_features()
            await bed.foundation.init_lights()
        
    # update statuses of sleepers/beds
    async def fetch_bed_statuses(self):
        data = await self.get('bed/familyStatus')
        for bed_status in data['beds']:
            if bed_status['bedId'] not in self.beds: continue
            for i, side in enumerate(["left", "right"]):
                self.beds[bed_status['bedId']].sleepers[i].in_bed = bed_status[side+'Side']['isInBed']
                self.beds[bed_status['bedId']].sleepers[i].pressure = bed_status[side+'Side']['pressure']
                self.beds[bed_status['bedId']].sleepers[i].sleep_number = bed_status[side+'Side']['sleepNumber']
        
        