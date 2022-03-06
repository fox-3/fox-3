# ツイート監視及びレポート用プログラム
# 任意のツイッターアカウント(複数指定可能)の過去のツイート最大１００件をチェックし、Buzzっている、もしくは炎上している可能性があればSlackへレポートを発出する。
# 本プログラムをタスクスケジューラ（Windows）、cron（Unix,Linux）で任意のスケジュールで実行すれば自動監視が可能となる。
# 注意点として、一度レポートが発出されたツイートは今後レポートされない。つまり、追跡レポート機能は備わっていない。当該機能追加は追加開発により可能。
# 用いたTwitterAPIは、GET /2/users/:id/tweets, GET /2/tweets/:id, GET statuses/retweets/:id
# Slackへのレポート発信は、SlackのWebhookURLを通じて行う。
# （注意）本プログラムを使用するためには、envファイルにTwitterAPI認証情報及びSlack WebhookURLを記述しなければならない。認証情報等は各人で取得しなければならない。
#  なお、Bemonitored.txt及びReportedTWT.txtはpickleモジュールで変換して記述してあるので、単純にファイルを開くだけでは認証情報読み取り不可。pickle使えば復元できるので気休め程度だけど。

import os, tweepy, requests, json, csv, requests, pickle #必要なモジュールをインポート
from dotenv import load_dotenv #dotenvモジュールをインポート。
                                # monitor.pyと同じフォルダ内に配置したファイル「env」内に保存したSlackのWebhookURL及びTwitterAPI認証情報を環境変数として呼び出すため（プログラム中に認証情報を記述したくないので。）。
from requests_oauthlib import OAuth1 #OAuth1.0認証用のモジュールをインポート。TwitterAPIの利用にOAuth認証が必要なため。
from requests_oauthlib import OAuth2 #OAuth2.0認証用モジュール
file = "../ref/ReportedTWT.txt" #レポート済みツイートIDが列挙されたファイルのパスを指定
file2 = "../ref/BeMonitored.txt" #監視対象ツイートIDが列挙されたファイルのパスを指定
load_dotenv("env") # refフォルダ内のファイル「env」内に保存したTwitterAPI認証情報を環境変数に追加。
WH_URL = os.getenv("SLWHurl") #↑で追加した環境変数から、SlackのWebhookURLを呼び出し。

from ref.TWMtool import TWP
# ↑は別途作成したTWMtool.pyに記述したクラスからTWPメソッドを呼び出すもの。既作成のものを再利用したかったので。

bearer_token = os.getenv("BearerToken") #TwitterAPI認証情報のひとつ。
headers = {"Authorization": "Bearer {}".format(bearer_token)} #TwitterAPIへのHTTPリクエストヘッダーを定義

with open(file2, 'rb') as fb2: #monitor.pyと同じフォルダ内に配置したファイル「BeMonitored.txt」から監視対象ツイッターアカウントIDのリストを呼び出し。
                                # つまり、このプログラムで任意の複数のツイッターIDのツイートを一気に監視できる。
    BeMon = pickle.load(fb2)
    for BeMonID in BeMon: # リストから一つずつツイッターIDを呼び出し、TwitterAPIへのHTTPリクエストURLを作成し、次いでr7にリクエストレスポンスをjson型で格納
                            # r7には監視対象ツイッターIDによる最新ツイート100件分（タイムライン）のデータが格納されており、１件分のデータには本文、IDだけでなく大量のメタデータ（リツイート数をはじめ）も含まれている。
        url = "https://api.twitter.com/2/users/"+str(BeMonID)+"/tweets" # TwitterAPIへのリクエストはURL、ヘッダ、ボディ（パラメータ）により構成される。公式HPのドキュメント記載の文法に従って組み立て。
        params7 = {"exclude":["retweets,replies"],"max_results":100, "expansions":"referenced_tweets.id,author_id","tweet.fields":"created_at,public_metrics", "user.fields":"name"}
        r7 = requests.request("get", url, headers=headers, params=params7).json()
        R = 0 # 変数Ｒはツイート数を格納するもの。0に↓の処理でメタデータ内から引き出したツイート毎リツイート数を積算し、ツイート100件分の総リツイート数把握
        L = 0 # 変数Ｌはいいね数を格納するもの。

        for D in r7["data"]: # ↑で説明した積算処理
            R = R+D["public_metrics"]["retweet_count"]
            L = L+D["public_metrics"]["like_count"]

        TC = r7["meta"]["result_count"]    # 変数TCはr7に格納されているツイートの件数。リクエストしたのは100件だが、過去を遡っても100件未満しかツイートされていない可能性あるので。
        print("TWitterID: "+str(BeMonID)+"のツイートを監視中") # ここから先６行は、処理中のメッセージ出力部分。Slackにレポートが発信されればいいのでこのメッセージは不必要なのだが、メンテナンス性確保のため残した。
        print("Retweets: "+str(R))
        print("Likes: "+str(L))
        print("TweetsCount: " + str(r7["meta"]["result_count"]))
        print("AverageRetweets: "+str(R/TC))
        print("AverageLikes: "+str(L/TC))

        params8 = {"expansions":"referenced_tweets.id,author_id","tweet.fields":"created_at,public_metrics", "user.fields":"name"}
        # ↑の変数params8は↓の繰り返し処理の中で特定ツイートに関する情報をTwitterAPIにリクエストする際に用いるもの。
        
        for D in r7["data"]: #ここから先は、ツイート毎のリプライ数、リツイート数、いいね数を把握し、それらを過去実績と照らし合わせてBuzz/炎上評価、次いで必要に応じレポート作成をするループ処理
            ID = D["id"]
            RPT = D["public_metrics"]["reply_count"]
            RT = D["public_metrics"]["retweet_count"]
            LT = D["public_metrics"]["like_count"]

            with open(file,'rb') as f: 
                RTWTID = pickle.load(f)
                if ID in RTWTID: # レポート済のツイートIDであれば、以後の処理は行わない。
                    print("ID: "+str(ID)+" レポート済IDのため処置なし。")
                else:
                    if RT >= R/TC*3 and LT >= L/TC*1.5: # Buzz評価基準、リツイート数は過去平均より３倍以上、いいね数は過去平均より1.5倍以上
                        N1 = "Tweet監視「臨時リポート_ReTweet＆いいね多数」\n\n" # 以下、Slackへ発信されるレポート文作成処理
                        N2 = "↓の既発信TweetのReTweet数が目標突破\n\n"
                        url2 =  "https://api.twitter.com/2/tweets/"+str(D["id"])
                        r8 = requests.request("get", url2,params=params8, headers=headers).json() #このリクエストで特定ツイートに関する情報を入手
                        # R7（タイムライン取得用）で特定ツイートに関する情報は大体入手出来ているが、一部情報は特定ツイートを狙い撃ちにしたAPIを用いないと得られないので、そのAPI宛に追加リクエストをしている。
                        N3 = "Tweet発信元: "+r8["includes"]["users"][0]["name"]+"\n"
                        N4 = "発信日時（Ztime）: "+r8["data"]["created_at"]+"\n"
                        N5 = "ReTweet数: "+str(RT)+"　（参考）過去100Tweetの平均ReTweet数は"+str(int(R/TC))+"\n"
                        N6 = "いいねの数: "+str(LT)+"　（参考）過去100Tweetの平均いいね数は"+str(int(L/TC))+"\n"
                        N7 = "リプライ数: "+str(RPT)+"\n\n"
                        N8 = "～～～Tweet本文（冒頭40文字）ここから～～～: \n"+D["text"][0:80]+"\n～～～Tweet本文ここまで～～～\n\n"
                        params6 = {"query":str(D["id"])+" is:retweet", "max_results":50, "expansions":"author_id"}
                        N9 = "ReTweet者一覧(20名抽出）: "+"\n"
                        url3 = "https://api.twitter.com/1.1/statuses/retweets/"+str(D["id"])+".json" # リツイート関連の情報をリクエストするTwitterAPI URL
                        param4 = {"count":20} #取得するリツイート数を20に指定（レポートにリツイート者名を全部載せると冗長なので）
                        RTD = TWP().twi1(params=param4, url=url3) #別に作成したTWMtool.pyのTWPクラスを再利用（楽をした）
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
                        #print(datetime.strptime(r8["data"]["created_at"], '%a %b %d %H:%M:%S %z %Y'))
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
