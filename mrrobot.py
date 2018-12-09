#import libraries
#for reddit
import praw
#for data visualisaton
import plotly
import plotly.graph_objs as go
import requests
import nltk
import time
#for configurations
import yaml
from nltk import sent_tokenize
from bs4 import BeautifulSoup
from InstagramAPI import InstagramAPI


all_phrases = []
reddit_comments = []

# Function that counts the number of keywords in phrases list
def collect_stat(keywords, phrases):
        result = {}
        for keyword in keywords:
                result[keyword] = 0
                for phrase in phrases:
                        if (keyword in phrase):
                                result[keyword]+=1
        return result


# Loading configuration from config.yaml
print('Loading configuration...')
try:
        with open('config.yaml', 'r') as stream:
                CONFIG = yaml.load(stream)
                #print(CONFIG)

except Exception as exc:
        print('Cannot load configuration: %s' % str(exc))
        sys.exit(1)


print('Loading NLTK libraries...')
nltk.download('punkt')

# Collect data from mr. Robot Script 
for episode in range(1,10):
    url = "https://raw.githubusercontent.com/lenchevsky/huco_data/master/s01e0%s.htm" % episode
    response = requests.request("GET", url)

    soup = BeautifulSoup(response.text,"html.parser")
    result = soup.find("div", {"class":"scrolling-script-container"})
    all_phrases.extend(sent_tokenize(result.text))


# Log into Reddit
reddit = praw.Reddit(client_id=CONFIG['reddit_client'],
                     client_secret=CONFIG['reddit_secret'],
                     user_agent='mrrobot.py (by /u/lz_terner)',
                     username=CONFIG['reddit_username'],
                     password=CONFIG['reddit_password'])

# Get comments from Reddit submission
n=0
for submission in reddit.subreddit('MrRobot').hot(limit=CONFIG['reddit_submission_limit']):
    n+=1
    print('Getting Reddit Submission %s of %s...' % (n, CONFIG['reddit_submission_limit']))
    reddit_comments.append(submission.title)
    for comment in submission.comments.list():
            try:
                    reddit_comments.append(comment.body)
            except:
                    pass        
    
# Log into Instagram       
api = InstagramAPI(CONFIG['instagram_username'],CONFIG['instagram_password'])
if (api.login()):
    time.sleep(2)

    instagram_comments = {}

    # For each language collect tagged posts and their comments
    for language in CONFIG['languages']:

        has_more_hashtags = True
        hashtag_max_id = ''
        hashtags = []
    
        instagram_comments[language['name']] = []

        max_hashtag_post_count = CONFIG['instagram_limit_hashtag_post']
        max_comments_count = CONFIG['instagram_limit_comments']
        hastag = language['instagram_hashtag']


        while has_more_hashtags:
                api.getHashtagFeed(hastag,hashtag_max_id)
                for tagged_post in api.LastJson['items']:
                            hashtags.append(str(tagged_post['pk']))

                has_more_hashtags = api.LastJson.get('more_available', False)

                if len(hashtags)>=max_hashtag_post_count:
                                    has_more_hashtags = False

                print('Received %s Instagram post tagged with #%s hastag...' % (len(hashtags), hastag))

                if has_more_hashtags:
                        hashtag_max_id = api.LastJson.get('next_max_id', '')
                        time.sleep(2)

        
        print('Today we received %s post tagged with #%s hastag' % (len(hashtags), hastag))


        parsed_post_num = 1


        for media_id in hashtags:
                try:
                        print('Getting comments for post %d of %d...' % (parsed_post_num, len(hashtags)))
                        parsed_post_num+=1

                        has_more_comments = True
                        comment_max_id = ''

                        while has_more_comments:
                                api.getMediaComments(media_id, max_id=comment_max_id)
                                instagram_comments[language['name']].append(api.LastJson['caption']['text'])
                                for comment in api.LastJson['comments']:
                                            instagram_comments[language['name']].append(comment['text'])

                                has_more_comments = api.LastJson.get('has_more_comments', False)
                            
                                if len(comments)>=max_comments_count:
                                            has_more_comments=False

                                if has_more_comments:
                                        comment_max_id = api.LastJson.get('next_max_id', '')
                                        time.sleep(2)
                                    
                except:
                        #print("Can't parse media_id %s" % media_id)
                        pass
    
else:
    print("Can't login!")


script_plotly_data = []
reddit_plotly_data = []
instagram_plotly_data = []

# Create bars for our graphs
for meta in CONFIG['languages']:
        print('Looking for %s keywords in the script' % meta['name'])
        script_data_dic = collect_stat(meta['keywords'], all_phrases)
        script_plotly_data.append(go.Bar(
                x=list(script_data_dic.keys()),
                y=list(script_data_dic.values()),
                name=meta['name']
        ))

        print('Looking for %s keywords in the Reddit' % meta['name'])
        reddit_data_dic = collect_stat(meta['keywords'], reddit_comments)
        reddit_plotly_data.append(go.Bar(
                x=list(reddit_data_dic.keys()),
                y=list(reddit_data_dic.values()),
                name=meta['name']
        ))

        print('Looking for %s keywords in the Instagram' % meta['name'])
        instagram_data_dic = collect_stat(meta['keywords'], instagram_comments[language['name']])
        instagram_plotly_data.append(go.Bar(
                x=list(instagram_data_dic.keys()),
                y=list(instagram_data_dic.values()),
                name=meta['name']
        ))


layout = go.Layout(
    barmode='stack'
)

fig_script = go.Figure(data=script_plotly_data, layout=layout)
plotly.offline.plot(fig_script, filename='script.html', auto_open=True)

fig_reddit = go.Figure(data=reddit_plotly_data, layout=layout)
plotly.offline.plot(fig_reddit, filename='reddit.html', auto_open=True)

fig_instagram = go.Figure(data=instagram_plotly_data, layout=layout)
plotly.offline.plot(fig_instagram, filename='instagram.html', auto_open=True)