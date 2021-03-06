# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/core/actions/#custom-actions/

# from typing import Any, Text, Dict, List

import urllib.request, json
import operator
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction
from rasa_sdk.events import AllSlotsReset
from datetime import date

class ActionGetSideEffects(Action):
     def name(self):
         return "action_get_side_effects"

     def run(self, dispatcher, tracker, domain):
         
         side_effects = {}

         medicine = tracker.get_slot('medicine')
         if medicine == None:
             dispatcher.utter_message(text="No drug with the given name found. Please check if the spelling is right, or if there is an alternative name for the drug.")
             return [AllSlotsReset()]

         url = "https://api.fda.gov/drug/event.json?search=patient.drug.medicinalproduct:\"" + medicine.upper() + "\"&limit=10"
         print(url)
         with urllib.request.urlopen(url) as record:
             values = json.load(record)
             record.close()
         for each_res in values['results']:
             for reaction in each_res['patient']['reaction']:
                 se = reaction['reactionmeddrapt']
                 if se in side_effects:
                     side_effects[se] += 1
                 else:
                     side_effects[se] = 1
         
         
         sorted_effects = sorted(side_effects.items(), key = operator.itemgetter(1), reverse = True)
         say_effects = ""
         count = len(sorted_effects)
         l = 0
         for eff in sorted_effects:
             if eff[0] != "No adverse event":
                 say_effects += (eff[0] + ", ")
                 l += 1
             if l == 7:
                 break

         if l == 0:
             say_effects += "No side effects found. Please check if you gave the right spelling of the medicine."
         elif l == 1:
             say_effects += ("is the side effect caused due to" + medicine[0].upper() + medicine[1:].lower())
         else:
             say_effects += ("are the side effects caused due to " + medicine[0].upper() + medicine[1:].lower())

         print(say_effects)

         dispatcher.utter_message(text=say_effects)

         return [AllSlotsReset()]
     
class ActionHospitalSearch(Action):
     def name(self):
         return "action_get_hospital_search"

     def run(self, dispatcher, tracker, domain):
         
         hospital_search = []
         
         lat_long = {"hyderabad" : ("17.3850", "78.4867"), "bangalore" : ("12.9716", "77.5946"), "chennai" : ("13.0827", "80.2707"), "pune" : ("18.5204", "73.8567"), "delhi" : ("28.7041", "77.1025"), "kolkata" : ("22.5726", "88.3639"), "mumbai" : ("19.0760", "72.8777"), "jaipur" : ("26.9124", "75.7873"), "mysore" : ("12.2958", "76.6394"), "agra" : ("27.1767", "78.0081"), "vizag" : ("17.6868", "83.2185"), "goa" : ("15.2993", "74.1240"), "amritsar" : ("31.6340", "74.8723"), "kochi" : ("9.9312", "76.2673"), "ahmedabad" : ("23.0225", "72.5714"), "thiruvananthapuram" : ("8.5241", "76.9366"), "kolhapur" : ("16.7050", "74.2433"), "solapur" : ("17.6599", "75.9064"), "madurai" : ("9.9252", "78.1198"), "kanchipuram" : ("12.8185", "79.6947"), "lucknow" : ("26.8467", "80.9462")}

         location = (tracker.get_slot('location')).lower()
         if location not in lat_long:
             dispatcher.utter_message(text="Apologies :( The search for hospitals is currently unavailable in the given location.")
             return [AllSlotsReset()]
         url = "https://api.tomtom.com/search/2/categorySearch/hospital.json?limit=10&lat=" + lat_long[location][0] + "&lon=" + lat_long[location][1] + "&radius=10000&key=your_api_key"
         print(url)
         with urllib.request.urlopen(url) as record:
             res = json.load(record)
             record.close()
         
         say_hospitals = ""

         for idx, each in enumerate(res['results']):
             say_hospitals += str(idx+1) + ". "+ each['poi']['name'] + " - "
             say_hospitals += each['address']['freeformAddress'] + "\n"

         dispatcher.utter_message(text=say_hospitals)

         return [AllSlotsReset()]


class ActionGetDiagnosisAndSpecializations(Action):
     def name(self):
         return "action_get_diagnosis_and_specializations"

     def run(self, dispatcher, tracker, domain):
         auth_token = "your_api_key"

         with open('Symptoms_Sandbox.json') as f:
             data = json.load(f)
             f.close()
         symptoms_id_map = {}
         for each in data:
             symptoms_id_map[each['Name'].lower()] = each['ID']
         url = "https://sandbox-healthservice.priaid.ch/diagnosis?symptoms=["
         symptoms = tracker.get_slot('symptoms')
         gender = tracker.get_slot('gender')
         yob = tracker.get_slot('year_of_birth')

         symptoms_ids = []
         check= set([])
         for each in symptoms:
             each = each.lower()
             if each in symptoms_id_map:
                 if symptoms_id_map[each] not in check:
                    symptoms_ids.append(symptoms_id_map[each])
                    check.add(symptoms_id_map[each])
         print(symptoms_ids, gender, yob)
         for idx, sid in enumerate(symptoms_ids):
             url += str(sid)
             if idx != len(symptoms_ids)-1:
                 url += ","
         url += "]&gender="
         if type(gender) == list:
            url += gender[0]
         else:
             url += gender
         url += "&year_of_birth="
         url += yob[0]
         url += "&token="
         url += auth_token
         url += "&format=json&language=en-gb"

         print(url)
         with urllib.request.urlopen(url) as record:
             results = json.load(record)
             record.close()

         say_diseases = ""
         for each in results:
             say_diseases += "You may have " + each['Issue']['Name'] + " with a predicted accuracy of " + str(each['Issue']['Accuracy']) + ". "
             if len(each['Specialisation']) != 0:
                 say_diseases += "You may have to visit "
                 for idx, specialist in enumerate(each['Specialisation']):
                     say_diseases += specialist['Name']
                     if idx != len(each['Specialisation']) - 1:
                         say_diseases += ", "
                 
                 if len(each['Specialisation']) == 1:
                     say_diseases += " department. \n"
                 else:
                     say_diseases += " departments. \n"

         if say_diseases == "":
             say_diseases += "No possible diseases found!"
         else:
             say_diseases += "Take care..."

         dispatcher.utter_message(text=say_diseases)

         return [AllSlotsReset()]
         #return [SlotSet("symptoms", None), SlotSet("gender", None), SlotSet("year_of_birth", None)]


class SymptomsForm(FormAction):

    def name(self):
        return "symptoms_analysis_form"

    @staticmethod
    def required_slots(tracker):
        return ["symptoms", "gender", "year_of_birth"]

    def validate_year_of_birth(self, value, dispatcher, tracker, domain):
        curr_year = int(str(date.today())[:4])
        if int(value[0]) < 1800 or int(value[0]) > curr_year:
            dispatcher.utter_message(text="Please enter a valid year of birth. The acceptable range is from 1800 to " + str(curr_year))
            return {"year_of_birth":None}
        return {"year_of_birth":value}

    def validate_gender(self, value, dispatcher, tracker, domain):
        if type(value) == list:
            if value[0] == "male" or value[0] == "female":
                return {"gender":value}
            else:
                dispatcher.utter_message(text="Please input male/female")
                return {"gender":None}
        if value == "male" or value == "female":
            return {"gender":value}
        dispatcher.utter_message(text="Please input male/female")
        return {"gender":None}

    def submit(self, dispatcher, tracker, domain):
        dispatcher.utter_message(template="utter_submit")
        return []
