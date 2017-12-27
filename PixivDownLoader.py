import requests
import re
import http.cookiejar
from bs4 import BeautifulSoup
import queue
import os
import platform

class UrlStruct():
    def __init__(self,title, urlType, imageUrl):
        self.imageUrl = imageUrl
        self.urlType = urlType
        self.title = title


class PixivSpider(object):
    def __init__(self):
        self.session = requests.Session()
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36'}
        self.session.headers = self.headers
        self.session.cookies = http.cookiejar.LWPCookieJar(filename='cookies')
        try:
            # 加载cookie
            self.session.cookies.load(filename='cookies', ignore_discard=True)
        except:
            print('cookies無法載入\n')
        self.params ={
            'lang': 'en',
            'source': 'pc',
            'view_type': 'page',
            'ref': 'wwwtop_accounts_index'
        }
        self.datas = {
            'pixiv_id': '',
            'password': '',
            'captcha': '',
            'g_reaptcha_response': '',
            'post_key': '',
            'source': 'pc',
            'ref': 'wwwtop_accounts_indes',
            'return_to': 'https://www.pixiv.net/'
            }
    def get_postkey(self):
        login_url = 'https://accounts.pixiv.net/login' # 登陆的URL
        # 获取登录页面
        res = self.session.get(login_url, params=self.params)
        # 获取post_key
        pattern = re.compile(r'name="post_key" value="(.*?)">')
        r = pattern.findall(res.text)
        self.datas['post_key'] = r[0]
    def already_login(self):
        # 请求用户配置界面，来判断是否登录
        url = 'https://www.pixiv.net/setting_user.php'
        login_code = self.session.get(url, allow_redirects=False).status_code
        if login_code == 200:
            return True
        else:
            return False
    def login(self, account, password):
        post_url = 'https://accounts.pixiv.net/api/login?lang=en' # 提交POST请求的URL
        # 设置postkey
        self.get_postkey()
        self.datas['pixiv_id'] = account
        self.datas['password'] = password
        # 发送post请求模拟登录
        result = self.session.post(post_url, data=self.datas)
        print(result.json())
        # 储存cookies
        self.session.cookies.save(ignore_discard=True, ignore_expires=True)

    def accountClear(self):
        os.remove("cookies")
        self.__init__()


class CreateDownloadList():
    def __init__(self, session, memberID):
        self.memberID = memberID
        self.session = session
        self.threadPool = queue.Queue(0)

    def getImageList(self):
        url = 'https://www.pixiv.net/member_illust.php?id=' + self.memberID + '&type=all'

        emptyFlag = False
        page = 1
        while( not emptyFlag ):
            pageUrl = url + '&p=' + str(page)
            #print(pageUrl)
            res = self.session.get(pageUrl)
            soup = BeautifulSoup(res.text, "html.parser")

            for imagelink in soup.select('li.image-item'):

                title = imagelink.select('h1')[0]['title']
                topicUrl = "https://www.pixiv.net" + imagelink.select('a')[0]['href']

                topicUrl = topicUrl.replace('medium', 'manga')
                #print(topicUrl)

                if self.checkAlive(topicUrl):
                    urlType = "manga"
                    self.mangaList(title, urlType, topicUrl)


                else:
                    urlType = "medium"
                    topicUrl = topicUrl.replace('manga', 'medium')
                    self.mediumList(title, urlType, topicUrl)


                print(title)
                print(urlType)
                #print(topicUrl)

                #print(imagelink)
            if len(soup.select('li.image-item')) == 0:
                emptyFlag = True
            else:
                page += 1
        
        return True

    def mangaList(self, title, urlType, topicUrl):
        mangaPage = 0
        mangaEmptyFlag = False
        topicUrl = topicUrl.replace('manga', 'manga_big')
        mangaUrl = topicUrl + '&page=' + str(mangaPage)
        while( self.checkAlive(mangaUrl) ):
            mangaRes = self.session.get(mangaUrl)
            imageSoup = BeautifulSoup(mangaRes.text, "html.parser")
            imageUrl = imageSoup.select('img')[0]['src']
            print(imageUrl)
            self.threadPool.put(UrlStruct(title, urlType, imageUrl))
            self.saveImage(topicUrl, imageUrl, title)

            #next image
            mangaPage += 1
            mangaUrl = topicUrl + '&page=' + str(mangaPage)

    def mediumList(self, title, urlType, topicUrl):
        topicRes = self.session.get(topicUrl)
        topicSoup = BeautifulSoup(topicRes.text, "html.parser")
        imageUrl = topicSoup.select('img.original-image')[0]['data-src']
        print(imageUrl)
        self.threadPool.put(UrlStruct(title, urlType, imageUrl))
        self.saveImage(topicUrl, imageUrl, title)

    def saveImage(self, topicUrl, imageUrl, title):
        header = {  
            'Referer': topicUrl,  
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.75 Safari/537.36'  
        }
        filePath = self.memberID + '/' + str(imageUrl).split('/')[-1]
        f = open(filePath, 'wb')
        resImage = self.session.get(imageUrl, headers = header)
        f.write(resImage.content)
        f.close()
        del resImage


    def checkAlive(self, url):
        if url == "checkAlive":
            url = 'https://www.pixiv.net/member_illust.php?id=' + self.memberID
        responseCode = self.session.get(url).status_code
        
        if responseCode == 200:
            return True
        else:
            return False

class DownloadImage():
    def __init__(self):
        print("")

def clrscr():
    system = platform.system()
    if(system.lower() == 'windows'):
        os.system('cls')
    elif(system.lower() == 'darwin'):
        os.system('clear')

if __name__ == "__main__":

    clrscr()
    spider = PixivSpider()
    DLImageList = "NONE"

    if spider.already_login():
        print('已經存在登入資訊\n')
    else:
        account = input('請輸入帳號\n>>> ')
        password = input('請輸入密碼\n>>> ')
        spider.login(account, password)
        
    while(True):
        print("1. 切換Pixiv帳號")
        print("2. 下載繪師的所有畫作")
        select = input('select\n\n>>> ')
        clrscr()

        if select == '1':
            spider.accountClear()
            account = input('請輸入帳號\n>>> ')
            password = input('請輸入密碼\n>>> ')
            spider.login(account, password)

        elif select == '2':
            member = input('請輸入畫師ID:\n>>> ')
            DLImageList = CreateDownloadList(spider.session, member)
            if DLImageList.checkAlive("checkAlive"):
                print("找到繪師")
                if not os.path.exists(member): 
                    os.makedirs(member)
                DLImageList.getImageList()
            else:
                print("找不到該繪師")

