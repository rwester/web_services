# -*- coding: utf-8 -*-
"""
@author: rwester
@date: 05/13/2016
Script to request and process xml from Zillow APIs
"""
import urllib, urllib2
import xml.etree.cElementTree as ET
import time

class ZillowAPI(object):
    def __init__(self, key, time_delay=.5):
        self.zillow_key = key # zillow api key
        self.time_delay = time_delay # delay due to request frequency limits 
        self.DEEP_SEARCH_API = 'https://www.zillow.com/webservice/GetDeepSearchResults.htm?'   
        self.UPDATED_DETAILS_API = 'https://www.zillow.com/webservice/GetUpdatedPropertyDetails.htm?'
        
    def __response_error(self, error_text):
        raise ValueError("Error in XML response: %s" % error_text)

    def parse_xml(self, element):
        """
        Parses XML to python dictionary
        """
        def __xml_to_dict(element):
            results = {}
            for e in element:
                results[e.tag] = __xml_to_dict(e) if len(e) > 0 else e.text
                if bool(e.attrib) == True:
                    results.update(e.attrib)
            return results
        return {element.tag: __xml_to_dict(element)}
        
    def getDeepSearchResults(self, address, optional_args=None, handle_error=False):
        """
        Address must be a tuple containing the address and city/state/zip  Ex: ('2114 Bigelow Ave', 'Seattle, WA')
        
        At the time of writing this the only optional_param available is rentzestimate: boolean, default False
        
        If handle_error is True will return an empty dictionary, if False will raise an exception
        
        Note: Response can have multiple results, therefore a primary key of result_<int> is return where int is an int from 0 to 
        max number of results. If response only contains one result the returned dictionary will still have primary key of "result_0"
        
        """
        # Checking input vaues
        if isinstance(address, tuple):
            # Define query params
            encode_params = {'zws-id': self.zillow_key, 'address': address[0], 'citystatezip': address[1]} # required
            if optional_args:
                encode_params.update(optional_args) # add optional args
        else:
            raise TypeError("Addres must be tuple of address and city/state/zip for example: ('2114 Bigelow Ave', 'Seattle, WA'), got %s"  % type(address))

        # Send response
        encodedParams = urllib.urlencode(encode_params)
        self.dsr_response = urllib2.urlopen(self.DEEP_SEARCH_API+encodedParams).read() # make accessible from main
        time.sleep(self.time_delay) # delay to space out requests
        
        # Process response        
        self.dsr_xml_et = ET.fromstring(self.dsr_response) # make accessible from main  
        if int(self.dsr_xml_et.find('./message/code').text) == 0:
            results = {}
            elements = self.dsr_xml_et.findall('./response/results/*') # starting point
            for n, element in enumerate(elements): # response can have multiple results, for example a condo complex with many units
                results[element.tag+'_'+str(n)] = self.parse_xml(element)['result']
        else:
            error_str = self.dsr_xml_et.find('./message/text').text
            if handle_error == True:
                print "ERROR: " + error_str
                results = {}
            else:
                self.__response_error(error_str)
        return results
        
    def getUpdatedPropertyDetails(self, zpid, handle_error=False):
        """
        Returns updated property info given a zpid (zillow property id)
        If handle_error is True will return an empty dictionary, if False will raise an exception
        """     
        # Send response
        encodedParams = urllib.urlencode({'zws-id': self.zillow_key, 'zpid': zpid})
        self.upd_response = urllib2.urlopen(self.UPDATED_DETAILS_API+encodedParams).read()
        time.sleep(self.time_delay) # delay to space out requests
        
        # Process response
        self.upd_xml_et = ET.fromstring(self.upd_response)        
        if int(self.upd_xml_et.find('./message/code').text) == 0:
            elements = self.upd_xml_et.find('./response') # starting point
            results = self.parse_xml(elements)['response']
        else:
            error_str = self.upd_xml_et.find('./message/text').text
            if handle_error == True:
                print "ERROR: " + error_str
                results = {}
            else:
                self.__response_error(error_str)
        return results
        
if __name__=='__main__':
    # Example use
    zillow = ZillowAPI('some zillow key')
    results = zillow.getDeepSearchResults(("2114 Bigelow Ave", "Seattle, WA"), optional_args={'rentzestimate': 'True'})  
    print results
    print "\n"
    updated_results = zillow.getUpdatedPropertyDetails(results['result_0']['zpid'])
    print updated_results
    
    
