from django.conf import settings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import numpy as np
from PIL import Image
from moviepy.editor import ImageSequenceClip
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image, ImageDraw, ImageFont, ImageGrab
from moviepy.editor import ImageSequenceClip
from selenium.webdriver.common.action_chains import ActionChains
from natsort import natsorted
import timeit
import time
from selenium.webdriver.common.keys import Keys
from base64 import b64encode
from urllib.parse import urlparse
from moviepy.editor import VideoFileClip, concatenate_videoclips
import csv
import shutil

from .models import *



def openbrowser_and_capture_csv(website, output_folder, redirection_count , scrolling , time_frame):
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
        # print(total_height)
        
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
        
        # try:
        #     screenshot_file = os.path.join(output_folder, f"screenshot{redirection_count}for_{num}.png")
        #     driver.save_screenshot(screenshot_file)
        #     screenshot_list.append(screenshot_file)
        #     num+=1
            
        #     driver.get("https://www.google.com")
            
        #     screenshot_file = os.path.join(output_folder, f"screenshot{redirection_count}for_{num}.png")
        #     driver.save_screenshot(screenshot_file)
        #     screenshot_list.append(screenshot_file)
        #     num+=1
            
            
            
        #     for step in range(1, 6):
        #         if step == 1:
        #             screenshot_file = os.path.join(output_folder, f"screenshot{redirection_count}for_{num}.png")
        #             driver.save_screenshot(screenshot_file)
        #             screenshot_list.append(screenshot_file)
        #             num+=1
        #         elif step == 2:
        #             screenshot_file = os.path.join(output_folder, f"screenshot{redirection_count}for_{num}.png")
        #             driver.save_screenshot(screenshot_file)
        #             screenshot_list.append(screenshot_file)
        #             num+=1
                    
        #             search_bar = driver.find_element("name", "q")
        #             search_bar.click
        #             search_bar.send_keys(website)
        #         elif step == 3:
        #             search_bar.send_keys(Keys.RETURN)
        #         elif step==4:
        #             text_list = extract_text_from_url(website)
        #             print(text_list)
                    
        #             for text in text_list:
        #                 try:
        #                     mobiloitte_link = driver.find_element(By.PARTIAL_LINK_TEXT, text)
        #                     screenshot_file = os.path.join(output_folder, f"screenshot{redirection_count}for_{num}.png")
        #                     driver.save_screenshot(screenshot_file)
        #                     screenshot_list.append(screenshot_file)
        #                     num+=1
                            
        #                     driver.execute_script("arguments[0].style.border=' 9px solid red'", mobiloitte_link)
        #                     screenshot_file = os.path.join(output_folder, f"screenshot{redirection_count}for_{num}.png")
        #                     driver.save_screenshot(screenshot_file)
        #                     screenshot_list.append(screenshot_file)
                            
        #                     num+=1

        #                     # screenshot_file = os.path.join(output_folder, f"screenshot{redirection_count}for_{num}.png")
        #                     # driver.save_screenshot(screenshot_file)
        #                     # screenshot_list.append(screenshot_file)
        #                     # num+=1
        #                     break
        #                 except Exception as e:
        #                     print("0",{str(e)})
        #                     pass
        #             # pass
            
                    
        #         screenshot_file = os.path.join(output_folder, f"screenshot{redirection_count}for_{num}.png")
        #         driver.save_screenshot(screenshot_file)
        #         screenshot_list.append(screenshot_file)
        #         num+=1
        # except Exception as e:
        #     print("1.",{str(e)})
        #     pass

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
                if scrolling=='yes':
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
    
    
        

        # os.remove(os.path.join(output_folder, screenshot_file))


def load_image_csv(args):
    output_folder, file = args
    image_path = os.path.join(output_folder, file)
    img = Image.open(image_path)

    return np.array(img)



 

def remove_elements_csv(lst):
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


def extract_text_from_url_csv(url):
    parsed_url = urlparse(url)
    domain_words = parsed_url.netloc.split('.')

    path = parsed_url.path.strip('/')

    path = path.replace('-', ' ').replace('_', ' ')

    path_words = [word.lower() for word in path.split('/') if word]

    result = domain_words + path_words
    r = remove_elements_csv(result)
    return r



def read_csv(file_path):
    data = []
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append({
                "sr_no": row["sr_no"],
                "website_url": row["website_url"],
                "scrolling": row["scrolling"],
                "time": row["time"]
            })
    return data

def make_video_csv(output_folder, output_video_file, time_frame):
    screenshot_files = natsorted([f for f in os.listdir(output_folder)])
    images = []

    duplicate_folder = output_folder + "_duplicate"
    os.makedirs(duplicate_folder, exist_ok=True)
    
    for screenshot_file in screenshot_files:
        image_path = os.path.join(output_folder, screenshot_file)
        img = Image.open(image_path)

        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        draw.text((10, 10), "Clicked Link", (255, 0, 0), font=font)

        img_array = np.array(img)
        images.append(img_array)
        
    duration = float(time_frame)

    fps = len(images) / duration

    clip = ImageSequenceClip(images, fps=fps)
    clip.write_videofile(output_video_file, codec='libx264', fps=fps)

    for screenshot_file in screenshot_files:
        image_path = os.path.join(output_folder, screenshot_file)
        shutil.move(image_path, os.path.join(duplicate_folder, screenshot_file))

    return f"http://172.16.6.221:8005/{output_video_file}"


# def merge_videos(output_folder, output_video_file , duration,time_f):
#     screenshot_files = natsorted([f for f in os.listdir(output_folder)])
#     images = []

#     for screenshot_file in screenshot_files:
#         image_path = os.path.join(output_folder, screenshot_file)
#         img = Image.open(image_path)

#         draw = ImageDraw.Draw(img)
#         font = ImageFont.load_default()
#         draw.text((10, 10), "Clicked Link", (255, 0, 0), font=font)

#         img_array = np.array(img)
#         images.append(img_array)
        
#     print(screenshot_files)

        
#     fps = len(images) / duration
    
    
#     print(fps)



#     clip = ImageSequenceClip(images, fps=fps)
#     clip.write_videofile(output_video_file, codec='libx264', fps=fps)

    
#     # for screenshot_file in screenshot_files:
#     #     os.remove(os.path.join(output_folder, screenshot_file))





def extract_numeric_part_csv(s):
    # Helper function to extract the numeric part from a string using regular expression
    import re
    match = re.search(r'\d+', s)
    return int(match.group()) if match else None





def merge_videos_csv(output_folder, output_video_file_prefix, duration, timelist):
    screenshot_files = natsorted([f for f in os.listdir(output_folder)])
    images = {}
    imagelist=[]

    video_clips = []
    video_paths = []

    for screenshot_file in screenshot_files:
        image_path = os.path.join(output_folder, screenshot_file)
        img = Image.open(image_path)

        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        draw.text((10, 10), "Clicked Link", (255, 0, 0), font=font)

        img_array = np.array(img)
        imagelist.append(img_array)

        screenshot_prefix = extract_numeric_part_csv(screenshot_file)

        if screenshot_prefix is not None:
            images.setdefault(screenshot_prefix, []).append(img_array)

    
    for prefix, img_array_list in images.items():
        i = prefix  
        fps = len(img_array_list) / int(timelist[i-1])

        clip = ImageSequenceClip(img_array_list, fps=fps)
        video_path = f"video_{prefix}.mp4"
        clip.write_videofile(video_path, codec='libx264', fps=fps)
        video_clips.append(clip)

        video_paths.append(f"http://172.16.6.221:8005/{video_path}")

    final_fps = len(imagelist) / duration
    
    # print("1")
    final_video_path = "final_merged_video.mp4"
    final_clip = concatenate_videoclips(video_clips, method="compose")
    final_clip.write_videofile(final_video_path, codec='libx264', fps=24)

    # print("2")
    # data=Final_video.objects.create(video="final_merged_video.mp4")
    # data.save()
    video_paths.append(f"http://172.16.6.221:8005/{final_video_path}")
    for screenshot_file in screenshot_files:
        os.remove(os.path.join(output_folder, screenshot_file))

    
    
    # context={"video_url":video_clips}
    
    return video_paths




def merge_video( output_video_file_prefix, num_videos):
    video_clips = []

    for i in range(1, num_videos + 1):
        video_file = f"output{i}.mp4"
        video_clip = VideoFileClip(video_file)
        video_clips.append(video_clip)

    final_clip = concatenate_videoclips(video_clips, method="compose")
    final_clip.write_videofile(f"{output_video_file_prefix}_merged.mp4", codec='libx264', fps=24)

    return f"{output_video_file_prefix}_merged.mp4"