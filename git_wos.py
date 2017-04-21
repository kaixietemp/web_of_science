import re
import requests
from lxml import html
import pandas as pd 
import time
import os
#import pickle
os.chdir(r'K:\\wos')

class SpiderMain(object):
    def __init__(self,sid,startYear,endYear,journal):
        self.headers={
            'Origin':'https://apps.webofknowledge.com',
            'Referer':'https://apps.webofknowledge.com/UA_GeneralSearch_input.do?product=UA&search_mode=GeneralSearch&SID=R1ZsJrXOFAcTqsL6uqh&preferencesSaved=',
            'User-Agent':"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36",
            'Content-Type':'application/x-www-form-urlencoded'
        }
        self.form_data={
            'fieldCount':1,
            'action':'search',
            'product':'WOS',
            'search_mode':'GeneralSearch',
            'SID':sid,
            'max_field_count':25,
            'formUpdated':'true',
            'value(input1)':journal,
            'value(select1)':'SO',
            'value(hidInput1)':'',
            'limitStatus':'collapsed',
            'ss_lemmatization':'On',
            'ss_spellchecking':'Suggest',
            'SinceLastVisit_UTC':'',
            'SinceLastVisit_DATE':'',
            'period':'Range Selection',
            'range':'ALL',
            'period':'Year Range',
            'startYear':startYear,
            'endYear':endYear,
            'editions':'SCI',
            'update_back2search_link_param':'yes',
            'ssStatus':'display:none',
            'ss_showsuggestions':'ON',
            'ss_query_language':'auto',
            'ss_numDefaultGeneralSearchFields':1,
            'ss_query_language':'',
            'rs_sort_by':'PY.D;LD.D;SO.A;VL.D;PG.A;AU.A'
        }

    # the first step is to get all papers' url of a specific query
    # the second step is to get all details for every paper 
    
    def craw_first_step(self, root_url,sid):
        urls = [] #links for all papers
        s = requests.Session()
        r = s.post(root_url,data=self.form_data,headers=self.headers)
        tree = html.fromstring(r.content)
           
        #get the total number of pages of a query result
        num_pages = tree.xpath('//span[@id="pageCount.top"]/text()')[0] #done
        
        new_url = tree.xpath('//a[@class="smallV110"]/@href') #done
        qid = int(re.findall(r'qid=\d',new_url[0])[0].replace('qid=',''))
        del new_url

        for i in range(1,int(num_pages)+1):
            print('scraping links on page no.{0} of all {1} pages'.format(i,num_pages))
            #create all urls on a specific page
            url = 'https://apps.webofknowledge.com/summary.do?product=WOS&parentProduct=WOS&search_mode=GeneralSearch&parentQid=&qid='+str(qid)+'&SID='+sid+'&&update_back2search_link_param=yes&page='+str(i)
            new_r = s.get(url,headers=self.headers)
            new_tree = html.fromstring(new_r.content)
                                         
            new_url = new_tree.xpath('//a[@class="smallV110"]/@href') #done
            new_url = list(set(new_url))
            new_url = ['http://apps.webofknowledge.com/'+ x  for x in new_url]
            urls = urls +new_url
            print('waiting for 1 seconds')
            time.sleep(1)
        return(urls)


    def craw_second_step(self,links):   #done
        journals = []
        pub_months = []
        pub_years = []
        titles = []
        authors = []
        corres_authors = []
        corres_addresses = []
        abstracts = []
        
        d = 1
        not_working_urls = []
        for url in links:
            url = url.replace('\n','')
            print('scraping details of paper no.{} of all {} papers'.format(d,len(links)))
            s = requests.Session()
            r = s.get(url)
                
            tree = html.fromstring(r.content)
            #get publication year and month
            for i in range(4,8):
                if(re.search('[a-zA-Z]{3}\s\d{4}',tree.xpath('(//p[@class="FR_field"])['+str(i)+']/value/text()')[0]) != None):
                    pub_year = tree.xpath('(//p[@class="FR_field"])['+str(i)+']/value/text()') 
                    pub_month = re.sub(r'\d{4}','',pub_year[0])
                    pub_year = re.sub(r'[a-zA-Z]{3}\s','',pub_year[0])
                            
                    pub_years.append(pub_year)
                    pub_months.append(pub_month)                                            
                    break
            if(i == 8):
                not_working_urls.append(url)
                continue
            
            
            #get abstract
            abstract = tree.xpath('(//div[@class="block-record-info"])[2]/p/text()') 
            abstract = [re.sub(r'\(C\) \d{4} Elsevier Ltd. All rights reserved.','',x) for x in abstract]
            abstracts.append(abstract)
            #get title
            title = tree.xpath('(//div[@class="title"])/value/text()') 
            titles = titles + title
            #get authors
            author = tree.xpath('(//a[@title="Find more records by this author"])/text()') 
            authors.append(author)
            #get corresponding author
            corres_author = tree.xpath('(//div[@class="block-record-info"])[4]/p[1]/text()') 
            corres_author = [x for x in corres_author if x!='\n']
            corres_author = [re.sub(r' \(reprint author\) ','',x) for x in corres_author]
            corres_authors.append(corres_author)
            
            #get corresponding address
            corres_address = tree.xpath('(//td[@class="fr_address_row2"])[1]/text()') 
            corres_addresses.append(corres_address)
            #get the journal name
            journal = tree.xpath('(//span[@class="hitHilite"])[1]/text()')  
            journals = journals + journal  
                
                
            print('waiting for 1 second')
            time.sleep(1)
            d = d + 1
        for item in not_working_urls:
            links.remove(item)
        res = pd.DataFrame({'LINKS':links,'JOURNALS':journals,'PUB_YEARS':pub_years,'PUB_MONTHS':pub_months,'TITLES':titles,'AUTHORS':authors,'CORRES_AUTHORS':corres_authors,'CORRES_ADDRESSES':corres_addresses,'ABSTRACTS':abstracts})
        #return(links,not_working_urls,journals,titles,authors,corres_authors,corres_addresses,pub_years,pub_months,abstracts)
        return(res,not_working_urls)
             

    

if __name__=="__main__":
    root_url = 'https://apps.webofknowledge.com/WOS_GeneralSearch.do'
    
#==============================================================================
    journal = 'ieee transactions on intelligent transportation systems'   #edit to the name of the journal to scraping
    start_Year = 2000  #edit your period
    end_Year = 2016    #edit your period
#==============================================================================

    root = 'http://www.webofknowledge.com/'
    s = requests.get(root)
    sid = re.findall(r'SID=\w+&',s.url)[0].replace('SID=','').replace('&','')

    obj_spider = SpiderMain(sid,start_Year,end_Year,journal)
        
    obj_links = obj_spider.craw_first_step(root_url,sid)
    
    filename_links = 'all_links_'+journal+'_'+str(start_Year)+'_'+str(end_Year)+'.txt'
    f = open(filename_links,'w')
    for item in obj_links:
        f.write('%s\n' %  item)
    f.close()
    #with open(filename_links,'r') as f:
     #   obj_links = f.read().splitlines()
       
    res,not_working_urls = obj_spider.craw_second_step(obj_links)
    filename_details = 'all_details_'+journal+'_'+str(start_Year)+'_'+str(end_Year)+'.csv'
    res.to_csv(os.path.join(os.getcwd(),filename_details),index=False,sep=';')
    
    if not_working_urls != []:
        filename_not_working = 'not working urls in' + str(journal) + '.csv'
        f = open(filename_not_working,'w')
        for x in not_working_urls:
            f.write("%s\n" % x)
        f.close()
