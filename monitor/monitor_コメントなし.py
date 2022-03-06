import os, tweepy, requests, json, csv, requests, pickle
from dotenv import load_dotenv 
from requests_oauthlib import OAuth1 
from requests_oauthlib import OAuth2 
file = "../ref/ReportedTWT.txt" 
file2 = "../ref/BeMonitored.txt" 
load_dotenv("env") 
WH_URL = os.getenv("SLWHurl") 

from ref.TWMtool import TWP
bearer_token = os.getenv("BearerToken") 
headers = {"Authorization": "Bearer {}".format(bearer_token)} 

with open(file2, 'rb') as fb2: 
    BeMon = pickle.load(fb2)
    for BeMonID in BeMon: 
        url = "https://api.twitter.com/2/users/"+str(BeMonID)+"/tweets" 
        params7 = {"exclude":["retweets,replies"],"max_results":100, "expansions":"referenced_tweets.id,author_id","tweet.fields":"created_at,public_metrics", "user.fields":"name"}
        r7 = requests.request("get", url, headers=headers, params=params7).json()
        R = 0 
        L = 0 

        for D in r7["data"]: 
            R = R+D["public_metrics"]["retweet_count"]
            L = L+D["public_metrics"]["like_count"]

        TC = r7["meta"]["result_count"]    
        print("TWitterID: "+str(BeMonID)+"のツイートを監視中") 
        print("Retweets: "+str(R))
        print("Likes: "+str(L))
        print("TweetsCount: " + str(r7["meta"]["result_count"]))
        print("AverageRetweets: "+str(R/TC))
        print("AverageLikes: "+str(L/TC))

        params8 = {"expansions":"referenced_tweets.id,author_id","tweet.fields":"created_at,public_metrics", "user.fields":"name"}     
        for D in r7["data"]: 
            ID = D["id"]
            RPT = D["public_metrics"]["reply_count"]
            RT = D["public_metrics"]["retweet_count"]
            LT = D["public_metrics"]["like_count"]

            with open(file,'rb') as f: 
                RTWTID = pickle.load(f)
                if ID in RTWTID: 
                    print("ID: "+str(ID)+" レポート済IDのため処置なし。")
                else:
                    if RT >= R/TC*3 and LT >= L/TC*1.5: 
                        N1 = "Tweet監視「臨時リポート_ReTweet＆いいね多数」\n\n" 
                        N2 = "↓の既発信TweetのReTweet数が目標突破\n\n"
                        url2 =  "https://api.twitter.com/2/tweets/"+str(D["id"])
                        r8 = requests.request("get", url2,params=params8, headers=headers).json()
                        N3 = "Tweet発信元: "+r8["includes"]["users"][0]["name"]+"\n"
                        N4 = "発信日時（Ztime）: "+r8["data"]["created_at"]+"\n"
                        N5 = "ReTweet数: "+str(RT)+"　（参考）過去100Tweetの平均ReTweet数は"+str(int(R/TC))+"\n"
                        N6 = "いいねの数: "+str(LT)+"　（参考）過去100Tweetの平均いいね数は"+str(int(L/TC))+"\n"
                        N7 = "リプライ数: "+str(RPT)+"\n\n"
                        N8 = "～～～Tweet本文（冒頭40文字）ここから～～～: \n"+D["text"][0:80]+"\n～～～Tweet本文ここまで～～～\n\n"
                        params6 = {"query":str(D["id"])+" is:retweet", "max_results":50, "expansions":"author_id"}
                        N9 = "ReTweet者一覧(20名抽出）: "+"\n"
                        url3 = "https://api.twitter.com/1.1/statuses/retweets/"+str(D["id"])+".json"
                        param4 = {"count":20} 
                        RTD = TWP().twi1(params=param4, url=url3) 
                        SlackTXT = N1+N2+N3+N4+N5+N6+N7+N8+N9
                        for N in RTD:
                            SlackTXT = SlackTXT + N["user"]["name"]+"\n"
                        SlackTXT = SlackTXT + "Tweet監視「臨時リポート_ReTweet多数」以上"
                        requests.post(WH_URL, data=json.dumps({"text":SlackTXT}))
                        with open(file, 'wb') as fb:
                            RTWTID.append(ID)
                            pickle.dump(RTWTID, fb)
                            print("「臨時リポート_ReTweet多数」発行、ツイートID "+str(ID)+"を既報告ツイートIDリストに加えました。")
                
                

                    elif D["public_metrics"]["retweet_count"] >= R/TC*3:
                        N1 = "Tweet監視「臨時リポート_炎上の可能性あり」\n\n"
                        N2 = "↓の既発信TweetのReTweet数が目標突破の一方、いいねの数は大きく伸びず。\n\n"
                        url2 =  "https://api.twitter.com/2/tweets/"+str(D["id"])
                        r8 = requests.request("get", url2,params=params8, headers=headers).json()
                        N3 = "Tweet発信元: "+r8["includes"]["users"][0]["name"]+"\n"
                        N4 = "発信日時（Ztime）: "+r8["data"]["created_at"]+"\n"
                        N5 = "ReTweet数: "+str(RT)+"　（参考）過去100Tweetの平均ReTweet数は"+str(int(R/TC))+"\n"
                        N6 = "いいねの数: "+str(LT)+"　（参考）過去100Tweetの平均いいね数は"+str(int(L/TC))+"\n"
                        N7 = "リプライ数: "+str(RPT)+"\n\n"
                        N8 = "～～～Tweet本文（冒頭40文字）ここから～～～: \n"+D["text"][0:80]+"\n～～～Tweet本文ここまで～～～\n\n"
                        params6 = {"query":str(D["id"])+" is:retweet", "max_results":50, "expansions":"author_id"}
                        N9 = "ReTweet者一覧(20名抽出）: "+"\n"
                        url3 = "https://api.twitter.com/1.1/statuses/retweets/"+str(D["id"])+".json"
                        param4 = {"count":20}
                        RTD = TWP().twi1(params=param4, url=url3)
                        SlackTXT = N1+N2+N3+N4+N5+N6+N7+N8+N9
                        for N in RTD:
                            SlackTXT = SlackTXT + N["user"]["name"]+"\n"
                        SlackTXT = SlackTXT + "Tweet監視「臨時リポート_ReTweet多数」以上"
                        requests.post(WH_URL, data=json.dumps({"text":SlackTXT}))
                        with open(file, 'wb') as fb:
                            RTWTID.append(ID)
                            pickle.dump(RTWTID, fb)
                            print("「臨時リポート_ReTweet多数」発行、ツイートID "+str(ID)+"を既報告ツイートIDリストに加えました。")
