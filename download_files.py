#%%
        
        
from TikTokApi import TikTokApi
from yt_dlp import YoutubeDL
import asyncio
import os
import pandas as pd
import random
from datetime import datetime
import time
import argparse

# Create the parser
parser = argparse.ArgumentParser(description='Process some integers.')

# Add the arguments
parser.add_argument('--ms_token', type=str, required=True, help='The ms_token to use found in the browser dev console cookies under Applications')
parser.add_argument('--initialize', type=bool, default=False, help='Whether to initialize or not')

# Parse the arguments
args = parser.parse_args()

# Now you can use args.ms_token and args.initialize in your code

#Set the ms token to the one in your browser dev console cookies under Applications
ms_token = args.ms_token
initialize = args.initialize



# Be careful it seems to go haywire and download a lot of videos that are related to all the videos in the dataset so far
async def get_related_videos(input_video_url: str, df: pd.DataFrame, count: int=5, use_sleep=True):
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, 
                                headless=False, suppress_resource_load_types=["image", "media", "font", "stylesheet"])
        input_video = api.video(
            url=input_video_url
        )
        
        print('Getting related videos for video: ' + input_video_url)
        print(input_video)
        
        video_count = 0

        async for video in input_video.related_videos(count=count):
            
            try:
            
            
                video_as_dict = video.as_dict
                
                id = video.id
                username = video.author.username
                filename = username + "_" + id + ".mp4"
                url = "https://www.tiktok.com/@" + username + "/video/" + id
                print('id: ' + id)
                print('username: ' + username)
                print('filename: ' + filename)
                print('url: ' + url)
                desc = video_as_dict['desc']
                stats = video.stats
                collectCount = stats['collectCount']
                commentCount = stats['commentCount']
                diggCount = stats['diggCount']
                playCount = stats['playCount']
                shareCount = stats['shareCount']
                createTime = video.as_dict['createTime']
                downloadTime = datetime.now()

                
                print("Related video found: " + url)
                print('Number of related videos found:' + str(video_count))
                video_count += 1
                
                print('Downloading video...')
                download_video(username, id, "TikTokVideos/")
                
                #Update and save after every video is downloaded
                df = df.append({'id': id, 'filename': filename, 'url': url, 'desc': desc, 'createTime': createTime, 'downloadTime': downloadTime, 'author': username, 'collectCount': collectCount, 'commentCount': commentCount, 'diggCount': diggCount, 'playCount': playCount, 'shareCount': shareCount}, ignore_index=True)
                df.to_csv('video_data.csv', index=False)
                
                print('Dataframe row added:')
                print(df.iloc[-1])
                
                # random_time = random.randint(2, 5)
                # await asyncio.sleep(random_time)            
                # print('Downloading video...')
                # download_video(username, id, "TikTokVideos/")
            except Exception as e:
                print('Error in getting related videos')
                print(e)
                
            if use_sleep:
            
                random_time = random.randint(2, 5)
                await asyncio.sleep(random_time)
    
    return df

async def trending_videos(df, count=30):
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, 
                                headless=False, suppress_resource_load_types=["image", "media", "font", "stylesheet"])


        async for video in api.trending.videos(count=count):
            print(video)
            print(video.as_dict)
            print()
            print('desc: ' + video.as_dict['desc'])
            print('createTime: ' + str(video.as_dict['createTime']))
            
            video_as_dict = video.as_dict
            
            id = video.id
            username = video.author.username
            filename = username + "_" + id + ".mp4"
            url = "https://www.tiktok.com/@" + username + "/video/" + id
            desc = video_as_dict['desc']
            stats = video.stats
            collectCount = stats['collectCount']
            commentCount = stats['commentCount']
            diggCount = stats['diggCount']
            playCount = stats['playCount']
            shareCount = stats['shareCount']
            createTime = video.as_dict['createTime']
            downloadTime = datetime.now()
            
            
            print("Trending video found: " + url)

            
            #Download video
            print('Downloading video...')
            download_video(username, id, "TikTokVideos/")
            
            #Update and save after every video is downloaded
            df = df.append({'id': id, 'filename': filename, 'url': url, 'desc': desc, 'createTime': createTime, 'downloadTime': downloadTime, 'author': username, 'collectCount': collectCount, 'commentCount': commentCount, 'diggCount': diggCount, 'playCount': playCount, 'shareCount': shareCount}, ignore_index=True)
            df.to_csv('video_data.csv', index=False)
            
    return df

async def get_video_info(input_video_url: str):
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3)
        video = api.video(
            url=input_video_url
        )
        
        video_info = await video.info()
        

            
        #video_as_dict = video.as_dict
        print(video_info)
        
        print(video_info['author'])
        print(video_info['video']['duration'])
        print(video_info['video']['duration']['preciseDuration'])
        
            
#Select random video from the input list of videos
def select_random_video(videos: list):
    return random.choice(videos)

def download_video(username, id, folder):

    '''
    Given a video id and target folder, this function will download video to that folder
    '''

    ytdl_format_options = {
        #'outtmpl': os.path.join(folder, '%(uploader)s_%(id)s.%(ext)s')
        'outtmpl': os.path.join(folder, f'{username}_{id}.%(ext)s')
    }
    
    print("Downloading video from: " + "https://www.tiktok.com/@" + username + "/video/" + id)

    with YoutubeDL(ytdl_format_options) as ydl:
        ydl.download(["https://www.tiktok.com/@" + username + "/video/" + id])

#Takes df as input and loops through all the video urls in the df and gets related videos - RUNS INTO AN ERROR AT SOME POINT, UNSURE HOW TO FIX BUT JUST RERUN THIS MULITPLE TIMES TO GET A LOT OF VIDEOS
def get_related_videos_from_df(df):
    url_list = df['url']
    
    random.shuffle(url_list)
    
    for i, url in enumerate(url_list):
        print('Getting related videos for video ' + str(i) + ' of ' + str(len(url_list)) + ' videos')
        df = asyncio.run(get_related_videos(url, df, count=1, use_sleep=True))
        random_time = random.randint(2, 5)
        time.sleep(random_time)
        
    return df

#Removes duplicates from the video directory and the csv file
def remove_duplicates(df, video_dir='TikTokVideos/'):
    
    # Create a copy of the original DataFrame
    original_df = df.copy()
    
    print(f"Number of videos in csv: {len(df)}")
    print(f"Number of videos in directory: {len(os.listdir(video_dir))}")
    
    #Removes duplicates from csv
    df.drop_duplicates(subset='filename', keep='first', inplace=True)
    print(f"Number of videos in csv after removing duplicates: {len(df)}")
    
    # Get a list of all filenames in the directory without their extensions
    filenames_in_dir = [(filename) for filename in os.listdir(video_dir)]
    
    # Keep only the rows in the DataFrame where the filename is in filenames_in_dir
    df = df[df['filename'].isin(filenames_in_dir)]
    print(f"Number of videos in csv after removing rows that don't exist in directory: {len(df)}")
    
    # Find the rows that were removed
    removed_rows = pd.concat([original_df, df]).drop_duplicates(keep=False)

    # Print the removed rows
    print("Removed rows:")
    print(removed_rows)
    
    # Get a list of all filenames in the DataFrame
    filenames = df['filename'].tolist()
    
    remove_count = 0
    
    #Removes files from video directory that don't exist in csv
    for filename in os.listdir(video_dir):
        # If the filename is not in filenames, delete it
        if (filename) not in filenames:
            remove_count += 1
            print(f"Removing {(filename)}")
            os.remove(os.path.join(video_dir, filename))
            
    print(f"Number of files removed: {remove_count}")
    
    print(f"Number of videos in directory after removing files that don't exist in csv: {len(os.listdir(video_dir))}")
    
    df.to_csv('video_data.csv', index=False)
    
    return df


# import nest_asyncio
# nest_asyncio.apply()

try:
    print('Starting scraping data')

    if initialize:
        
        print('Initializing data')
        
        #Sets up df with columns
        agg_df = pd.DataFrame(columns = ['id', 'filename', 'url', 'desc', 'createTime', 'downloadTime', 'author', 'collectCount', 'commentCount', 'diggCount', 'playCount', 'shareCount'])
        
        #Adds new trending videos to video folder and csv
        scraped_data = asyncio.run(trending_videos(agg_df))
    else:
        
        print('Adding related videos to dataset')
        
        #Reload csv data
        agg_df = pd.read_csv('video_data.csv')
        
        #Handles removing duplicate videos and making sure the video folder matches the csv
        remove_duplicates(agg_df)


        #Adds videos related to the videos in the dataset currently (will run for a long time and then hit an error, but still adds a lot of related videos)
        get_related_videos_from_df(agg_df)
        
        
except Exception as e:
    print('Error in scraping data')
    print(e)
    
    
finally:
    print('Reloading csv and removing duplicates')
    # #Reload csv data
    agg_df = pd.read_csv('video_data.csv')

    #Handles removing duplicate videos and making sure the video folder matches the csv
    remove_duplicates(agg_df)



#Example of video dict
# {'id': '7353678370997095710', 'desc': 'Wait for it 💀 @Barstool Outdoors (via:@James) ', 'createTime': '1712161734', 'scheduleTime': 0, 'video': {'id': '', 'height': 1024, 'width': 576, 'duration': 15, 'ratio': '540p', 'cover': 'https://p16-sign.tiktokcdn-us.com/obj/tos-useast8-p-0068-tx2/okejIIcTo2t5EarNwrCXQEfgADL8IMAwGxGqfI?x-expires=1712556000&x-signature=BfWk8QIczQ3wWcGy1a8OPPhb9X4%3D', 'originCover': 'https://p19-sign.tiktokcdn-us.com/obj/tos-useast8-p-0068-tx2/ab4099c614ec43ce8886e860c7e00bd3_1712161737?x-expires=1712556000&x-signature=AzzGJOr%2FVVjTiKxs%2FlZz7E0ETK0%3D', 'dynamicCover': 'https://p19-sign.tiktokcdn-us.com/obj/tos-useast8-p-0068-tx2/ed890d351f914833914cdb4bdc2eb019_1712161737?x-expires=1712556000&x-signature=zNw9fVnH0IPI5f7WX3su6Ww0AnE%3D', 'playAddr': 'https://v16-webapp-prime.us.tiktok.com/video/tos/useast8/tos-useast8-ve-0068c003-tx2/okwLoICxQMjqIcItEe2TbIwfM5EBrGfxGgIAAI/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=4198&bt=2099&cs=0&ds=6&ft=4KJMyMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=0&rc=OjM5NmYzODg8ZDc5aWhnOEBpM3J5aHc5cjhycjMzaTczNEBeNGBfNjA0Xl4xYC8vYmA2YSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&btag=e00088000&expire=1712406814&l=20240406063319446A871603231B3A2116&ply_type=2&policy=2&signature=650e4a84344b6cf0a4645365a5f7164e&tk=tt_chain_token', 'downloadAddr': 'https://v16-webapp-prime.us.tiktok.com/video/tos/useast8/tos-useast8-pve-0068-tx2/oIwT8GcQoHLwIEteIA2brqM6BIjxGAf0IIfCgm/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=tiktok_m&cd=0%7C0%7C1%7C&cv=1&br=4134&bt=2067&cs=0&ds=3&ft=4KJMyMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=0&rc=Ozk5NTM5aDM2NzdpOWZkM0BpM3J5aHc5cjhycjMzaTczNEBgLzIvYS5hNjMxYzQtMWAzYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&btag=e00088000&expire=1712406814&l=20240406063319446A871603231B3A2116&ply_type=2&policy=2&signature=33f4ca0c94af8d0a3d6a0b7c2f172c5d&tk=tt_chain_token', 'shareCover': [''], 'reflowCover': '', 'bitrate': 2150128, 'encodedType': 'normal', 'format': 'mp4', 'videoQuality': 'normal', 'encodeUserTag': '', 'codecType': 'h264', 'definition': '540p', 'subtitleInfos': [{'UrlExpire': '1712406814', 'Size': '488', 'LanguageID': '1', 'LanguageCodeName': 'cmn-Hans-CN', 'Url': 'https://v16m-webapp.tiktokcdn-us.com/a5f9c6a4af63e117f72a0dec449f1b7f/6611411e/video/tos/useast8/tos-useast8-v-0068-tx2/cea31557f9dc4a3c98bbb57724071912/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=13866&bt=6933&ds=4&ft=4KLMeMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=13&rc=M3J5aHc5cjhycjMzaTczNEBpM3J5aHc5cjhycjMzaTczNEBeZWtmMmRrNDNgLS1kMTJzYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&l=20240406063319446A871603231B3A2116&btag=e00048000', 'Format': 'webvtt', 'Version': '4', 'Source': 'MT'}, {'UrlExpire': '1712406814', 'Size': '552', 'LanguageID': '4', 'LanguageCodeName': 'kor-KR', 'Url': 'https://v16m-webapp.tiktokcdn-us.com/865ed98e1bd821916cb7a9fd9f4b871e/6611411e/video/tos/useast8/tos-useast8-v-0068-tx2/fdfa7d3e73144c6a87487f194209ad5d/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=13866&bt=6933&ds=4&ft=4KLMeMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=13&rc=M3J5aHc5cjhycjMzaTczNEBpM3J5aHc5cjhycjMzaTczNEBeZWtmMmRrNDNgLS1kMTJzYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&l=20240406063319446A871603231B3A2116&btag=e00048000', 'Format': 'webvtt', 'Version': '4', 'Source': 'MT'}, {'UrlExpire': '1712406814', 'Size': '524', 'LanguageID': '20', 'LanguageCodeName': 'deu-DE', 'Url': 'https://v16m-webapp.tiktokcdn-us.com/b310dc23c37ac0466773acc807ea8c46/6611411e/video/tos/useast8/tos-useast8-v-0068-tx2/56d4ca298c8d4b8480d7ab6d9095e003/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=13866&bt=6933&ds=4&ft=4KLMeMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=13&rc=M3J5aHc5cjhycjMzaTczNEBpM3J5aHc5cjhycjMzaTczNEBeZWtmMmRrNDNgLS1kMTJzYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&l=20240406063319446A871603231B3A2116&btag=e00048000', 'Format': 'webvtt', 'Version': '4', 'Source': 'MT'}, {'UrlExpire': '1712406814', 'Size': '518', 'LanguageID': '7', 'LanguageCodeName': 'fra-FR', 'Url': 'https://v16m-webapp.tiktokcdn-us.com/058e371ce6a69c5fe6f1419701dd568d/6611411e/video/tos/useast8/tos-useast8-v-0068-tx2/cef860577db847ba9171b386589cb058/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=13866&bt=6933&ds=4&ft=4KLMeMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=13&rc=M3J5aHc5cjhycjMzaTczNEBpM3J5aHc5cjhycjMzaTczNEBeZWtmMmRrNDNgLS1kMTJzYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&l=20240406063319446A871603231B3A2116&btag=e00048000', 'Format': 'webvtt', 'Version': '4', 'Source': 'MT'}, {'UrlExpire': '1712406814', 'Size': '671', 'LanguageID': '6', 'LanguageCodeName': 'rus-RU', 'Url': 'https://v16m-webapp.tiktokcdn-us.com/2ab6545fa892ca43e86616ba68f9c9a4/6611411e/video/tos/useast8/tos-useast8-v-0068-tx2/a4cb0ca73a8e4607856b88051bad6b27/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=13866&bt=6933&ds=4&ft=4KLMeMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=13&rc=M3J5aHc5cjhycjMzaTczNEBpM3J5aHc5cjhycjMzaTczNEBeZWtmMmRrNDNgLS1kMTJzYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&l=20240406063319446A871603231B3A2116&btag=e00048000', 'Format': 'webvtt', 'Version': '4', 'Source': 'MT'}, {'UrlExpire': '1712406814', 'Size': '415', 'LanguageID': '2', 'LanguageCodeName': 'eng-US', 'Url': 'https://v16m-webapp.tiktokcdn-us.com/d4f7484d4bc88432badb939829a35daa/6611411e/video/tos/useast8/tos-useast8-v-0068-tx2/1b0718ece074428088545a369919876b/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=13866&bt=6933&ds=4&ft=4KLMeMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=13&rc=M3J5aHc5cjhycjMzaTczNEBpM3J5aHc5cjhycjMzaTczNEBeZWtmMmRrNDNgLS1kMTJzYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&l=20240406063319446A871603231B3A2116&btag=e00048000', 'Format': 'webvtt', 'Version': '1', 'Source': 'ASR'}, {'UrlExpire': '1712406814', 'Size': '545', 'LanguageID': '9', 'LanguageCodeName': 'spa-ES', 'Url': 'https://v16m-webapp.tiktokcdn-us.com/ff26a3b1f54ad9507773e76f320bcb46/6611411e/video/tos/useast8/tos-useast8-v-0068-tx2/d75f1c7a27b444e4bf6daacca01d28b8/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=13866&bt=6933&ds=4&ft=4KLMeMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=13&rc=M3J5aHc5cjhycjMzaTczNEBpM3J5aHc5cjhycjMzaTczNEBeZWtmMmRrNDNgLS1kMTJzYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&l=20240406063319446A871603231B3A2116&btag=e00048000', 'Format': 'webvtt', 'Version': '4', 'Source': 'MT'}, {'UrlExpire': '1712406814', 'Size': '531', 'LanguageID': '23', 'LanguageCodeName': 'ind-ID', 'Url': 'https://v16m-webapp.tiktokcdn-us.com/8cb11ba26690f4a9224124d8809f1dff/6611411e/video/tos/useast8/tos-useast8-v-0068-tx2/f3e2aadf66fa4a9d8a9d591f2577e98b/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=13866&bt=6933&ds=4&ft=4KLMeMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=13&rc=M3J5aHc5cjhycjMzaTczNEBpM3J5aHc5cjhycjMzaTczNEBeZWtmMmRrNDNgLS1kMTJzYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&l=20240406063319446A871603231B3A2116&btag=e00048000', 'Format': 'webvtt', 'Version': '4', 'Source': 'MT'}, {'UrlExpire': '1712406814', 'Size': '505', 'LanguageID': '34', 'LanguageCodeName': 'ara-SA', 'Url': 'https://v16m-webapp.tiktokcdn-us.com/32e87b5c8f71a353e8d8c412a6051e15/6611411e/video/tos/useast8/tos-useast8-v-0068-tx2/bcb40a530cd145c9b340bfeb88519f00/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=13866&bt=6933&ds=4&ft=4KLMeMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=13&rc=M3J5aHc5cjhycjMzaTczNEBpM3J5aHc5cjhycjMzaTczNEBeZWtmMmRrNDNgLS1kMTJzYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&l=20240406063319446A871603231B3A2116&btag=e00048000', 'Format': 'webvtt', 'Version': '4', 'Source': 'MT'}, {'UrlExpire': '1712406814', 'Size': '676', 'LanguageID': '3', 'LanguageCodeName': 'jpn-JP', 'Url': 'https://v16m-webapp.tiktokcdn-us.com/59b15ce3390a8cb9db7b62994b60e9b4/6611411e/video/tos/useast8/tos-useast8-v-0068-tx2/71d5f613bc2544359f034f7bb70d42a8/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=13866&bt=6933&ds=4&ft=4KLMeMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=13&rc=M3J5aHc5cjhycjMzaTczNEBpM3J5aHc5cjhycjMzaTczNEBeZWtmMmRrNDNgLS1kMTJzYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&l=20240406063319446A871603231B3A2116&btag=e00048000', 'Format': 'webvtt', 'Version': '4', 'Source': 'MT'}, {'UrlExpire': '1712406814', 'Size': '514', 'LanguageID': '8', 'LanguageCodeName': 'por-PT', 'Url': 'https://v16m-webapp.tiktokcdn-us.com/dca64acce775f211363000e5fcc83555/6611411e/video/tos/useast8/tos-useast8-v-0068-tx2/d1c141114c09457ba84b3e01601447ac/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=13866&bt=6933&ds=4&ft=4KLMeMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=13&rc=M3J5aHc5cjhycjMzaTczNEBpM3J5aHc5cjhycjMzaTczNEBeZWtmMmRrNDNgLS1kMTJzYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&l=20240406063319446A871603231B3A2116&btag=e00048000', 'Format': 'webvtt', 'Version': '4', 'Source': 'MT'}, {'UrlExpire': '1712406814', 'Size': '568', 'LanguageID': '10', 'LanguageCodeName': 'vie-VN', 'Url': 'https://v16m-webapp.tiktokcdn-us.com/03530bfd25d711282e804c28b9b418a7/6611411e/video/tos/useast8/tos-useast8-v-0068-tx2/c98de8ab13054ea1903ae6ba6f1944c7/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=13866&bt=6933&ds=4&ft=4KLMeMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=13&rc=M3J5aHc5cjhycjMzaTczNEBpM3J5aHc5cjhycjMzaTczNEBeZWtmMmRrNDNgLS1kMTJzYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&l=20240406063319446A871603231B3A2116&btag=e00048000', 'Format': 'webvtt', 'Version': '4', 'Source': 'MT'}, {'UrlExpire': '1712406814', 'Size': '514', 'LanguageID': '26', 'LanguageCodeName': 'ita-IT', 'Url': 'https://v16m-webapp.tiktokcdn-us.com/b00e69ca42fcb0c2a31413b6792c9283/6611411e/video/tos/useast8/tos-useast8-v-0068-tx2/3b3e208228da4f6eae1fad735a49938d/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=13866&bt=6933&ds=4&ft=4KLMeMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=13&rc=M3J5aHc5cjhycjMzaTczNEBpM3J5aHc5cjhycjMzaTczNEBeZWtmMmRrNDNgLS1kMTJzYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&l=20240406063319446A871603231B3A2116&btag=e00048000', 'Format': 'webvtt', 'Version': '4', 'Source': 'MT'}], 'zoomCover': {'240': 'https://p16-sign.tiktokcdn-us.com/tos-useast8-p-0068-tx2/okejIIcTo2t5EarNwrCXQEfgADL8IMAwGxGqfI~tplv-photomode-zoomcover:240:240.jpeg?x-expires=1712556000&x-signature=Fg48dkv5INoOYtMXv0aOkETB4eY%3D', '480': 'https://p16-sign.tiktokcdn-us.com/tos-useast8-p-0068-tx2/okejIIcTo2t5EarNwrCXQEfgADL8IMAwGxGqfI~tplv-photomode-zoomcover:480:480.jpeg?x-expires=1712556000&x-signature=nGSOyzO3dx4SSx5Z4rLb9Tmz1Ic%3D', '720': 'https://p16-sign.tiktokcdn-us.com/tos-useast8-p-0068-tx2/okejIIcTo2t5EarNwrCXQEfgADL8IMAwGxGqfI~tplv-photomode-zoomcover:720:720.jpeg?x-expires=1712556000&x-signature=5a49jctpzvIVOOijHXlF%2BOeg4kw%3D', '960': 'https://p19-sign.tiktokcdn-us.com/tos-useast8-p-0068-tx2/okejIIcTo2t5EarNwrCXQEfgADL8IMAwGxGqfI~tplv-photomode-zoomcover:960:960.jpeg?x-expires=1712556000&x-signature=93chzvRXYrURoHfCZORzZrPW5bg%3D'}, 'volumeInfo': {'Loudness': -24.7, 'Peak': 0.83176}, 'bitrateInfo': [{'Bitrate': 2150128, 'QualityType': 20, 'GearName': 'normal_540_0', 'PlayAddr': {'DataSize': '4228766', 'Uri': 'v15044gf0000co6o75nog65tienvhoa0', 'UrlList': ['https://v16-webapp-prime.us.tiktok.com/video/tos/useast8/tos-useast8-ve-0068c003-tx2/okwLoICxQMjqIcItEe2TbIwfM5EBrGfxGgIAAI/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=4198&bt=2099&cs=0&ds=6&ft=4KJMyMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=0&rc=OjM5NmYzODg8ZDc5aWhnOEBpM3J5aHc5cjhycjMzaTczNEBeNGBfNjA0Xl4xYC8vYmA2YSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&btag=e00088000&expire=1712406814&l=20240406063319446A871603231B3A2116&ply_type=2&policy=2&signature=650e4a84344b6cf0a4645365a5f7164e&tk=tt_chain_token', 'https://v19-webapp-prime.us.tiktok.com/video/tos/useast8/tos-useast8-ve-0068c003-tx2/okwLoICxQMjqIcItEe2TbIwfM5EBrGfxGgIAAI/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=4198&bt=2099&cs=0&ds=6&ft=4KJMyMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=0&rc=OjM5NmYzODg8ZDc5aWhnOEBpM3J5aHc5cjhycjMzaTczNEBeNGBfNjA0Xl4xYC8vYmA2YSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&btag=e00088000&expire=1712406814&l=20240406063319446A871603231B3A2116&ply_type=2&policy=2&signature=650e4a84344b6cf0a4645365a5f7164e&tk=tt_chain_token'], 'UrlKey': 'v15044gf0000co6o75nog65tienvhoa0_h264_540p_2150128', 'FileHash': '19f382135958ab8c6656ec8aacf13222', 'FileCs': 'c:0-14139-2a07'}, 'CodecType': 'h264'}, {'Bitrate': 1297279, 'QualityType': 2, 'GearName': 'adapt_lowest_1080_1', 'PlayAddr': {'DataSize': '2551424', 'Uri': 'v15044gf0000co6o75nog65tienvhoa0', 'UrlList': ['https://v16-webapp-prime.us.tiktok.com/video/tos/useast8/tos-useast8-ve-0068c002-tx2/oMsEODDlFC4WDhNRbR1UAB4EJ7fIEVQfAmY14E/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=2532&bt=1266&cs=2&ds=4&ft=4KJMyMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=15&rc=Zjo7NGg7Z2VkNWQ8Zmc1aUBpM3J5aHc5cjhycjMzaTczNEAuNi5iYC8wNjExM2EwMS5gYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&btag=e00088000&expire=1712406814&l=20240406063319446A871603231B3A2116&ply_type=2&policy=2&signature=8c15de601756989e1c5cc696745f7350&tk=tt_chain_token', 'https://v19-webapp-prime.us.tiktok.com/video/tos/useast8/tos-useast8-ve-0068c002-tx2/oMsEODDlFC4WDhNRbR1UAB4EJ7fIEVQfAmY14E/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=2532&bt=1266&cs=2&ds=4&ft=4KJMyMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=15&rc=Zjo7NGg7Z2VkNWQ8Zmc1aUBpM3J5aHc5cjhycjMzaTczNEAuNi5iYC8wNjExM2EwMS5gYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&btag=e00088000&expire=1712406814&l=20240406063319446A871603231B3A2116&ply_type=2&policy=2&signature=8c15de601756989e1c5cc696745f7350&tk=tt_chain_token'], 'UrlKey': 'v15044gf0000co6o75nog65tienvhoa0_bytevc1_1080p_1297279', 'FileHash': 'dc38852162ed073f3bf250bf76cddc0f', 'FileCs': 'c:0-14661-6be0'}, 'CodecType': 'h265_hvc1'}, {'Bitrate': 1015871, 'QualityType': 24, 'GearName': 'lower_540_0', 'PlayAddr': {'DataSize': '1997965', 'Uri': 'v15044gf0000co6o75nog65tienvhoa0', 'UrlList': ['https://v16-webapp-prime.us.tiktok.com/video/tos/useast8/tos-useast8-ve-0068c001-tx2/okXDzAHQMwIf2hf2CsXQAcMtIGAjeWnRgn8jqw/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=1984&bt=992&cs=0&ds=6&ft=4KJMyMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=4&rc=NWRlZzhkO2Q8ZjtoMzhmOUBpM3J5aHc5cjhycjMzaTczNEAyNi4yLjQvXjQxYmFgYTQ1YSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&btag=e00088000&expire=1712406814&l=20240406063319446A871603231B3A2116&ply_type=2&policy=2&signature=6735e9349c7f8de941316a42e2615392&tk=tt_chain_token', 'https://v19-webapp-prime.us.tiktok.com/video/tos/useast8/tos-useast8-ve-0068c001-tx2/okXDzAHQMwIf2hf2CsXQAcMtIGAjeWnRgn8jqw/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=1984&bt=992&cs=0&ds=6&ft=4KJMyMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=4&rc=NWRlZzhkO2Q8ZjtoMzhmOUBpM3J5aHc5cjhycjMzaTczNEAyNi4yLjQvXjQxYmFgYTQ1YSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&btag=e00088000&expire=1712406814&l=20240406063319446A871603231B3A2116&ply_type=2&policy=2&signature=6735e9349c7f8de941316a42e2615392&tk=tt_chain_token'], 'UrlKey': 'v15044gf0000co6o75nog65tienvhoa0_h264_540p_1015871', 'FileHash': '607ade7b556af2a1eddfef10dfd01977', 'FileCs': 'c:0-14139-b73b'}, 'CodecType': 'h264'}, {'Bitrate': 791305, 'QualityType': 14, 'GearName': 'adapt_lower_720_1', 'PlayAddr': {'DataSize': '1556301', 'Uri': 'v15044gf0000co6o75nog65tienvhoa0', 'UrlList': ['https://v16-webapp-prime.us.tiktok.com/video/tos/useast8/tos-useast8-pve-0068-tx2/o8wIrGg8TLxoACqefM2tjnACcIQjeIwGINhCAb/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=1544&bt=772&cs=2&ds=3&ft=4KJMyMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=14&rc=PDo6N2dkMzRpOzxmOjs5PEBpM3J5aHc5cjhycjMzaTczNEAzMl9fXi41XjAxMF8zX2AyYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&btag=e00088000&expire=1712406814&l=20240406063319446A871603231B3A2116&ply_type=2&policy=2&signature=9439256511be9a6e49dec9230f4f3bdd&tk=tt_chain_token', 'https://v19-webapp-prime.us.tiktok.com/video/tos/useast8/tos-useast8-pve-0068-tx2/o8wIrGg8TLxoACqefM2tjnACcIQjeIwGINhCAb/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=1544&bt=772&cs=2&ds=3&ft=4KJMyMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=14&rc=PDo6N2dkMzRpOzxmOjs5PEBpM3J5aHc5cjhycjMzaTczNEAzMl9fXi41XjAxMF8zX2AyYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&btag=e00088000&expire=1712406814&l=20240406063319446A871603231B3A2116&ply_type=2&policy=2&signature=9439256511be9a6e49dec9230f4f3bdd&tk=tt_chain_token'], 'UrlKey': 'v15044gf0000co6o75nog65tienvhoa0_bytevc1_720p_791305', 'FileHash': '678f8c849ba141de33e40508c3fc2548', 'FileCs': 'c:0-14664-aa6a'}, 'CodecType': 'h265_hvc1'}, {'Bitrate': 693076, 'QualityType': 25, 'GearName': 'lowest_540_0', 'PlayAddr': {'DataSize': '1363109', 'Uri': 'v15044gf0000co6o75nog65tienvhoa0', 'UrlList': ['https://v16-webapp-prime.us.tiktok.com/video/tos/useast8/tos-useast8-ve-0068c003-tx2/o0ztc2goQIwfuFCIwBMIbG5CGIfrqxmeAATLYj/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=1352&bt=676&cs=0&ds=6&ft=4KJMyMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=5&rc=aDppNGkzM2Q6MzloZDNmO0BpM3J5aHc5cjhycjMzaTczNEAxNS4uXzYwNl8xYC40YTUvYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&btag=e00088000&expire=1712406814&l=20240406063319446A871603231B3A2116&ply_type=2&policy=2&signature=4577cd04a683668ff47fadd09be01fd7&tk=tt_chain_token', 'https://v19-webapp-prime.us.tiktok.com/video/tos/useast8/tos-useast8-ve-0068c003-tx2/o0ztc2goQIwfuFCIwBMIbG5CGIfrqxmeAATLYj/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=1352&bt=676&cs=0&ds=6&ft=4KJMyMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=5&rc=aDppNGkzM2Q6MzloZDNmO0BpM3J5aHc5cjhycjMzaTczNEAxNS4uXzYwNl8xYC40YTUvYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&btag=e00088000&expire=1712406814&l=20240406063319446A871603231B3A2116&ply_type=2&policy=2&signature=4577cd04a683668ff47fadd09be01fd7&tk=tt_chain_token'], 'UrlKey': 'v15044gf0000co6o75nog65tienvhoa0_h264_540p_693076', 'FileHash': '07d3d25dab1150cfcf55d2875e631214', 'FileCs': 'c:0-14139-75e9'}, 'CodecType': 'h264'}, {'Bitrate': 597373, 'QualityType': 28, 'GearName': 'adapt_540_1', 'PlayAddr': {'DataSize': '1174885', 'Uri': 'v15044gf0000co6o75nog65tienvhoa0', 'UrlList': ['https://v16-webapp-prime.us.tiktok.com/video/tos/useast8/tos-useast8-ve-0068c001-tx2/oEYIfCxBQT2IqKGCwbeGeIojctALgPwACoBMIr/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=1166&bt=583&cs=2&ds=6&ft=4KJMyMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=11&rc=ODc6Ojs3ZDhpZ2c7NTo2N0BpM3J5aHc5cjhycjMzaTczNEAyLTE0NjYvNTYxYTItLzBjYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&btag=e00088000&expire=1712406814&l=20240406063319446A871603231B3A2116&ply_type=2&policy=2&signature=259353e67627f3b5987bb6c4dda179c5&tk=tt_chain_token', 'https://v19-webapp-prime.us.tiktok.com/video/tos/useast8/tos-useast8-ve-0068c001-tx2/oEYIfCxBQT2IqKGCwbeGeIojctALgPwACoBMIr/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=unwatermarked&cd=0%7C0%7C0%7C&cv=1&br=1166&bt=583&cs=2&ds=6&ft=4KJMyMzm8Zmo07F2O-4jVIa.QpWrKsd.&mime_type=video_mp4&qs=11&rc=ODc6Ojs3ZDhpZ2c7NTo2N0BpM3J5aHc5cjhycjMzaTczNEAyLTE0NjYvNTYxYTItLzBjYSNeZWtmMmRrNDNgLS1kMTJzcw%3D%3D&btag=e00088000&expire=1712406814&l=20240406063319446A871603231B3A2116&ply_type=2&policy=2&signature=259353e67627f3b5987bb6c4dda179c5&tk=tt_chain_token'], 'UrlKey': 'v15044gf0000co6o75nog65tienvhoa0_bytevc1_540p_597373', 'FileHash': '5ef19ff0a14e9bd688f650953ab291cd', 'FileCs': 'c:0-14664-e94e'}, 'CodecType': 'h265_hvc1'}]}, 'author': {'id': '6646764999833403398', 'shortId': '', 'uniqueId': 'barstoolsports', 'nickname': 'Barstool Sports', 'avatarLarger': 'https://p16-sign-va.tiktokcdn.com/tos-maliva-avt-0068/7310278359605968902~c5_1080x1080.jpeg?lk3s=a5d48078&x-expires=1712556000&x-signature=VOLXyliZNiisJ4qoA9BzOe9swu0%3D', 'avatarMedium': 'https://p16-sign-va.tiktokcdn.com/tos-maliva-avt-0068/7310278359605968902~c5_720x720.jpeg?lk3s=a5d48078&x-expires=1712556000&x-signature=7taJchA4J8LR%2Bi6x7LUSPpgvGBA%3D', 'avatarThumb': 'https://p16-sign-va.tiktokcdn.com/tos-maliva-avt-0068/7310278359605968902~c5_100x100.jpeg?lk3s=a5d48078&x-expires=1712556000&x-signature=mYClk%2FnY2lamLfeuqsgjREgOlac%3D', 'signature': '🗣 Viva La Stool\n\nCheck Out All Of Our Merch Below ⬇️', 'createTime': 0, 'verified': True, 'secUid': 'MS4wLjABAAAAV-FnuTQImr7z9AvHTeDfA1zge-srWKQv8vEEQT5mKno29McR2xS1-br6cXWZUUHx', 'ftc': False, 'relation': 0, 'openFavorite': False, 'commentSetting': 0, 'duetSetting': 0, 'stitchSetting': 0, 'privateAccount': False, 'secret': False, 'isADVirtual': False, 'roomId': '', 'uniqueIdModifyTime': 0, 'ttSeller': False, 'downloadSetting': 0, 'recommendReason': '', 'nowInvitationCardUrl': '', 'nickNameModifyTime': 0, 'isEmbedBanned': False, 'canExpPlaylist': False, 'suggestAccountBind': False}, 'music': {'id': '7352547371709975339', 'title': 'original sound', 'playUrl': 'https://v16-webapp-prime.us.tiktok.com/video/tos/useast5/tos-useast5-v-27dcd7-tx/o88TGEIAQoLaPSkuoe3BfyAQGeE6LHHqECQMvY/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=0&dr=0&er=0&lr=default&cd=0%7C0%7C0%7C0&br=250&bt=125&ft=GcAInInz7ThepB9rXq8Zmo&mime_type=audio_mpeg&qs=6&rc=NmY0OWdoPDllZjYzZmZnN0BpM28zaWs5cnJxcjMzZzU8NEBfNjBjMzYtXl4xMl5eMjM2YSNjMW1lMmQ0cTFgLS1kMS9zcw%3D%3D&btag=e00088000&expire=1712406814&l=20240406063319446A871603231B3A2116&ply_type=3&policy=3&signature=56884d8a0ce4364e5a5ac9e178a45c17&tk=0', 'coverLarge': 'https://p16-sign.tiktokcdn-us.com/tos-useast5-avt-0068-tx/2d12eaf8f6cdc35a61366b5c76f51c43~c5_1080x1080.jpeg?lk3s=a5d48078&x-expires=1712556000&x-signature=aIGaDw%2FD9cFOruYGyJyk5C%2BOy2Q%3D', 'coverMedium': 'https://p16-sign.tiktokcdn-us.com/tos-useast5-avt-0068-tx/2d12eaf8f6cdc35a61366b5c76f51c43~c5_720x720.jpeg?lk3s=a5d48078&x-expires=1712556000&x-signature=c8NRdejU%2FLe65F3oer9jTFPj95s%3D', 'coverThumb': 'https://p16-sign.tiktokcdn-us.com/tos-useast5-avt-0068-tx/2d12eaf8f6cdc35a61366b5c76f51c43~c5_100x100.jpeg?lk3s=a5d48078&x-expires=1712556000&x-signature=P7Pxt07jujjh6NY%2B4cpYx%2B4TTbE%3D', 'authorName': 'James', 'original': False, 'duration': 15, 'scheduleSearchTime': 0, 'collected': False, 'preciseDuration': {'preciseDuration': 15.595063, 'preciseShootDuration': 15.595063, 'preciseAuditionDuration': 15.595063, 'preciseVideoDuration': 15.595063}}, 'challenges': [], 'stats': {'diggCount': 1200000, 'shareCount': 283600, 'commentCount': 6540, 'playCount': 7300000, 'collectCount': '88087'}, 'statsV2': {'diggCount': '1200000', 'shareCount': '283600', 'commentCount': '6540', 'playCount': '7300000', 'collectCount': '88087'}, 'warnInfo': [], 'originalItem': False, 'officalItem': False, 'textExtra': [{'awemeId': '', 'start': 15, 'end': 33, 'hashtagName': '', 'type': 0, 'subType': 0, 'userId': '6738431433789178885', 'isCommerce': False, 'userUniqueId': 'barstooloutdoors', 'secUid': 'MS4wLjABAAAACgUTGP9hILWdcaI5ACTC8vjOHEFfqimB61CxNlXlB4cKF9ikKwvFlS0DI08fummV'}, {'awemeId': '', 'start': 39, 'end': 45, 'hashtagName': '', 'type': 0, 'subType': 0, 'userId': '7350112050763056174', 'isCommerce': False, 'userUniqueId': 'jakeados62g', 'secUid': 'MS4wLjABAAAAH0AG2pVOYFvM5WGzGOJGxw08LCBUaKMEYnX3j7kDo355XXnauhMKmG2H4PSJYWE1'}], 'secret': False, 'forFriend': False, 'digged': False, 'itemCommentStatus': 0, 'takeDown': 0, 'effectStickers': [], 'privateItem': False, 'duetEnabled': True, 'stitchEnabled': True, 'stickersOnItem': [], 'shareEnabled': True, 'comments': [], 'duetDisplay': 0, 'stitchDisplay': 0, 'indexEnabled': True, 'diversificationLabels': ['Hilarious Fails', 'Performance'], 'locationCreated': 'US', 'suggestedWords': ['Getting Winded', 'kids getting the wind knocked out of them', 'winded', 'jump and hang playground', 'fitcore playground', 'playground', 'landscape structures playground', "winded can't breathe", 'people getting winded', 'People Playground'], 'contents': [{'desc': 'Wait for it 💀 @Barstool Outdoors (via:@James) ', 'textExtra': [{'awemeId': '', 'start': 15, 'end': 33, 'hashtagName': '', 'type': 0, 'subType': 0, 'userId': '6738431433789178885', 'isCommerce': False, 'userUniqueId': 'barstooloutdoors', 'secUid': 'MS4wLjABAAAACgUTGP9hILWdcaI5ACTC8vjOHEFfqimB61CxNlXlB4cKF9ikKwvFlS0DI08fummV'}, {'awemeId': '', 'start': 39, 'end': 45, 'hashtagName': '', 'type': 0, 'subType': 0, 'userId': '7350112050763056174', 'isCommerce': False, 'userUniqueId': 'jakeados62g', 'secUid': 'MS4wLjABAAAAH0AG2pVOYFvM5WGzGOJGxw08LCBUaKMEYnX3j7kDo355XXnauhMKmG2H4PSJYWE1'}]}], 'diversificationId': 10002, 'collected': False, 'channelTags': [], 'item_control': {}}
    


# %%
