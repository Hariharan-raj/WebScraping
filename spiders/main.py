import scrapy
import re
from itunesbot.items import AppItem
import itunesbot.spiders.country_code_map as ccode
from urllib.parse import urlparse
from bs4 import BeautifulSoup

def extractFirst(val):
    return val.extract_first(default='Not Found')

def extractFirstNum(val):
    return val.extract_first(default=0)

def extractFirstElseNone(val):
    return val.extract_first(default=None)


class AppSpider(scrapy.Spider):
    name = "argos_itunes"


    def __init__(self,
                 start='https://itunes.apple.com/us/genre/ios-shopping/id6024?mt=8',
                 start_letter='A',
                 end_letter='Z',
                 popular=None,
                 *args,
                 **kwargs):

        """
        This will instantiate the spider .
        The spider will being the crawl based on the inputs provided and will do only 1 of the below possible scenarios
        a. If start and popular is provided , then Popular Apps are only fetched.
        b. Else If start , start_letter and end_letter is provided , then do Alphabetwise Crawl

        :param start: The start url from which the spider will begin the crawling
        :param start_letter: Batch control , specifies the Page to start with
        :param end_letter: Batch control , specifies the Page to end with
        :param popular: Only Popular Apps - roughly it will give you Top 200 apps
        :param args: Additional arguments
        :param kwargs: Additional Keyword Arguments
        """

        super(AppSpider, self).__init__(*args, **kwargs)
        #Pattern to get itunes app link
        self.pat_app_link = re.compile(r'https://itunes.apple.com/[\w][\w]/app/(.)*')

        self.base_url = start
        #Set whether to get Popular Apps only or not
        if popular is not None:
            self.popular = bool(popular)
        else:
            self.popular = False

        # Set the Letters as provided in the arguments
        self.start_letter = start_letter
        self.end_letter = end_letter

        #Set to store urls already visited
        self.urlsvisited = {}

    def start_requests(self):

        self.logger.info('Setting up the Spider')

        # Check if Popular is provided or not
        # This is only the Popular Apps for the given Genre/Category
        if self.popular:
            self.logger.info('Popular Apps Fetch -- Started')
            yield scrapy.Request(url=self.base_url, callback=self.parseCategory)

        # Then letter wise fetch needs to be done
        # This is Alphabet Wise
        else:
            self.logger.info('Alphabetwise Fetch -- Started')
            self.logger.info('Range given is {}-{}'.format(self.start_letter,self.end_letter))
            letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ*'
            start_index = letters.index(self.start_letter)
            end_index = letters.index(self.end_letter) + 1
            for letter in letters[start_index:end_index]:
                url = '{}&letter={}'.format(self.base_url,letter)
                self.logger.info('Send request to url : {}'.format(url))
                yield scrapy.Request(url=url, callback=self.parseAlphabetWise)


    def parseCategory(self,response):

        """
        This will parse the genres page in App Store and will fetch the popular apps
        :param response: Response as received when hitting the url
        :return: Scrapy Request object
        """

        for link in response.css('a[href^="https://itunes.apple.com/"]::attr(href)').extract():
            match = re.match(self.pat_app_link,link)
            if match:
                self.logger.info('App url {} -- request sent'.format(link))
                yield scrapy.Request(url=link,callback=self.parseAppDetails_v2)


    '''
    This will get the list of Apps in the Page Wise and Alphabetical Display of Apps.
    Will be used only 
    '''
    def parseAlphabetWise(self,response):

        """
        Gets the List of App urls in the Alphabetwise and Pagewise Display Layouts

        :param response: URL Request Response
        :return: Scrapy Request Object
        """

        #Get the App Links
        for link in response.css('a[href^="https://itunes.apple.com/"]::attr(href)').extract():
            match = re.match(self.pat_app_link,link)
            if match:
                request = scrapy.Request(url=link,callback=self.parseAppDetails_v2)
                request.meta['handle_httpstatus_list'] = [403,503]
                self.logger.info('App url {} -- request sent'.format(link))
                yield request

        #Go to next Page if available
        for link in response.css('#selectedgenre > ul:nth-child(2) > li > a::attr(href)').extract():

            #Check if link already visited or not
            #if link in self.urlsvisited:
            #    continue
            #else:
            #    self.urlsvisited[link] = True
            #yield scrapy.Request(url=link,callback=self.parseAlphabetWise)
            self.logger.info('AppList url {} -- request sent'.format(link))
            yield scrapy.Request(url=link, callback=self.parseCategory)


    '''
    This will parse the App Detail Page and extract all the required information
    Extracted Information will be stored as Scrapy Item
    '''
    def parseAppDetails(self,response):
        
        DOWNLOAD_DELAY = 5
        self.logger.info('App Details Extraction : {} -- started'.format(response.url))
        # Enhanced Code Starts Below
        appitem = AppItem()
        appitem['app_for_watch'] = False
        # Store the App URL
        appitem['app_url'] = response.url
        if (response.status != 200):
            self.logger.info('App url {} -- non 200 response'.format(response.url))
            appitem['app_crawl_status'] = 'fail'
            return appitem

        appitem['app_crawl_status'] = 'success'
        # Store the Language in which this App URL Page was crawled
        appitem['app_html_lang'] = extractFirst(response.css('html::attr(lang)'))
        # Store the App Title on seen on the Title Bar of the Page
        appitem['app_title'] = extractFirst(response.css('head > title::text'))
        # Store the App Name as seen
        appitem['app_name'] = extractFirst(response.css('#title > div.left > h1::text'))
        # Store the App Publisher
        appitem['app_publisher'] = extractFirst(response.css('#title > div.left > h2::text'))
        # Store the App Publisher's Store Site
        appitem['app_publisher_store_site'] = extractFirst(response.css('#title > div.right > a::attr(href)'))

        # Store the App Publisher Home Site
        appitem['app_publisher_home_site'] = extractFirst(
            response.css('#content > div > div.center-stack > div.app-links > a:nth-child(1)::attr(href)'))
        # Store the App Support Site if available
        appitem['app_support_site'] = extractFirst(
            response.css('#content > div > div.center-stack > div.app-links > a:nth-child(2)::attr(href)'))

        for row in response.css('#left-stack > div.lockup.product.application > ul > li'):
            # Store the App Pricing
            rec = row.xpath('span[contains(@itemprop,"offers")]/div/text()').extract_first()
            if rec is not None:
                appitem['app_pricing'] = rec
                if "Free" in appitem['app_pricing']:
                    appitem['is_paid'] = False
                else:
                    appitem['is_paid'] = True
                continue
            # Store the App Category
            rec = row.xpath('@class').extract_first()
            if rec is not None and "genre" in rec:
                appitem['app_category_name'] = row.css('a > span::text').extract_first()
                # Store the App Category Id
                categoryURL = extractFirst(row.css('a::attr(href)'))
                try:
                    part = urlparse(categoryURL)
                    segments = part.path.split('/')
                    appitem['app_category_id'] = segments[4].replace('id', '')
                except:
                    appitem['app_category_id'] = 'na'
                continue

            # Store the App Updated Date and Release Date
            elif rec is not None and 'release' in rec:
                # Store the App Updated Date
                last_updated_date = extractFirst(row.css('span:nth-child(2)::text'))
                appitem['app_date_updated'] = last_updated_date

                # Store the App Release Date
                release_date = extractFirst(row.css('span:nth-child(2)::attr(content)'))
                appitem['app_date_published'] = release_date
                continue

            # Store the App Languages
            elif rec is not None and 'language' in rec:
                appitem['app_lang'] = extractFirst(row.xpath('text()'))
                continue

            # Store the App Version
            rec = row.xpath('span[contains(@itemprop,"softwareVersion")]/text()').extract_first()
            if rec is not None:
                appitem['app_version'] = rec
                continue

            # Store the App Size
            rec = extractFirst(row.css('span::text'))
            if "size" in rec.lower():
                appitem['app_size'] = extractFirst(row.xpath('text()'))
                continue
            elif "watch" in rec.lower():
                appitem['app_for_watch'] = True
                continue

            # Store the App Seller
            rec = row.xpath('span[contains(@itemprop,"author")]/span/text()').extract_first()
            if rec is not None:
                appitem['app_seller'] = rec
                continue

        # Store the App Content Rating
        tmp = response.css('#left-stack > div.lockup.product.application > div.app-rating > a::text').extract_first()
        if tmp:
            appitem['app_content_rating'] = tmp
        else:
            tmp = response.css('#left-stack > div.lockup.product.application > div > a::text').extract_first()
            if tmp:
                appitem['app_content_rating'] = tmp
            else:
                appitem['app_content_rating'] = 'Not found'

        # Store the App Content Rating Reasons
        tmp = ''
        for row in response.css('#left-stack > div.lockup.product.application > div.app-rating > ul > li'):
            tmp = tmp + row.xpath('text()').extract_first().strip()
        appitem['app_content_rating_reasons'] = tmp

        # Store the App compatability
        appitem['app_compatibility'] = extractFirst(response.xpath('//*[@id="left-stack"]/div[1]/p/span[2]/text()'))

        # Store the Current Version Ratings Value
        appitem['app_rating_value_cv'] = float(extractFirstNum(
            response.css('#left-stack > div.extra-list.customer-ratings > div:nth-child(3) > span:nth-child(1)::text')))
        # Store the Current Version Review Counts
        cv_reviewCount = extractFirstNum(
            response.css('#left-stack > div.extra-list.customer-ratings > div:nth-child(3) > span.rating-count::text'))
        if cv_reviewCount != 0:
            cv_reviewCount = cv_reviewCount.replace("Ratings", "").strip()
        appitem['app_review_counts_cv'] = int(cv_reviewCount)
        # Store the Current Version Star Ratings
        appitem['app_star_rating_cv'] = appitem['app_rating_value_cv']

        # Get the App Current Version Ratings
        appitem['app_rating_cv'] = extractFirst(
            response.css('#left-stack > div.extra-list.customer-ratings > div:nth-child(3)::attr(aria-label)'))
        # Get the App All Version Ratings
        appitem['app_rating_av'] = extractFirst(
            response.css('#left-stack > div.extra-list.customer-ratings > div:nth-child(5)::attr(aria-label)'))

        # If possible , get the App All Version Review Counts
        try:
            if 'Ratings' in appitem['app_rating_av']:
                tok = appitem['app_rating_av'].split(',')
                rt = tok[1].strip('Ratings').strip(' ')
                appitem['app_review_counts_av'] = rt
        except Exception as e:
            pass

        # Get the App Top In app Purchases if available
        inapp = response.css('#left-stack > div.extra-list.in-app-purchases > h4').extract_first()
        if inapp:
            appitem['has_inapp'] = True
        else:
            appitem['has_inapp'] = False

        tmp = ''
        for inappdata in response.css('#left-stack > div.extra-list.in-app-purchases > ol > li'):
            tmp = tmp + ' '.join(inappdata.css('span::text').extract())
            tmp = tmp + '||'
        appitem['inapp_info'] = tmp

        # Store the App Description
        appitem['app_description'] = ' '.join(
            response.css('#content > div > div.center-stack > div:nth-child(1) > p::text').extract())

        # Store the Version Remarks
        appitem['app_version_remarks'] = ' '.join(
            response.css('#content > div > div.center-stack > div:nth-child(3) > p::text').extract())

        # Get Similar Apps bought by Customer
        tmp = ''
        for sa in response.css('#content > div > div.center-stack > div:nth-child(6) > div.content > div > div'):
            # tmp = tmp + sa.xpath('@aria-label').extract_first().strip() + ' | '
            tmp = tmp + sa.xpath('a/@href').extract_first().rstrip() + '||'
        appitem['app_cust_also_bought'] = tmp

        # Store the Customer Reviews
        tmp = ''
        for sa in response.css('#content > div > div.center-stack > div.customer-reviews > div'):
            tmp = tmp + sa.xpath('h5/div/@aria-label').extract_first() + ':'
            tmp = tmp.replace('\n', '')
            tmp = tmp.replace('\t', '')
            tmp = tmp + sa.xpath('p/text()').extract_first().strip() + '|'
            tmp = tmp.lstrip().replace('\n', '').replace('\t', '')
        appitem['app_customer_reviews'] = tmp

        # Store the App Geo and App Id
        part = urlparse(response.url)
        segments = part.path.split('/')
        appitem['app_geo'] = segments[1]
        appitem['app_num'] = segments[4].replace('id', '')

        if appitem['app_geo'] in ccode.country_codes_map:
            appitem['app_country'] = ccode.country_codes_map[appitem['app_geo']]
        # End of Enhanced Code Addition

        self.logger.info('App Details Extraction : {} -- done'.format(response.url))
        return appitem
    
    # Updating the App Details Parser to incorporate the new layout 
    # Dec 6 - hari 
    def parseAppDetails_v2(self,response):

        self.logger.info('App Details Extraction : {} -- started'.format(response.url))
        # Enhanced Code Starts Below
        appitem = AppItem()
        appitem['app_for_watch'] = False
        # Store the App URL
        appitem['app_url'] = response.url
        extras = {}
        if (response.status != 200):
            
            self.logger.info('App url {} -- non 200 response'.format(response.url))
            appitem['app_crawl_status'] = 'fail'
            return appitem

        kvmap={'Seller':'app_seller', 'Size':'app_size', 'Category':'app_category_name', 'Price':'app_pricing', 'App Support':'app_support_site', 'Developer Website':'app_publisher_home_site', 'Privacy Policy':'app_privacy_policy', 'Copyright':'app_copyright', 'Age Rating':'app_rating', 'In-App Purchases':'inapp_info'}                
        Soup = BeautifulSoup(response.text, 'lxml')
        app_name = Soup.find('h1',{'class' : 'product-header__title app-header__title'}).text
        appitem['app_name'] = re.sub('[\s] +',' ',app_name).strip()
        app_info = Soup.find_all("div",{"class":"information-list__item l-row"})
        app_related_links = Soup.find("div",{"class" : 'l-column small-hide medium-show medium-9 medium-offset-3 large-10 large-offset-2'})
        customer_ratings = Soup.find("div",{"class":"we-customer-ratings__averages"})
        try:
                app_ratings=customer_ratings.text
                appitem['app_content_rating']=re.sub('[\s] +',' ',app_ratings).strip()
        except:
                appitem['app_content_rating']='not sufficent ratings'

        for x in app_info:
                try:
                        key=(x.find('dt',{'class' : 'information-list__item__term medium-valign-top l-column medium-3 large-2'})).text
                        value=(x.find('dd',{'class' : 'information-list__item__definition l-column medium-9 large-6'})).text

                        # Check if key is present in kvmap 
                        # If key not present , then standardize the key and add it to extras 
                        if key in kvmap:
                            appitem[re.sub('[\s] +',' ',kvmap[key]).strip()]=re.sub('[\s] +',' ',value).strip()
                        else:
                            stdkey = key.replace(' ','_').lower()
                            extras[stdkey] = value
                except:
                        value='nil'
        for link in app_related_links.findAll('a', href=True):
                        # Check if key is present in kvmap 
                        # If key not present , then standardize the key and add it to extras 
                        if link.text in kvmap:
                            appitem[kvmap[link.text]]=re.sub('[\s] +',' ',link['href']).strip()
                        else:
                            stdkey = link.text.replace(' ','_').lower()
                            extras[stdkey] = re.sub('[\s] +',' ',link['href']).strip()
        
        # Add the extras to the appitem
        appitem['app_extras'] = re.sub('[\s] +',' ',extras).strip()

            # Updating the App Details Parser 
            # Dec 14 - Hariharan
        # Add the app supports to the appitem
        temp=[]
        supports = soup.findAll('div',attrs={"class":"supports-list__item__copy"})
        for x in supports:
             y = x.find('h3').text
             temp.append(y.strip())
        appitem['app_supports'] = temp
            
        #Add the app descrption to the appitem
        description = soup.find("div",{"class" : 'section__description'})
        appitem['app_version_remarks']=description.find('p').get_text())

        #Add the apps by same developer and the similar apps
        d={}
        c={}
        temp2=soup.find_all("section",{"class":'l-content-width section section--bordered'})
        for h2tags in temp2:
            temp=h2tags.find_all("h2",{"class":'section__headline'})
            for x in temp:
                names = x.get_text().strip()
                if names == 'More By This Developer':
                    app_info=h2tags.find_all("div",{"class" : 'we-lockup__title '})
                    app_links=h2tags.find_all("a",{"class" : 'targeted-link'})
                    for z in app_links:
                        app_href=(z.attrs['href'])
                        app_names=z.find("div",{"class" : 'we-truncate we-truncate--single-line ember-view targeted-link__target'})
                        app_name=(app_names.get_text())
                        d[re.sub('[\s] +',' ',app_name).strip()]=re.sub('[\s] +',' ',app_href).strip()
                        appitem['more_apps_by_developer']=d
                elif names == 'You May Also Like':
                    app_info=h2tags.find_all("div",{"class" : 'we-lockup__title '})
                    app_links=h2tags.find_all("a",{"class" : 'targeted-link'})
                    for z in app_links:
                        app_href=(z.attrs['href'])
                        app_names=z.find("div",{"class" : 'we-truncate we-truncate--single-line ember-view targeted-link__target'})
                        app_name=(app_names.get_text())
                        c[re.sub('[\s] +',' ',app_name).strip()]=re.sub('[\s] +',' ',app_href).strip()
                        appitem['similar_apps']=c

        return appitem  
