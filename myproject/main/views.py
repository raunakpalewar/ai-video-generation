import speech_recognition as sr
import openai
import dotenv
import os
from gtts import gTTS
from django.http import FileResponse
import io
import requests
from html2image import Html2Image
import numpy as np
from rest_framework.response import Response
from rest_framework.views import APIView
from django.templatetags.static import static
import urllib.request as ur
from moviepy.editor import ImageSequenceClip,concatenate_videoclips,ImageClip,AudioFileClip,concatenate_audioclips,VideoFileClip,VideoClip,concatenate,CompositeVideoClip
from PIL import Image
import cv2
from django.utils import timezone
from django.conf import settings
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.exceptions import ObjectDoesNotExist
import shutil
import hashlib
from io import BytesIO
import cloudinary
from concurrent.futures import ThreadPoolExecutor
import random
import timeit
from .script_csv import *
from .script_json import *
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures
# import pyttsx3
import json
import mysql.connector as con
from mysql.connector import Error
import re


dotenv.load_dotenv()    

openai.api_key = os.environ.get("SECRET_KEY")

# base_url = 'https://pyaivideo-generator.mobiloitte.io/' 
# base_url='https://pytest-aivideo.mobiloitte.io/'
base_url = 'http://127.0.0.1:8001/'
def RandomNumber():
    return random.randint(000000000,999999999)  


def speech_to_text(audiopath):
    sound = audiopath
    r = sr.Recognizer()
    with sr.AudioFile(sound) as source:
        r.adjust_for_ambient_noise(source, duration=0.00001)
        audio = r.listen(source)
        try:
            return r.recognize_google(audio)
        except Exception as e:
            return str(e)


def intro_modification(text):
    prompt=f"""
   convert the provided text into high value text for generation of a voice script for speech in 2-3 lines
   text: {text}
    """ 
    response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
                    )
    document = response.choices[0].message.content.strip()
    return document



def script_modification(text,companyName,organizationName,prospectName):
    prompt=f"""
     text: {text}
   plase modify the above text and convert into high value text
   and change some words if available in text with the below mention word
    text to be changed if available in above text:
     companyName:{companyName}
     organizationname:{organizationName}
     prospectName:{prospectName}
    """ 
    response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
                    )
    document = response.choices[0].message.content.strip()
    print('SCRIPT',document)
    return document


def text_convertion(text):
   
    prompt = f'''
    please convert the provided description into the high text/script
    make sure the response is meaningful and all the points in description provided is included.
    Description {text}
    '''
    response = openai.Completion.create(
        engine='text-davinci-003',
        temperature=0.5,           
        prompt=prompt,             
        n=1,                       
        stop=None,   
    )
    return response.choices[0].text


def sample_text_convertion(text):
    prompt = f"""
    Please understand the description given as the input and create a script for presentation of the description provided
      {text}
    """ 
    response = openai.Completion.create(
        engine='text-davinci-003',
        temperature=0.5,           
        prompt=prompt,             
        n=1,                       
        stop=None,   
    )
    return response.choices[0].text


def text_to_speech(text, filename, request):
    print(text, "hereeeeee")
    speech = gTTS(text=text, lang='en', slow=False, tld='co.in')
    
    # Create the "audio" folder if it doesn't exist
    audio_folder = os.path.join(os.getcwd(), 'static/audio')
    os.makedirs(audio_folder, exist_ok=True)
    current_datetime = RandomNumber()
    file_path = os.path.join(audio_folder, f'{filename}_{current_datetime}.wav')
    speech.save(file_path)

   
    audio_url = base_url + 'static/audio/' + f'{filename}_{current_datetime}.wav'
    return audio_url






class FetchScreenShot(APIView):
    @swagger_auto_schema(
        operation_summary="The 'url' to Image creation API",
        operation_description="",
        manual_parameters=[
            openapi.Parameter('webUrl', openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Web URL", default="https://www.salesmeetings.ai/"),
        ]
    )
    def get(self, request):
        webUrl = request.query_params.get('webUrl')
        hti = Html2Image()
        output_folder = os.path.join(os.getcwd())
        os.makedirs(output_folder, exist_ok=True)
        
        hti.output_path = output_folder
        screenshot_file_name = f"{hashlib.md5(webUrl.encode()).hexdigest()}_{timezone.now().strftime('%Y%m%d%H%M')}.jpg"
        hti.screenshot(url=webUrl, save_as=screenshot_file_name)
        # screenshot_file_path = os.path.join(output_folder, screenshot_file_name)
        cloudinary_response = cloudinary.uploader.upload(
        os.path.join(output_folder, screenshot_file_name),
        folder='screenshots',  
        overwrite=True)
        cloudinary_url = cloudinary_response.get('secure_url', '')
        
        screenshot_url = base_url + 'static/image/' + screenshot_file_name
        os.remove(screenshot_file_name)
        
        return Response({'status': status.HTTP_200_OK, 'Image': screenshot_url,'cloudinary_url':cloudinary_url})


# final api for video creation

class AIVideoCreation(APIView):
    @swagger_auto_schema(operation_summary="The Image to video creation API",
                         operation_description="This api required a  userid, target organization organizationID,and templateId of template",
                         manual_parameters=[
                             openapi.Parameter('userId',openapi.IN_QUERY,type=openapi.TYPE_STRING,description="user id ",default=""),
                             openapi.Parameter('organizationId',openapi.IN_QUERY,type=openapi.TYPE_STRING,default=""),
                             openapi.Parameter('templateId',openapi.IN_QUERY,type=openapi.TYPE_STRING,default="")
                         ]
                         )
    def post(self,request):
        try:   
            userId=request.query_params.get('userId')
            organizationId=request.query_params.get('organizationId')
            templateId=request.query_params.get('templateId')

            url=f"https://nodepune-aivideogenerator.mobiloitte.io/api/v1/user/getDataDetailsApi?userId={userId}&organizationId={organizationId}&templateId={templateId}"

            res = requests.get(url=url)
            print("this is another work")
            res = res.json()
            user_email = res['result']['user']['email']
            organization_name = res['result']['organization'][0]['organizationName']

 
            print(base_url)
            img_list = []
            audio_text_list = []
            audio_clips = []
            audio_durations = []
            audio_file_name = []

            for template in res['result']['template']['template']:
                audio_text=''
                if template['type'] == 'URL':
                    print('we are in url now')

                    hti = Html2Image()
                    output_folder =  os.path.join(os.getcwd())
                    # output_folder='/home/python/pipelines/python-pipelines/workspace/ai-video-generator-scott-harris-23054103-python-pune/media/image'
                    os.makedirs(output_folder, exist_ok=True)
                    print("output_folder ==>",output_folder)
                    hti.output_path = output_folder
                    screenshot_file_name = f"{user_email}_{timezone.now().strftime('%Y%m%d%H%M')}.jpg"
                    hti.screenshot(url=template['media'], save_as=screenshot_file_name)
                    print("screenshot" ,template['media'])
                    screenshot = base_url + 'media/audio/' + screenshot_file_name
                    cloudinary_response = cloudinary.uploader.upload(
                    os.path.join(output_folder, screenshot_file_name),
                    folder='screenshots',  
                    overwrite=True)
                    os.remove(screenshot_file_name)
                    cloudinary_url = cloudinary_response.get('secure_url', '')
                    print("cloudinary_url",cloudinary_url)
                    img_list.append(cloudinary_url)
                elif template['type'] == 'IMAGE':
                    img_list.append(template['media'])
                else:
                    img_list.append(template['media'])
                
                print(template['audioUrl'])
                if template['audioUrl'] != '':
                    print("url")
                    # audio = ur.urlopen(template['audioUrl'])
                    response = requests.get(template['audioUrl'])
                    audio_file = response.content
                    bytecontent=BytesIO(audio_file)

                    recognizer = sr.Recognizer()

                    with sr.AudioFile(bytecontent) as source:
                        recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                        audio = recognizer.listen(source)

                        audio_text = recognizer.recognize_google(audio)

                    audio = text_to_speech(text_convertion(audio_text), user_email, request)
                    audio = ur.urlopen(audio)
                    file = f"{user_email}_{timezone.now().strftime('%Y%m%d%H%M')}.wav"
                    
                    with open(file, 'wb') as f:
                        audio_file_name.append(file)
                        f.write(audio.read())
                    

                    audio_clip = AudioFileClip(file)
                    audio_clips.append(audio_clip)
                    audio_duration = audio_clip.duration
                    audio_duration_seconds = int(audio_duration)
                    audio_durations.append(audio_duration_seconds)
                    os.remove(file)
                
                elif template["audioDescription"] != '':
                    print("audioDiscription")
                    audio = text_to_speech(text_convertion(template["audioDescription"]), user_email, request)
                    audio = ur.urlopen(audio)
                    file = f"{user_email}_{timezone.now().strftime('%Y%m%d%H%M')}.wav"
                    with open(file, 'wb') as f:
                        audio_file_name.append(file)
                        f.write(audio.read())

                    audio_clip = AudioFileClip(file)
                    audio_clips.append(audio_clip)
                    audio_duration = audio_clip.duration
                    audio_duration_seconds = int(audio_duration)
                    audio_durations.append(audio_duration_seconds)
                    os.remove(file)

                else:
                    title = template['title']
                    description = template['description']
                    footer = template['footer']
                    audio_text = f'title is {title}, description is {description} and footer is {footer}'
                    
                    audio = text_to_speech(text_convertion(audio_text), user_email, request)
                    audio = ur.urlopen(audio)
                    file = f"{user_email}_{timezone.now().strftime('%Y%m%d%H%M')}.wav"
                    with open(file, 'wb') as f:
                        audio_file_name.append(file)
                        f.write(audio.read())

                    audio_clip = AudioFileClip(file)
                    os.remove(file)
                    audio_clips.append(audio_clip)
                    audio_duration = audio_clip.duration
                    audio_duration_seconds = int(audio_duration)
                    audio_durations.append(audio_duration_seconds)

            intro_text=f"hi {res['result']['organization'][0]['prospectName']}, i am  {res['result']['user']['firstName']} we are reaching out to you from mobiloitte technologies for collaboration with {res['result']['organization'][0]['organizationName']}"
            intro_audio=text_to_speech(intro_text,user_email,request)
            audio=ur.urlopen(intro_audio)
            print("intro_audio",intro_audio)
            file = f"{user_email}_{timezone.now().strftime('%Y%m%d%H%M')}.wav"
            with open(file, 'wb') as f:
                f.write(audio.read())
                audio_clip = AudioFileClip(file)
            concat_audio=concatenate_audioclips([audio_clip,audio_clips[0]])
            audio_folder = os.path.join(os.getcwd(), 'static/audio')
            os.makedirs(audio_folder, exist_ok=True)
            current_datetime = timezone.now().strftime('%Y%m%d%H%M%S')
            
            file_path = os.path.join(audio_folder, f'comined_audio_{current_datetime}.wav')
            concat_audio.write_audiofile(file_path)
            os.remove(file)


            print("this is done here ")
            print("old audio clips ", audio_clips)
            audio=base_url+'static/audio/'+ f'comined_audio_{current_datetime}.wav'
            audio=ur.urlopen(audio)
            file = f"{user_email}_{timezone.now().strftime('%Y%m%d%H%M')}.wav"
            with open(file, 'wb') as f:
                f.write(audio.read())

            print('old audio duration' , audio_durations)
            intro_audio_clip = AudioFileClip(file)
            audio_duration=intro_audio_clip.duration
            audio_duration_seconds = int(audio_duration)
            audio_durations[0]=audio_duration_seconds
            audio_clips[0]=intro_audio_clip
            os.remove(file)

            print('old audio duration' , audio_durations)
        

            print("new audio clips ",audio_clips)

            duration = iter(audio_durations)
            print(duration)
            clips = []
            images = []
        
            for image in img_list:
                split_image = image.split('.')
                print(split_image, "")
                if split_image[-1] != 'mp4':
                    image = ur.urlopen(image)
                    print("image=", image)
                    img_arr = np.array(bytearray(image.read()), dtype=np.uint8)
                    img = cv2.imdecode(img_arr, cv2.IMREAD_UNCHANGED)
                    img = cv2.resize(img, (720, 480))
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        
                    clip = ImageClip(img_rgb).set_duration(next(duration))
                    clips.append(clip)
                
                else:
                    video_file = f"{user_email}_{timezone.now().strftime('%Y%m%d%H%M')}.mp4"
                    decode_image = ur.urlopen(image).read()
                    print("this is video ")

                    with open(video_file, 'wb') as f1:
                        f1.write(decode_image)
                    video_file_path=VideoFileClip(video_file)
                    clips.append(video_file_path.without_audio())
                    os.remove(video_file)
            
            # concat the converted clips into a video and add audio to the
            print("the video concat is start ")
            final_clip = concatenate_videoclips(clips, method='compose')
            final_audio_clips=concatenate_audioclips(audio_clips)
            final_clip = final_clip.set_audio(final_audio_clips)

            video_folder = os.path.join(os.getcwd(), 'static/videos')
            os.makedirs(video_folder, exist_ok=True)
            current_datetime = timezone.now().strftime('%Y%m%d%H%M')
            video_path = os.path.join(video_folder, f'{user_email}_{current_datetime}.mp4')
            print("the video creation is start ")
            final_clip.write_videofile(video_path, fps=24)
            static_video_url =base_url + static(os.path.join('videos', f'{user_email}_{current_datetime}.mp4'))
            
            # shutil.rmtree('static/image')
            shutil.rmtree('static/audio')
            static_video_url=static_video_url.replace('//static','/static')

            node_video_url = 'https://nodepune-aivideogenerator.mobiloitte.io/api/v1/user/updateVideoUrl'

            headers = {
                'accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            data = {
                'organizationId': organizationId,
                'videoUrl': static_video_url
            }

            response = requests.put(node_video_url, headers=headers, data=data)
            print(response)
            return Response({'status':status.HTTP_200_OK,"videoLink":static_video_url,"responseMessage":"video is successfully created"},status=status.HTTP_200_OK)
                        
        except ObjectDoesNotExist:
            return Response({'status':status.HTTP_400_BAD_REQUEST,'responseMessage':'all input are requried '})
        except Exception as e:
            print(str(e))
            return Response({'status':status.HTTP_500_INTERNAL_SERVER_ERROR,"responseMessage":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)   
        



class SpeechToText(APIView):
    @swagger_auto_schema(operation_summary="The Image to video creation API",
                         operation_description="This api required a  userid, target organization organizationID,and templateId of template",
                         manual_parameters=[
                             openapi.Parameter('audio_url',openapi.IN_QUERY,type=openapi.TYPE_STRING,description="Audio URl",default=""),
                             
                         ]
                         )
    def post(self, request):

        audio_url = request.query_params.get('audio_url')

        # Fetch the audio file from the URL
        response = requests.get(audio_url)
        audio_file = response.content
        bytecontent=BytesIO(audio_file)
        # Initialize the speech recognition object
        recognizer = sr.Recognizer()

        # Convert audio to text
        try:
            with sr.AudioFile(bytecontent) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                audio = recognizer.listen(source)

                audio_text = recognizer.recognize_google(audio)
            return Response({'text': audio_text})
        except sr.UnknownValueError:
            return Response({'error': 'Speech Recognition could not understand the audio'})
        except sr.RequestError as e:
            return Response({'error': f'Could not request results from Google Speech Recognition service: {e}'})

# https://www2.cs.uic.edu/~i101/SoundFiles/gettysburg.wav













#The Multiple Video creation API



class MultipleAIVideoCreation(APIView):
    @swagger_auto_schema(
        operation_summary="Mutltiple Video Creation API ",
        operation_description="This API requires a userid, target organization organizationID, and templateId of the template",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[""],
            properties={
                'array': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'company_name': openapi.Schema(type=openapi.TYPE_STRING, default='mobiloitte technologies'),
                            'templateID': openapi.Schema(type=openapi.TYPE_STRING, default='64d728434756d168cb0a3e71'),
                            'organization': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'organizationId':openapi.Schema(type=openapi.TYPE_STRING,default='64d1da847ef1df3bb6dd6700'),
                                    'organizationName': openapi.Schema(type=openapi.TYPE_STRING,default='experinace io'),
                                    'prospectName': openapi.Schema(type=openapi.TYPE_STRING,default='scott'),
                                }
                            ),
                            'template': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'media': openapi.Schema(type=openapi.TYPE_STRING,default='https://res.cloudinary.com/mobiloitte-technology-pvt-ltd/image/upload/v1691475963/xaeqiiyohsytl7py8bgz.jpg'),
                                        'type': openapi.Schema(type=openapi.TYPE_STRING,enum=['IMAGE','VIDEO','URL'],default='IMAGE'),
                                        'title': openapi.Schema(type=openapi.TYPE_STRING,default='title'),
                                        'description': openapi.Schema(type=openapi.TYPE_STRING,default='description'),
                                        'footer': openapi.Schema(type=openapi.TYPE_STRING,default=''),
                                        'audioDescription': openapi.Schema(type=openapi.TYPE_STRING,default='This is the first screen '),
                                        'audioUrl': openapi.Schema(type=openapi.TYPE_STRING,default=''),
                                        'audioScript':openapi.Schema(type=openapi.TYPE_STRING,default=''),
                                    }
                                ),
                            ),
                        },
                    ),
                ),
            },
        ),
    )
                        
    def post(self,request):
        try:   
            video_links={}
            array=request.data['array']
            for data in array:
                tempate_id_url = f"https://nodepune-aivideogenerator.mobiloitte.io/api/v1/template/getTemplateByTemplateId?templateId={data['templateID']}"
                headers = {'accept': 'application/json'}

                response_data = requests.get(tempate_id_url, headers=headers)
                response_data=response_data.json()
                try:
                    if 'coatName' not in response_data['result']:
                        return Response({'status':status.HTTP_404_NOT_FOUND,'responseMessage':'Please check the coat name'},status=status.HTTP_404_NOT_FOUND)
                    else:
                        if response_data['result']['coatName'] == "":
                            return Response({'status':status.HTTP_404_NOT_FOUND,'responseMessage':'Please check the coat name'},status=status.HTTP_404_NOT_FOUND)
                except:
                    pass






                user_email=data['organization']['organizationId']

                print(base_url)
                img_list = []
                audio_text_list = []
                audio_clips = []
                audio_durations = []
                audio_file_name = []

                for template in data['template']:
                    audio_text=''
                    if template['type'] == 'URL':
                        print('we are in url now')

                        hti = Html2Image()
                        output_folder =  os.path.join(os.getcwd())
                        # output_folder='/home/python/pipelines/python-pipelines/workspace/ai-video-generator-scott-harris-23054103-python-pune/media/image'
                        os.makedirs(output_folder, exist_ok=True)
                        print("output_folder ==>",output_folder)
                        hti.output_path = output_folder
                        screenshot_file_name = f"{user_email}_{RandomNumber()}.jpg"
                        hti.screenshot(url=template['media'], save_as=screenshot_file_name)
                        print("screenshot" ,template['media'])
                        # screenshot = base_url + 'media/audio/' + screenshot_file_name
                        cloudinary_response = cloudinary.uploader.upload(
                        os.path.join(output_folder, screenshot_file_name),
                        folder='screenshots',  
                        overwrite=True)
                        os.remove(screenshot_file_name)
                        cloudinary_url = cloudinary_response.get('secure_url', '')
                        print("cloudinary_url",cloudinary_url)
                        img_list.append(cloudinary_url)
                    elif template['type'] == 'IMAGE':
                        img_list.append(template['media'])
                    else:
                        img_list.append(template['media'])
                    

                    if 'mp4' in template['media']:
                        if template['audioUrl'] == '' and template['audioDescription'] == '':
                            video_file = f"{user_email}_{RandomNumber()}.mp4"
                            decode_image = ur.urlopen(template['media']).read()
                            print("this is video ")

                            with open(video_file, 'wb') as f1:
                                f1.write(decode_image)
                            video_file_path=VideoFileClip(video_file)
                            audio_clip = video_file_path.audio
                            audio_clips.append(audio_clip)
                            audio_duration = audio_clip.duration
                            audio_duration_seconds = int(audio_duration)
                            audio_durations.append(audio_duration_seconds)
    
                            os.remove(video_file)


                        elif template['audioScript'] != '':
                            print('Script url',template['audioScript'])
                            audio=text_to_speech(script_modification(template['audioScript'],data['company_name'],data['organization']['organizationName'],data['organization']['prospectName']),user_email,request)
                            audio = ur.urlopen(audio)
                            file = f"{user_email}_{RandomNumber()}.wav"
                            with open(file, 'wb') as f:
                                audio_file_name.append(file)
                                f.write(audio.read())

                            audio_clip = AudioFileClip(file)
                            audio_clips.append(audio_clip)
                            audio_duration = audio_clip.duration
                            audio_duration_seconds = int(audio_duration)
                            audio_durations.append(audio_duration_seconds)
                            os.remove(file)


                        elif template['audioUrl'] != '':
                            print("url")
                            # audio = ur.urlopen(template['audioUrl'])
                            response = requests.get(template['audioUrl'])
                            audio_file = response.content
                            bytecontent=BytesIO(audio_file)

                            recognizer = sr.Recognizer()

                            with sr.AudioFile(bytecontent) as source:
                                recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                                audio = recognizer.listen(source)

                                audio_text = recognizer.recognize_google(audio)

                            audio = text_to_speech(text_convertion(audio_text), user_email, request)
                            audio = ur.urlopen(audio)
                            file = f"{user_email}_{RandomNumber()}.wav"
                            
                            with open(file, 'wb') as f:
                                audio_file_name.append(file)
                                f.write(audio.read())
                            

                            audio_clip = AudioFileClip(file)
                            audio_clips.append(audio_clip)
                            audio_duration = audio_clip.duration
                            audio_duration_seconds = int(audio_duration)
                            audio_durations.append(audio_duration_seconds)
                            os.remove(file)
                        else:
                            audio = text_to_speech(text_convertion(template["audioDescription"]), user_email, request)
                            audio = ur.urlopen(audio)
                            file = f"{user_email}_{RandomNumber()}.wav"
                            with open(file, 'wb') as f:
                                audio_file_name.append(file)
                                f.write(audio.read())

                            audio_clip = AudioFileClip(file)
                            audio_clips.append(audio_clip)
                            audio_duration = audio_clip.duration
                            audio_duration_seconds = int(audio_duration)
                            audio_durations.append(audio_duration_seconds)
                            os.remove(file)


                    elif template['audioUrl'] != '':
                        print("url")
                        # audio = ur.urlopen(template['audioUrl'])
                        response = requests.get(template['audioUrl'])
                        audio_file = response.content
                        bytecontent=BytesIO(audio_file)

                        recognizer = sr.Recognizer()

                        with sr.AudioFile(bytecontent) as source:
                            recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                            audio = recognizer.listen(source)

                            audio_text = recognizer.recognize_google(audio)

                        audio = text_to_speech(text_convertion(audio_text), user_email, request)
                        audio = ur.urlopen(audio)
                        file = f"{user_email}_{RandomNumber()}.wav"
                        
                        with open(file, 'wb') as f:
                            audio_file_name.append(file)
                            f.write(audio.read())
                        

                        audio_clip = AudioFileClip(file)
                        audio_clips.append(audio_clip)
                        audio_duration = audio_clip.duration
                        audio_duration_seconds = int(audio_duration)
                        audio_durations.append(audio_duration_seconds)
                        os.remove(file)
                    
                    elif template["audioDescription"] != '':
                        print("audioDiscription")
                        audio = text_to_speech(text_convertion(template["audioDescription"]), user_email, request)
                        audio = ur.urlopen(audio)
                        file = f"{user_email}_{RandomNumber()}.wav"
                        with open(file, 'wb') as f:
                            audio_file_name.append(file)
                            f.write(audio.read())

                        audio_clip = AudioFileClip(file)
                        audio_clips.append(audio_clip)
                        audio_duration = audio_clip.duration
                        audio_duration_seconds = int(audio_duration)
                        audio_durations.append(audio_duration_seconds)
                        os.remove(file)
                    
                    elif template['audioScript'] != '':
                        print('Script url',template['audioScript'])
                        audio=text_to_speech(script_modification(template['audioScript'],data['company_name'],data['organization']['organizationName'],data['organization']['prospectName']),user_email,request)
                        audio = ur.urlopen(audio)
                        file = f"{user_email}_{RandomNumber()}.wav"
                        with open(file, 'wb') as f:
                            audio_file_name.append(file)
                            f.write(audio.read())

                        audio_clip = AudioFileClip(file)
                        audio_clips.append(audio_clip)
                        audio_duration = audio_clip.duration
                        audio_duration_seconds = int(audio_duration)
                        audio_durations.append(audio_duration_seconds)
                        os.remove(file)

                    else:
                        title = template['title']
                        description = template['description']
                        footer = template['footer']
                        audio_text = f'title is {title}, description is {description} and footer is {footer}'
                        
                        audio = text_to_speech(text_convertion(audio_text), user_email, request)
                        audio = ur.urlopen(audio)
                        file = f"{user_email}_{RandomNumber()}.wav"
                        with open(file, 'wb') as f:
                            audio_file_name.append(file)
                            f.write(audio.read())

                        audio_clip = AudioFileClip(file)
                        os.remove(file)
                        audio_clips.append(audio_clip)
                        audio_duration = audio_clip.duration
                        audio_duration_seconds = int(audio_duration+1)
                        audio_durations.append(audio_duration_seconds)


                # text=f"hi {data['organization']['prospectName']},we represent {data['company_name']} and we are reaching out for collaboration with your company {data['organization']['organizationName']}"
                # intro_text=intro_modification(text)
                # print("intro_text",intro_text)
                # intro_audio=text_to_speech(intro_text,user_email,request)
                # audio=ur.urlopen(intro_audio)
                # print("intro_audio",intro_audio)
                # file = f"{user_email}_{RandomNumber()}.wav"
                # with open(file, 'wb') as f:
                #     f.write(audio.read())
                #     audio_clip = AudioFileClip(file)
                # concat_audio=concatenate_audioclips([audio_clip,audio_clips[0]])
                # audio_folder = os.path.join(os.getcwd(), 'static/audio')
                # os.makedirs(audio_folder, exist_ok=True)
                # current_datetime = RandomNumber()
                
                # file_path = os.path.join(audio_folder, f'comined_audio_{current_datetime}.wav')
                # concat_audio.write_audiofile(file_path)
                # os.remove(file)


                # print("this is done here ")
                # print("old audio clips ", audio_clips)
                # audio=base_url+'static/audio/'+ f'comined_audio_{current_datetime}.wav'
                # audio=ur.urlopen(audio)
                # file = f"{user_email}_{RandomNumber()}.wav"
                # with open(file, 'wb') as f:
                #     f.write(audio.read())

                # print('old audio duration' , audio_durations)
                # intro_audio_clip = AudioFileClip(file)
                # audio_duration=intro_audio_clip.duration
                # audio_duration_seconds = int(audio_duration+1)
                # audio_durations[0]=audio_duration_seconds
                # audio_clips[0]=intro_audio_clip
                # os.remove(file)

                # print('old audio duration' , audio_durations)
            

                # print("new audio clips ",audio_clips)

                duration = iter(audio_durations)
                print(duration)
                clips = []
                images = []
            
                for image in img_list:
                    split_image = image.split('.')
                    print(split_image, "")
                    if split_image[-1] != 'mp4':
                        image = ur.urlopen(image)
                        print("image=", image)
                        img_arr = np.array(bytearray(image.read()), dtype=np.uint8)
                        img = cv2.imdecode(img_arr, cv2.IMREAD_UNCHANGED)
                        img = cv2.resize(img, (720, 480))
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                            
                        clip = ImageClip(img_rgb).set_duration(next(duration))
                        clips.append(clip)
                    
                    else:
                        print(audio_durations)
                        video_file = f"{user_email}_{timezone.now().strftime('%Y%m%d%H%M')}.mp4"
                        decode_image = ur.urlopen(image).read()
                        print("this is video ")

                        with open(video_file, 'wb') as f1:
                            f1.write(decode_image)
                        video_file_path=VideoFileClip(video_file).set_duration(next(duration))
                        clips.append(video_file_path)
                        os.remove(video_file)
                        
                        print(audio_clips)
                # concat the converted clips into a video and add audio to the
                print("the video concat is start ")
                final_clip = concatenate_videoclips(clips, method='compose')
                final_audio_clips=concatenate_audioclips(audio_clips)
                final_clip = final_clip.set_audio(final_audio_clips)

                video_folder = os.path.join(os.getcwd(), 'static/videos')
                os.makedirs(video_folder, exist_ok=True)
                current_datetime = RandomNumber()
                video_path = os.path.join(video_folder, f'{user_email}{current_datetime}.mp4')
                final_clip.write_videofile(video_path, fps=24)
                static_video_url =base_url + static(os.path.join('videos', f'{user_email}{current_datetime}.mp4'))
                
                # shutil.rmtree('static/image')
                
                static_video_url=static_video_url.replace('//static','/static')

                url = 'https://nodepune-aivideogenerator.mobiloitte.io/api/v1/user/updateVideoUrl'
                headers = {
                    'accept': 'application/json',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                pass_data = {
                    'organizationId':data['organization']['organizationId'],
                    'videoUrl': static_video_url
                }

                response = requests.put(url, headers=headers, data=pass_data)

                print(response_data)
                video_links['VideoLink']={
                    'coatname':response_data['result']['coatName'],
                    'organizationId': data['organization']['organizationId'],
                    'videoUrl': static_video_url
                }
                
            return Response({'status':status.HTTP_200_OK,"videoLinks":video_links,"responseMessage":"Video created Successfully"},status=status.HTTP_200_OK)
                            
        except ObjectDoesNotExist:
            return Response({'status':status.HTTP_400_BAD_REQUEST,'responseMessage':'Invalid input!,please check'},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(str(e))
            return Response({'status':status.HTTP_500_INTERNAL_SERVER_ERROR,"responseMessage":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)   
        




class AIvideoCreationWithMultiTreading(APIView):
    def VideoCreation(self,data,request):
        try:   
                tempate_id_url = f"https://nodepune-aivideogenerator.mobiloitte.io/api/v1/template/getTemplateByTemplateId?templateId={data['templateID']}"
                headers = {'accept': 'application/json'}

                response_data = requests.get(tempate_id_url, headers=headers)
                response_data=response_data.json()
                try:
                    if 'coatName' not in response_data['result']:
                        return Response({'status':status.HTTP_404_NOT_FOUND,'responseMessage':'Please check the coat name'},status=status.HTTP_404_NOT_FOUND)
                    else:
                        if response_data['result']['coatName'] == "":
                            return Response({'status':status.HTTP_404_NOT_FOUND,'responseMessage':'Please check the coat name'},status=status.HTTP_404_NOT_FOUND)
                except:
                    pass






                user_email=data['organization']['organizationId']
                
                print(base_url)
                img_list = []
                audio_text_list = []
                audio_clips = []
                audio_durations = []
                audio_file_name = []

                for template in data['template']:
                    audio_text=''
                    if template['type'] == 'URL':
                        print('we are in url now')

                        hti = Html2Image()
                        output_folder =  os.path.join(os.getcwd())
                        # output_folder='/home/python/pipelines/python-pipelines/workspace/ai-video-generator-scott-harris-23054103-python-pune/media/image'
                        os.makedirs(output_folder, exist_ok=True)
                        print("output_folder ==>",output_folder)
                        hti.output_path = output_folder
                        screenshot_file_name = f"{user_email}_{RandomNumber()}.jpg"
                        hti.screenshot(url=template['media'], save_as=screenshot_file_name)
                        print("screenshot" ,template['media'])
                        # screenshot = base_url + 'media/audio/' + screenshot_file_name
                        cloudinary_response = cloudinary.uploader.upload(
                        os.path.join(output_folder, screenshot_file_name),
                        folder='screenshots',  
                        overwrite=True)
                        os.remove(screenshot_file_name)
                        cloudinary_url = cloudinary_response.get('secure_url', '')
                        print("cloudinary_url",cloudinary_url)
                        img_list.append(cloudinary_url)
                    elif template['type'] == 'IMAGE':
                        img_list.append(template['media'])
                    else:
                        img_list.append(template['media'])
                    

                    if 'mp4' in template['media']:
                        if template['audioUrl'] == '' and template['audioDescription'] == '':
                            video_file = f"{user_email}_{RandomNumber()}.mp4"
                            decode_image = ur.urlopen(template['media']).read()
                            print("this is video ")

                            with open(video_file, 'wb') as f1:
                                f1.write(decode_image)
                            video_file_path=VideoFileClip(video_file)
                            audio_clip = video_file_path.audio
                            audio_clips.append(audio_clip)
                            audio_duration = audio_clip.duration
                            audio_duration_seconds = int(audio_duration)
                            audio_durations.append(audio_duration_seconds)
    
                            os.remove(video_file)


                        elif template['audioScript'] != '':
                            print('Script url',template['audioScript'])
                            audio=text_to_speech(script_modification(template['audioScript'],data['company_name'],data['organization']['organizationName'],data['organization']['prospectName']),user_email,request)
                            audio = ur.urlopen(audio)
                            file = f"{user_email}_{RandomNumber()}.wav"
                            with open(file, 'wb') as f:
                                audio_file_name.append(file)
                                f.write(audio.read())

                            audio_clip = AudioFileClip(file)
                            audio_clips.append(audio_clip)
                            audio_duration = audio_clip.duration
                            audio_duration_seconds = int(audio_duration)
                            audio_durations.append(audio_duration_seconds)
                            os.remove(file)


                        elif template['audioUrl'] != '':
                            print("url")
                            # audio = ur.urlopen(template['audioUrl'])
                            response = requests.get(template['audioUrl'])
                            audio_file = response.content
                            bytecontent=BytesIO(audio_file)

                            recognizer = sr.Recognizer()

                            with sr.AudioFile(bytecontent) as source:
                                recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                                audio = recognizer.listen(source)

                                audio_text = recognizer.recognize_google(audio)

                            audio = text_to_speech(text_convertion(audio_text), user_email, request)
                            audio = ur.urlopen(audio)
                            file = f"{user_email}_{RandomNumber()}.wav"
                            
                            with open(file, 'wb') as f:
                                audio_file_name.append(file)
                                f.write(audio.read())
                            

                            audio_clip = AudioFileClip(file)
                            audio_clips.append(audio_clip)
                            audio_duration = audio_clip.duration
                            audio_duration_seconds = int(audio_duration)
                            audio_durations.append(audio_duration_seconds)
                            os.remove(file)
                        else:
                            audio = text_to_speech(text_convertion(template["audioDescription"]), user_email, request)
                            audio = ur.urlopen(audio)
                            file = f"{user_email}_{RandomNumber()}.wav"
                            with open(file, 'wb') as f:
                                audio_file_name.append(file)
                                f.write(audio.read())

                            audio_clip = AudioFileClip(file)
                            audio_clips.append(audio_clip)
                            audio_duration = audio_clip.duration
                            audio_duration_seconds = int(audio_duration)
                            audio_durations.append(audio_duration_seconds)
                            os.remove(file)


                    elif template['audioUrl'] != '':
                        print("url")
                        # audio = ur.urlopen(template['audioUrl'])
                        response = requests.get(template['audioUrl'])
                        audio_file = response.content
                        bytecontent=BytesIO(audio_file)

                        recognizer = sr.Recognizer()

                        with sr.AudioFile(bytecontent) as source:
                            recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                            audio = recognizer.listen(source)

                            audio_text = recognizer.recognize_google(audio)

                        audio = text_to_speech(text_convertion(audio_text), user_email, request)
                        audio = ur.urlopen(audio)
                        file = f"{user_email}_{RandomNumber()}.wav"
                        
                        with open(file, 'wb') as f:
                            audio_file_name.append(file)
                            f.write(audio.read())
                        

                        audio_clip = AudioFileClip(file)
                        audio_clips.append(audio_clip)
                        audio_duration = audio_clip.duration
                        audio_duration_seconds = int(audio_duration)
                        audio_durations.append(audio_duration_seconds)
                        os.remove(file)
                    
                    elif template["audioDescription"] != '':
                        print("audioDiscription")
                        audio = text_to_speech(text_convertion(template["audioDescription"]), user_email, request)
                        audio = ur.urlopen(audio)
                        file = f"{user_email}_{RandomNumber()}.wav"
                        with open(file, 'wb') as f:
                            audio_file_name.append(file)
                            f.write(audio.read())

                        audio_clip = AudioFileClip(file)
                        audio_clips.append(audio_clip)
                        audio_duration = audio_clip.duration
                        audio_duration_seconds = int(audio_duration)
                        audio_durations.append(audio_duration_seconds)
                        os.remove(file)
                    
                    elif template['audioScript'] != '':
                        print('Script url',template['audioScript'])
                        audio=text_to_speech(script_modification(template['audioScript'],data['company_name'],data['organization']['organizationName'],data['organization']['prospectName']),user_email,request)
                        audio = ur.urlopen(audio)
                        file = f"{user_email}_{RandomNumber()}.wav"
                        with open(file, 'wb') as f:
                            audio_file_name.append(file)
                            f.write(audio.read())

                        audio_clip = AudioFileClip(file)
                        audio_clips.append(audio_clip)
                        audio_duration = audio_clip.duration
                        audio_duration_seconds = int(audio_duration)
                        audio_durations.append(audio_duration_seconds)
                        os.remove(file)

                    else:
                        title = template['title']
                        description = template['description']
                        footer = template['footer']
                        audio_text = f'title is {title}, description is {description} and footer is {footer}'
                        
                        audio = text_to_speech(text_convertion(audio_text), user_email, request)
                        audio = ur.urlopen(audio)
                        file = f"{user_email}_{RandomNumber()}.wav"
                        with open(file, 'wb') as f:
                            audio_file_name.append(file)
                            f.write(audio.read())

                        audio_clip = AudioFileClip(file)
                        os.remove(file)
                        audio_clips.append(audio_clip)
                        audio_duration = audio_clip.duration
                        audio_duration_seconds = int(audio_duration+1)
                        audio_durations.append(audio_duration_seconds)


                # text=f"hi {data['organization']['prospectName']},we represent {data['company_name']} and we are reaching out for collaboration with your company {data['organization']['organizationName']}"
                # intro_text=intro_modification(text)
                # print("intro_text",intro_text)
                # intro_audio=text_to_speech(intro_text,user_email,request)
                # audio=ur.urlopen(intro_audio)
                # print("intro_audio",intro_audio)
                # file = f"{user_email}_{RandomNumber()}.wav"
                # with open(file, 'wb') as f:
                #     f.write(audio.read())
                #     audio_clip = AudioFileClip(file)
                # concat_audio=concatenate_audioclips([audio_clip,audio_clips[0]])
                # audio_folder = os.path.join(os.getcwd(), 'static/audio')
                # os.makedirs(audio_folder, exist_ok=True)
                # current_datetime = RandomNumber()
                
                # file_path = os.path.join(audio_folder, f'comined_audio_{current_datetime}.wav')
                # concat_audio.write_audiofile(file_path)
                # os.remove(file)


                # print("this is done here ")
                # print("old audio clips ", audio_clips)
                # audio=base_url+'static/audio/'+ f'comined_audio_{current_datetime}.wav'
                # audio=ur.urlopen(audio)
                # file = f"{user_email}_{RandomNumber()}.wav"
                # with open(file, 'wb') as f:
                #     f.write(audio.read())

                # print('old audio duration' , audio_durations)
                # intro_audio_clip = AudioFileClip(file)
                # audio_duration=intro_audio_clip.duration
                # audio_duration_seconds = int(audio_duration+1)
                # audio_durations[0]=audio_duration_seconds
                # audio_clips[0]=intro_audio_clip
                # os.remove(file)

                # print('old audio duration' , audio_durations)
            

                # print("new audio clips ",audio_clips)

                duration = iter(audio_durations)
                print(duration)
                clips = []
                images = []
            
                for image in img_list:
                    split_image = image.split('.')
                    print(split_image, "")
                    if split_image[-1] != 'mp4':
                        image = ur.urlopen(image)
                        print("image=", image)
                        img_arr = np.array(bytearray(image.read()), dtype=np.uint8)
                        img = cv2.imdecode(img_arr, cv2.IMREAD_UNCHANGED)
                        img = cv2.resize(img, (720, 480))
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                            
                        clip = ImageClip(img_rgb).set_duration(next(duration))
                        clips.append(clip)
                    
                    else:
                        print(audio_durations)
                        video_file = f"{user_email}_{timezone.now().strftime('%Y%m%d%H%M')}.mp4"
                        decode_image = ur.urlopen(image).read()
                        print("this is video ")

                        with open(video_file, 'wb') as f1:
                            f1.write(decode_image)
                        video_file_path=VideoFileClip(video_file)
                        next(duration)
                        video_file_path=video_file_path.set_duration(video_file_path.duration)
                        clips.append(video_file_path)
                        os.remove(video_file)
                        
                        print(audio_clips)
                # concat the converted clips into a video and add audio to the
                print("the video concat is start ")
                final_clip = concatenate_videoclips(clips, method='compose')
                final_audio_clips=concatenate_audioclips(audio_clips)
                final_clip = final_clip.set_audio(final_audio_clips)

                video_folder = os.path.join(os.getcwd(), 'static/videos')
                os.makedirs(video_folder, exist_ok=True)
                current_datetime = RandomNumber()
                video_path = os.path.join(video_folder, f'{user_email}{current_datetime}.mp4')
                final_clip.write_videofile(video_path, fps=24)
                static_video_url =base_url + static(os.path.join('videos', f'{user_email}{current_datetime}.mp4'))
                
                # shutil.rmtree('static/image')
                
                static_video_url=static_video_url.replace('//static','/static')

                url = 'https://nodepune-aivideogenerator.mobiloitte.io/api/v1/user/updateVideoUrl'
                headers = {
                    'accept': 'application/json',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                pass_data = {
                    'organizationId':data['organization']['organizationId'],
                    'videoUrl': static_video_url
                }

                response = requests.put(url, headers=headers, data=pass_data)

                VideoLink={
                    'coatname':response_data['result']['coatName'],
                    'organizationId': data['organization']['organizationId'],
                    'videoUrl': static_video_url
                }
                # shutil.rmtree('static/audio')
                return VideoLink
                
            
                            
        except ObjectDoesNotExist:
            return Response({'status':status.HTTP_400_BAD_REQUEST,'responseMessage':'Invalid input!,please check'},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("error500",str(e))
            return {"error":str(e)}
        
    @swagger_auto_schema(
        operation_summary="Mutltiple Video Creation API ",
        operation_description="This API requires a userid, target organization organizationID, and templateId of the template",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[""],
            properties={
                'array': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'company_name': openapi.Schema(type=openapi.TYPE_STRING, default='mobiloitte technologies'),
                            'templateID': openapi.Schema(type=openapi.TYPE_STRING, default='64d728434756d168cb0a3e71'),
                            'organization': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'organizationId':openapi.Schema(type=openapi.TYPE_STRING,default='64d1da847ef1df3bb6dd6700'),
                                    'organizationName': openapi.Schema(type=openapi.TYPE_STRING,default='experinace io'),
                                    'prospectName': openapi.Schema(type=openapi.TYPE_STRING,default='scott'),
                                }
                            ),
                            'template': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'media': openapi.Schema(type=openapi.TYPE_STRING,default='https://res.cloudinary.com/mobiloitte-technology-pvt-ltd/image/upload/v1691475963/xaeqiiyohsytl7py8bgz.jpg'),
                                        'type': openapi.Schema(type=openapi.TYPE_STRING,enum=['IMAGE','VIDEO','URL'],default='IMAGE'),
                                        'title': openapi.Schema(type=openapi.TYPE_STRING,default='title'),
                                        'description': openapi.Schema(type=openapi.TYPE_STRING,default='description'),
                                        'footer': openapi.Schema(type=openapi.TYPE_STRING,default=''),
                                        'audioDescription': openapi.Schema(type=openapi.TYPE_STRING,default='This is the first screen '),
                                        'audioUrl': openapi.Schema(type=openapi.TYPE_STRING,default=''),
                                        'audioScript':openapi.Schema(type=openapi.TYPE_STRING,default=''),
                                    }
                                ),
                            ),
                        },
                    ),
                ),
            },
        ),
    )
    def post(self,request):
        try:
            finaloutput=[]
            array=request.data['array']
            with ThreadPoolExecutor() as executor:
                # for data in array:
                futures = executor.map(self.VideoCreation,array,[request] * len(array))
                    # future=executor.submit(self.VideoCreation,data,request)
                for future in futures:
                    finaloutput.append(future)
                            
                    
                shutil.rmtree('static/audio')
            return Response({'status':status.HTTP_200_OK,"videoLink":finaloutput,"responseMessage":"Video is successfully created"},status=status.HTTP_200_OK)
        
        except ObjectDoesNotExist:
            return Response({'status':status.HTTP_400_BAD_REQUEST,'responseMessage':'Invalid input!,please check'},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status':status.HTTP_500_INTERNAL_SERVER_ERROR,"responseMessage":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)   
        





#Chayanshi Verma

from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.conf import settings
import timeit
# from myapp.script_csv import *
# from myapp.script_json import *
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures
import pyttsx3
import json
from django.templatetags.static import static
from django.conf import settings

#Website link video recording API

baseurl = "http://127.0.0.1:8000/"



class Screen_recording_csv(APIView):
    csv_clip = []
    @swagger_auto_schema(
            operation_description="Screen Recording of the webpage",
            operation_summary='Screen Recording of the webpage',
            tags=['Screen Recording'],
            request_body=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'csv_file': openapi.Schema(type=openapi.TYPE_FILE),
                },
            ),
        )
    def create_video(self,entry):
        try:
            # entry = args[0] 
            print("in create video function>>>>>>>>>>>>>>>>>>>>>>")
            duration=0
            timelist=[]

            redirection_count = int(entry["sr_no"])
            url_to_record = [entry["website_url"]]
            scroll=[entry['scrolling']]
            time_f=[entry['time']]
            google_search=[entry['google_search']]
            
            
            # print(entry)
            output_folder = f"screenshots{entry['sr_no']}"
            output_video_file = f"output{redirection_count}.mp4"
    
            website=url_to_record[0]
            scrolling=scroll[0]
            time_frame=time_f[0]
            google_s=google_search[0]

            timelist.append(time_frame)
            duration+=int(time_frame)
            print("making video......")
            
            
            openbrowser_and_capture_csv(website, output_folder , redirection_count , scrolling , time_frame,google_s)
            clip =  make_video_csv(output_folder,output_video_file, time_frame)
            self.csv_clip.append(clip)
        except Exception as e:
            print("1",str(e))
    
    def post(self,request):
        try: 
            data=request.data
            try:
                csv_file = data.get("csv_file")
                csv_file_path = "temp_csv_file.csv"
                with open(csv_file_path, "wb") as f:
                    f.write(csv_file.read())
                csv_data = read_csv(csv_file_path)
                print(csv_data)
            except Exception as e:
                return Response({"Response":f"File not found {str(e)}","status":status.HTTP_404_NOT_FOUND},status.HTTP_404_NOT_FOUND)

            t1 = time.perf_counter()
            entry = []
            for e in csv_data:
                entry.append(e)

            with concurrent.futures.ThreadPoolExecutor(4) as executor:
                executor.map(self.create_video, entry)

            t2 = time.perf_counter()
            num_videos = len(csv_data)
            output_video_file_prefix = "output"
            
            # duplicate_output_video_folder="screenshots_duplicate"
            # merge_video_file = f"merge_video.mp4"
            # video=merge_videos_csv(duplicate_output_video_folder, merge_video_file , duration,timelist)

            num_videos = len(csv_data)
            output_video_file_prefix = "output"
            # video=merge_video( output_video_file_prefix, num_videos)
            stop = timeit.default_timer()
            print(self.csv_clip)
            print('Time: ', t2-t1)

            return Response({"generated_video":self.csv_clip,"merged_video":"http://127.0.0.1:8000/","Response":"Video Generated Successfully", "status": status.HTTP_200_OK}, status.HTTP_200_OK)
        except Exception as e:
            print("2",str(e))
            return Response({"response":f"vedio not created {str(e)}", "status": status.HTTP_400_BAD_REQUEST}, status.HTTP_400_BAD_REQUEST)
    
class ScreenRecording_jsonFile(APIView):
    json_clip = []
    # i = 0
    websitelist=[]
    directory = os.path.join(os.getcwd(), 'video_screenshot')
    @swagger_auto_schema(
        operation_description="Screen Recording of the webpage",
        operation_summary='Screen Recording of the webpage',
        tags=['Screen Recording'],)
    
    def create_video(self, args):
        website_detail, user_id, unique_i = args
        print("in create video")
        print("-+-+ ", website_detail)
        
        try:
            
            print("i = ", unique_i)
            url = website_detail['url']
            scroll = website_detail['scroll']
            time_duration = website_detail['time_duration']
            google_search = website_detail['google_search']
            output_folder = os.path.join(self.directory, f'user_{user_id}_website_{unique_i}')
            os.makedirs(output_folder, exist_ok=True)

            output_folder = os.path.join(self.directory, f'user_{user_id}_website_{unique_i}')
            os.makedirs(output_folder, exist_ok=True)

            openbrowser_and_capture_json(url, output_folder,unique_i, scroll, time_duration,google_search)

            output_video_file = os.path.join(self.directory, f'user_{user_id}_website_{unique_i}.mp4')
            clip = make_video_json(user_id,output_folder, output_video_file, time_duration)
            self.json_clip.append(clip)

        except Exception as e:
            print(e)

    def user_thread(self,users):
        print("\n ------------in user thread function")

        try:
            print("\n\n ++users", users)
            website_links = users['website_links']
            user_id = users['user_id']

            website_link = []
            for keys, values in website_links.items():
                website_link.append(values)

            print("list website", website_link)
            with ThreadPoolExecutor(max_workers=len(website_link)) as executor:
                args_list = [(website_detail, user_id, i) for i,website_detail in enumerate(website_link)]

                # Use executor.map with the list of tuples
                executor.map(self.create_video, args_list)

        except Exception as e:
            print(e)

    def post(self,request):
        try:
            website_data=get_website_data_json()

            if not os.path.exists(self.directory):
                os.makedirs(self.directory)

            new_file_path = os.path.join(self.directory, 'website_data.json')
            with open(new_file_path, 'w') as json_file:
                json.dump(website_data, json_file)

            users = save_user_and_website_details_from_json(website_data)
            t1 = time.perf_counter()
            
            api_response=[]
            print("len of website data ",len(website_data['result']))
            number_of_threads = len(website_data['result'])

            print("------users in dict",users)
            # self.user_thread(users)
            with concurrent.futures.ThreadPoolExecutor(number_of_threads) as executor:
                executor.map(self.user_thread, users)

            t2 = time.perf_counter()
            print('Time: ', t2-t1)
            return Response({"message": "Data fetched and processed successfully.","Response":self.json_clip,'status':status.HTTP_200_OK},status.HTTP_200_OK)
        except Exception as e:
            return Response({"Message": f'error: {str(e)}',"status":status.HTTP_400_BAD_REQUEST},status.HTTP_400_BAD_REQUEST)



#Text to Speech API  
# json_file_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'lang.json')
   
def load_languages():
    # with open(json_file_path, 'r') as file:
    #     data = json.load(file)
    # # return data['voices']
    #     return data
    pass
    
class TexttoSpeech(APIView):
     @swagger_auto_schema(
            operation_description="Screen Recording of the webpage",
            operation_summary='Screen Recording of the webpage',
            tags=['Text to Speech'],
            request_body=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'Text': openapi.Schema(type=openapi.TYPE_STRING),
                    'Language': openapi.Schema(type=openapi.TYPE_STRING),
                    'Gender': openapi.Schema(type=openapi.TYPE_STRING)
                },
            ),
        )
     def post(self,request):
        data = request.data

        try:
            engine = pyttsx3.init()
            engine_voices = engine.getProperty('voices')
            languages = load_languages()
            voice_id = ""
            voice_index = None
            for voice in languages['voices']:
                # print(voice)
                if voice['full_name'] == data.get('Language') and voice['gender'] == f"VoiceGender{data.get('Gender')}":
                    print("voice['name']",voice['name'])
                    voice_id = voice['name']
                
            if voice_id is not None:
                print(f"Setting voice to: {voice_id}")
                # Find the index of the voice by its ID
                for v in engine_voices:
                    # print(voice_id)
                    if v.name == voice_id:
                        print(v.id, v.name)
                        voice_index = v.id
                        break

            #set Voice to engine 
            if voice_index is not None:
                engine.setProperty('voice', voice_index)
            else:
                return Response({'status':status.HTTP_400_BAD_REQUEST,'response':'Invalid voice index. Provided Gender or Langauage is not avavible'},status=status.HTTP_400_BAD_REQUEST)


            # output_file_path = os.path.join(BASE_DIR, 'Ressponse_Audio.mp3')
            # engine.save_to_file(data.get('Text'), output_file_path)
            
            print("Saving the final video")
            audio_folder = os.path.join(os.getcwd(), 'static/audio')
            os.makedirs(audio_folder, exist_ok=True)
            audio_path = os.path.join(audio_folder, 'Output_audio.mp3')
            engine.save_to_file(data.get('Text'), audio_path)
            engine.runAndWait()

            static_audio_url = baseurl + static(os.path.join('audio_folder', 'Output_audio.mp3'))
            print(static_audio_url)
            static_audio_url = static_audio_url.replace('//static', '/static')


            return Response({'status': status.HTTP_200_OK, 'response': static_audio_url}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status':status.HTTP_500_INTERNAL_SERVER_ERROR,'response':str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



# crm code 

from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
# Create your views here.
import requests
import json
DOMAIN = 'https://chayanshi-dev-ed.develop.my.salesforce.com/'


def generate_token():    
    payload = {
        'grant_type': 'password',
        'client_id': '3MVG95mg0lk4bathAuqIXg.yJXjuXXdkveK.16xB_DwqWmEInjHny14yygXu_GPk7kcv68Ej9w3JBkgTZ56cV',
        'client_secret': 'F3A2A5AE7E8AC4E9E3BC1E5FDFCACD3B068AB9B76191695644A19F1DD5B7E67E',
        'username': "vermaanshi198@gmail.com",
        'password': "Chayanshi0209"
    }
    oauth_endpoint = '/services/oauth2/token'
    response = requests.post(DOMAIN + oauth_endpoint, data=payload)
    return response.json()

access_token = generate_token()['access_token']

print("access_token",access_token)
tag_object_name = 'tags__c'



headers = {
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json'
        }

def get_all_columns(object_name):
        endpoint = f'/services/data/v56.0/sobjects/{object_name}/describe/'
        response = requests.get(DOMAIN + endpoint, headers=headers)
        if response.status_code == 200:
            print(response.json())
            return [field['name'] for field in response.json()['fields']]
        else:
            return None

def select_all_columns(object_name):
        all_columns = get_all_columns(object_name)
        if all_columns:
            query = f"SELECT {', '.join(all_columns)} FROM {object_name}"
            return query
        else:
            return None






 

class GetAllTagsDetail(APIView):
    @swagger_auto_schema(
        operation_description="Retrieve Tags with associated user details",
        operation_summary="Get Tags Details",
        tags=['Tags'],
        responses={200: openapi.Schema(type=openapi.TYPE_OBJECT)}
    )
    def get(self, request):
        # Your existing token generation logic
        access_token = generate_token()['access_token']

        if not access_token:
            return Response({"error": "Access token not obtained. Check the error message for details."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json'
        }
        endpoint = f'/services/data/v56.0/query/'
        soql_query = select_all_columns(tag_object_name)
        response = requests.get(DOMAIN + endpoint, headers=headers, params={'q': soql_query})

        user_data = response.json()

        return Response(user_data, status=status.HTTP_200_OK)



class CreateTag(APIView):
    @swagger_auto_schema(
        operation_description="Create a new tag",
        operation_summary="Create tag",
        tags=['Tags'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['organisation_name','customer_name'],
            properties={
                'organisation_name': openapi.Schema(type=openapi.TYPE_STRING),
                'organisation_website_url': openapi.Schema(type=openapi.TYPE_STRING),
                'customer_name': openapi.Schema(type=openapi.TYPE_STRING),
                'linkedin': openapi.Schema(type=openapi.TYPE_STRING),
                'instagram': openapi.Schema(type=openapi.TYPE_STRING),
                'facebook': openapi.Schema(type=openapi.TYPE_STRING),
                'twitter': openapi.Schema(type=openapi.TYPE_STRING),
                'threads': openapi.Schema(type=openapi.TYPE_STRING),
                'youtube':openapi.Schema(type=openapi.TYPE_STRING)
            }
        )
    )
    def post(self, request):
        try:
            # access_token = generate_token()['access_token']

            if not access_token:
                return Response({"error": "Access token not obtained. Check the error message for details."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # headers = {
            #     'Authorization': 'Bearer ' + access_token,
            #     'Content-Type': 'application/json'
            # }

            tag_object_name = 'tags__c'
            user_record_data = {
                'organisation_name__c': request.data.get('organisation_name'),
                'organisation_website_url__c': request.data.get('organisation_website_url'),
                'customer__c': request.data.get('customer_name'),
                'linkedin__c': request.data.get('linkedin'),
                'instagram__c': request.data.get('instagram'),
                'facebook__c': request.data.get('facebook'),
                'twitter__c': request.data.get('twitter'),
                'threads__c': request.data.get('threads'),
                'youtube__c': request.data.get('youtube'),

                
            }

            endpoint = f'/services/data/v56.0/sobjects/{tag_object_name}/'
            response = requests.post(DOMAIN + endpoint, headers=headers, json=user_record_data)

            return Response({"message":"Data added successfully","status":status.HTTP_201_CREATED,"response":response}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"message":"Fail to add data","status":status.HTTP_400_BAD_REQUEST,"response":response}, status=status.HTTP_400_BAD_REQUEST)



class Upload_tags_values(APIView):
    @swagger_auto_schema(
        operation_description="Create a new tag",
        operation_summary="Create tag",
        tags=['Tags'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['organisation_name','customer_name'],
            properties={
                'customer_id': openapi.Schema(type=openapi.TYPE_STRING),
                
            }
        )
    )
    def post(self, request):
        # Your existing token generation logic
        access_token = generate_token()['access_token']

        if not access_token:
            return Response({"error": "Access token not obtained. Check the error message for details."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json'
        }
        endpoint = f'/services/data/v56.0/query/'
        soql_query = select_all_columns(tag_object_name)
        response = requests.get(DOMAIN + endpoint, headers=headers, params={'q': soql_query})

        user_data = response.json()

        return Response(user_data, status=status.HTTP_200_OK)







# sql connections




# class Get_BaseVideo_sql(APIView):
    
#     data = {}
#     database = None
#     @swagger_auto_schema(
#         operation_summary="Multiple Video Creation API",
#         operation_description="This API requires a userid, target organization organizationID, and templateId of the template",
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             required=[""],
#             properties={
#                 "video_template_id":openapi.Schema(type=openapi.TYPE_INTEGER, description="user id"),
#             }
#         )
#     )
#     def post(self,request):
#         video_data = []
#         video_template_id = request.data['video_template_id']
#         try:
#             db = con.connect(host='172.16.2.45',user='adminscott',password='Mobiloitte@1',database='aivdohvov02')
#             print(db)
#             if db.is_connected():
#                 db_Info = db.get_server_info()
#                 print("Connected to MySQL Server version ", db_Info)

#                 # Fetching column names
#                 table_name = "base_video_refferal"
#                 cursor = db.cursor(dictionary=True)
#                 cursor.execute(f"DESCRIBE {table_name}")
#                 columns = [column['Field'] for column in cursor.fetchall()]

#                 # Fetching and printing records
#                 sql_select_Query = f"SELECT * FROM {table_name}"
#                 cursor.execute(sql_select_Query)
#                 records = cursor.fetchall()
#                 print("recordsss  ",records)

#                 for i,row in enumerate(records):
#                     print("for loop")
#                     print("\getting row",i)
#                     for column in columns:
#                         # print(f"{column}: {row[column]}")
#                         self.data[column] = row[column]

                    
#                     video_id = row['type']
#                     # print(video_id)
#                     if video_id:
#                         video_type_query = f"SELECT * FROM video_referral_type WHERE id = {video_id}"
#                         cursor.execute(video_type_query)
#                         video_type_data = cursor.fetchall()
#                         self.data['type'] = video_type_data

#                     background_id = row['background_video']
#                     # print(background_id)
#                     if background_id:
#                         background_query = f"SELECT * FROM background_video WHERE id = {background_id}"
#                         cursor.execute(background_query)
#                         background_data = cursor.fetchall()
#                         self.data['background_video'] = background_data

#                     website_id = row['website_details']
#                     # print(website_id)
#                     if website_id:
#                         website_query = f"SELECT * FROM website_details WHERE id = {website_id}"
#                         cursor.execute(website_query)
#                         website_data = cursor.fetchall()
#                         self.data['website_details'] = website_data

#                     audio_id = row['audio_template']
#                     # print("audio_id",audio_id)
#                     if audio_id:
#                         audio_query = f"SELECT * FROM base_audio_refferal WHERE id = {audio_id}"
#                         cursor.execute(audio_query)
#                         audio_data = cursor.fetchall()
#                         self.data['audio_template'] = audio_data

#                     # print("self.data['audio_template']",self.data['audio_template'][0]['media_type'])
#                     audio_type__id = self.data['audio_template'][0]['media_type']
#                     # print("audio_id",audio_id)
#                     if audio_type__id:
#                         audio_type_query = f"SELECT * FROM audio_referral_type WHERE id = {audio_type__id}"
#                         cursor.execute(audio_type_query)
#                         audio_type_data = cursor.fetchall()
#                         self.data['audio_template'][0]['media_type'] = audio_type_data

#                     # print("\ndata ",i,self.data)
#                     video_data.append(self.data)
#                     print('length of video data for every loop', len(video_data))

#             print('length of video data')
#             print(video_data)
#             return Response({"status":status.HTTP_200_OK,'Response':video_data},status=status.HTTP_200_OK)
        
#         except Error as e:
#             print("Error while connecting to MySQL", e)
#             return Response({"status":status.HTTP_400_BAD_REQUEST,'Response':f"Can't connect to Database {str(e)}"},status=status.HTTP_400_BAD_REQUEST)
        
#         finally:
#             if db.is_connected():
#                 cursor.close()
#                 db.close()
#                 print("MySQL connection is closed")
                
                
                





# video creatin code 




# class Get_BaseVideo_sql(APIView):
    
   
#     @swagger_auto_schema(
#         operation_summary="Multiple Video Creation API",
#         operation_description="This API requires a userid, target organization organizationID, and templateId of the template",
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             required=[""],
#             properties={
#                 "video_template_id":openapi.Schema(type=openapi.TYPE_INTEGER, description="user id"),
#             }
#         )
#     )
#     def post(self,request):
#         data = {}
#         database = None
#         video_data = []
#         video_template_id = request.data['video_template_id']
#         try:
#             db = con.connect(host='172.16.2.45',user='adminscott',password='Mobiloitte@1',database='aivdohvov02')
#             print(db)
#             if db.is_connected():
#                 db_Info = db.get_server_info()
#                 print("Connected to MySQL Server version ", db_Info)

#                 # Fetching column names
#                 table_name = "base_video_refferal"
#                 cursor = db.cursor(dictionary=True)
#                 cursor.execute(f"DESCRIBE {table_name}")
#                 columns = [column['Field'] for column in cursor.fetchall()]

#                 # Fetching and printing records
#                 sql_select_Query = f"SELECT * FROM {table_name}"
#                 cursor.execute(sql_select_Query)
#                 records = cursor.fetchall()
#                 print("recordsss  ",records)

#                 for i,row in enumerate(records):
#                     data = {}
#                     print("for loop")
#                     print("\getting row",i)
#                     for column in columns:
#                         # print(f"{column}: {row[column]}")
#                         data[column] = row[column]

                    
#                     video_id = row['type']
#                     video_type_data = None
#                     print(video_type_data)
#                     if video_id:
#                         video_type_query = f"SELECT * FROM video_referral_type WHERE id = {video_id}"
#                         cursor.execute(video_type_query)
#                         video_type_data = cursor.fetchall()
#                         print("video data ",video_type_data)
#                         data['type'] = video_type_data
#                         print("video data ",data['type'])
                        
                
#                     background_id = row['background_video']
#                     background_data =None
#                     # print(background_id)
#                     if background_id:
#                         background_query = f"SELECT * FROM background_video WHERE id = {background_id}"
#                         cursor.execute(background_query)
#                         background_data = cursor.fetchall()
#                         data['background_video'] = background_data

#                     website_id = row['website_details']
#                     website_data =None
#                     # print(website_id)
#                     if website_id:
#                         website_query = f"SELECT * FROM website_details WHERE id = {website_id}"
#                         cursor.execute(website_query)
#                         website_data = cursor.fetchall()
#                         data['website_details'] = website_data

#                     audio_id = row['audio_template']
#                     audio_data = None
#                     # print("audio_id",audio_id)
#                     if audio_id:
#                         audio_query = f"SELECT * FROM base_audio_refferal WHERE id = {audio_id}"
#                         cursor.execute(audio_query)
#                         audio_data = cursor.fetchall()
#                         data['audio_template'] = audio_data

#                     # print("data['audio_template']",data['audio_template'][0]['media_type'])
#                     if data['audio_template']:
#                         audio_type_data=None
#                         audio_type__id = data['audio_template'][0]['media_type']
#                         # print("audio_id",audio_id)
#                         if audio_type__id:
#                             audio_type_query = f"SELECT * FROM audio_referral_type WHERE id = {audio_type__id}"
#                             cursor.execute(audio_type_query)
#                             audio_type_data = cursor.fetchall()
#                             data['audio_template'][0]['media_type'] = audio_type_data

#                     # print("\ndata ",i,data)
#                     video_data.append(data)
#                     print('length of video data for every loop', len(video_data))

#             print('length of video data')
#             print(video_data)
#             return Response({"status":status.HTTP_200_OK,'Response':video_data},status=status.HTTP_200_OK)
        
#         except Error as e:
#             print("Error while connecting to MySQL", e)
#             return Response({"status":status.HTTP_400_BAD_REQUEST,'Response':f"Can't connect to Database {str(e)}"},status=status.HTTP_400_BAD_REQUEST)
        
#         finally:
#             if db.is_connected():
#                 cursor.close()
#                 db.close()
#                 print("MySQL connection is closed")




# def retrivedata(video_template_id):
#     video_position = f"{base_url}/mysql/Get_BaseVideo_sql"
#     response=requests.post(video_position ,json={"video_template_id": video_template_id})
#     print("response ????????????",response)
    
#     if response.status_code==200:
#         website_data=response.json()
        
#         return website_data
#     else:
#         return f"Error occurred while fetching data. Status code: {response.status_code}"
    



# class VideoCreationWithPostion(APIView):
#     @staticmethod
#     def set_media_position(W, H, user):
#         pos_list = []
#         width = 100
#         height = 100
#         if len(user) == 1:
#             width = W/2
#             height = H/2
#         elif len(user)>1:
#             width=W
#             height = H
#             for i in range(len(user)):
#                 width = width/2
#                 height = height/2
        
#         for i in range(len(user)):
#             pos = None  
#             print(i)
#             if i == 0:
#                 if int(int(user[i]) ) == 0:
#                     pos = (W/4, H/4)
#                 elif int(int(user[i]) ) == 1:
#                     pos = (W/2, 0) 
#                 elif int(user[i])  == 2:
#                     pos = (W/2, H/2)
#                 elif int(user[i])  == 3:
#                     pos = (0, H/2)
#                 elif int(user[i])  == 4:
#                     pos = (0, 0)
#                 elif int(user[i])  == 5:
#                     pos = (W, H) 
#             else:
#                 W = W/2
#                 H = H/2
#                 if int(user[i])  == 0:
#                     pos = (W/4, H/4)
#                 elif int(user[i])  == 1:
#                     pos = (W/2, 0)
#                 elif int(user[i])  == 2:
#                     pos = (W/2, H/2)
#                 elif int(user[i])  == 3:
#                     pos = (0, H/2)
#                 elif int(user[i])  == 4:
#                     pos = (0, 0)
#                 elif int(user[i])  == 5:
#                     pos = (W, H)
            
#             pos_list.append(pos)
        
#         return pos_list, width,height
   
   

#     @swagger_auto_schema(
#         operation_summary="Multiple Video Creation API",
#         operation_description="This API requires a userid, target organization organizationID, and templateId of the template",
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             required=[""],
#             properties={
#                 "video_template_id":openapi.Schema(type=openapi.TYPE_INTEGER, description="user id"),
#             }
#         )
#     )
    
    
#     def post(self, request):
#         # try:
#             t1 = time.perf_counter()
            
#             # video_data=''
#             video_template_id = request.data['video_template_id']
#             print("video_template_id",video_template_id)
#             try:
#                 video_data = retrivedata(video_template_id)
#             except Exception as e:
#                 print(str(e))
#             print(">>>    >>>>>>>>>>>>>>", video_data)
            
            
            
#             all_data = video_data['Response']
#             print(all_data)


#             clips = []
#             audio_clips = []
#             audio_clip_duration=[]

#             # user = data['User']
#             # customerName = user['customerName']
#             # customerCompany = user['customerCompany']
            
            
                       
#             # mediaData = data['media']
#             # mediaSorted = sorted(mediaData, key= lambda x:x['sequence'])
            
            
#             current_start_time = 0
#             current_sequence_duration = 0
#             for i,screen in enumerate(all_data):
#                 background = screen['background_video'][0]
#                 print("backgroung0", background)
#                 bg_type = 'Video'
#                 bg_file = background['media']
#                 print(bg_file)
#                 media, type,title, audioScript, audioURL, position, sequence, websiteDetails= (
#                     screen['media'],
#                     screen['type'][0]['name'],
#                     screen['title'],
#                     screen['audio_template'][0]['Description'],
#                     screen['audio_url'],
#                     screen['position_composition_id'],
#                     screen['sequence'],
#                     screen['website_details'],
                    
#                 )
                
#                 # print(mediaSorted[i])
#                 if type == 'URL':
#                     positions = []
#                     positions.append(position)
#                     print(positions,"positionsssssssss")
#                     redirection_count = len(websiteDetails)
#                     for website in websiteDetails:
#                         if audioScript:
                            
#                             print("AudioScript>>>>>>>>>>",audioScript)
#                             audio = text_to_speech(audioScript, 'position_audio', request)
#                             audio = ur.urlopen(audio)
#                             file = f"position_audio_{timezone.now().strftime('%Y%m%d%H%M')}.wav"
                        
#                         elif audioURL:
#                             res = requests.get(audioURL)
#                             bytecontent = BytesIO(res.content)
                            
#                             recognizer = sr.Recognizer()
#                             with sr.AudioFile(bytecontent) as source:
#                                 recognizer.adjust_for_ambient_noise(source, duration=0.00001)
#                                 audio = recognizer.listen(source)
#                                 audioText = recognizer.recognize_google(audio)
                            
#                             audio = text_to_speech(audioText, "audio", request)
#                             audio = ur.urlopen(audio)
#                             file = f"audio_{RandomNumber()}.wav" 
                        
#                         with open(file, 'wb') as f:
#                             f.write(audio.read())
                        
#                         audio_clip = AudioFileClip(filename=file)
#                         audio_clips.append(audio_clip) 
#                         audio_duration = audio_clip.duration
#                         audio_duration_seconds = int(audio_duration)
#                         audio_clip_duration.append(audio_duration_seconds)
                        
                        
#                         position, width,height = set_media_position(W=1920,H=1080, user=positions)
#                         sum_tuple = tuple(sum(x) for x in zip(*position))
#                         x,y = int(sum_tuple[0]), int(sum_tuple[1])
                        
#                         os.remove(file)
#                         output_folder = f'static/web/'
#                         videofileName = f'static/videos/jagga_video.mp4'
#                         scroll = None
#                         search = None
#                         if website['scroll'] == 'T':
#                             scroll = True
#                         else:
#                             scroll =False    
#                         print(website['websearch'])
#                         if website['websearch'] == 'T':
#                             search = True
#                         else:
#                             search = False    
#                         openbrowser_and_capture_json(website=website['url'], output_folder=output_folder, redirection_count=redirection_count, scrolling=scroll, google_search_c=search)
                        
#                         clip = make_video_json(output_folder=output_folder, output_video_file=videofileName,time_frame=audio_duration_seconds)
                        
#                         start_time = sum(audio_clip_duration[:i]) if i > 0 else 0    
#                         print("Start times::::::", start_time)     
#                         clip = clip.set_audio(audio_clip).set_position((x, y)).set_start(start_time)
#                         clip = clip.resize(width=width, height=height) 
#                         clips.append(clip)
                        
                        
#                 if type == 'Image':
#                     image = ur.urlopen(media)
#                     img_arr = np.array(bytearray(image.read()), dtype=np.uint8)
#                     img = cv2.imdecode(img_arr, cv2.IMREAD_UNCHANGED)
#                     img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    
#                     if audioScript != "":
#                         audio = text_to_speech(audioScript, 'position_audio', request)
#                         audio = ur.urlopen(audio)
#                         file = f"position_audio_{timezone.now().strftime('%Y%m%d%H%M')}.wav"
                        
#                     elif audioURL != "":
#                         res = requests.get(audioURL)
#                         bytecontent = BytesIO(res.content)
                        
#                         recognizer = sr.Recognizer()
#                         with sr.AudioFile(bytecontent) as source:
#                             recognizer.adjust_for_ambient_noise(source, duration=0.00001)
#                             audio = recognizer.listen(source)
#                             audioText = recognizer.recognize_google(audio)
                        
#                         audio = text_to_speech(audioText, "audio", request)
#                         audio = ur.urlopen(audio)
#                         file = f"audio_{RandomNumber()}.wav" 
                        
#                     with open(file, 'wb') as f:
#                         f.write(audio.read())
                            

#                     audio_clip = AudioFileClip(filename=file)
#                     audio_clips.append(audio_clip)
#                     audio_duration = audio_clip.duration
#                     audio_duration_seconds = int(audio_duration)
#                     audio_clip_duration.append(audio_duration_seconds)
                    
#                     os.remove(file)
                    
#                     positions = position.split(',')
#                     position, width,height = set_media_position(W=1920,H=1080, user=positions)
#                     sum_tuple = tuple(sum(x) for x in zip(*position))
#                     x,y = int(sum_tuple[0]), int(sum_tuple[1])
                    
#                     clip = ImageClip(img_rgb).set_duration(audio_duration_seconds)
#                     # start_time = sum(audio_clip_duration[:i]) if i > 0 else 0
#                     # ! commented code for sequencing of multi overlay media:::::::: NOT WORKING 
#                     # if i == 0 or sequence != mediaSorted[i - 1]['sequence']:
#                     #     current_start_time += current_sequence_duration  # Update start time
#                     #     current_sequence_duration = 0 
#                     # if sequence == mediaSorted[i - 1]['sequence']:
#                     #     current_sequence_duration = max(current_sequence_duration, audio_clip_duration[i])  # Update sequence duration

#                     #     # Match previous video duration to the maximum (only for non-first videos in a sequence):
#                     #     if i > 0:  # Ensure first video in a sequence isn't modified
#                     #         audio_clip_duration[i - 1] = current_sequence_duration

#                     start_time = sum(audio_clip_duration[:i]) if i > 0 else 0         
#                     clip = clip.set_audio(audio_clip).set_position((x, y)).set_start(start_time)
                    
                    
#                     # if i > 0 and sequence != mediaSorted[i - 1]['sequence']:
#                     #     audio_clip_duration.pop()
                        
                        
#                     clip = clip.resize(width=width, height=height) 
#                     clips.append(clip)

                
#                 elif type == 'Video':
#                     if audioScript != "":
#                         audio = text_to_speech(audioScript, 'position_audio', request)
#                         audio = ur.urlopen(audio)
#                         file = f"position_audio_{timezone.now().strftime('%Y%m%d%H%M')}.wav"                    
                        
#                     elif audioURL != "":
#                         res = requests.get(audioURL)
#                         bytecontent = BytesIO(res.content)
                        
#                         recognizer = sr.Recognizer()
#                         with sr.AudioFile(bytecontent) as source:
#                             recognizer.adjust_for_ambient_noise(source, duration=0.00001)
#                             audio = recognizer.listen(source)
#                             audioText = recognizer.recognize_google(audio)
                        
#                         audio = text_to_speech(audioText, "audio", request)
#                         audio = ur.urlopen(audio)
#                         file = f"audio_{RandomNumber()}.wav" 
                        
#                     with open(file, 'wb') as f:
#                         f.write(audio.read())
#                         print("Length of written audio file:", os.path.getsize(file))

#                     audio_clip = AudioFileClip(filename=file)
#                     audio_clips.append(audio_clip)
#                     audio_duration = audio_clip.duration
#                     audio_duration_seconds = int(audio_duration)
#                     audio_clip_duration.append(audio_duration_seconds)
                    
#                     os.remove(file)
#                     position = str(position)
#                     positions = position.split(',')
                    
#                     video_clip = VideoFileClip(media)
#                     position, width,height = set_media_position(W=1920,H=1080, user=positions)
                    
#                     sum_tuple = tuple(sum(x) for x in zip(*position))
#                     x,y = int(sum_tuple[0]), int(sum_tuple[1])
                    
                    
#                     # ! commented code for sequencing of multi overlay media:::::::: NOT WORKING
                    
#                     # if i == 0 or sequence != mediaSorted[i - 1]['sequence']:
#                     #     current_start_time += current_sequence_duration  # Update start time
#                     #     current_sequence_duration = 0 
#                     # if sequence == mediaSorted[i - 1]['sequence']:
#                     #     current_sequence_duration = max(current_sequence_duration, audio_clip_duration[i])  # Update sequence duration

#                     #     # Match previous video duration to the maximum (only for non-first videos in a sequence):
#                     #     if i > 0:  # Ensure first video in a sequence isn't modified
#                     #         audio_clip_duration[i - 1] = current_sequence_duration
                            
#                     start_time = sum(audio_clip_duration[:i]) if i > 0 else 0        
#                     video = video_clip.set_audio(audio_clip).set_position((x, y)).set_start(start_time)
                    
#                     # if i > 0 and sequence != mediaSorted[i - 1]['sequence']:
#                     #     audio_clip_duration.pop()
                    
#                     # video=video.set_start(start_time)
#                     video=video.resize(width=width,height=height)
#                     video= video.subclip(0,audio_duration_seconds)
#                     clips.append(video)
                    

#             video_folder = os.path.join(os.getcwd(), 'static/videos')
#             os.makedirs(video_folder, exist_ok=True)
#             current_datetime = RandomNumber()
#             video_path = os.path.join(video_folder, f'customer_{current_datetime}.mp4')


#             # Load the background Image Video
#             if bg_type == "Image":
#                 image = ur.urlopen(bg_file)
#                 img_arr = np.array(bytearray(image.read()), dtype=np.uint8)
#                 img = cv2.imdecode(img_arr, cv2.IMREAD_UNCHANGED)
#                 img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

#                 background_clip = ImageClip(img_rgb).set_duration(sum(audio_clip_duration))
#                 repeated_background = background_clip.resize(width=1920,height=1080)

                
#             # Load the background video
#             elif bg_type == "Video":
#                 background_clip = VideoFileClip(bg_file)
#                 background_clip = background_clip.without_audio()
#                 background_clip = background_clip.resize(width=1920, height=1080)  # Adjust the size as needed
#                 repeated_background = background_clip.loop(duration=sum(audio_clip_duration))
    
#             final_clip = CompositeVideoClip([repeated_background] + clips)
            

#             final_clip.write_videofile(video_path, fps=24)
#             static_video_url = base_url + static(os.path.join('videos', f'customer_{current_datetime}.mp4'))
            
#             t2 = time.perf_counter()
#             print('Time: ', t2-t1)
#             return Response({'url': static_video_url, "Status": status.HTTP_200_OK},status.HTTP_200_OK)
     
#         # except Exception as e:
#         #     return Response({"Error": str(e), "Status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status.HTTP_500_INTERNAL_SERVER_ERROR)




# new code for position 






def retrivedata(video_template_id):
    video_position = f"{base_url}/mysql/Get_BaseVideo_sql"
    response=requests.post(video_position ,json={"video_template_id": video_template_id})
    print("response ????????????",response)
    
    if response.status_code==200:
        website_data=response.json()
        
        return website_data
    else:
        return f"Error occurred while fetching data. Status code: {response.status_code}"






class Get_BaseVideo_sql(APIView):
    data = {}
    database = None
    @swagger_auto_schema(
        operation_summary="Multiple Video Creation API",
        tags=['MySQL'],
        operation_description="This API requires a userid, target organization organizationID, and templateId of the template",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[""],
            properties={
                "video_template_id":openapi.Schema(type=openapi.TYPE_INTEGER, description="video template id"),
                # "user_id":openapi.Schema(type=openapi.TYPE_INTEGER, description="user_id"),
            }
        )
    )
    def post(self,request):
        video_data = []
        person_data=[]
        user_id = None
        user_details = None
        resposne = {}
        background_video_data =None
        try:
            db = con.connect(host='172.16.2.45',user='adminscott',password='Mobiloitte@1',database='aivdohvov02')
            print(db)
            if db.is_connected():
                db_Info = db.get_server_info()
                print("Connected to MySQL Server version ", db_Info)

                # Fetching column names
                table_name = "base_video_refferal"
                cursor = db.cursor(dictionary=True)
                cursor.execute(f"DESCRIBE {table_name}")
                columns = [column['Field'] for column in cursor.fetchall()]

                # Fetching and printing records
                sql_select_Query = f"SELECT * FROM {table_name} WHERE video_template = {request.data['video_template_id']}"
                cursor.execute(sql_select_Query)
                records = cursor.fetchall()
                print("recordsss  ",records)

                for i,row in enumerate(records):
                    self.data = {}
                    print("for loop")
                    print("\getting row",i)
                    for column in columns:
                        # print(f"{column}: {row[column]}")
                        self.data[column] = row[column]

                    video_id = row['type']
                    # print(video_id)
                    if video_id:
                        video_type_query = f"SELECT * FROM video_referral_type WHERE id = {video_id}"
                        cursor.execute(video_type_query)
                        video_type_data = cursor.fetchall()
                        self.data['type'] = video_type_data[0]

                    # background_id = row['background_video']
                    # # print(background_id)
                    # if background_id:
                    #     background_query = f"SELECT * FROM background_video WHERE id = {background_id}"
                    #     cursor.execute(background_query)
                    #     background_data = cursor.fetchall()
                    #     self.data['background_video'] = background_data[0]

                    website_id = row['website_details']
                    # print(website_id)
                    if website_id:
                        website_query = f"SELECT * FROM website_details WHERE id = {website_id}"
                        cursor.execute(website_query)
                        website_data = cursor.fetchall()
                        self.data['website_details'] = website_data

                    audio_id = row['audio_template']
                    # print("audio_id",audio_id)
                    if audio_id:
                        audio_query = f"SELECT * FROM base_audio_refferal WHERE id = {audio_id}"
                        cursor.execute(audio_query)
                        audio_data = cursor.fetchall()
                        self.data['audio_template'] = audio_data[0]
                        self.data['audio_template']['Description'] = re.sub('<[^>]*>', '', self.data['audio_template']['Description'])

                    # print("self.data['audio_template']",self.data['audio_template'][0]['media_type'])
                    if self.data['audio_template']:
                        audio_type__id = self.data['audio_template']['media_type']
                        # print("audio_id",audio_id)
                        if audio_type__id:
                            audio_type_query = f"SELECT * FROM audio_referral_type WHERE id = {audio_type__id}"
                            cursor.execute(audio_type_query)
                            audio_type_data = cursor.fetchall()
                            self.data['audio_template']['media_type'] = audio_type_data[0]

                    position_composition_id = row['position_composition_id']
                    # print(background_id)
                    if position_composition_id:
                        position_composition_query = f"SELECT * FROM position_composition WHERE id = {position_composition_id}"
                        cursor.execute(position_composition_query)
                        position_composition_data = cursor.fetchall()
                        position_1 = position_composition_data[0]['position_Position_id']
                        position_2 = int(position_composition_data[0]['position_composition_id'])
                        self.data['position_composition_id'] = [position_1,position_2]

                    video_template_id = row['video_template']
                    # print(background_id)
                    if video_template_id:
                        video_template_query = f"SELECT * FROM vdo_template WHERE vdo_template_id = {request.data['video_template_id']}"
                        cursor.execute(video_template_query)
                        video_template_data = cursor.fetchall()
                        user_id = video_template_data[0]['fk_users_id']
                        background_id = video_template_data[0]['background_video']
                        print("background_id",background_id)
                        self.data['video_template'] = video_template_data[0]

                        if background_id:
                            background_query = f"SELECT * FROM background_video WHERE id = {background_id}"
                            cursor.execute(background_query)
                            background_data = cursor.fetchall()
                            background_video_data = background_data[0]
                            background_video_type = background_data[0]['type']

                            if background_video_type:
                                video_type_query = f"SELECT * FROM video_referral_type WHERE id = {background_video_type}"
                                cursor.execute(video_type_query)
                                bgvideo_type_data = cursor.fetchall()
                                background_video_data['type'] = bgvideo_type_data[0]['name']

                        print("user_id",user_id)
                        if user_id:
                            user_query = f"SELECT * FROM users WHERE user_Id = {user_id}"
                            cursor.execute(user_query)
                            user_data = cursor.fetchall()
                            user_org_id = user_data[0]['user_organization_user_org_id']
                            print("user_org_id  ",user_org_id)
                            user_details = user_data[0]
                            
                            if user_org_id:
                                user_org_query = f"SELECT * FROM user_organization WHERE user_org_id = {user_org_id}"
                                cursor.execute(user_org_query)
                                user_org_data = cursor.fetchall()
                                user_details['user_organization_user_org_id'] = user_org_data[0]
                    
                    
                    print("===========",self.data['type']['name'])
                    if self.data['type']['name'] == "personalised":
                        print(self.data)
                        print("crm video data getting")
                        customer_data = get_CustomerDetails(user_id,self.data['Tag_personalised'])
                        print("\ncustomer_data",customer_data)
                        person_data.append(self.data)
                        person_data[0]['Tag_personalised'] = customer_data
                        # person_data.append(customer_data)
                    

                    # print(">>>>>>>>user_id",video_data)
                    # print("\ndata ",i,self.data)
                    # print(video_data, "videodata:\n")
                    # print(self.data, "asvavs")
                    # print("type name",self.data['type']['name'])
                    if self.data['type']['name'] != "personalised":
                        # if request.data['user_id'] == user_id:
                            video_data.append(self.data)
                            print('length of video data for every loop', len(resposne))
            
            print(resposne)
            resposne = {
                'user_details':user_details,
                'base_videos':video_data,
                'personalised':person_data,
                'background_video_data':background_video_data
                
                }
            return Response({"status":status.HTTP_200_OK,'Response':resposne},status=status.HTTP_200_OK)

        except Error as e:
            print("Error while connecting to MySQL", e)
            return Response({"status":status.HTTP_400_BAD_REQUEST,'Response':f"Can't connect to Database {str(e)}"},status=status.HTTP_400_BAD_REQUEST)
        
        finally:
            if db.is_connected():
                cursor.close()
                db.close()
                print("MySQL connection is closed")


#function for get customer
def get_CustomerDetails(user_id,tag):
    print("in get customer funtion--------------",user_id)
    customer_data = []
    user_data = {}
    try:
        db = con.connect(host='172.16.2.45',user='adminscott',password='Mobiloitte@1',database='aivdohvov02')
        print(db)
        if db.is_connected():
            db_Info = db.get_server_info()
            print("Connected to MySQL Server version ", db_Info)

            # Fetching column names
            table_name = "customer"
            cursor = db.cursor(dictionary=True)
            cursor.execute(f"DESCRIBE {table_name}")
            columns = [column['Field'] for column in cursor.fetchall()]

            # Fetching and printing records
            customer_select_Query = f"SELECT * FROM {table_name} WHERE users_id={user_id}"
            cursor.execute(customer_select_Query)
            customer_records = cursor.fetchall()
            # print("recordsss  ",records)

            for i,row in enumerate(customer_records):
                data = {}
                print("for loop")
                print("\getting row",i)
                for column in columns:
                    # print(f"{column}: {row[column]}")
                    data[column] = row[column]

                # if user_id:
                #     user_query = f"SELECT * FROM users WHERE user_Id = {user_id}"
                #     cursor.execute(user_query)
                #     user_data = cursor.fetchall()
                #     user_data= user_data[0]

                print("tag id ",tag)
                if tag:
                    tag_value_query = f"SELECT * FROM tagged_values WHERE tag_id = {tag}"
                    cursor.execute(tag_value_query)
                    tag_value_data = cursor.fetchall()
                    tag_value_data= tag_value_data
                
                print("tag_value_data",tag_value_data)
                # print("\ndata ",i,self.data)
                # print(video_data, "videodata:\n")
                # print(self.data, "asvavs")
                customer_data.append(data)
                user_data['customers'] = data
                user_data['customers']['tag_values'] = tag_value_data
                # print("user_data",user_data)
                # customer_data.append(data)
                print('length of video data for every loop', len(user_data))

        print("------------user_data",user_data)
        return user_data
    
    except Error as e:
        print("Error while connecting to MySQL", e)
        return e
    
    finally:
        if db.is_connected():
            cursor.close()
            db.close()
            print("MySQL connection is closed")
            

#Api to get all customer details as per customer group
class Get_customers(APIView):
    @swagger_auto_schema(
        operation_summary="Multiple Video Creation API",
        tags=['MySQL'],
        operation_description="This API requires a userid, target organization organizationID, and templateId of the template",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[""],
            properties={
                "video_template_id":openapi.Schema(type=openapi.TYPE_INTEGER, description="video template id"),
                "customer_group_id":openapi.Schema(type=openapi.TYPE_INTEGER, description="customer group id"),
            }
        )
    )
    def post(self,request):
        input_template_id = request.data['video_template_id']
        input_customer_group_id = request.data['customer_group_id']

        customer_data = []
        base_video_data =[]
        data = {}
        mytagvalues = []

        
        try:
            db = con.connect(host='172.16.2.45',user='adminscott',password='Mobiloitte@1',database='aivdohvov02')
            print(db)
            if db.is_connected():
                db_Info = db.get_server_info()
                print("Connected to MySQL Server version ", db_Info)

                # Fetching column names
                cursor = db.cursor(dictionary=True)

                # Fetching customer records as per custoemr group
                customer_select_Query = f"SELECT customer_customer FROM customer_group_has_customer WHERE customer_group = '{input_customer_group_id}'"

                cursor.execute(customer_select_Query)
                customer_records = cursor.fetchall()
                print("recordsss  ",customer_records)
                for i,row in enumerate(customer_records):
                    data = {}
                    cust_record = None
                    # customer_id = None
                    # print("\n getting row",i)
                    # print("row",row)

                    customer_id = row['customer_customer']
                    if customer_id:
                        customer_query = "SELECT * FROM customer WHERE customer_id = %s"
                        cursor.execute(customer_query, (customer_id,))
                        cust_record = cursor.fetchall()
                        cust_record = cust_record[0]
                    
                    # print("row",i,cust_record['organizationName'])
                    if cust_record['organizationName']:
                        customer_org_query = "SELECT * FROM customer_orgnazation WHERE Organisation_id = %s"
                        cursor.execute(customer_org_query, (cust_record['organizationName'],))
                        org_record = cursor.fetchall()
                        cust_record['organizationName'] = org_record[0]

                    customer_data.append(cust_record)

                

                # Fetching template records as per custoemr group
                template_select_Query = f"SELECT background_video FROM vdo_template WHERE vdo_template_id = {input_template_id}"
                cursor.execute(template_select_Query)
                template_records = cursor.fetchall()
                # print("template recordsss  ",template_records)

                background_video = template_records[0]
                # print(background_video)
                background_select_Query = f"SELECT * FROM background_video WHERE id = {background_video['background_video']}"
                cursor.execute(background_select_Query)
                background_records = cursor.fetchall()
                background_records=background_records[0]
                # print("background recordsss  ",background_records)

                    # print("customer_data",customer_data)
                
                background_type_select_Query = f"SELECT name FROM video_referral_type WHERE id = {background_records['type']}"
                cursor.execute(background_type_select_Query)
                background_type_records = cursor.fetchall()
                background_records['type']=background_type_records[0]
                # print("background type recordsss  ",background_type_records)


                # base_video_data['background'] = background_records


                #Template Details
                basevideo_select_Query = f"SELECT * FROM base_video_refferal WHERE video_template = {input_template_id}"
                cursor.execute(basevideo_select_Query)
                base_video_records = cursor.fetchall()
                base_video_columns = [column['Field'] for column in cursor.fetchall()]
                base_video_records = base_video_records
                print("base video recordsss  ",base_video_records)

                for i,record in enumerate(base_video_records):
                    data = {}
                    # print("\n i",record)
                    for key,value in record.items():
                        data[key] = value

                    # print("\n ",i, data)
                    # print(data['position_composition_id'])

                    if record['website_details']:
                        website_query = f"SELECT * FROM website_details WHERE id = {record['website_details']}"
                        cursor.execute(website_query)
                        website_data = cursor.fetchall()
                        data['website_details'] = website_data
                    
                    if data['position_composition_id']:
                        position_composition_query = f"SELECT * FROM position_composition WHERE id = {data['position_composition_id']}"
                        cursor.execute(position_composition_query)
                        position_composition_data = cursor.fetchall()
                        position_1 = position_composition_data[0]['position_Position_id']
                        position_2 = int(position_composition_data[0]['position_composition_id'])
                        data['position_composition_id'] = [position_1,position_2]
                    

                    if data['audio_template']:
                        audio_query = f"SELECT * FROM base_audio_refferal WHERE id = {data['audio_template']}"
                        cursor.execute(audio_query)
                        audio_data = cursor.fetchall()
                        data['audio_template'] = audio_data[0]
                        if data['audio_template']['Description']:
                            data['audio_template']['Description'] = re.sub('<[^>]*>', '', data['audio_template']['Description'])

                        if data['audio_template']['media_type']:
                            audio_query = f"SELECT name FROM audio_referral_type WHERE id = {data['audio_template']['media_type']}"
                            cursor.execute(audio_query)
                            audio_data = cursor.fetchall()
                            data['audio_template']['media_type'] = audio_data[0]

                    if data['type']:
                        media_type_select_Query = f"SELECT name FROM video_referral_type WHERE id = {data['type']}"
                        cursor.execute(media_type_select_Query)
                        type_record = cursor.fetchall()
                        data['type']=type_record[0]
                    #     print("background type recordsss  ",type_record)

                    # print("\n data['Tag_personalised']",data['Tag_personalised'])
                    # print("\n",customer_data)

                    if data['Tag_personalised']:
                        for customer in customer_data:
                            mytagvalues=[]
                            cust_id = customer['customer_id']
                            tag_value_query = f"SELECT * FROM tagged_values WHERE tag_id={data['Tag_personalised']}"
                            cursor.execute(tag_value_query)
                            tag_value_data = cursor.fetchall()
                            tag_value_data= tag_value_data
                            for i in tag_value_data:
                                    if cust_id == i['customer_customer_id']:
                                        mytagvalues.append(i)
                                        
  
                            # print("\ntag_value_data",mytagvalues)
                            # print("\ntag_value_data", mytagvalues)
                            customer['base_video'] = data.copy()
                            customer['base_video']['Tag_personalised'] = mytagvalues
                            
                            # print(customer) 
                            personalized_audio = generate_personalized_audio(customer)
                            # print("\npersonalized_audio",personalized_audio)
                            customer['personalized_audio_script'] = personalized_audio


                    # base_video_data.append(data)

            
                data = {
                    'customers':customer_data,
                    # 'base_video':base_video_data,
                    'background':background_records
                }

            return Response({"status":status.HTTP_200_OK,'Response':data},status=status.HTTP_200_OK)

        except Error as e:
            print("Error while connecting to MySQL", e)
            return Response({"status":status.HTTP_400_BAD_REQUEST,'Response':f"Can't connect to Database {str(e)}"},status=status.HTTP_400_BAD_REQUEST)
        
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'db' in locals() and db.is_connected():
                db.close()
                print("MySQL connection is closed")


#Function for Personalized audio script for customer
def generate_personalized_audio(customer_details):
    openai.api_key = "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"

    customer_name = customer_details['prospectName']
    org_name = customer_details['organizationName']['organizationName']

    prompt = f"Generate a personalized audio script for customer. customer name is {customer_name} and customer organization name is {org_name}"
    messages = [
        {"role": "system", "content": "Every audio script should be a concise paragraph without music effects or specific mentions. Avoid unnecessary elements like newline characters or explicit indications of the script's end. Focus on delivering a smooth and coherent message about the organization, its products, and services."},
        {"role": "user", "content": prompt},
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    assistant_reply = response['choices'][0]['message']['content']

    return assistant_reply


def retrive_customer_details(video_template_id,customer_group_id):
    video_position = f"{base_url}/Get_customers/"
    
    data={
        "video_template_id":video_template_id,
        "customer_group_id":customer_group_id
    }
    
    response=requests.post(video_position ,json=data)
    print("response ????????????",response)
    
    if response.status_code==200:
        customer_data=response.json()
        
        return customer_data
    else:
        return f"Error occurred while fetching data. Status code: {response.status_code}"
    


def calculate_start_time(sequence_list, duration_list):
    sequence_start_times = {}
    start_times = []

    for i, sequence in enumerate(sequence_list):
        if sequence not in sequence_start_times:
            sequence_start_times[sequence] = 0

        start_time = sequence_start_times[sequence]
        sequence_start_times[sequence] += duration_list[i]

        start_times.append(start_time)

    return start_times




def adjust_start_times(video_durations, sorted_videos):
        adjusted_start_times = [0]

        for i in range(1, len(sorted_videos)):
            if sorted_videos[i]["sequence"] == sorted_videos[i-1]["sequence"]:
                adjusted_start_times.append(adjusted_start_times[-1])
            else:
                adjusted_start_times.append(adjusted_start_times[-1] + video_durations[i-1])
        return adjusted_start_times



def set_media_position(W, H, user):
        pos_list = []
        width = 100
        height = 100
        if len(user) == 1:
            width = W/2
            height = H/2
        elif len(user)>1:
            width=W
            height = H
            for i in range(len(user)):
                width = width/2
                height = height/2
        
        for i in range(len(user)):
            pos = None  
            print(i)
            if i == 0:
                if int(user[i])  == 0:
                    pos = (W/4, H/4)
                elif int(user[i])  == 1:
                    pos = (W/2, 0) 
                elif int(user[i])  == 2:
                    pos = (W/2, H/2)
                elif int(user[i])  == 3:
                    pos = (0, H/2)
                elif int(user[i])  == 4:
                    pos = (0, 0)
                elif int(user[i])  == 5:
                    pos = (W, H) 
            else:
                W = W/2
                H = H/2
                if int(user[i])  == 0:
                    pos = (W/4, H/4)
                elif int(user[i])  == 1:
                    pos = (W/2, 0)
                elif int(user[i])  == 2:
                    pos = (W/2, H/2)
                elif int(user[i])  == 3:
                    pos = (0, H/2)
                elif int(user[i])  == 4:
                    pos = (0, 0)
                elif int(user[i])  == 5:
                    pos = (W, H)
            
            pos_list.append(pos)
        
        return pos_list, width,height



class VideoCreationWithPostion(APIView):
    
    @swagger_auto_schema(
        operation_summary="Multiple Video Creation API",
        operation_description="This API requires a userid, target organization organizationID, and templateId of the template",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[""],
            properties={
                "video_template_id":openapi.Schema(type=openapi.TYPE_INTEGER, description="user id"),
            }
        )
    )
    
    
    def post(self, request):
        # try:
            time_list={}
            t1 = time.perf_counter()
            video_template_id = request.data['video_template_id']
            print("video_template_id",video_template_id)
            try:
                video_data = retrivedata(video_template_id)
            except Exception as e:
                print(str(e))
            print(">>>    >>>>>>>>>>>>>>", video_data)
            
            
            base_video_data = video_data['Response']['base_videos']
            personalised_data = video_data['Response']['personalised']
            background_data=video_data['Response']['background_video_data']
            
            print(".................................",background_data)
            
            print(base_video_data)


            clips = []
            audio_clips = []
            audio_clip_duration=[]

            # user = data['User']
            # customerName = user['customerName']
            # customerCompany = user['customerCompany']
            
            
                       
            # mediaData = data['media']
            # mediaSorted = sorted(mediaData, key= lambda x:x['sequence'])
            
            sequence_list=[]
            audio_start_duration=[]
            
            current_start_time = 0
            current_sequence_duration = 0
            
            total_cut_duration=0
            # videos_sorted = sorted(base_video_data, key=lambda x: x['sequence'])
            
            videos_sorted = sorted(base_video_data, key=lambda x: x['sequence'] if x['sequence'] is not None else 1)



 
            
            print("\n>>>>>>>>>>>>>>>videos_sorted.",videos_sorted)
            
            sorted_video_paths = [video["media"] for video in videos_sorted if "media" in video]
            videos = [VideoFileClip(video_path) for video_path in sorted_video_paths if video_path]
            print("\n++++++++++++++videos.", videos)
            video_durations = [video.duration for video in videos]
            adjusted_start_times = adjust_start_times(video_durations, videos_sorted)

            print(">>>>>>>>>>>>>>adjusted_start_times : ", adjusted_start_times)
            
            for i,screen in enumerate(videos_sorted):

                media, type,title, audioScript, audioURL, audioType, position, sequence, websiteDetails=(
                    screen['media'],
                    screen['type']['name'],
                    screen['title'],
                    screen['audio_template']['Description'],
                    screen['audio_template']['Audio_url'],
                    screen['audio_template']['media_type']['name'],
                    screen['position_composition_id'],
                    screen['sequence'],
                    screen['website_details'],
                )
                print("Positionnnnnn>>>", position)
                print("Type>>>>>>>>>>",type)
                
                sequence_list.append(sequence)                
                
                if personalised_data:
                    web_redirection = len(personalised_data)
                    print("in personalized data")
                    for data in personalised_data:
                        personalized_clips =[]
                        personalised_audioURL, personalised_audioScript, personalised_audioType, personalised_position, personalised_sequence, Tag_personalised=(
                        data['audio_template']['Audio_url'],
                        data['audio_template']['Description'],
                        data['audio_template']['media_type']['name'],
                        data['position_composition_id'],
                        data['sequence'],
                        data['Tag_personalised']['customers'],
                        )
                        
                        if personalised_audioType == 'audio_script':
                            print("AudioScript>>>>>>>>>>",personalised_audioScript)
                            audio = text_to_speech(personalised_audioScript, 'position_audio', request)
                            audio = ur.urlopen(audio)
                            print("herereereref")
                            file = f"position_audio_{timezone.now().strftime('%Y%m%d%H%M')}.wav"
                        
                        elif personalised_audioType == 'audio_url':
                            res = requests.get(personalised_audioURL)
                            bytecontent = BytesIO(res.content)
                            
                            recognizer = sr.Recognizer()
                            with sr.AudioFile(bytecontent) as source:
                                recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                                audio = recognizer.listen(source)
                                audioText = recognizer.recognize_google(audio)
                            
                            audio = text_to_speech(audioText, "audio", request)
                            audio = ur.urlopen(audio)
                            file = f"audio_{RandomNumber()}.wav" 
                        
                        with open(file, 'wb') as f:
                            f.write(audio.read())
                            "hereee"
                        
                        audio_clip = AudioFileClip(filename=file)
                        audio_clips.append(audio_clip) 
                        audio_duration = audio_clip.duration
                        audio_duration_seconds = int(audio_duration)
                        audio_clip_duration.append(audio_duration_seconds)
                        audio_start_duration.append(audio_duration_seconds)
                        
                        print("personalised position", personalised_position)
                        personalised_position, width,height = set_media_position(W=1920,H=1080, user=personalised_position)
                        sum_tuple = tuple(sum(x) for x in zip(*personalised_position))
                        x,y = int(sum_tuple[0]), int(sum_tuple[1])
                        
                        os.remove(file)
                        output_folder = f'static/web/'
                        videofileName = f'static/videos/position_video_{RandomNumber}.mp4'
                        redirections = len(Tag_personalised['tag_values'])
                        
                        
                        
                        for tag in Tag_personalised['tag_values']:
                            url = tag['value']
                            # perso_scroll = tag['scroll']
                            # websearch = tag['websearch']
                            
                            perso_scroll = tag['scroll'] == 'T'
                            websearch = tag['websearch'] == 'T'
                            openbrowser_and_capture_json(website=url, output_folder=output_folder, redirection_count=web_redirection, scrolling=perso_scroll, google_search_c=websearch)
                        
                            personalized_clip = make_video_json(output_folder=output_folder, output_video_file=videofileName,time_frame=audio_duration_seconds)
                            personalized_clips.append(personalized_clip)
                            
                        
                        
                        
                        clip = concatenate_videoclips(personalized_clips)            
                        
                        if i == 0:
                            start_time = 0
                    
                        elif adjusted_start_times[i] != 0:
                            adjusted_start_times[i] =  max(adjusted_start_times[i], audio_clip_duration[i])
                            total_cut_duration+=max(adjusted_start_times[i], audio_clip_duration[i])
                            
                            
                        print("Start times::::::", start_time)     
                        clip = clip.set_audio(audio_clip).set_position((x, y)).set_start(adjusted_start_times[i])
                        clip = clip.resize(width=width, height=height) 
                        clips.append(clip)   
                        
                    time_list['for_crm']= time.perf_counter()-t1
                            
                if type == 'URL':
                    web_clips =[]
                    # positions.append(position)
                    # print(positions,"positionsssssssss")
                    
                    redirection_count = len(websiteDetails)
                    
                    if audioType == 'audio_script':
                        print("AudioScript>>>>>>>>>>",audioScript)
                        audio = text_to_speech(audioScript, 'position_audio', request)
                        audio = ur.urlopen(audio)
                        print("herereereref")
                        file = f"position_audio_{timezone.now().strftime('%Y%m%d%H%M')}.wav"
                    
                    elif audioType == 'audio_url':
                        res = requests.get(audioURL)
                        bytecontent = BytesIO(res.content)
                        
                        recognizer = sr.Recognizer()
                        with sr.AudioFile(bytecontent) as source:
                            recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                            audio = recognizer.listen(source)
                            audioText = recognizer.recognize_google(audio)
                        
                        audio = text_to_speech(audioText, "audio", request)
                        audio = ur.urlopen(audio)
                        file = f"audio_{RandomNumber()}.wav" 
                    
                    with open(file, 'wb') as f:
                        f.write(audio.read())
                        "hereee"
                    
                    audio_clip = AudioFileClip(filename=file)
                    audio_clips.append(audio_clip) 
                    audio_duration = audio_clip.duration
                    audio_duration_seconds = int(audio_duration)
                    audio_clip_duration.append(audio_duration_seconds)
                    
                    
                    position, width,height = set_media_position(W=1920,H=1080, user=position)
                    sum_tuple = tuple(sum(x) for x in zip(*position))
                    x,y = int(sum_tuple[0]), int(sum_tuple[1])
                    
                    os.remove(file)
                    output_folder = f'static/web/'
                    videofileName = f'static/videos/jagga_video.mp4'
                    
                    for website in websiteDetails:
                        scroll = None
                        search = None
                        if website['scroll'] == 'T':
                            scroll = True
                        else:
                            scroll =False    
                        print(website['websearch'])
                        if website['websearch'] == 'T':
                            search = True
                        else:
                            search = False    
                        openbrowser_and_capture_json(website=website['url'], output_folder=output_folder, redirection_count=redirection_count, scrolling=scroll, google_search_c=search)
                        
                        web_clip = make_video_json(output_folder=output_folder, output_video_file=videofileName,time_frame=audio_duration_seconds)
                        web_clips.append(web_clip)
                        
                    clip = concatenate_videoclips(web_clips)
                    
                    
                    if i == 0:
                        start_time = 0
                    
                    elif adjusted_start_times[i] != 0:
                        start_time =  max(adjusted_start_times[i], audio_clip_duration[i])
                        total_cut_duration+=max(adjusted_start_times[i], audio_clip_duration[i])

                     
                    # start_time = sum(audio_clip_duration[:i]) if i > 0 else 0    
                    print("Start times::::::", start_time)     
                    clip = clip.set_audio(audio_clip).set_position((x, y)).set_start(adjusted_start_times[i])
                    clip = clip.resize(width=width, height=height) 
                    clips.append(clip)
                    
                    time_list['for_url']= time.perf_counter()-t1
                        
                        
                if type == 'Image':
                    image = ur.urlopen(media)
                    img_arr = np.array(bytearray(image.read()), dtype=np.uint8)
                    img = cv2.imdecode(img_arr, cv2.IMREAD_UNCHANGED)
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    
                    if audioType == 'audio_script':
                        audio = text_to_speech(audioScript, 'position_audio', request)
                        audio = ur.urlopen(audio)
                        file = f"position_audio_{timezone.now().strftime('%Y%m%d%H%M')}.wav"
                        
                    elif audioType == 'audio_url':
                        res = requests.get(audioURL)
                        bytecontent = BytesIO(res.content)
                        
                        recognizer = sr.Recognizer()
                        with sr.AudioFile(bytecontent) as source:
                            recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                            audio = recognizer.listen(source)
                            audioText = recognizer.recognize_google(audio)
                        
                        audio = text_to_speech(audioText, "audio", request)
                        audio = ur.urlopen(audio)
                        file = f"audio_{RandomNumber()}.wav" 
                        
                    with open(file, 'wb') as f:
                        f.write(audio.read())
                            

                    audio_clip = AudioFileClip(filename=file)
                    audio_clips.append(audio_clip)
                    audio_duration = audio_clip.duration
                    audio_duration_seconds = int(audio_duration)
                    audio_clip_duration.append(audio_duration_seconds)
                    
                    os.remove(file)
                    
                    # positions = position.split(',')
                    position, width,height = set_media_position(W=1920,H=1080, user=position)
                    sum_tuple = tuple(sum(x) for x in zip(*position))
                    x,y = int(sum_tuple[0]), int(sum_tuple[1])
                    
                    clip = ImageClip(img_rgb).set_duration(audio_duration_seconds)
                    # start_time = sum(audio_clip_duration[:i]) if i > 0 else 0
                    # ! commented code for sequencing of multi overlay media:::::::: NOT WORKING 
                    
                 
                
                            
                    
                    
                    # if i == 0 or sequence != mediaSorted[i - 1]['sequence']:
                    #     current_start_time += current_sequence_duration  # Update start time
                    #     current_sequence_duration = 0 
                    # if sequence == mediaSorted[i - 1]['sequence']:
                    #     current_sequence_duration = max(current_sequence_duration, audio_clip_duration[i])  # Update sequence duration

                    #     # Match previous video duration to the maximum (only for non-first videos in a sequence):
                    #     if i > 0:  # Ensure first video in a sequence isn't modified
                    #         audio_clip_duration[i - 1] = current_sequence_duration
                    
                    # if sequence ==

                    # if i == 0:
                    #     start_time = 0
                
                    if adjusted_start_times[i] != 0:
                        adjusted_start_times[i] =  max(adjusted_start_times[i], audio_clip_duration[i])
                        total_cut_duration+=max(adjusted_start_times[i], audio_clip_duration[i])
                            
                    # start_time = sum(audio_clip_duration[:i]) if i > 0 else 0         
                    clip = clip.set_audio(audio_clip).set_position((x, y)).set_start(adjusted_start_times[i])
                    
                    
                    
                    
                    
                    # if i > 0 and sequence != mediaSorted[i - 1]['sequence']:
                    #     audio_clip_duration.pop()
                        
                        
                    clip = clip.resize(width=width, height=height) 
                    clips.append(clip)
                    
                    time_list['for_image']= time.perf_counter()-t1

                
                elif type == 'Video':
                    if audioType == 'audio_script':
                        audio = text_to_speech(audioScript, 'position_audio', request)
                        audio = ur.urlopen(audio)
                        file = f"position_audio_{timezone.now().strftime('%Y%m%d%H%M')}.wav"                    
                        
                    elif audioType == 'audio_url':
                        res = requests.get(audioURL)
                        bytecontent = BytesIO(res.content)
                        
                        recognizer = sr.Recognizer()
                        with sr.AudioFile(bytecontent) as source:
                            recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                            audio = recognizer.listen(source)
                            audioText = recognizer.recognize_google(audio)
                        
                        audio = text_to_speech(audioText, "audio", request)
                        audio = ur.urlopen(audio)
                        file = f"audio_{RandomNumber()}.wav" 
                        
                    with open(file, 'wb') as f:
                        f.write(audio.read())
                        print("Length of written audio file:", os.path.getsize(file))

                    audio_clip = AudioFileClip(filename=file)
                    audio_clips.append(audio_clip)
                    audio_duration = audio_clip.duration
                    audio_duration_seconds = int(audio_duration)
                    audio_clip_duration.append(audio_duration_seconds)
                    
                    os.remove(file)
                    # position = str(position)
                    # positions = position.split(',')
                    print("position", position[0])
                    video_clip = VideoFileClip(media)
                    position, width,height = set_media_position(W=1920,H=1080, user=position)
                    
                    sum_tuple = tuple(sum(x) for x in zip(*position))
                    x,y = int(sum_tuple[0]), int(sum_tuple[1])
                    
                    
                    # ! commented code for sequencing of multi overlay media:::::::: NOT WORKING
                    
                    # if i == 0 or sequence != mediaSorted[i - 1]['sequence']:
                    #     current_start_time += current_sequence_duration  # Update start time
                    #     current_sequence_duration = 0 
                    # if sequence == mediaSorted[i - 1]['sequence']:
                    #     current_sequence_duration = max(current_sequence_duration, audio_clip_duration[i])  # Update sequence duration

                    #     # Match previous video duration to the maximum (only for non-first videos in a sequence):
                    #     if i > 0:  # Ensure first video in a sequence isn't modified
                    #         audio_clip_duration[i - 1] = current_sequence_duration
                    
                    # if i == 0:
                        # start_time = 0
                
                    if adjusted_start_times[i] != 0:
                        adjusted_start_times[i] =  max(adjusted_start_times[i], audio_clip_duration[i])  
                        total_cut_duration+=max(adjusted_start_times[i], audio_clip_duration[i])
                            
                    # start_time = sum(audio_clip_duration[:i]) if i > 0 else 0        
                    video = video_clip.set_audio(audio_clip).set_position((x, y)).set_start(adjusted_start_times[i])
                    
                    # if i > 0 and sequence != mediaSorted[i - 1]['sequence']:
                    #     audio_clip_duration.pop()
                    
                    # video=video.set_start(start_time)
                    video=video.resize(width=width,height=height)
                    video= video.subclip(0,audio_duration_seconds)
                    clips.append(video)
                    
                    time_list['for_video']= time.perf_counter()-t1
                    

            video_folder = os.path.join(os.getcwd(), 'static/videos')
            os.makedirs(video_folder, exist_ok=True)
            current_datetime = RandomNumber()
            video_path = os.path.join(video_folder, f'customer_{current_datetime}.mp4')


            # Load the background Image Video
            # print("bg_type>>>>>>>>>>>",background_data['type'])
            
            
            if background_data['type'] == "Image":
 
                bg_file = background_data['media']
                
                
                # print(bg_file)
                image = ur.urlopen(bg_file)
                img_arr = np.array(bytearray(image.read()), dtype=np.uint8)
                img = cv2.imdecode(img_arr, cv2.IMREAD_UNCHANGED)
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                time_abc=sum(video_durations)-total_cut_duration
                
                print("/n video duration", sum(video_durations) , "???????????? cut time",time_abc)
                background_clip = ImageClip(img_rgb).set_duration(time_abc)
                repeated_background = background_clip.resize(width=1920,height=1080)

                
            # Load the background video
            elif background_data['type'] == "Video":
                bg_file = background_data['media']

                background_clip = VideoFileClip(bg_file)
                background_clip = background_clip.without_audio()
                background_clip = background_clip.resize(width=1920, height=1080)  # Adjust the size as needed
                
                time_abc=sum(video_durations)-total_cut_duration
                
                print("/n video duration", sum(video_durations) , "???????????? cut time",time_abc)
                repeated_background = background_clip.loop(duration=time_abc)
    
            final_clip = CompositeVideoClip([repeated_background] + clips)
            time_list['for_background']= time.perf_counter()-t1

            final_clip.write_videofile(video_path, fps=24)
            static_video_url = base_url + static(os.path.join('videos', f'customer_{current_datetime}.mp4'))
            
            t2 = time.perf_counter()
            print('Time: ', t2-t1)
            time_list['final_time']= time.perf_counter()-t1
            print(time_list)
            return Response({'url': static_video_url, "Status": status.HTTP_200_OK},status.HTTP_200_OK)
     
        # except Exception as e:
        #     return Response({"Error": str(e), "Status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status.HTTP_500_INTERNAL_SERVER_ERROR)








class Videos_for_Customer(APIView):
    @swagger_auto_schema(
        operation_summary="Multiple Video Creation API",
        tags=['Video creation'],
        operation_description="This API requires a userid, target organization organizationID, and templateId of the template",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[""],
            properties={
                "video_template_id":openapi.Schema(type=openapi.TYPE_INTEGER, description="video template id"),
                "customer_group_id":openapi.Schema(type=openapi.TYPE_INTEGER, description="customer group id"),
            }
        )
    )
    def post(self,request):
        try:
            video_template_id = request.data['video_template_id']
            customer_group_id = request.data['customer_group_id']
            
            try:
                api_data=retrive_customer_details(video_template_id,customer_group_id)
            except Exception as e:
                print(e)
                return Response({"message":"could not receive data","status":status.HTTP_400_BAD_REQUEST},status.HTTP_400_BAD_REQUEST)
            
            
            background_detail=api_data['Response']['background']
            
            customer_list = []
            for customer in api_data['Response']['customers']:
                video_clips=[]
                customer_details = {
                    "customer_id": customer.get("customer_id"),
                    "organizationName": customer.get("organizationName"),
                    "prospectName": customer.get("prospectName"),
                    "emailAddress": customer.get("emailAddress"),
                    "websiteUrl1": customer.get("websiteUrl1"),
                    "websiteUrl2": customer.get("websiteUrl2"),
                    "websiteUrl3": customer.get("websiteUrl3"),
                    "personalized_audio_script":customer.get("personalized_audio_script")
                }
                
                base_video_details = customer.get("base_video", {})
                if base_video_details:
                    customer_details["base_video"] = {
                        "id": base_video_details.get("id"),
                        "media": base_video_details.get("media"),
                        "type": base_video_details.get("type", {}).get("name"),
                        "title": base_video_details.get("title"),
                        "audio_description": base_video_details.get("audio_template", {}).get("Description"),
                        "audio_url": base_video_details.get("audio_template", {}).get("Audio_url"),
                        "audio_type": base_video_details.get("audio_template", {}).get("media_type", {}).get("name"),
                        "position_composition_id": base_video_details.get("position_composition_id"),
                        "sequence": base_video_details.get("sequence"),
                        "website_details": base_video_details.get("website_details",[]),
                        "Tag_personalised": base_video_details.get("Tag_personalised", []),
                    }

                customer_list.append(customer_details)
                
            print("dsfiofjklj------------------",customer_list)
            
            audio_start_duration = []
            clips = []
            audio_clips = []
            audio_clip_duration = []

            video_response=[]
                
                
            for i, customer_details in enumerate(customer_list):
                x = 1
                print(f"Customer {i + 1} Details:")
                video_clips=[]
                web_clips =[]
                
                
                
                personalized_audio_script=customer_details.get("personalized_audio_script")
                if personalized_audio_script:
                    print("Audio Type: Audio Script")
                    audio_description = personalized_audio_script
                    audio = text_to_speech(audio_description, 'position_audio', request)
                    audio = ur.urlopen(audio)
                    
                    file = f"position_audio_{timezone.now().strftime('%Y%m%d%H%M')}.wav"
                    
                    with open(file, 'wb') as f:
                        f.write(audio.read())
                    
                    audio_clip = AudioFileClip(filename=file)
                    audio_clips.append(audio_clip)
                    audio_duration = audio_clip.duration
                    audio_duration_seconds = int(audio_duration)
                    audio_clip_duration.append(audio_duration_seconds)
                    audio_start_duration.append(audio_duration_seconds)
                    
                
                output_folder = f'static/web/'
                videofileName = f'static/videos/jagga_video.mp4'
                website_urls = [
                    customer_details.get("websiteUrl1"),
                    customer_details.get("websiteUrl2"),
                    customer_details.get("websiteUrl3"),
                ]
                for url in website_urls:
                    if url:
                        print(f"Processing website URL: {url}")
                        openbrowser_and_capture_json(url, output_folder, x, True, True)  
                        
                        web_clip = make_video_json(output_folder=output_folder, output_video_file=videofileName,time_frame=audio_duration_seconds)
                        web_clips.append(web_clip)
                        
                        video_clips.append(web_clip)
                        
                        print("Processing completed for website URL.\n")
                        x += 1
                
                for key, value in customer_details.items():
                    
                    print(customer_details.items())
                    if key == "base_video":
                        media_type = value.get("type")
                        if media_type:
                            if media_type == "URL":
                                website_details_list = value.get("website_details", [])  # Get the list of website details
                                
                                for website in website_details_list:
                                    website_url = website.get("url")
                                    scroll = website.get("scroll")
                                    web_search = website.get("websearch")
                                    if scroll == 'T':
                                        scroll = True
                                    else:
                                        scroll =False    
                                    if web_search == 'T':
                                        search = True
                                    else:
                                        search = False    
                                    openbrowser_and_capture_json(website=website_url, output_folder=output_folder, redirection_count=x, scrolling=scroll, google_search_c=search)
                                    web_clip = make_video_json(output_folder=output_folder, output_video_file=videofileName,time_frame=10)
                                    web_clips.append(web_clip)
                                    video_clips.append(web_clips)
                                    
                                    x+=1
                                    
                            elif media_type == "Video":
                                video_file_path = value.get("media")
                                clip = VideoFileClip(video_file_path)

                                video_folder = os.path.join(os.getcwd(), 'static/videos')
                                os.makedirs(video_folder, exist_ok=True)
                                current_datetime = RandomNumber()
                                video_path = os.path.join(video_folder, f'customer_{current_datetime}.mp4')

                                video_clips.append(clip)
            
                            elif media_type == "Image":
                                print("Media Type: Image")
                                image_file_path = value.get("media")
                                image = ur.urlopen(image_file_path)
                                img_arr = np.array(bytearray(image.read()), dtype=np.uint8)
                                img = cv2.imdecode(img_arr, cv2.IMREAD_UNCHANGED)
                                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                                
                            
                                clip = ImageClip(img_rgb).set_duration(audio_duration_seconds)
                            
                                clips.append(clip)
                                
                                            
                                            
                            elif media_type == "personalised":
                                personalized_tags = value.get("Tag_personalised", [])
                                for tag in personalized_tags:
                                    personalized_url = tag.get("value")
                                    scroll = tag.get("scroll") == "T"
                                    if scroll=='T':
                                        scroll=True
                                    web_search = tag.get("websearch") == "T"
                                    if web_search=='T':
                                        web_search=True
                                    
                                    print(f"Processing personalized URL: {personalized_url}")
                                    openbrowser_and_capture_json(website=personalized_url, output_folder=x, redirection_count=x, scrolling=scroll, google_search_c=web_search)
                                    x+=1
                                    web_clip = make_video_json(output_folder=output_folder, output_video_file=videofileName,time_frame=audio_duration_seconds)
                                    web_clips.append(web_clip)
                                    video_clips.append(web_clip)
                                    print("Processing completed for personalized URL.\n")
                                    x += 1
                                
                            else:
                                print("Media Type: Unknown")

                        audio_type = value.get("audio_type")
                        # if audio_type:
                        #     if audio_type == "audio_script":
                        #         print("Audio Type: Audio Script")
                        #         audio_description = value.get("audio_description")
                        #         audio = text_to_speech(audio_description, 'position_audio', request)
                        #         audio = ur.urlopen(audio)
                        #         file = f"position_audio_{timezone.now().strftime('%Y%m%d%H%M')}.wav"
                        #         with open(file, 'wb') as f:
                        #             f.write(audio.read())
                        #         audio_clip = AudioFileClip(filename=file)
                        #         audio_clips.append(audio_clip)
                        #         audio_duration = audio_clip.duration
                        #         audio_duration_seconds = int(audio_duration)
                        #         audio_clip_duration.append(audio_duration_seconds)
                        #         audio_start_duration.append(audio_duration_seconds)
                                
                        #     elif audio_type == "audio_url":
                        #         print("Audio Type: Audio URL")
                        #         audio_url = value.get("audio_url")
                        #         res = requests.get(audio_url)
                        #         bytecontent = BytesIO(res.content)
                                
                        #         recognizer = sr.Recognizer()
                        #         with sr.AudioFile(bytecontent) as source:
                        #             recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                        #             audio = recognizer.listen(source)
                        #             audioText = recognizer.recognize_google(audio)
                                
                        #         audio = text_to_speech(audioText, "audio", request)
                        #         audio = ur.urlopen(audio)
                        #         file = f"audio_{RandomNumber()}.wav"
                        #         with open(file, 'wb') as f:
                        #             f.write(audio.read())
                        #         audio_clip = AudioFileClip(filename=file)
                        #         audio_clips.append(audio_clip)
                        #         audio_duration = audio_clip.duration
                        #         audio_duration_seconds = int(audio_duration)
                        #         audio_clip_duration.append(audio_duration_seconds)

    
                print('here for making video   ............')    
                print(video_clips)  
                
                flattened_video_clips = [clip for sublist in video_clips for clip in sublist]

                concatenated_clips = concatenate_videoclips(video_clips , method="compose")
                video_path = f'static/videos/customer_{i + 1}.mp4'
                concatenated_clips.write_videofile(video_path, codec='libx264', fps=24)
                    
                                
                try:
                    print("Position....")
                    position_composition_id = base_video_details.get("position_composition_id")

                    # Call set_media_position with position_composition_id
                    position, width, height = set_media_position(W=1920, H=1080, user=position_composition_id)

                    sum_tuple = tuple(sum(x) for x in zip(*position))
                    x, y = int(sum_tuple[0]), int(sum_tuple[1])
                    
                    concatenated_clips = concatenated_clips.set_audio(audio_clip)
                    concatenated_clips = concatenated_clips.set_position((x, y))
                    concatenated_clips = concatenated_clips.resize(width=width, height=height)
                    concatenated_clips = concatenated_clips.set_duration(audio_duration_seconds)

                    
                    print('concatenated completed fully ')


                    # repeated_background = None
                    print(background_detail['type'])
                    
                    
                    if background_detail['type']['name'] == 'Image':
                        bg_file = background_detail['media']

                        image = ur.urlopen(bg_file)
                        img_arr = np.array(bytearray(image.read()), dtype=np.uint8)
                        img = cv2.imdecode(img_arr, cv2.IMREAD_UNCHANGED)
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                        background_clip = ImageClip(img_rgb).set_duration(audio_duration_seconds)
                        repeated_background = background_clip.resize(width=1920, height=1080)

                        print('started making final video')
                        # Create final_clip using CompositeVideoClip
                        final_clip = CompositeVideoClip([repeated_background, concatenated_clips])
                        
                        video_path = f'static/videos/final_video_customer_{i + 1}.mp4'
                        
                        final_clip.write_videofile(video_path, fps=24)
                        static_video_url = base_url + static(os.path.join('videos', f'customer_{i + 1}.mp4'))
                        video_response.append(static_video_url)
                        
                    elif background_detail['type']['name'] == 'Video':
                        bg_file = background_detail['media']

                        background_clip = VideoFileClip(bg_file)
                        background_clip = background_clip.without_audio()
                        background_clip = background_clip.resize(width=1920, height=1080)  # Adjust the size as needed

                        # Make sure repeated_background has the same duration as concatenated_clips
                        repeated_background = background_clip.loop(duration=audio_duration_seconds)
                        print('started making final video')
                        final_clip = CompositeVideoClip([repeated_background, concatenated_clips])
                        
                        video_path = f'static/videos/final_video_customer_{i + 1}.mp4'
                        
                        final_clip.write_videofile(video_path, fps=24)
                        static_video_url = base_url + static(os.path.join('videos', f'customer_{i + 1}.mp4'))
                        video_response.append(static_video_url)
                    
                    print("\n")
                except Exception as e:
                    print(str(e))
                    
                        

            
            return Response({"message":"success","video_data":video_response},status.HTTP_200_OK)
        except Exception as e :
            print(str(e))
            return Response({"Message":"error occoured","error discription":str(e),"status":status.HTTP_500_INTERNAL_SERVER_ERROR},status.HTTP_500_INTERNAL_SERVER_ERROR)









# new code

def retrive_customer_details2(video_template_id,customer_group_id):
    video_position = f"{base_url}/Get_customers2/"
    
    data={
        "video_template_id":video_template_id,
        "customer_group_id":customer_group_id
    }
    
    response=requests.post(video_position ,json=data)
    print("response ????????????",response)
    
    if response.status_code==200:
        customer_data=response.json()
        
        return customer_data
    else:
        return f"Error occurred while fetching data. Status code: {response.status_code}"
    



class Get_customers2(APIView):
    @swagger_auto_schema(
        operation_summary="Multiple Video Creation API",
        tags=['MySQL'],
        operation_description="This API requires a userid, target organization organizationID, and templateId of the template",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[""],
            properties={
                "video_template_id":openapi.Schema(type=openapi.TYPE_INTEGER, description="video template id"),
                "customer_group_id":openapi.Schema(type=openapi.TYPE_INTEGER, description="customer group id"),
            }
        )
    )
    
    def post(self,request):
        input_template_id = request.data['video_template_id']
        input_customer_group_id = request.data['customer_group_id']

        customer_data = []
        base_video_data =[]
        data = {}
        mytagvalues = []
        customer_videos = []
        
        try:
            db = con.connect(host='172.16.2.45',user='adminscott',password='Mobiloitte@1',database='aivdohvov02')
            print(db)
            if db.is_connected():
                db_Info = db.get_server_info()
                print("Connected to MySQL Server version ", db_Info)

                # Fetching column names
                cursor = db.cursor(dictionary=True)

                # Fetching customer records as per custoemr group
                customer_select_Query = f"SELECT customer_customer FROM customer_group_has_customer WHERE customer_group = '{input_customer_group_id}'"

                cursor.execute(customer_select_Query)
                customer_records = cursor.fetchall()
                # print("recordsss  ",customer_records)
                for i,row in enumerate(customer_records):
                    data = {}
                    cust_record = None
                    # customer_id = None
                    print("\n getting row",i)
                    # print("row",row)

                    customer_id = row['customer_customer']
                    if customer_id:
                        customer_query = "SELECT * FROM customer WHERE customer_id = %s"
                        cursor.execute(customer_query, (customer_id,))
                        cust_record = cursor.fetchall()
                        cust_record = cust_record[0]
                    
                    print("row",i,cust_record['organizationName'])
                    if cust_record['organizationName']:
                        customer_org_query = "SELECT * FROM customer_orgnazation WHERE Organisation_id = %s"
                        cursor.execute(customer_org_query, (cust_record['organizationName'],))
                        org_record = cursor.fetchall()
                        cust_record['organizationName'] = org_record[0]

                    customer_data.append(cust_record)

                # Fetching template records as per custoemr group
                template_select_Query = f"SELECT background_video FROM vdo_template WHERE vdo_template_id = {input_template_id}"
                cursor.execute(template_select_Query)
                template_records = cursor.fetchall()
                # print("template recordsss  ",template_records)

                background_video = template_records[0]
                print(background_video)
                background_select_Query = f"SELECT * FROM background_video WHERE id = {background_video['background_video']}"
                cursor.execute(background_select_Query)
                background_records = cursor.fetchall()
                background_records=background_records[0]
                # print("background recordsss  ",background_records)

                    # print("customer_data",customer_data)
                
                background_type_select_Query = f"SELECT name FROM video_referral_type WHERE id = {background_records['type']}"
                cursor.execute(background_type_select_Query)
                background_type_records = cursor.fetchall()
                background_records['type']=background_type_records[0]
                # print("background type recordsss  ",background_type_records)


                # base_video_data['background'] = background_records


                #Template Details
                basevideo_select_Query = f"SELECT * FROM base_video_refferal WHERE video_template = {input_template_id}"
                cursor.execute(basevideo_select_Query)
                base_video_records = cursor.fetchall()
                base_video_columns = [column['Field'] for column in cursor.fetchall()]
                base_video_records = base_video_records
                # print("base video recordsss  ",base_video_records)

                # print("\nbase_video_records",base_video_records)
                # print("\n\n")
                for i,record in enumerate(base_video_records):
                    data = {}
                    customer = {}
                    print("\n i",i,record)
                    for key,value in record.items():
                        data[key] = value

                    # print("\n ",i, data)
                    # print(data['position_composition_id'])

                    if data['website_details']:
                        website_query = f"SELECT * FROM website_details WHERE id = {data['website_details']}"
                        cursor.execute(website_query)
                        website_data = cursor.fetchall()
                        data['website_details'] = website_data

                    if data['position_composition_id']:
                        position_composition_query = f"SELECT * FROM position_composition WHERE id = {data['position_composition_id']}"
                        cursor.execute(position_composition_query)
                        position_composition_data = cursor.fetchall()
                        position_1 = position_composition_data[0]['position_Position_id']
                        position_2 = int(position_composition_data[0]['position_composition_id'])
                        data['position_composition_id'] = [position_1,position_2]
                    

                    if data['audio_template']:
                        audio_query = f"SELECT * FROM base_audio_refferal WHERE id = {data['audio_template']}"
                        cursor.execute(audio_query)
                        audio_data = cursor.fetchall()
                        data['audio_template'] = audio_data[0]
                        if data['audio_template']['Description']:
                            data['audio_template']['Description'] = re.sub('<[^>]*>', '', data['audio_template']['Description'])

                        if data['audio_template']['media_type']:
                            audio_query = f"SELECT name FROM audio_referral_type WHERE id = {data['audio_template']['media_type']}"
                            cursor.execute(audio_query)
                            audio_data = cursor.fetchall()
                            data['audio_template']['media_type'] = audio_data[0]

                    if data['type']:
                        media_type_select_Query = f"SELECT name FROM video_referral_type WHERE id = {data['type']}"
                        cursor.execute(media_type_select_Query)
                        type_record = cursor.fetchall()
                        data['type']=type_record[0]
                        # print("background type recordsss  ",type_record)

                    # print("\n data['Tag_personalised']",data['Tag_personalised'])
                    # print("\n",customer_data)

                    tag_value_cust = {}
                    if data['Tag_personalised']:
                        tag_value_query = f"SELECT * FROM tagged_values WHERE tag_id={data['Tag_personalised']}"
                        cursor.execute(tag_value_query)
                        tag_value_data = cursor.fetchall()
                        data['Tag_personalised'] = tag_value_data
                        print("((((((()))))))",tag_value_data)


                    base_video_data.append(data)

                    # personalized_audio = generate_personalized_audio(customer)
                    # print("\npersonalized_audio",personalized_audio)
                    # customer['personalized_audio_script'] = personalized_audio

            result_dict = []
            print("/////////////base_video",base_video_data)
            # Iterate through customers
            for customer in customer_data:
                customer_videos=[]
                customer_id = customer["customer_id"]
                print(customer)
                
                for video in base_video_data:
                    if video['Tag_personalised']:
                        for tag_value in video['Tag_personalised']:
                            print(">>>>>>",tag_value)
                            try:
                                if int(tag_value['customer_customer_id']) == int(customer_id):
                                    temp_base_video = video
                                    temp_base_video['Tag_personalised']=tag_value
                                    customer_videos.append(temp_base_video)
                            except:
                                pass
    

                final_base_videos = customer_videos if customer_videos else None

                personalized_audio = generate_personalized_audio(customer)
                # print("\npersonalized_audio",personalized_audio)
                customer['personalized_audio_script'] = personalized_audio

                customer['base_video']=final_base_videos
                result_dict.append(customer)
                        
            data = {
                'customers':result_dict,
                # 'base_video':base_video_data,
                'background':background_records
            }

            return Response({"status":status.HTTP_200_OK,'Response':data},status=status.HTTP_200_OK)

        except Error as e:
            print("Error while connecting to MySQL", e)
            return Response({"status":status.HTTP_400_BAD_REQUEST,'Response':f"Can't connect to Database {str(e)}"},status=status.HTTP_400_BAD_REQUEST)
        
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'db' in locals() and db.is_connected():
                db.close()
                print("MySQL connection is closed")






class Videos_for_Customer2(APIView):
    vdo_not_created = []
    customer_url_list = []
    @swagger_auto_schema(
        operation_summary="Multiple Video Creation API",
        tags=['Video Creation'],
        operation_description="This API requires a userid, target organization organizationID, and templateId of the template",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[""],
            properties={
                "video_template_id":openapi.Schema(type=openapi.TYPE_INTEGER, description="video template id"),
                "customer_group_id":openapi.Schema(type=openapi.TYPE_INTEGER, description="customer group id"),
            }
        )
    )
    def post(self,request):
        # try:
            results=[]
            final_result = []
            video_template_id = request.data['video_template_id']
            customer_group_id = request.data['customer_group_id']
            vdo_not_created = []
            try:
                api_data=retrive_customer_details2(video_template_id,customer_group_id)
            except Exception as e:
                print(e)
                return Response({"message":"could not receive data","status":status.HTTP_400_BAD_REQUEST},status.HTTP_400_BAD_REQUEST)
            
            
            background_detail=api_data['Response']['background']
            print(">>>>>",background_detail)
            customer_list = []
            customer_url_list = []
            
            with concurrent.futures.ThreadPoolExecutor(len(api_data['Response']['customers'])) as executor:
                # Use executor.map to apply create_video_wrapper to each customer-background_detail pair.
                results = list(executor.map(self.create_video, api_data['Response']['customers'],  [background_detail] * len(api_data['Response']['customers']),[request] * len(api_data['Response']['customers'])))
                          
            # for customer in api_data['Response']['customers']:
                # video_clips=[]
                # customer_details = {
                #     "customer_id": customer.get("customer_id"),
                #     "organizationName": customer.get("organizationName"),
                #     "prospectName": customer.get("prospectName"),
                #     "emailAddress": customer.get("emailAddress"),
                #     "websiteUrl1": customer.get("websiteUrl1"),
                #     "websiteUrl2": customer.get("websiteUrl2"),
                #     "websiteUrl3": customer.get("websiteUrl3"),
                #     "personalized_audio_script":customer.get("personalized_audio_script")
                # }
                # time_list={}
                # t1 = time.perf_counter()

                # clips = []
                # audio_clips = []
                # audio_clip_duration=[]
                # audio_start_duration=[]
                # total_cut_duration=0
                # sequence_list=[]
                # audio_duration_seconds = 0
                # video_durations =[]
                # base_video_details = customer.get("base_video", {})
                # if base_video_details:

                #     videos_sorted = sorted(base_video_details, key=lambda x: x['sequence'] if x['sequence'] is not None else 1)

                #     print("\n>>>>>>>>>>>>>>>videos_sorted.",videos_sorted)
                #     for video in range(len(videos_sorted)):
                #         video_durations.append(20)
                    
                #     adjusted_start_times = adjust_start_times(video_durations, videos_sorted)
                        
                #     # sorted_video_paths = [video["media"] for video in videos_sorted if "media" in video]
                #     # videos = [VideoFileClip(video_path) for video_path in sorted_video_paths if video_path]
                #     # print("\n++++++++++++++videos.", videos)
                #     # if videos != []:
                #     #     video_durations = [video.duration for video in videos]
                #     # adjusted_start_times = adjust_start_times(video_durations, videos_sorted)
                #     # if videos_sorted:
                #     #     print("Length of videos_sorted:", len(videos_sorted))
                #     #     sorted_video_paths = [video["Tag_personalised"]['value'] for video in videos_sorted if "Tag_personalised" in video]
                #     #     print("Length of sorted_video_paths:", sorted_video_paths)
                        
                #     #     videos = []
                #     #     for video_path in sorted_video_paths:
                #     #         print("Current video_path:", video_path)
                #     #         if video_path:
                #     #             video = VideoFileClip(video_path)
                #     #             videos.append(video)
                                
                #     #     print("\n++++++++++++++videos.", videos)

                #     #     if videos:
                #     #         video_durations = [video.duration for video in videos]
                #     #     adjusted_start_times = adjust_start_times(video_durations, videos_sorted)
                #     # else:
                #     #     print("No base videos found.")


                #     # print(">>>>>>>>>>>>>>adjusted_start_times : ", adjusted_start_times)
                #     for i,base_video in enumerate(videos_sorted):
                #             print("baes_video.........",base_video)
                #             media, type,title, audioScript, audioURL, audioType, position, sequence, websiteDetails,Tag_personalised=(
                #                 base_video['media'],
                #                 base_video['type']['name'],
                #                 base_video['title'],
                #                 base_video['audio_template']['Description'],
                #                 base_video['audio_template']['Audio_url'],
                #                 base_video['audio_template']['media_type']['name'],
                #                 base_video['position_composition_id'],
                #                 base_video['sequence'],
                #                 base_video['website_details'],
                #                 base_video['Tag_personalised']
                #             )
                #             print("Positionnnnnn>>>", position)
                #             print("Type>>>>>>>>>>",type)

                #             sequence_list.append(sequence)

                #             if type=='personalised':
                #                 if audioType == 'audio_script':
                #                     print("AudioScript>>>>>>>>>>",audioScript)
                #                     audio = text_to_speech(audioScript, 'position_audio', request)
                #                     audio = ur.urlopen(audio)
                #                     print("herereereref")
                #                     file = f"position_audio_{timezone.now().strftime('%Y%m%d%H%M')}.wav"
                            
                #                 elif audioType == 'audio_url':
                #                     res = requests.get(audioURL)
                #                     bytecontent = BytesIO(res.content)
                                    
                #                     recognizer = sr.Recognizer()
                #                     with sr.AudioFile(bytecontent) as source:
                #                         recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                #                         audio = recognizer.listen(source)
                #                         audioText = recognizer.recognize_google(audio)
                                    
                #                     audio = text_to_speech(audioText, "audio", request)
                #                     audio = ur.urlopen(audio)
                #                     file = f"audio_{RandomNumber()}.wav" 
                                
                #                 with open(file, 'wb') as f:
                #                     f.write(audio.read())
                #                     "hereee"
                                
                #                 audio_clip = AudioFileClip(filename=file)
                #                 audio_clips.append(audio_clip) 
                #                 audio_duration = audio_clip.duration
                #                 audio_duration_seconds = int(audio_duration)
                #                 audio_clip_duration.append(audio_duration_seconds)
                #                 audio_start_duration.append(audio_duration_seconds)
                                
                #                 # print("personalised position", position)
                #                 personalised_position, width,height = set_media_position(W=1920,H=1080, user=position)
                #                 sum_tuple = tuple(sum(x) for x in zip(*personalised_position))
                #                 x,y = int(sum_tuple[0]), int(sum_tuple[1])
                                
                #                 os.remove(file)
                #                 output_folder = f'static/web/'
                #                 videofileName = f'static/videos/position_video_{RandomNumber}.mp4'
                #                 # redirections = len(Tag_personalised)

                #                 redirections = 1
                #                 url = Tag_personalised['value']
                #                 # perso_scroll = tag['scroll']
                #                 # websearch = tag['websearch']
                                
                #                 perso_scroll = Tag_personalised['scroll'] == 'T'
                #                 websearch = Tag_personalised['websearch'] == 'T'

                                
                #                 openbrowser_and_capture_json(website=url, output_folder=output_folder, redirection_count=redirections, scrolling=perso_scroll, google_search_c=websearch)

                #                 redirections+=1

                #                 clip = make_video_json(output_folder=output_folder, output_video_file=videofileName,time_frame=audio_duration_seconds)
                #                 if i == 0:
                #                     start_time = 0
                            
                #                 elif adjusted_start_times[i] != 0:
                #                     adjusted_start_times[i] =  max(adjusted_start_times[i], audio_clip_duration[i])
                #                     total_cut_duration+=max(adjusted_start_times[i], audio_clip_duration[i])
                                    
                                    
                #                 print("Start times::::::", start_time)     
                #                 clip = clip.set_audio(audio_clip).set_position((x, y)).set_start(adjusted_start_times[i])
                #                 clip = clip.resize(width=width, height=height) 
                #                 clips.append(clip)  

                #             elif type == 'URL':
                #                 web_clips =[]
                #                 # positions.append(position)
                #                 # print(positions,"positionsssssssss")
                                
                #                 redirection_count = len(websiteDetails)
                                
                #                 if audioType == 'audio_script':
                #                     print("AudioScript>>>>>>>>>>",audioScript)
                #                     audio = text_to_speech(audioScript, 'position_audio', request)
                #                     audio = ur.urlopen(audio)
                #                     print("herereereref")
                #                     file = f"position_audio_{timezone.now().strftime('%Y%m%d%H%M')}.wav"
                                
                #                 elif audioType == 'audio_url':
                #                     res = requests.get(audioURL)
                #                     bytecontent = BytesIO(res.content)
                                    
                #                     recognizer = sr.Recognizer()
                #                     with sr.AudioFile(bytecontent) as source:
                #                         recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                #                         audio = recognizer.listen(source)
                #                         audioText = recognizer.recognize_google(audio)
                                    
                #                     audio = text_to_speech(audioText, "audio", request)
                #                     audio = ur.urlopen(audio)
                #                     file = f"audio_{RandomNumber()}.wav" 
                                
                #                 with open(file, 'wb') as f:
                #                     f.write(audio.read())
                #                     "hereee"
                                
                #                 audio_clip = AudioFileClip(filename=file)
                #                 audio_clips.append(audio_clip) 
                #                 audio_duration = audio_clip.duration
                #                 audio_duration_seconds = int(audio_duration)
                #                 audio_clip_duration.append(audio_duration_seconds)
                                
                                
                #                 position, width,height = set_media_position(W=1920,H=1080, user=position)
                #                 sum_tuple = tuple(sum(x) for x in zip(*position))
                #                 x,y = int(sum_tuple[0]), int(sum_tuple[1])
                                
                #                 os.remove(file)
                #                 output_folder = f'static/web/'
                #                 videofileName = f'static/videos/jagga_video.mp4'
                                
                #                 for website in websiteDetails:
                #                     scroll = None
                #                     search = None
                #                     if website['scroll'] == 'T':
                #                         scroll = True
                #                     else:
                #                         scroll =False    
                #                     print(website['websearch'])
                #                     if website['websearch'] == 'T':
                #                         search = True
                #                     else:
                #                         search = False    
                #                     openbrowser_and_capture_json(website=website['url'], output_folder=output_folder, redirection_count=redirection_count, scrolling=scroll, google_search_c=search)
                                    
                #                     web_clip = make_video_json(output_folder=output_folder, output_video_file=videofileName,time_frame=audio_duration_seconds)
                #                     web_clips.append(web_clip)
                                    
                #                 clip = concatenate_videoclips(web_clips)
                                
                                
                #                 if i == 0:
                #                     start_time = 0
                                
                #                 elif adjusted_start_times[i] != 0:
                #                     start_time =  max(adjusted_start_times[i], audio_clip_duration[i])
                #                     total_cut_duration+=max(adjusted_start_times[i], audio_clip_duration[i])

                                
                #                 # start_time = sum(audio_clip_duration[:i]) if i > 0 else 0    
                #                 print("Start times::::::", start_time)     
                #                 clip = clip.set_audio(audio_clip).set_position((x, y)).set_start(adjusted_start_times[i])
                #                 clip = clip.resize(width=width, height=height) 
                #                 clips.append(clip)
                                
                #                 time_list['for_url']= time.perf_counter()-t1
                                    
                                    
                #             elif type == 'Image':
                #                 image = ur.urlopen(media)
                #                 img_arr = np.array(bytearray(image.read()), dtype=np.uint8)
                #                 img = cv2.imdecode(img_arr, cv2.IMREAD_UNCHANGED)
                #                 img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                                
                #                 if audioType == 'audio_script':
                #                     audio = text_to_speech(audioScript, 'position_audio', request)
                #                     audio = ur.urlopen(audio)
                #                     file = f"position_audio_{timezone.now().strftime('%Y%m%d%H%M')}.wav"
                                    
                #                 elif audioType == 'audio_url':
                #                     res = requests.get(audioURL)
                #                     bytecontent = BytesIO(res.content)
                                    
                #                     recognizer = sr.Recognizer()
                #                     with sr.AudioFile(bytecontent) as source:
                #                         recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                #                         audio = recognizer.listen(source)
                #                         audioText = recognizer.recognize_google(audio)
                                    
                #                     audio = text_to_speech(audioText, "audio", request)
                #                     audio = ur.urlopen(audio)
                #                     file = f"audio_{RandomNumber()}.wav" 
                                    
                #                 with open(file, 'wb') as f:
                #                     f.write(audio.read())
                                        

                #                 audio_clip = AudioFileClip(filename=file)
                #                 audio_clips.append(audio_clip)
                #                 audio_duration = audio_clip.duration
                #                 audio_duration_seconds = int(audio_duration)
                #                 audio_clip_duration.append(audio_duration_seconds)
                                
                #                 os.remove(file)
                                
                #                 # positions = position.split(',')
                #                 position, width,height = set_media_position(W=1920,H=1080, user=position)
                #                 sum_tuple = tuple(sum(x) for x in zip(*position))
                #                 x,y = int(sum_tuple[0]), int(sum_tuple[1])
                                
                #                 clip = ImageClip(img_rgb).set_duration(audio_duration_seconds)
                #                 # start_time = sum(audio_clip_duration[:i]) if i > 0 else 0
                #                 # ! commented code for sequencing of multi overlay media:::::::: NOT WORKING 
                                
                            
                            
                                        
                                
                                
                #                 # if i == 0 or sequence != mediaSorted[i - 1]['sequence']:
                #                 #     current_start_time += current_sequence_duration  # Update start time
                #                 #     current_sequence_duration = 0 
                #                 # if sequence == mediaSorted[i - 1]['sequence']:
                #                 #     current_sequence_duration = max(current_sequence_duration, audio_clip_duration[i])  # Update sequence duration

                #                 #     # Match previous video duration to the maximum (only for non-first videos in a sequence):
                #                 #     if i > 0:  # Ensure first video in a sequence isn't modified
                #                 #         audio_clip_duration[i - 1] = current_sequence_duration
                                
                #                 # if sequence ==

                #                 # if i == 0:
                #                 #     start_time = 0
                            
                #                 if adjusted_start_times[i] != 0:
                #                     adjusted_start_times[i] =  max(adjusted_start_times[i], audio_clip_duration[i])
                #                     total_cut_duration+=max(adjusted_start_times[i], audio_clip_duration[i])
                                        
                #                 # start_time = sum(audio_clip_duration[:i]) if i > 0 else 0         
                #                 clip = clip.set_audio(audio_clip).set_position((x, y)).set_start(adjusted_start_times[i])
                                
                                
                                
                                
                                
                #                 # if i > 0 and sequence != mediaSorted[i - 1]['sequence']:
                #                 #     audio_clip_duration.pop()
                                    
                                    
                #                 clip = clip.resize(width=width, height=height) 
                #                 clips.append(clip)
                                
                #                 time_list['for_image']= time.perf_counter()-t1

                            
                #             elif type == 'Video':
                #                 if audioType == 'audio_script':
                #                     audio = text_to_speech(audioScript, 'position_audio', request)
                #                     audio = ur.urlopen(audio)
                #                     file = f"position_audio_{timezone.now().strftime('%Y%m%d%H%M')}.wav"                    
                                    
                #                 elif audioType == 'audio_url':
                #                     res = requests.get(audioURL)
                #                     bytecontent = BytesIO(res.content)
                                    
                #                     recognizer = sr.Recognizer()
                #                     with sr.AudioFile(bytecontent) as source:
                #                         recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                #                         audio = recognizer.listen(source)
                #                         audioText = recognizer.recognize_google(audio)
                                    
                #                     audio = text_to_speech(audioText, "audio", request)
                #                     audio = ur.urlopen(audio)
                #                     file = f"audio_{RandomNumber()}.wav" 
                                    
                #                 with open(file, 'wb') as f:
                #                     f.write(audio.read())
                #                     print("Length of written audio file:", os.path.getsize(file))

                #                 audio_clip = AudioFileClip(filename=file)
                #                 audio_clips.append(audio_clip)
                #                 audio_duration = audio_clip.duration
                #                 audio_duration_seconds = int(audio_duration)
                #                 audio_clip_duration.append(audio_duration_seconds)
                                
                #                 os.remove(file)
                #                 # position = str(position)
                #                 # positions = position.split(',')
                #                 print("position", position[0])
                #                 video_clip = VideoFileClip(media)
                #                 position, width,height = set_media_position(W=1920,H=1080, user=position)
                                
                #                 sum_tuple = tuple(sum(x) for x in zip(*position))
                #                 x,y = int(sum_tuple[0]), int(sum_tuple[1])
                                
                                
                #                 # ! commented code for sequencing of multi overlay media:::::::: NOT WORKING
                                
                #                 # if i == 0 or sequence != mediaSorted[i - 1]['sequence']:
                #                 #     current_start_time += current_sequence_duration  # Update start time
                #                 #     current_sequence_duration = 0 
                #                 # if sequence == mediaSorted[i - 1]['sequence']:
                #                 #     current_sequence_duration = max(current_sequence_duration, audio_clip_duration[i])  # Update sequence duration

                #                 #     # Match previous video duration to the maximum (only for non-first videos in a sequence):
                #                 #     if i > 0:  # Ensure first video in a sequence isn't modified
                #                 #         audio_clip_duration[i - 1] = current_sequence_duration
                                
                #                 # if i == 0:
                #                     # start_time = 0
                            
                #                 if adjusted_start_times[i] != 0:
                #                     adjusted_start_times[i] =  max(adjusted_start_times[i], audio_clip_duration[i])  
                #                     total_cut_duration+=max(adjusted_start_times[i], audio_clip_duration[i])
                                        
                #                 # start_time = sum(audio_clip_duration[:i]) if i > 0 else 0        
                #                 video = video_clip.set_audio(audio_clip).set_position((x, y)).set_start(adjusted_start_times[i])
                                
                #                 # if i > 0 and sequence != mediaSorted[i - 1]['sequence']:
                #                 #     audio_clip_duration.pop()
                                
                #                 # video=video.set_start(start_time)
                #                 video=video.resize(width=width,height=height)
                #                 video= video.subclip(0,audio_duration_seconds)
                #                 clips.append(video)
                                
                #                 time_list['for_video']= time.perf_counter()-t1
                                

                #     video_folder = os.path.join(os.getcwd(), 'static/videos')
                #     os.makedirs(video_folder, exist_ok=True)
                #     current_datetime = RandomNumber()
                #     video_path = os.path.join(video_folder, f'customer_{current_datetime}.mp4')

                #     print("background_detail['type']",background_detail['type']['name'])
                #     if background_detail['type']['name'] == "Image":
                #         print("background")
                #         bg_file = background_detail['media']

                #         # print(bg_file)
                #         image = ur.urlopen(bg_file)
                #         img_arr = np.array(bytearray(image.read()), dtype=np.uint8)
                #         img = cv2.imdecode(img_arr, cv2.IMREAD_UNCHANGED)
                #         img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        
                #         time_abc=sum(video_durations)-total_cut_duration
                        
                #         print("/n video duration", sum(video_durations) , "???????????? cut time",time_abc)
                #         background_clip = ImageClip(img_rgb).set_duration(time_abc)
                #         repeated_background = background_clip.resize(width=1920,height=1080)

                #         final_clip = CompositeVideoClip([repeated_background] + clips)
                #         time_list['for_background']= time.perf_counter()-t1

                #         final_clip.write_videofile(video_path, fps=24)
                #         static_video_url = base_url + static(os.path.join('videos', f'customer_{current_datetime}.mp4'))
                        
                #         print(">>>>>>>",static_video_url)
                #         customer_url_list = [
                #             {
                #                 'video for customer':f"{customer_details['customer_id']} - {customer_details['prospectName']}",
                #                 'video url':static_video_url
                #             }
                #         ]

                #         t2 = time.perf_counter()
                #         print('Time: ', t2-t1)
                #         time_list['final_time']= time.perf_counter()-t1
                #         print(time_list) 

                #     # Load the background video
                #     elif background_detail['type']['name'] == "Video":
                #         bg_file = background_detail['media']

                #         background_clip = VideoFileClip(bg_file)
                #         background_clip = background_clip.without_audio()
                #         background_clip = background_clip.resize(width=1920, height=1080)  # Adjust the size as needed
                        
                #         time_abc=sum(video_durations)-total_cut_duration
                        
                #         print("/n video duration", sum(video_durations) , "???????????? cut time",time_abc)
                #         repeated_background = background_clip.loop(duration=audio_duration_seconds)
            
                #         final_clip = CompositeVideoClip([repeated_background] + clips)
                #         time_list['for_background']= time.perf_counter()-t1

                #         final_clip.write_videofile(video_path, fps=24)
                #         static_video_url = base_url + static(os.path.join('videos', f'customer_{current_datetime}.mp4'))
                        
                #         print(">>>>>>>",static_video_url)
                        # customer_url_list = [
                        #     {
                        #         'video for customer':f"{customer_details['customer_id']} - {customer_details['prospectName']}",
                        #         'video url':static_video_url
                        #     }
                        # ]

                        # t2 = time.perf_counter()
                        # print('Time: ', t2-t1)
                        # time_list['final_time']= time.perf_counter()-t1
                        # print(time_list) 

                # else:
                #     vdo_not_created.append({'customer_id':customer_details['customer_id'],'customer_name':customer_details['prospectName']})

            return Response({"status":status.HTTP_200_OK,"Response":results,"video_not_created":self.vdo_not_created},status.HTTP_200_OK)
        # except Exception as e :
        #     print(str(e))
        #     return Response({"Message":"error occoured","error discription":str(e),"status":status.HTTP_500_INTERNAL_SERVER_ERROR},status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create_video(self,customer,background_detail,request):
        print("---------in function background_detail",background_detail)
        video_clips=[]
        customer_details = {
            "customer_id": customer.get("customer_id"),
            "organizationName": customer.get("organizationName"),
            "prospectName": customer.get("prospectName"),
            "emailAddress": customer.get("emailAddress"),
            "websiteUrl1": customer.get("websiteUrl1"),
            "websiteUrl2": customer.get("websiteUrl2"),
            "websiteUrl3": customer.get("websiteUrl3"),
            "personalized_audio_script":customer.get("personalized_audio_script")
        }
        time_list={}
        t1 = time.perf_counter()

        clips = []
        audio_clips = []
        audio_clip_duration=[]
        audio_start_duration=[]
        total_cut_duration=0
        sequence_list=[]
        audio_duration_seconds = 0
        video_durations =[]
        
        base_video_details = customer.get("base_video")
        print("for customer",customer_details['prospectName'],  )
        if base_video_details:
            print("in base video for customer ",customer_details['prospectName'])
            videos_sorted = sorted(base_video_details, key=lambda x: x['sequence'] if x['sequence'] is not None else 1)
            # print("\n>>>>>>>>>>>>>>>videos_sorted.",videos_sorted)
            for video in range(len(videos_sorted)):
                video_durations.append(20)
            
            adjusted_start_times = adjust_start_times(video_durations, videos_sorted)

            # print(">>>>>>>>>>>>>>adjusted_start_times : ", adjusted_start_times)
            for i,base_video in enumerate(videos_sorted):
                    # print("baes_video.........",base_video)
                    media, type,title, audioScript, audioURL, audioType, position, sequence, websiteDetails,Tag_personalised=(
                        base_video['media'],
                        base_video['type']['name'],
                        base_video['title'],
                        base_video['audio_template']['Description'],
                        base_video['audio_template']['Audio_url'],
                        base_video['audio_template']['media_type']['name'],
                        base_video['position_composition_id'],
                        base_video['sequence'],
                        base_video['website_details'],
                        base_video['Tag_personalised']
                    )
                    # print("Positionnnnnn>>>", position)
                    # print("Type>>>>>>>>>>",type)

                    sequence_list.append(sequence)

                    if type=='personalised':
                        if audioType == 'audio_script':
                            print("AudioScript>>>>>>>>>>",customer_details['prospectName'])
                            audio = text_to_speech(audioScript, 'position_audio', request)
                            audio = ur.urlopen(audio)
                            print("herereereref")
                            file = f"position_audio_{timezone.now().strftime('%Y%m%d%H%M')}.wav"
                    
                        elif audioType == 'audio_url':
                            print("AudioUrl>>>>>>>>>>",customer_details['prospectName'])
                            res = requests.get(audioURL)
                            bytecontent = BytesIO(res.content)
                            
                            recognizer = sr.Recognizer()
                            with sr.AudioFile(bytecontent) as source:
                                recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                                audio = recognizer.listen(source)
                                audioText = recognizer.recognize_google(audio)
                            
                            audio = text_to_speech(audioText, "audio", request)
                            audio = ur.urlopen(audio)
                            file = f"audio_{RandomNumber()}.wav" 
                        
                        with open(file, 'wb') as f:
                            f.write(audio.read())
                            "hereee"
                        
                        audio_clip = AudioFileClip(filename=file)
                        audio_clips.append(audio_clip) 
                        audio_duration = audio_clip.duration
                        audio_duration_seconds = audio_duration_seconds+int(audio_duration)
                        audio_clip_duration.append(audio_duration_seconds)
                        audio_start_duration.append(audio_duration_seconds)
                        
                        # print("personalised position", position)
                        personalised_position, width,height = set_media_position(W=1920,H=1080, user=position)
                        sum_tuple = tuple(sum(x) for x in zip(*personalised_position))
                        x,y = int(sum_tuple[0]), int(sum_tuple[1])
                        
                        os.remove(file)
                        output_folder = f'static/web/'
                        videofileName = f'static/videos/position_video_{RandomNumber}.mp4'
                        # redirections = len(Tag_personalised)

                        redirections = 1
                        url = Tag_personalised['value']
                        # perso_scroll = tag['scroll']
                        # websearch = tag['websearch']
                        
                        perso_scroll = Tag_personalised['scroll'] == 'T'
                        websearch = Tag_personalised['websearch'] == 'T'

                        
                        openbrowser_and_capture_json(website=url, output_folder=output_folder, redirection_count=redirections, scrolling=perso_scroll, google_search_c=websearch)

                        redirections+=1

                        clip = make_video_json(output_folder=output_folder, output_video_file=videofileName,time_frame=audio_duration)
                        if i == 0:
                            start_time = 0
                    
                        elif adjusted_start_times[i] != 0:
                            adjusted_start_times[i] =  max(adjusted_start_times[i], audio_clip_duration[i])
                            total_cut_duration+=max(adjusted_start_times[i], audio_clip_duration[i])
                            
                            
                        print("Start times::::::", start_time,customer_details['prospectName'])     
                        clip = clip.set_audio(audio_clip).set_position((x, y)).set_start(adjusted_start_times[i])
                        clip = clip.resize(width=width, height=height) 
                        clips.append(clip)  

                    elif type == 'URL':
                        web_clips =[]
                        # positions.append(position)
                        # print(positions,"positionsssssssss")
                        
                        redirection_count = len(websiteDetails)
                        
                        if audioType == 'audio_script':
                            print("AudioScript>>>>>>>>>>",audioScript)
                            audio = text_to_speech(audioScript, 'position_audio', request)
                            audio = ur.urlopen(audio)
                            print("herereereref")
                            file = f"position_audio_{timezone.now().strftime('%Y%m%d%H%M')}.wav"
                        
                        elif audioType == 'audio_url':
                            res = requests.get(audioURL)
                            bytecontent = BytesIO(res.content)
                            
                            recognizer = sr.Recognizer()
                            with sr.AudioFile(bytecontent) as source:
                                recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                                audio = recognizer.listen(source)
                                audioText = recognizer.recognize_google(audio)
                            
                            audio = text_to_speech(audioText, "audio", request)
                            audio = ur.urlopen(audio)
                            file = f"audio_{RandomNumber()}.wav" 
                        
                        with open(file, 'wb') as f:
                            f.write(audio.read())
                            "hereee"
                        
                        audio_clip = AudioFileClip(filename=file)
                        audio_clips.append(audio_clip) 
                        audio_duration = audio_clip.duration
                        audio_duration_seconds = audio_duration_seconds+int(audio_duration)
                        audio_clip_duration.append(audio_duration_seconds)
                        
                        
                        position, width,height = set_media_position(W=1920,H=1080, user=position)
                        sum_tuple = tuple(sum(x) for x in zip(*position))
                        x,y = int(sum_tuple[0]), int(sum_tuple[1])
                        
                        os.remove(file)
                        output_folder = f'static/web/'
                        videofileName = f'static/videos/jagga_video.mp4'
                        
                        for website in websiteDetails:
                            scroll = None
                            search = None
                            if website['scroll'] == 'T':
                                scroll = True
                            else:
                                scroll =False    
                            print(website['websearch'])
                            if website['websearch'] == 'T':
                                search = True
                            else:
                                search = False    
                            openbrowser_and_capture_json(website=website['url'], output_folder=output_folder, redirection_count=redirection_count, scrolling=scroll, google_search_c=search)
                            
                            web_clip = make_video_json(output_folder=output_folder, output_video_file=videofileName,time_frame=audio_duration)
                            web_clips.append(web_clip)
                            
                        clip = concatenate_videoclips(web_clips)
                        
                        
                        if i == 0:
                            start_time = 0
                        
                        elif adjusted_start_times[i] != 0:
                            start_time =  max(adjusted_start_times[i], audio_clip_duration[i])
                            total_cut_duration+=max(adjusted_start_times[i], audio_clip_duration[i])

                        
                        # start_time = sum(audio_clip_duration[:i]) if i > 0 else 0    
                        print("Start times::::::", start_time)     
                        clip = clip.set_audio(audio_clip).set_position((x, y)).set_start(adjusted_start_times[i])
                        clip = clip.resize(width=width, height=height) 
                        clips.append(clip)
                        
                        time_list['for_url']= time.perf_counter()-t1
                            
                            
                    elif type == 'Image':
                        image = ur.urlopen(media)
                        img_arr = np.array(bytearray(image.read()), dtype=np.uint8)
                        img = cv2.imdecode(img_arr, cv2.IMREAD_UNCHANGED)
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        
                        if audioType == 'audio_script':
                            audio = text_to_speech(audioScript, 'position_audio', request)
                            audio = ur.urlopen(audio)
                            file = f"position_audio_{timezone.now().strftime('%Y%m%d%H%M')}.wav"
                            
                        elif audioType == 'audio_url':
                            res = requests.get(audioURL)
                            bytecontent = BytesIO(res.content)
                            
                            recognizer = sr.Recognizer()
                            with sr.AudioFile(bytecontent) as source:
                                recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                                audio = recognizer.listen(source)
                                audioText = recognizer.recognize_google(audio)
                            
                            audio = text_to_speech(audioText, "audio", request)
                            audio = ur.urlopen(audio)
                            file = f"audio_{RandomNumber()}.wav" 
                            
                        with open(file, 'wb') as f:
                            f.write(audio.read())
                                

                        audio_clip = AudioFileClip(filename=file)
                        audio_clips.append(audio_clip)
                        audio_duration = audio_clip.duration
                        audio_duration_seconds = audio_duration_seconds+int(audio_duration)
                        audio_clip_duration.append(audio_duration_seconds)
                        
                        os.remove(file)
                        
                        # positions = position.split(',')
                        position, width,height = set_media_position(W=1920,H=1080, user=position)
                        sum_tuple = tuple(sum(x) for x in zip(*position))
                        x,y = int(sum_tuple[0]), int(sum_tuple[1])
                        
                        clip = ImageClip(img_rgb).set_duration(audio_duration_seconds)
                    
                        if adjusted_start_times[i] != 0:
                            adjusted_start_times[i] =  max(adjusted_start_times[i], audio_clip_duration[i])
                            total_cut_duration+=max(adjusted_start_times[i], audio_clip_duration[i])
                                
                        # start_time = sum(audio_clip_duration[:i]) if i > 0 else 0         
                        clip = clip.set_audio(audio_clip).set_position((x, y)).set_start(adjusted_start_times[i])
                        
                        
                        
                        
                        
                        # if i > 0 and sequence != mediaSorted[i - 1]['sequence']:
                        #     audio_clip_duration.pop()
                            
                            
                        clip = clip.resize(width=width, height=height) 
                        clips.append(clip)
                        
                        time_list['for_image']= time.perf_counter()-t1

                    
                    elif type == 'Video':
                        if audioType == 'audio_script':
                            audio = text_to_speech(audioScript, 'position_audio', request)
                            audio = ur.urlopen(audio)
                            file = f"position_audio_{timezone.now().strftime('%Y%m%d%H%M')}.wav"                    
                            
                        elif audioType == 'audio_url':
                            res = requests.get(audioURL)
                            bytecontent = BytesIO(res.content)
                            
                            recognizer = sr.Recognizer()
                            with sr.AudioFile(bytecontent) as source:
                                recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                                audio = recognizer.listen(source)
                                audioText = recognizer.recognize_google(audio)
                            
                            audio = text_to_speech(audioText, "audio", request)
                            audio = ur.urlopen(audio)
                            file = f"audio_{RandomNumber()}.wav" 
                            
                        with open(file, 'wb') as f:
                            f.write(audio.read())
                            print("Length of written audio file:", os.path.getsize(file))

                        audio_clip = AudioFileClip(filename=file)
                        audio_clips.append(audio_clip)
                        audio_duration = audio_clip.duration
                        audio_duration_seconds = audio_duration_seconds+int(audio_duration)
                        audio_clip_duration.append(audio_duration_seconds)
                        
                        os.remove(file)
                        # position = str(position)
                        # positions = position.split(',')
                        print("position", position[0])
                        video_clip = VideoFileClip(media)
                        position, width,height = set_media_position(W=1920,H=1080, user=position)
                        
                        sum_tuple = tuple(sum(x) for x in zip(*position))
                        x,y = int(sum_tuple[0]), int(sum_tuple[1])
                        
                    
                        if adjusted_start_times[i] != 0:
                            adjusted_start_times[i] =  max(adjusted_start_times[i], audio_clip_duration[i])  
                            total_cut_duration+=max(adjusted_start_times[i], audio_clip_duration[i])
                                
                        # start_time = sum(audio_clip_duration[:i]) if i > 0 else 0        
                        video = video_clip.set_audio(audio_clip).set_position((x, y)).set_start(adjusted_start_times[i])
                        
                        # if i > 0 and sequence != mediaSorted[i - 1]['sequence']:
                        #     audio_clip_duration.pop()
                        
                        # video=video.set_start(start_time)
                        video=video.resize(width=width,height=height)
                        video= video.subclip(0,audio_duration_seconds)
                        clips.append(video)
                        
                        time_list['for_video']= time.perf_counter()-t1
                        

            video_folder = os.path.join(os.getcwd(), 'static/videos')
            os.makedirs(video_folder, exist_ok=True)
            current_datetime = RandomNumber()
            video_path = os.path.join(video_folder, f"{customer_details['customer_id']}_customer_{current_datetime}.mp4")

            # print("background_detail['type']",background_detail['type']['name'])
            print(background_detail)
            if background_detail['type']['name'] == "Image":
                print("background")
                bg_file = background_detail['media']

                # print(bg_file)
                image = ur.urlopen(bg_file)
                img_arr = np.array(bytearray(image.read()), dtype=np.uint8)
                img = cv2.imdecode(img_arr, cv2.IMREAD_UNCHANGED)
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                time_abc=sum(video_durations)-total_cut_duration
                
                print("/n video duration", sum(video_durations) , "???????????? cut time",time_abc)
                background_clip = ImageClip(img_rgb).set_duration(time_abc)
                repeated_background = background_clip.resize(width=1920,height=1080)

                final_clip = CompositeVideoClip([repeated_background] + clips)
                time_list['for_background']= time.perf_counter()-t1

                final_clip.write_videofile(video_path, fps=24)
                static_video_url = base_url + static(os.path.join('videos', f'customer_{current_datetime}.mp4'))
                
                print(">>>>>>>",static_video_url)
                customer_url_list = [
                    {
                        'video for customer':f"{customer_details['customer_id']} - {customer_details['prospectName']}",
                        'video url':static_video_url
                    }
                ]

                t2 = time.perf_counter()
                print('Time: ', t2-t1)
                time_list['final_time']= time.perf_counter()-t1
                print(time_list) 

            # Load the background video
            elif background_detail['type']['name'] == "Video":
                bg_file = background_detail['media']

                background_clip = VideoFileClip(bg_file)
                background_clip = background_clip.without_audio()   
                background_clip = background_clip.resize(width=1920, height=1080)  # Adjust the size as needed
                
                time_abc=sum(video_durations)-total_cut_duration
                
                print("/n video duration", sum(video_durations) , "???????????? cut time",time_abc)
                repeated_background = background_clip.loop(duration=audio_duration_seconds)

                final_clip = CompositeVideoClip([repeated_background] + clips)
                time_list['for_background']= time.perf_counter()-t1

                final_clip.write_videofile(video_path, fps=24)
                static_video_url = base_url + static(os.path.join('videos', f"{customer_details['prospectName']}_customer_{current_datetime}.mp4"))
                
                print(">>>>>>>",static_video_url,customer_details['customer_id'])
        
            return {'customer_id':customer_details['customer_id'],'url':static_video_url}
        else:
            return {'msg':'video not created','customer_id':customer_details['customer_id'],'customer_name':customer_details['prospectName']}

        
   


