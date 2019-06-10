#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 04 12:23:08 2019

@author: braulio.gonzalez
"""

import requests
from bs4 import BeautifulSoup
import time
import csv
from fake_useragent import UserAgent

#generating fake header agents
ua = UserAgent().random

#agent headers - NOT being used, using crawlera headers
headers = {"User-Agent": ua, "referer": "no-referrer-when-downgrade", "Connection": "close"}

# create file to write data to
# with open('expert_insights_products.csv', 'w') as csvfile_out:
#     writer = csv.writer(csvfile_out, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

#data source url
data_source = 'https://www.g2.com/'

def get_request(url):
    """
    attempts to make a conection to retrieve url content
    if connection unsuccessful None object returned
    """
    try:
        response = requests.get(url, headers=headers, timeout=15)
        raw_html = response.content
    except requests.exceptions.RequestException as e:
        return None
    return raw_html

def write_to_files(file, vars):
    """
    function used to write to file 
    takes in file name, and list or tuple
    that is being written
    """
    with open(file, 'a') as f:
        writer = csv.writer(f)
        # vars has to be list or tuple
        writer.writerow(vars)
    f.close

 
def category_source_urls(main_source_url):
    """ 
    function made to extract all category 
    links from the data source url
    """
    #appending the category sitmap path to the root url
    main_source_url += 'categories?category_type=software'
    #making the http request and getting raw html
    req = get_request(main_source_url)
    if req == None:
        return 'issue makeing reqest, no links generated'
    else:
        #parse the the html get all links for the categories
        soup = BeautifulSoup(req, 'html.parser')
        containrize_links = soup.select_one('div.row.column.newspaper-columns.large-up-3.medium-up-2')
        links = []
        for a in containrize_links.find_all('a',href=True):
            if a.text:
                links.append('https://www.g2.com' + a['href'])
        return links #return list of links

category_links = category_source_urls(data_source)

#checking to see if links were not generated
if category_links != 'issue makeing reqest, no links generated':
    #crawl and scrape all category links for products
    for link in category_links:
        response = get_request(link)
        print('making request',link)
        if response == None:
            print("issue crawling link," , link)
            write_to_files("analyzo_fail.csv", [link, "issue crawling link" ])
        else:
            soup = BeautifulSoup(response, 'html.parser')
            #containerize all product cards to extract product information
            product_container = soup.select_one('div.panel-primary')
            product_cards = product_container.find_all('div',{'class':'plan-panel-body'})
            id_count = 1
            for product in product_cards:
                try:
                    product_name = [product.find('h3', {'class': "media-heading"}).a.get_text() if product.find('h3', {'class': "media-heading"}).a.get_text() else 'no name'][0]
                    product_desc = [product.find('h3', {'class': "media-heading"}).next_sibling.strip() if product.find('h3', {'class': "media-heading"}).next_sibling.strip() else 'no product description'][0]
                    num_of_upvotes =[product.find('span', {'class':'fa-stack'}).next_sibling.next_sibling.get_text() if product.find('span', {'class':'fa-stack'}).next_sibling.next_sibling.get_text() else 'no upvotes found'][0]
                    product_url = [product.select_one('a.visitWebSitebtn')['data-value'] if product.select_one('a.visitWebSitebtn')['data-value'] else 'no product url found'][0]
                    write_to_files('analyzo_products.csv',[id_count, product_name, product_desc, num_of_upvotes, product_url, link])
                    id_count += 1
                except:
                    write_to_files('analyzo_products.csv',[id_count, 'error retreving data, no data points found', link])
                    id_count += 1
        time.sleep(45)
else:
    print(category_links, "crawler failed ")

print('finished writing to file')

# test links
# no pagination -https://www.g2.com/categories/e-commerce-analytics
# paginated - https://www.g2.com/categories/e-commerce-platforms

def paginated(url):
    html =  get_request(url)
    parsed_html = BeautifulSoup(html,"html.parser").find('a', {'class':'pagination__named-link'})
    if html != None and parsed_html != None:
        #xtract the data from all the pages of products
        pagination_section = BeautifulSoup(html, "html.parser").select_one('ul.pagination.text-center.branded-pagination')
        last_number = int(pagination_section('li')[-1].a['href'].split('page=')[1][0])
        for i in range(last_number):
            print i
    else:
        #no pagination follow the same scraping method