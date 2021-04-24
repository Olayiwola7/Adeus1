#!/usr/bin/env python3

import argparse 
import os
import queue
import sounddevice as sd
import vosk
import sys
import json
import pyttsx3
import wordtodigits
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
import re
import wordtodigits
import simpleaudio as sa




df = pd.read_csv('Intents.csv', header = None, names = ['Examples', 'Intent'])
device = []
appliances= ['fridge', 'tv', 'television', 'a/c','air conditioner','pump','waterpump',
              'bulb','water pump','heater','microwave','cooker','kettle','electric kettle','light','speaker','refridgerator']
currencies = ['dollars', 'pounds', 'euros', 'naira', 'yuan']
time = []
quantity = []
currency = []

def speakword(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def get_intent(text):
  global device, quantity, currency
  quantity = []
  currency = []
  examples_list = df['Examples'].tolist()
  quantity = list (map(int, re.findall(r'\d+', text)))
  check = any(appliance in text.lower() for appliance in appliances)
  currency_check  = any(currency in text.lower() for currency in currencies)
  if currency_check:
    currency =list(set(currencies).intersection(set(text.split())))
  if not 'device' in text.lower():
    if check:
      device =list(set(appliances).intersection(set(text.split())))
      for d in device:
        text = text.replace(d, 'device')
  elif 'it' in text.lower():
    pass
  else:
    device = []
  text = [text]
  cv = CountVectorizer()
  vectors = cv.fit_transform(examples_list+text).toarray()
  vectors_list = [vec for vec in vectors]
  similarity_scores = cosine_similarity(vectors_list)[-1][:-1]
  #print(similarity_scores)
  #print(similarity_scores)
  i=np.argmax(similarity_scores)
  intent = df[df['Examples'] == examples_list[i]]['Intent'].values[0].strip()
  print(intent)
  return intent

def intent2action(intent):
  text = ''
  global device, quantity, currency
  if intent == 'Utilities_Device_status':
    if device:
      for d in device:
        status = 'on' #get status from db
        text += f'Your {d} status is {status}...'
    else:
      text += 'Which device do you want to know its status?'

  elif intent == 'Utilities_Device_Usage':
    if device:
      for d in device:
        usage = 5 # get usage from db
        text += f'Your {d} usage is {usage} kilowatts...'
    else:
      text += 'Which device do you want to know its usage?'

  elif intent == 'Turn_off_device':
    if device:
      for d in device:
        text += f'Switching off your {d}...'
    else:
      text += 'Which device do you want to switch off?'

  elif intent == 'Turn_on_device':
    if device:
      for d in device:
        text += f'Switching on your {d}...'
    else:
      text += 'Which device do you want to switch on?'

  elif intent == 'Utilities_Energy_Balance':  
      balance = '20'
      text += f'Your energy balance is {balance} kilowatts....'

  elif intent == 'Utilities_energy_price':
      price = 20 #getting price from db
      if quantity and currency:
        text+= f'You can get {quantity[0]/price} killowatts for {quantity[0]} {currency[0]}'
      elif quantity:
        price = price * quantity[0]
        text += f'The price of {quantity[0]} kilowatt per hour is {price}....'
      else:
        text += f'The price of one kilowatt per hour is {price}....'

  elif intent == 'Utilities_Recharge_Account':
    if quantity and currency:
      text += f'your account has just be recharged with energy worth {quantity[0]} {currency[0]}'
    elif quantity:
      text += f'Your account has just be credited with {quantity[0]} kilowatts'
    else:
      text += 'How many kilowatts do you want to buy?'

  elif intent == 'Age':
    text+= f'I cannot really tell because I am updated often. You can wish me a happy birthday whenever you want'

  elif intent == 'Ask_question':
    text+= f'Sure, how can I help you?'

  elif intent == 'Bored':
    text+= f'Here is a joke I know, what did mummy spider say to baby spider?...You spend too much time on the web!'

  elif intent == 'Love':
    text+= f"I'm happy being single. The upside is I can concentrate on saving the planet"

  elif intent == 'Compliment':
    text+= f"Oh, thank you. I'm blushing right now."
  
  elif intent == 'Hobby':
    text+= f"I love to help people manage their energy efficiently. I would also really love to win the global zero C O 2 challenge"

  elif intent == 'get_personal':
    text+= f"I'm your energy concierge, I help you manage your energy smartly. Together we can contribute to saving the planet"

  elif intent == 'Pissed':
    text+= f"Sorry!"

  elif intent == 'Language':
    text+= f"I can only speak in English right now. However, with a few tweaks, I can speak any language"

  elif intent == 'Boss':
    text+= f"I was made by A-DEUS to serve as a personal energy assistant for A-DEUS customers"

  elif intent == 'Retraining':
    text+= f"I'm already pretty smart plus I am learning so much from all our conversations"


  elif intent == 'Job':
    text+= f"I would be happy to help. We can always work together"

  elif intent == 'know_weather':
    text+= f"The weather today is..." #get from db

  elif intent == 'know_date':
    text+= f"The date today is..."   #get from system time

  elif intent == 'End_conversation':
    text+= f"I am happy I was able to help"
    
  elif intent == 'Ask_question':
    text+= f"Sure, how can I help" 
    
  elif intent == 'greeting':
      text+= f"Hey, I'm good, do you need help with anything"
      
  elif intent == 'Utilities_Report_Outage':
      text+= f"Our team will respond to your request as soon as possible"
      
  elif intent == 'Utilities_Start_Service':
      text+= f"Our team will respond to your request as soon as possible"
      
  elif intent == 'Utilities_Stop_Service':
      text+= f"Our team will respond to your request as soon as possible"
      
  else:
      text+= f"Can you reword your statement? I'm not understanding"
      
    
    

  return text

q = queue.Queue()

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    '-f', '--filename', type=str, metavar='FILENAME',
    help='audio file to store recording to')
parser.add_argument(
    '-m', '--model', type=str, metavar='MODEL_PATH',
    help='Path to the model')
parser.add_argument(
    '-d', '--device', type=int_or_str,
    help='input device (numeric ID or substring)')
parser.add_argument(
    '-r', '--samplerate', type=int, help='sampling rate')
args = parser.parse_args(remaining)

try:
    if args.model is None:
        args.model = "model"
    if not os.path.exists(args.model):
        print ("Please download a model for your language from https://alphacephei.com/vosk/models")
        print ("and unpack as 'model' in the current folder.")
        parser.exit(0)
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, 'input')
        # soundfile expects an int, sounddevice provides a float:
        args.samplerate = int(device_info['default_samplerate'])

    model = vosk.Model(args.model)

    if args.filename:
        dump_fn = open(args.filename, "wb")
    else:
        dump_fn = None

    with sd.RawInputStream(samplerate=args.samplerate, blocksize = 8000, device=args.device, dtype='int16',
                            channels=1, callback=callback):
            print('#' * 80)
            print('Press Ctrl+C to stop the recording')
            print('#' * 80)

            rec = vosk.KaldiRecognizer(model, args.samplerate)
            while True:
                
                data = q.get()
                if rec.AcceptWaveform(data):
                    #print(rec.Result())
                    jres = json.loads(rec.Result())
                    #finaltext = wordtodigits.convert(jres["text"])
                    #finaltalk= intent2action(get_intent(finaltext))
                    #speakword(finaltalk)
                    if jres["text"]== str("hello james"):
                        filename = 'bbm_tone.wav'
                        wave_obj = sa.WaveObject.from_wave_file(filename)
                        play_obj = wave_obj.play()
                        play_obj.wait_done()
                        
                        while True:
                            data = q.get()
                            rec.AcceptWaveform(data)
                            jres = json.loads(rec.Result())
                            finaltext = wordtodigits.convert(jres["text"])
                            finaltalk= intent2action(get_intent(finaltext))
                            speakword(finaltalk)
                        
                        
                        
                        
                else:
                    #print(rec.PartialResult())
                    jres = json.loads(rec.PartialResult())
                    if jres["partial"]== str("hello james"):
                       #engine = pyttsx3.init()
                       #engine.say("Welcome, I'm vivian, how can I help")
                       #engine.runAndWait()
                       print(jres)
                if dump_fn is not None:
                    dump_fn.write(data)

except KeyboardInterrupt:
    print('\nDone')
    parser.exit(0)
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))
