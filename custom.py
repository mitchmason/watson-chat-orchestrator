import os, requests, json, string, datetime, csv
from pprint import pprint
import xmltodict
# ------------------------------------------------
# FUNCTIONS --------------------------------------
# ------------------------------------------------
#####
# in external modules
#####
def populate_entity_from_randr_result(doc):
	entity = {}
	entity['id'] = doc['id']
	entity['body'] = doc['body'][0]
	entity['title'] = doc['title'][0]
	entity['author'] = doc['author'][0]
	entity['RunBook_URL'] = doc['RunBook_URL'][0]
	return entity

#####
# local
#####
# Search helper funcs ----------------------------
def markup_randr_result(entity):
	return ('<p><b>' + entity['title'] + '</b><br><u>Body:</u> ' + entity['body'] + '<br><u>Runbook URL:</u> ' + entity['RunBook_URL'] + '<br><u>Document id:</u> ' + entity['id']+ '</p>')
		
def markup_randr_results(search_results, cursor):
	application_response = "I'm unable to find what you're looking for. Can you rephrase the question or ask something else?"
	if (len(search_results) > 0):
		entity = search_results[cursor]
		application_response = "I've retrieved <b>" + str(len(search_results)) + " documents</b> that may be of interest. You're viewing document number <b>#" + str(cursor + 1) + "</b>"
		application_response = application_response + markup_randr_result(entity)
		application_response = application_response + '<form action="/page" method="POST"><input type="submit" name="cursor-input" value="Next"/> <input type="submit" name="cursor-input" value="Prev"/> <input type="submit" type="submit" name="cursor-input" value="Accept"/> <input type="hidden" name="search-type" value="RANDR"></form>'
	return application_response
	
def populate_entity_from_wex_result(doc):
	entity = {}
	entity['Url'] = doc['@url']
	entity['FileType'] = doc['@filetypes']
	entity['Snippet'] = ""
	entity['FileName'] = ""
	contents = doc['content']
	for content in contents:
		name = content['@name']
		if name == 'snippet':
			entity['Snippet'] = content['#text']
		if name == 'filename':
			entity['FileName'] = content['#text']
	return entity
		
def markup_wex_results(search_results, cursor):
	application_response = "I'm unable to find what you're looking for. Can you rephrase the question or ask something else?"
	if (len(search_results) > 0):
		entity = search_results[cursor]
		application_response = "I've found the answer to your question in <b>" + str(len(search_results)) + " documents</b> with the most probable answers shown first. You're viewing answer <b>#" + str(cursor + 1) + "</b>"
		url = entity['Url']
		application_response = application_response + '<p style="font-size: small;"><i>' + entity['Snippet'] + '</i> <a href="' + url + '" style="font-size: small;" target="_blank">View document</a></p>'
		application_response = application_response + '<form action="/page" method="POST"><input type="submit" name="cursor-input" value="Next"/> <input type="submit" name="cursor-input" value="Prev"/> <input type="submit" type="submit" name="cursor-input" value="Accept"/> <input type="hidden" name="search-type" value="WEX"></form>'
	return application_response
	
#def get_custom_response(application_response):
	#custom_response = application_response
	#return custom_response

def respond_to_predictive_model(entity):
	response = "Can we entice you to stay with an attractive retention offer?"
	if type(entity) is list:
		campaign = entity[0]
		offer_type = campaign['data'][0][0]
		offer_propensity = campaign['data'][0][1]
		response = response + ' [Predicitve model shows a propensity of ' + str(offer_propensity) + ' that the customer will respond to a ' + offer_type + ']'
	return response