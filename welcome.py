# ------------------------------------------------
# IMPORTS ----------------------------------------
# ------------------------------------------------
#####
# Python dist and 3rd party libraries
#####
import os, requests, json, string, datetime
from os.path import join, dirname
from flask import Flask, request, render_template, redirect, url_for, session
from flask.sessions import SessionInterface
from beaker.middleware import SessionMiddleware
#####
# Other python modules in WEA demo framework
#####
import application, watson

# ------------------------------------------------
# GLOBAL VARIABLES -------------------------------
# ------------------------------------------------
#####
# Hardcoded env variables defaults for testing
#####
PERSONA_NAME = 'Partner'
PERSONA_IMAGE = ''
PERSONA_STYLE = 'Partner'
WATSON_IMAGE = ''
WATSON_STYLE = 'Watson'
CHAT_TEMPLATE = 'designer-index.html'
QUESTION_INPUT = 'response-input'
SEARCH_TYPE_INPUT = 'search-type'
SEARCH_VALUE_INPUT = 'search-values'
CURSOR_INPUT = 'cursor-input'
#####
# Overwrites by env variables
#####
if 'WATSON_STYLE' in os.environ:
	WATSON_STYLE = os.environ['WATSON_STYLE']
if 'PERSONA_STYLE' in os.environ:
	PERSONA_STYLE = os.environ['PERSONA_STYLE']
if 'CHAT_TEMPLATE' in os.environ:
	CHAT_TEMPLATE = os.environ['CHAT_TEMPLATE']
if 'QUESTION_INPUT' in os.environ:
	QUESTION_INPUT = os.environ['QUESTION_INPUT']
if 'CURSOR_INPUT' in os.environ:
	CURSOR_INPUT = os.environ['CURSOR_INPUT']
#####
# Session options
#####
session_opts = {
	'session.type': 'ext:memcached',
	'session.url': 'localhost:11211',
	'session.data_dir': './cache',
	'session.cookie_expires': 'true',
	'session.type': 'file',
	'session.auto': 'true'
}
#####
# Tokens
#####
PRESENT_FORM = '(--FORM--)'

# ------------------------------------------------
# CLASSES ----------------------------------------
# ------------------------------------------------
class BeakerSessionInterface(SessionInterface):
	def open_session(self, app, request):
		session = request.environ['beaker.session']
		return session

	def save_session(self, app, session, response):
		session.save()

# ------------------------------------------------
# FUNCTIONS --------------------------------------
# ------------------------------------------------
#####
# in external modules
#####
register_application = application.register_application
get_application_response = application.get_application_response
get_search_response = application.get_search_response
BMIX_get_conversation_message = watson.BMIX_get_conversation_message
BMIX_get_first_dialog_response_json = watson.BMIX_get_first_dialog_response_json
BMIX_get_next_dialog_response = watson.BMIX_get_next_dialog_response
BMIX_call_alchemy_api = watson.BMIX_call_alchemy_api
BMIX_analyze_tone = watson.BMIX_analyze_tone
get_stt_token = watson.get_stt_token
get_tts_token = watson.get_tts_token
#####
# local
#####
# Chat presentation funcs ------------------------
def create_post(style, icon, text, datetime, name):
	post = {}
	post['style'] = style
	post['icon'] = icon
	post['text'] = text
	post['datetime'] = datetime
	post['name'] = name
	return post

def post_watson_response(response):
	global WATSON_STYLE, WATSON_IMAGE 
	now = datetime.datetime.now()
	post = create_post(WATSON_STYLE, WATSON_IMAGE, response, now.strftime('%Y-%m-%d %H:%M'), 'Watson')
	g('POSTS',[]).append(post)
	return post

def post_user_input(input):
	global PERSONA_STYLE, PERSONA_IMAGE, PERSONA_NAME
	now = datetime.datetime.now()
	post = create_post(PERSONA_STYLE, PERSONA_IMAGE, input, now.strftime('%Y-%m-%d %H:%M'), PERSONA_NAME)
	g('POSTS',[]).append(post)
	return post

def get_chat_response(dialog_response):
	global PRESENT_FORM
	chat_response = dialog_response
	if PRESENT_FORM in dialog_response:
		responses = dialog_response.split(PRESENT_FORM)
		chat_response = responses[0]
	return chat_response
	
# Form presentation funcs ------------------------
def get_form(dialog_response):
	global PRESENT_FORM
	form = ''
	if PRESENT_FORM in dialog_response:
		responses = dialog_response.split(PRESENT_FORM)
		form = responses[1]
	return form

def	set_selected_values(form, option_value):
	option = '<option value="' + option_value + '">' + option_value + '</option>'
	if option_value != None:
		if option_value != '':
			form = form.replace(option, '<option value="' + option_value + '" selected="selected">' + option_value + '</option>')
	return form

# Watson helper funcs ----------------------------
def format_conversation_response(message):
	dialog_response = 'The chat-bot is not currently available. Try again?'
	if 'output' in message:
		output = message['output']
		if 'text' in output:
			dialog_response = ''
			text = output['text']
			for dialog_response_line in text:
				if str(dialog_response_line) != '':
					if len(dialog_response) > 0:
						dialog_response = dialog_response + ' ' + dialog_response_line
					else:
						dialog_response = dialog_response_line
	return dialog_response

def format_question(question):
	message = {}
	message['input'] = json.loads('{"text": "' + question + '"}')
	last_message = json.loads(g('MESSAGE', '{}'))
	if 'context' in last_message:
		message['context'] = last_message['context']
	return message

def add_alchemy_analysis(transcript, request, parameters, parameter):
	response = BMIX_call_alchemy_api(request, parameters)
	if parameter in response:
		transcript[parameter] = response[parameter]
	return transcript

def add_tones(transcript, text):
	response = BMIX_analyze_tone(text)
	if 'sentences_tone' in response:
		transcript['sentences_tone'] = response['sentences_tone']
	if 'document_tone' in response:
		transcript['document_tone'] = response['document_tone']
	return transcript

# Session var set and get funcs ------------------
def s(key, value):
	session[key] = value
	return session[key]

def g(key, default_value):
	if not key in session.keys():
		session[key] = default_value
	return session[key]

# ------------------------------------------------
# FLASK ------------------------------------------
app = Flask(__name__)
register_application(app)

@app.route('/')
def Index():
	global CHAT_TEMPLATE, STT_USERNAME, STT_PASSWORD, TTS_USERNAME, TTS_PASSWORD
#	Initialize SST & TTS tokens
	stt_token = get_stt_token()
	tts_token = get_tts_token()
	s('STT_TOKEN', stt_token)
	s('TTS_TOKEN', tts_token)
#	Initialize chat
	s('POSTS',[])
	message = BMIX_get_conversation_message({})
	s('MESSAGE', json.dumps(message))
	response = format_conversation_response(message)
	post_watson_response(response)
	return render_template(CHAT_TEMPLATE, posts=g('POSTS',[]), form='', stt_token=stt_token, tts_token=tts_token)

@app.route('/', methods=['POST'])
def Index_Post():
	global CHAT_TEMPLATE, QUESTION_INPUT
	question = request.form[QUESTION_INPUT]
#	Display original question
	post_user_input(question)
#	Reset display
	application_response = ''
	form = ''
#	Orchestrate services
	if len(question) == 0:
		application_response = "C'mon, you have to say something!"
	else:
		message = format_question(question)
		message = BMIX_get_conversation_message(message)
		s('MESSAGE', json.dumps(message))
		dialog_response = format_conversation_response(message)
		application_response = get_application_response(get_chat_response(dialog_response), message)
		form = get_application_response(get_form(dialog_response), message)
#	Display application_response
	post_watson_response(application_response)
	return render_template(CHAT_TEMPLATE, posts=g('POSTS',[]), form=form, stt_token=g('STT_TOKEN', ''), tts_token=g('TTS_TOKEN', ''))
	
@app.route('/page', methods=['POST'])
def Page_Post():
	global CHAT_TEMPLATE, CURSOR_INPUT, SEARCH_TYPE_INPUT
	form = ''
	tips = ''
#	Set vars from hidden form fields
	action = request.form[CURSOR_INPUT]
	search_type = request.form[SEARCH_TYPE_INPUT]
	possible_actions = {'Accept': 0, 'Next': 1, 'Prev': -1, 'Explore': 0}
	shift = possible_actions[action]
	if shift != 0:
		application_response = get_search_response(search_type, shift)
	elif action == 'Accept':
		application_response = 'Thank you for helping to make Watson smarter! What else can I help you with?'
#	Display application_response
	post_watson_response(application_response)
	return render_template(CHAT_TEMPLATE, posts=g('POSTS',[]), form='', stt_token=g('STT_TOKEN', ''), tts_token=g('TTS_TOKEN', ''))

#@app.route('/service')
#def Service():
	#response_json = BMIX_get_first_dialog_response_json()
	#if response_json != None:
		#s('DIALOG_CLIENT_ID', response_json['client_id'])
		#s('DIALOG_CONVERSATION_ID', response_json['conversation_id'])
	#return json.dumps(response_json, sort_keys=True, indent=4, separators=(',', ': '))
	
#@app.route('/service', methods=['POST'])
#def Service_Post():
	#data = json.loads(request.data)
	#client_id = data['client_id']
	#conversation_id = data['conversation_id']
	#question = data['question']
#	Orchestrate
	#application_response = ''
	#if len(question) == 0:
		#application_response = "C'mon, you have to say something!"
	#else:
		#dialog_response = BMIX_get_next_dialog_response(g('DIALOG_CLIENT_ID', 0), g('DIALOG_CONVERSATION_ID', 0), question)
		#application_response = get_application_response(get_chat_response(dialog_response))
	#return (application_response)

@app.route('/analyze', methods=['POST'])
def Analyze_Post():
	http_response = 'You sent me...'
	data = json.loads(request.data)
	if 'conversation_transcript' in data:
		if 'transcript' in data['conversation_transcript']:
			parameters = {}
			parameters['text'] = data['conversation_transcript']['transcript'].encode('utf-8','ignore')
			parameters['extract'] = 'concepts,keywords,doc-emotion,entities,taxonomy,doc-sentiment'
			parameters['disambiguate'] = '1'
			parameters['sentiment'] = '1'
			data['conversation_transcript'] = add_alchemy_analysis(data['conversation_transcript'], '/text/TextGetRankedConcepts', parameters, 'concepts')
			data['conversation_transcript'] = add_alchemy_analysis(data['conversation_transcript'], '/text/TextGetRankedNamedEntities', parameters, 'entities')
			data['conversation_transcript'] = add_alchemy_analysis(data['conversation_transcript'], '/text/TextGetRankedKeywords', parameters, 'keywords')
			data['conversation_transcript'] = add_alchemy_analysis(data['conversation_transcript'], '/text/TextGetTextSentiment', parameters, 'docSentiment')
			data['conversation_transcript'] = add_tones(data['conversation_transcript'], parameters['text'])
	if 'speaker_transcripts' in data:
		i = 0
		for speaker_transcript in data['speaker_transcripts']:
			if 'transcript' in speaker_transcript:
				parameters = {}
				parameters['text'] = speaker_transcript['transcript'].encode('utf-8','ignore')
				parameters['extract'] = 'concepts,keywords,doc-emotion,entities,taxonomy,doc-sentiment'
				parameters['disambiguate'] = '1'
				parameters['sentiment'] = '1'
				data['speaker_transcripts'][i] = add_alchemy_analysis(speaker_transcript, '/text/TextGetRankedConcepts', parameters, 'concepts')
				data['speaker_transcripts'][i] = add_alchemy_analysis(speaker_transcript, '/text/TextGetRankedNamedEntities', parameters, 'entities')
				data['speaker_transcripts'][i] = add_alchemy_analysis(speaker_transcript, '/text/TextGetRankedKeywords', parameters, 'keywords')
				data['speaker_transcripts'][i] = add_alchemy_analysis(speaker_transcript, '/text/TextGetTextSentiment', parameters, 'docSentiment')
				data['speaker_transcripts'][i] = add_tones(speaker_transcript, parameters['text'])
				i += 1
	http_response = json.dumps(data)
	return (http_response)

port = os.getenv('PORT', '5000')
if __name__ == "__main__":
	app.wsgi_app = SessionMiddleware(app.wsgi_app, session_opts)
	app.session_interface = BeakerSessionInterface()
#	app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
	app.run(host='0.0.0.0', port=int(port))