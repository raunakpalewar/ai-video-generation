import speech_recognition as sr
import os
from gtts import gTTS
import requests
import numpy as np
import urllib.request as ur
from moviepy.editor import ImageSequenceClip,concatenate_videoclips,ImageClip,AudioFileClip,concatenate_audioclips,VideoFileClip,VideoClip,concatenate,CompositeVideoClip
from PIL import Image
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import timeit
# import pyttsx3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import numpy as np
from PIL import Image
from moviepy.editor import ImageSequenceClip
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image, ImageDraw, ImageFont, ImageGrab
from moviepy.editor import ImageSequenceClip
from selenium.webdriver.common.action_chains import ActionChains
from natsort import natsorted
import timeit
from selenium.webdriver.common.keys import Keys
from base64 import b64encode
from urllib.parse import urlparse
import requests
from .models import *
import random
from io import BytesIO
import cv2
import time
import json

def RandomNumber():
    return random.randint(000000000,999999999)  



def text_to_speech(text, filename):
    print(text, "hereeeeee")
    speech = gTTS(text=text, lang='en', slow=False, tld='co.in')
    
    # Create the "audio" folder if it doesn't exist
    audio_folder = os.path.join(os.getcwd(), 'static/audio')
    os.makedirs(audio_folder, exist_ok=True)
    current_datetime = RandomNumber()
    file_path = os.path.join(audio_folder, f'{filename}_{current_datetime}.wav')
    speech.save(file_path)

   
    audio_url =  'static/audio/' + f'{filename}_{current_datetime}.wav'
    return audio_url



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



def adjust_start_times(video_durations, sorted_videos):
        adjusted_start_times = [0]

        for i in range(1, len(sorted_videos)):
            if sorted_videos[i]["sequence"] == sorted_videos[i-1]["sequence"]:
                adjusted_start_times.append(adjusted_start_times[-1])
            else:
                adjusted_start_times.append(adjusted_start_times[-1] + video_durations[i-1])
        return adjusted_start_times



def python_video_for_customer(customer):
    # customer_data=customer.to_dict()
    
    with open(customer, 'r') as file:
        customer_data = json.load(file)
    
    
    background_detail=customer_data['background']
    web_duration=0
    
    output_folder = f'static/web/'
    video_clips=[]
    web_clips=[]
    url_clips=[]
    x=1
    time_list={}
    video_durations =[]
    sequence_list=[]
    clips = []
    audio_clips = []
    audio_clip_duration=[]
    audio_start_duration=[]
    total_cut_duration=0
    sequence_list=[]
    audio_duration_seconds = 0
    video_durations =[]
    
    
    t1 = time.perf_counter()
    
    for key,values in customer_data.items():
        if key=='websiteUrl1' or key=='websiteUrl2' or key=='websiteUrl3':
            if customer_data[key]:
                openbrowser_and_capture(values, output_folder, x, True, True)  
                web_clip = make_video(output_folder=output_folder,time_frame=10)
                video_clips.append(web_clip)
                url_clips.append(web_clip)
                x+=1
            else:
                pass

    if url_clips:
        ll=len(url_clips)
        clip=concatenate_videoclips(url_clips)
        adjusted_start_times[0] =  0
        
        web_duration+=10*ll
        
        tp=adjust_start_times(web_duration,clip)
        
        
        
        personalised_position, width,height = set_media_position(W=1920,H=1080, user=[3,3])
        sum_tuple = tuple(sum(x) for x in zip(*personalised_position))
        x,y = int(sum_tuple[0]), int(sum_tuple[1])
        
        print("Start times::::::", start_time)     
        clip = clip.resize(width=width, height=height).set_position((x, y)).set_start(adjusted_start_times[0])
        clips.append(clip)
     
    
    for key,values in customer_data.items():

        base_video_details = customer.get("base_video")
        



        if base_video_details:
            print("in base video for customer ",customer_data['prospectName'])
            videos_sorted = sorted(base_video_details, key=lambda x: x['sequence'] if x['sequence'] is not None else 1)

            for video in range(len(videos_sorted)):
                video_durations.append(20)
            
            adjusted_start_times = adjust_start_times(video_durations, videos_sorted)

            for i,base_video in enumerate(videos_sorted):
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
                            print("AudioScript>>>>>>>>>>",customer_data['prospectName'])
                            audio = text_to_speech(audioScript, 'position_audio')
                            audio = ur.urlopen(audio)
                            print("herereereref")
                            file = f"position_audio_{timezone.now().strftime('%Y%m%d%H%M')}.wav"
                    
                        elif audioType == 'audio_url':
                            print("AudioUrl>>>>>>>>>>",customer_data['prospectName'])
                            res = requests.get(audioURL)
                            bytecontent = BytesIO(res.content)
                            
                            recognizer = sr.Recognizer()
                            with sr.AudioFile(bytecontent) as source:
                                recognizer.adjust_for_ambient_noise(source, duration=0.00001)
                                audio = recognizer.listen(source)
                                audioText = recognizer.recognize_google(audio)
                            
                            audio = text_to_speech(audioText, "audio")
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

                        
                        openbrowser_and_capture(website=url, output_folder=output_folder, redirection_count=redirections, scrolling=perso_scroll, google_search_c=websearch)

                        redirections+=1

                        clip = make_video(output_folder=output_folder,time_frame=audio_duration)
                        if i == 0:
                            start_time = 0 + (10 *(len(url_clips)))
                    
                        elif adjusted_start_times[i] != 0:
                            adjusted_start_times[i] =  max(adjusted_start_times[i], audio_clip_duration[i])
                            total_cut_duration+=max(adjusted_start_times[i], audio_clip_duration[i])
                            
                            
                        print("Start times::::::", start_time,customer_data['prospectName'])     
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
                            audio = text_to_speech(audioScript, 'position_audio')
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
                            
                            audio = text_to_speech(audioText, "audio")
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
                            openbrowser_and_capture(website=website['url'], output_folder=output_folder, redirection_count=redirection_count, scrolling=scroll, google_search_c=search)
                            
                            web_clip = make_video(output_folder=output_folder,time_frame=audio_duration)
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
                            audio = text_to_speech(audioScript, 'position_audio')
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
                            
                            audio = text_to_speech(audioText, "audio")
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
                            
                            
                        clip = clip.resize(width=width, height=height) 
                        clips.append(clip)
                        
                        time_list['for_image']= time.perf_counter()-t1

                    
                    elif type == 'Video':
                        if audioType == 'audio_script':
                            audio = text_to_speech(audioScript, 'position_audio')
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
                            
                            audio = text_to_speech(audioText, "audio")
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
            video_path = os.path.join(video_folder, f"{customer_data['customer_id']}_customer_{current_datetime}.mp4")

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
                static_video_url = static(os.path.join('videos', f'customer_{current_datetime}.mp4'))
                
                print(">>>>>>>",static_video_url)
                customer_url_list = [
                    {
                        'video for customer':f"{customer_data['customer_id']} - {customer_data['prospectName']}",
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
                static_video_url = static(os.path.join('videos', f"{customer_data['prospectName']}_customer_{current_datetime}.mp4"))
                
                print(">>>>>>>",static_video_url,customer_data['customer_id'])
        
            return {'customer_id':customer_data['customer_id'],'url':static_video_url}
        else:
            return {'msg':'video not created','customer_id':customer_data['customer_id'],'customer_name':customer_data['prospectName']}

        
    
            





def openbrowser_and_capture(website, output_folder, redirection_count , scrolling ,google_search_c):
    options = Options()
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-gpu")
    options.add_argument("--headless")  

    driver = webdriver.Chrome(options=options)
    driver.minimize_window
    
    try:
       
        WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        os.makedirs(output_folder, exist_ok=True)
        
        total_height = int(driver.execute_script("return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight );"))
        driver.set_window_size(1920, 1080)  # Set the window size to capture frames of 1920x200 pixels
        print(total_height)
        
        scroll_step = 400
        image_count = 0
        screenshot_list = []
        j=1
        num=0
        # website=url
        
        # itime = timeit.default_timer()
        # start_time = time.time()

        # while True:
        #     current_time = time.time()
        #     elapsed_time = current_time - start_time

        #     if elapsed_time <= float(time_frame):
        
        if google_search_c==True:
        
            try:
                screenshot_file = os.path.join(output_folder, f"screenshot{redirection_count}for_{num}.png")
                driver.save_screenshot(screenshot_file)
                screenshot_list.append(screenshot_file)
                num+=1
                
                driver.get("https://www.google.com")
                
                screenshot_file = os.path.join(output_folder, f"screenshot{redirection_count}for_{num}.png")
                driver.save_screenshot(screenshot_file)
                screenshot_list.append(screenshot_file)
                num+=1
                
                
                
                for step in range(1, 6):
                    if step == 1:
                        screenshot_file = os.path.join(output_folder, f"screenshot{redirection_count}for_{num}.png")
                        driver.save_screenshot(screenshot_file)
                        screenshot_list.append(screenshot_file)
                        num+=1
                    elif step == 2:
                        screenshot_file = os.path.join(output_folder, f"screenshot{redirection_count}for_{num}.png")
                        driver.save_screenshot(screenshot_file)
                        screenshot_list.append(screenshot_file)
                        num+=1
                        
                        search_bar = driver.find_element("name", "q")
                        search_bar.click
                        search_bar.send_keys(website)
                    elif step == 3:
                        search_bar.send_keys(Keys.RETURN)
                    elif step==4:
                        text_list = extract_text_from_url_json(website)
                        print(text_list)
                        
                        for text in text_list:
                            try:
                                mobiloitte_link = driver.find_element(By.PARTIAL_LINK_TEXT, text)
                                screenshot_file = os.path.join(output_folder, f"screenshot{redirection_count}for_{num}.png")
                                driver.save_screenshot(screenshot_file)
                                screenshot_list.append(screenshot_file)
                                num+=1
                                
                                driver.execute_script("arguments[0].style.border=' 9px solid red'", mobiloitte_link)
                                screenshot_file = os.path.join(output_folder, f"screenshot{redirection_count}for_{num}.png")
                                driver.save_screenshot(screenshot_file)
                                screenshot_list.append(screenshot_file)
                                
                                num+=1

                                # screenshot_file = os.path.join(output_folder, f"screenshot{redirection_count}for_{num}.png")
                                # driver.save_screenshot(screenshot_file)
                                # screenshot_list.append(screenshot_file)
                                # num+=1
                                break
                            except Exception as e:
                                print("0",{str(e)})
                                pass
                        # pass
                
                        
                    screenshot_file = os.path.join(output_folder, f"screenshot{redirection_count}for_{num}.png")
                    driver.save_screenshot(screenshot_file)
                    screenshot_list.append(screenshot_file)
                    num+=1
            except Exception as e:
                print("1.",{str(e)})
                pass

        driver.get(website)
        WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        total_height = int(driver.execute_script("""
                    var body = document.body,
                        html = document.documentElement;
                    var height = Math.max(
                        body.scrollHeight, body.offsetHeight,
                        html.clientHeight, html.scrollHeight, html.offsetHeight);
                    var offset = 200;  // Adjust this value based on the actual height of the browser head part and tab bar
                    return height + offset;
                """))
        
        if "linkedin" in website:
            sign_in_popup_element = WebDriverWait(driver, 2).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".contextual-sign-in-modal__modal-dismiss-icon > .artdeco-icon")))
            action = ActionChains(driver)
            action.click(sign_in_popup_element)
            action.perform()
        
    
        itime=timeit.default_timer()
        for i in range(0, total_height, scroll_step):
            # if elapsed_time > float(time_frame):
            #     print("time frame exeeded")
            #     driver.quit()
            #     return
            try:
                if scrolling==True:
                    driver.execute_script(f"window.scrollTo(0, {i});")
                print('now taking screenshot at', i)
                WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

                screenshot_file = os.path.join(output_folder, f"screenshot{redirection_count}for_{num}.png")
                screenshot=driver.save_screenshot(screenshot_file)
                screenshot_list.append(screenshot_file)
                
                jtime=timeit.default_timer()
                time_diff=jtime - itime
                
                if "instagram" in website:
                    try:
                        sign_in_popup_element = WebDriverWait(driver, 2).until(
                                EC.presence_of_element_located((By.XPATH, "//div/div/div/div/div[2]/div/div/div/div/div")))
                        break
                    except:
                        pass 
                num += 1
            except Exception as e:
                print({str(e)})
                continue
                    
            # else:
            #     # driver.back()
        driver.quit()
            # return
    except Exception as e:
        print({str(e)})
    
    
        
def make_video(output_folder, time_frame):
    screenshot_files = natsorted([f for f in os.listdir(output_folder)])
    images = []

    # duplicate_folder = "user_"+str(user_id)+ "_duplicate"
    # os.makedirs(duplicate_folder, exist_ok=True)
    
    for screenshot_file in screenshot_files:
        image_path = os.path.join(output_folder, screenshot_file)
        print("image_path>>>>>>>>>>",image_path)
        try:
            img = Image.open(image_path)
        except Exception as e:
            print(str(e))
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        draw.text((10, 10), "Clicked Link", (255, 0, 0), font=font)

        img_array = np.array(img)
        images.append(img_array)
        
    duration = float(time_frame)

    fps = len(images) / duration

    clip = ImageSequenceClip(images, fps=fps)
    # clip.write_videofile(output_video_file, codec='libx264', fps=fps)

    for screenshot_file in screenshot_files:
        image_path = os.path.join(output_folder, screenshot_file)
        # shutil.move(image_path, os.path.join(duplicate_folder, screenshot_file))
        os.remove(os.path.join(output_folder, screenshot_file))
    
    return clip

def load_image_json(args):
    output_folder, file = args
    image_path = os.path.join(output_folder, file)
    img = Image.open(image_path)

    return np.array(img)


def remove_elements_json(lst):
    common_tlds = [ "www",
    "com", "org", "net", "edu", "gov", "mil",
    "int", "arpa",
    "aero", "biz", "coop", "info", "museum", "name",
    "asia", "cat", "jobs", "mobi", "tel",
    "pro", "travel", "xxx", 
    "ac", "ad", "ae", "af", "ag", "ai", "al", "am", "an", "ao", "aq", "ar", "as", "at", "au",
    "aw", "ax", "az", "ba", "bb", "bd", "be", "bf", "bg", "bh", "bi", "bj", "bm", "bn", "bo",
    "br", "bs", "bt", "bv", "bw", "by", "bz", "ca", "cc", "cd", "cf", "cg", "ch", "ci", "ck",
    "cl", "cm", "cn", "co", "cr", "cu", "cv", "cw", "cx", "cy", "cz", "de", "dj", "dk", "dm",
    "do", "dz", "ec", "ee", "eg", "er", "es", "et", "eu", "fi", "fj", "fk", "fm", "fo", "fr",
    "ga", "gb", "gd", "ge", "gf", "gg", "gh", "gi", "gl", "gm", "gn", "gp", "gq", "gr", "gs",
    "gt", "gu", "gw", "gy", "hk", "hm", "hn", "hr", "ht", "hu", "id", "ie", "il", "im", "in",
    "io", "iq", "ir", "is", "it", "je", "jm", "jo", "jp", "ke", "kg", "kh", "ki", "km", "kn",
    "kp", "kr", "kw", "ky", "kz", "la", "lb", "lc", "li", "lk", "lr", "ls", "lt", "lu", "lv",
    "ly", "ma", "mc", "md", "me", "mg", "mh", "mk", "ml", "mm", "mn", "mo", "mp", "mq", "mr",
    "ms", "mt", "mu", "mv", "mw", "mx", "my", "mz", "na", "nc", "ne", "nf", "ng", "ni", "nl",
    "no", "np", "nr", "nu", "nz", "om", "pa", "pe", "pf", "pg", "ph", "pk", "pl", "pm", "pn",
    "pr", "ps", "pt", "pw", "py", "qa", "re", "ro", "rs", "ru", "rw", "sa", "sb", "sc", "sd",
    "se", "sg", "sh", "si", "sj", "sk", "sl", "sm", "sn", "so", "sr", "ss", "st", "sv", "sx",
    "sy", "sz", "tc", "td", "tf", "tg", "th", "tj", "tk", "tl", "tm", "tn", "to", "tr", "tt",
    "tv", "tw", "tz", "ua", "ug", "uk", "us", "uy", "uz", "va", "vc", "ve", "vg", "vi", "vn",
    "vu", "wf", "ws", "ye", "yt", "za", "zm", "zw","@","/",
    ]
    return [item for item in lst if item not in common_tlds]


def extract_text_from_url_json(url):
    parsed_url = urlparse(url)
    domain_words = parsed_url.netloc.split('.')

    path = parsed_url.path.strip('/')

    path = path.replace('-', ' ').replace('_', ' ')

    path_words = [word.lower() for word in path.split('/') if word]

    result = domain_words + path_words
    r = remove_elements_json(result)
    return r


def extract_numeric_part_json(s):
    import re
    match = re.search(r'\d+', s)
    return int(match.group()) if match else None




if __name__=="__main__":
    json_file_path = '../main/customer_json.json'
    result = python_video_for_customer(json_file_path)
    
    