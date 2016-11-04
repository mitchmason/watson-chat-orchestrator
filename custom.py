# ------------------------------------------------
# IMPORTS ----------------------------------------
# ------------------------------------------------
#####
# Python dist and 3rd party libraries
#####
import os, requests, json, string, datetime, csv
from pprint import pprint
import xmltodict
# ------------------------------------------------
# FUNCTIONS --------------------------------------
# ------------------------------------------------
#####
# local
#####
# Search helper funcs ----------------------------
def populate_entity_from_randr_result(doc):
	entity = {}
	entity['id'] = doc['id']
	entity['body'] = doc['body'][0]
	entity['title'] = doc['title'][0]
	entity['author'] = doc['author'][0]
	entity['RunBook_URL'] = doc['RunBook_URL'][0]
	return entity

def markup_randr_result(entity):
	return ('<p><b>' + entity['title'] + '</b><br><u>Body:</u> ' + entity['body'] + '<br><u>Runbook URL:</u> ' + entity['RunBook_URL'] + '<br><u>Document id:</u> ' + entity['id']+ '</p>')

def markup_randr_results(search_results, cursor):
	application_response = "I'm unable to find what you're looking for. Can you rephrase the question or ask something else?"
	if (len(search_results) > 0):
		entity = search_results[cursor]
		application_response = "I've retrieved <b>" + str(len(search_results)) + " documents</b> that may be of interest. You're viewing document number <b>#" + str(cursor + 1) + "</b>"
		application_response = application_response + markup_randr_result(entity)
		application_response = application_response + '<form action="/page" method="POST"><input type="submit" name="cursor_input" value="Next"/> <input type="submit" name="cursor_input" value="Prev"/> <input type="submit" type="submit" name="cursor_input" value="Accept"/> <input type="hidden" name="search-type" value="RANDR"></form>'
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
		application_response = application_response + '<form action="/page" method="POST"><input type="submit" name="cursor_input" value="Next"/> <input type="submit" name="cursor_input" value="Prev"/> <input type="submit" type="submit" name="cursor_input" value="Accept"/> <input type="hidden" name="search-type" value="WEX"></form>'
	return application_response

# Predictive Analytics helper funcs --------------
def set_predictive_model_from_context(context):
	model = {}
#	implement code to build predictive model from context
	return model

def set_context_from_predictive_model(entity):
	context = {}
	if type(entity) is list:
		campaign = entity[0]
		attr_names = campaign['header']
		attr_values = campaign['data'][0]
		i = 0
		for attr_name in attr_names:
			context[attr_name.replace('$', '').replace(' ', '_').replace('-', '_')] = attr_values[i]
			i += 1
	return context

# Custom service func ----------------------------
def APPLE_post(url, application_context):
	USERNAME = 'john'
	PASSWORD = 'appleseed'
	POST_SUCCESS = 200
	r = requests.post(url, auth=(USERNAME, PASSWORD), headers={'content-type': 'application/json'})
	application_context['REST_API_return_code'] = r.status_code
	if r.status_code == POST_SUCCESS:
		message = r.json()
		application_context['REST_API_message'] = message
	return application_context

def convert_date_format(date_string):
	month = date_string[0:2]
	day = date_string[3:5]
	year = date_string[6:]
	return(year + month + day)

def get_most_recent_order(rest_api_message):
	most_recent_order = {}
	if 'orders' in rest_api_message:
		orders = rest_api_message['orders']
		most_recent_delivery_date = '19991231'
		for order in orders:
			won = order.get('won', '')
			olssUrl = order.get('olssUrl', '')
			lineitems = order.get('lineItems', [])
			for lineitem in lineitems:
				deliveryStatus = lineitem.get('deliveryStatus', '')
				carrierWebsite = lineitem.get('carrierWebsite', '')
				carrierName = lineitem.get('carrierName', '')
				modelNumber = lineitem.get('modelNumber', '')
				carrierTrackingId = lineitem.get('carrierTrackingId', '')
				status = lineitem.get('status', '')
				productName = lineitem.get('productName', '')
				deliveryDate = lineitem.get('deliveryDate', '12/31/1999')
				lineitem['deliveryDate_yyyymmdd'] = convert_date_format(deliveryDate)
				if most_recent_order == {} or lineitem['deliveryDate_yyyymmdd'] > most_recent_delivery_date:
					most_recent_delivery_date = lineitem['deliveryDate_yyyymmdd']
					most_recent_order = order
	return most_recent_order
	
def invoke_custom_service(message_context, custom_service_label):
	application_context = {}
#	if message_context['Apple_REST_API'] == 'Orders list':
#		url = 'http://ec2-52-35-6-233.us-west-2.compute.amazonaws.com/mmap/order/orders'
#		application_context = APPLE_post(url, application_context)
#		application_context['REST_API_most_recent_order'] = get_most_recent_order(application_context['REST_API_message'])
#	elif message_context['Apple_REST_API'] == 'Order detail':
#		url = 'http://ec2-52-35-6-233.us-west-2.compute.amazonaws.com/mmap/order/order?ordernumber=W135'
#		application_context = APPLE_post(url, application_context)
#	elif message_context['Apple_REST_API'] == 'Warranty status':
#		url = 'http://ec2-52-35-6-233.us-west-2.compute.amazonaws.com/mmap/order/warranty?serialnumber=A246'
#		application_context = APPLE_post(url, application_context)
#	elif message_context['Apple_REST_API'] == 'Cancel order':
#		url = 'http://ec2-52-35-6-233.us-west-2.compute.amazonaws.com/mmap/order/cancelorder?ordernumber=W135'
#		application_context = APPLE_post(url, application_context)
	return application_context