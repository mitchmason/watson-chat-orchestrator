# ------------------------------------------------
# IMPORTS ----------------------------------------
# ------------------------------------------------
#####
# Python dist and 3rd party libraries
#####
import os, requests, json, string, datetime, csv
from flask import session
#####
# Other python modules in WEA demo framework
#####
import custom, watson
# ------------------------------------------------
# GLOBAL VARIABLES -------------------------------
# ------------------------------------------------
#####
# Tokens
#####
SEARCH_WITH_RANDR = '(--SEARCH_WITH_RANDR--)'
SEARCH_WITH_WEX = '(--SEARCH_WITH_WEX--)'
EVALUATE_PREDICTIVE_MODEL = '(--EVALUATE_PREDICTIVE_MODEL--)'
PRESENT_FORM = '(--FORM--)'
#####
# Replacement Strings
#####
#PRODUCT_NAME_OPTIONS_DEFAULT = "[option value='Product_Name']...Select...[/option]"
#PRODUCT_NAME_OPTIONS_POPULATED = ''
HASH_VALUES = {}
BODY = {}

# ------------------------------------------------
# FUNCTIONS --------------------------------------
# ------------------------------------------------
#####
# in external modules
#####
populate_entity_from_randr_result = custom.populate_entity_from_randr_result
markup_randr_results = custom.markup_randr_results
populate_entity_from_wex_result = custom.populate_entity_from_wex_result
markup_wex_results = custom.markup_wex_results
#get_custom_response = custom.get_custom_response
set_predictive_model_context = custom.set_predictive_model_context
BMIX_evaluate_predictive_model = watson.BMIX_evaluate_predictive_model
BMIX_retrieve_and_rank = watson.BMIX_retrieve_and_rank
WEX_retrieve = watson.WEX_retrieve

#####
# local
#####
# Search helper funcs ----------------------------
def get_search_response(search_type, shift):
	search_response = ''
	if search_type == "RANDR":
		s('RANDR_CURSOR', shift_cursor(g('RANDR_SEARCH_RESULTS', []), g('RANDR_CURSOR', 0), shift))
		search_response = markup_randr_results(g('RANDR_SEARCH_RESULTS', []), g('RANDR_CURSOR', 0))
	elif search_type == "WEX":
		s('WEX_CURSOR', shift_cursor(g('WEX_SEARCH_RESULTS', []), g('WEX_CURSOR', 0), shift))
		search_response = markup_wex_results(g('WEX_SEARCH_RESULTS', []), g('WEX_CURSOR', 0))
	return search_response

def search_randr(question):
	#global RANDR_SEARCH_ARGS
	randr_search_results = []
	randr_cursor = 0
	application_response = ''
	#docs = BMIX_retrieve_and_rank(question, RANDR_SEARCH_ARGS)
	docs = BMIX_retrieve_and_rank(question)
	i = 0
	for doc in docs:
		i += 1
		entity = populate_entity_from_randr_result(doc)
		randr_search_results.append(entity)
	application_response = markup_randr_results(randr_search_results, randr_cursor)
	s('RANDR_SEARCH_RESULTS', randr_search_results)
	s('RANDR_CURSOR', randr_cursor)
	return application_response

def search_wex(question):
	wex_search_results = []
	wex_cursor = 0
	application_response = ''
	docs = WEX_retrieve(question)
	i = 0
	for doc in docs:
		i += 1
		entity = populate_entity_from_wex_result(doc)
		wex_search_results.append(entity)
	application_response = markup_wex_results(wex_search_results, wex_cursor)
	s('WEX_SEARCH_RESULTS', wex_search_results)
	s('WEX_CURSOR', wex_cursor)
	return application_response

def shift_cursor(search_results, cursor, shift):
	cursor = cursor + shift
	if cursor < 0:
		cursor = max(len(search_results)-1,0)
	elif cursor >= len(search_results):
		cursor = 0
	return cursor
	
# Replacement str funcs --------------------------
def load_hash_values(app):
	hash_values = {}
	with app.open_resource('hash.csv') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			hash_values[row['key']] = row['value']
	return hash_values

def build_options(app, file_name, var_name):
	options = ''
	with app.open_resource(file_name) as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			options = options + '[option value="' + row[var_name] + '"]' + row[var_name] + '[/option]'
	return options
	
# TOA helper func --------------------------------
def load_body(app):
	body = {}
	#with app.open_resource('body.json', 'r') as myfile:
	#	json_data = myfile.read()
	#	body = json.loads(json_data)
	return body

def get_body():
	global BODY
	return BODY

def extract_search_arg(message):
	search_arg = ''
	if 'input' in message:
		input = message['input']
		if 'text' in input:
			search_arg = input['text']
	return search_arg

# Predictive Analytics helper funcs --------------
def extract_predictive_model(message):
	model = {}
	if 'context' in message:
		context = message['context']
		if 'predictive_model' in context:
			model = context['predictive_model']
	return model

# Session var set and get funcs ------------------
def s(key, value):
	session[key] = value
	return session[key]

def g(key, default_value):
	if not key in session.keys():
		session[key] = default_value
	return session[key]

# Application funcs ------------------------------
def register_application(app):
	#global HASH_VALUES, PRODUCT_NAME_OPTIONS_POPULATED
	global HASH_VALUES
	#PRODUCT_NAME_OPTIONS_POPULATED = build_options(app, 'Product-Names.csv', 'Product_Name')
	HASH_VALUES = load_hash_values(app)
	return app
	
def format_text(message):
	formatted_text = 'The chat-bot is not currently available. Try again?'
	if 'output' in message:
		output = message['output']
		if 'text' in output:
			formatted_text = ''
			text = output['text']
			for dialog_response_line in text:
				if str(dialog_response_line) != '':
					if len(formatted_text) > 0:
						formatted_text = formatted_text + ' ' + dialog_response_line
					else:
						formatted_text = dialog_response_line
	return formatted_text

def get_form(text):
	global PRESENT_FORM
	form = ''
	if PRESENT_FORM in text:
		responses = text.split(PRESENT_FORM)
		form = responses[1]
	return form

def get_chat(text):
	global PRESENT_FORM
	chat = text
	if PRESENT_FORM in text:
		responses = text.split(PRESENT_FORM)
		chat = responses[0]
	return chat
	
def get_application_message(message):
	global HASH_VALUES
	formatted_text = format_text(message)
	formatted_text = string.replace(formatted_text, '[', '<')
	formatted_text = string.replace(formatted_text, ']', '>')
	chat = get_chat(formatted_text)
	form = get_form(formatted_text)
	context = {}
	#application_message
	application_message = {'chat': chat, 'form': form, 'context': context}
	for key in HASH_VALUES:
		value = HASH_VALUES[key]
		application_message['chat'] = application_message['chat'].replace(key, value)
	#randr search requested
	if (application_message['chat'].startswith(SEARCH_WITH_RANDR)):
		search_arg = extract_search_arg(message)
		application_message['chat'] = search_randr(search_arg)
	#wex search requested
	if (application_message['chat'].startswith(SEARCH_WITH_WEX)):
		search_arg = extract_search_arg(message)
		application_message['chat'] = search_randr(search_arg)
	#predictive model evaluated
	if (application_message['chat'].startswith(EVALUATE_PREDICTIVE_MODEL)):
		application_message['chat'] = application_message['chat'].replace(EVALUATE_PREDICTIVE_MODEL, '')
		model = extract_predictive_model(message)
		#model = g('PREDICTIVE_MODEL', {})
		entity = BMIX_evaluate_predictive_model(model)
		application_message['context'] = set_predictive_model_context(entity)
	return application_message