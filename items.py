# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class AppItem(scrapy.Item):

    '''
    Enhanced the Fields Names to be extracted and naming them to be closer to their
    data that they indicate.
    '''
    app_html_lang = scrapy.Field() # Indicates Language the webpage is displayed in
    app_title = scrapy.Field() #Store the Title as shown in the browser
    app_name = scrapy.Field()  #Name of the App
    app_url = scrapy.Field()   #URL of the App in the AppStore
    app_publisher = scrapy.Field() #App's Publisher
    app_publisher_store_site = scrapy.Field() #App's Publisher Store Site to see more apps by the same publisher
    app_description = scrapy.Field()  #App Description
    app_publisher_home_site = scrapy.Field() #App's Publisher Home WebPage
    app_support_site = scrapy.Field() # Store App's Support Site
    app_designed_for = scrapy.Field() # Stores info of what the App is designed for
    app_for_watch = scrapy.Field() # Indicates whether App offers Watch App or not
    app_user_reviews = scrapy.Field() # Stores user reviews if available in Description Section
    app_pricing = scrapy.Field() # Stores Subscription Pricing if available in Description Section
    app_version_remarks = scrapy.Field() # Stores Info of whats new in the Version
    app_category_name = scrapy.Field() # Stores Name of Category
    app_category_id = scrapy.Field() # Stores Category Id as Category Name is language dependent
    app_date_published = scrapy.Field() # Date when app was published
    app_date_updated = scrapy.Field() # Stores when App was last updated
    is_paid = scrapy.Field() # Indicates whether app is Free or Paid
    app_version = scrapy.Field() # Version of App
    app_size = scrapy.Field() # App Size in MB
    app_lang = scrapy.Field() # Languages present for App
    app_seller = scrapy.Field()  # Seller of the App
    app_content_rating = scrapy.Field() # Content Rating of the App
    app_content_rating_reasons = scrapy.Field() # Reasons for Content Rating
    app_compatibility = scrapy.Field()# Compatibility Info of the App
    app_privacy_policy = scrapy.Field() #stores app privacy policy
    app_copyright = scrapy.Field() #stores copyright info

    #Customer Ratings
    #Current Version
    app_star_rating_cv = scrapy.Field() # Store Rating in stars for Current Version
    app_rating_value_cv = scrapy.Field() # Store Rating Value for Current Version
    app_review_counts_cv = scrapy.Field() # Store Review Counts for Current Version

    #All Versions
    app_star_rating_av = scrapy.Field()  # Store Rating in stars for All Version
    app_rating_value_av = scrapy.Field()  # Store Rating Value for All Version
    app_review_counts_av = scrapy.Field()  # Store Review Counts for All Version

    app_rating_cv = scrapy.Field()
    app_rating_av = scrapy.Field()

    has_inapp = scrapy.Field() # Indicates if In App Purchases present
    inapp_info = scrapy.Field() # The Top In App Purchases available

    supported_devices = scrapy.Field() # Indicates screenshots availability

    #Stores Customer Reviews as seen on the page
    #Format : CSV List of [User|Title|Details]
    app_customer_reviews = scrapy.Field()

    #Stores What other Apps that customers also bought
    #Format : CSV List of [AppName|AppGenre|AppURL|AppGenreURL]
    app_cust_also_bought = scrapy.Field()

    app_crawl_status = scrapy.Field() #Indicates whether crawler successfully crawled or not

    app_geo = scrapy.Field()
    app_num = scrapy.Field()
    app_country = scrapy.Field()

    #End of New Fields
