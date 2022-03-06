## ReadMe
# ツイート監視及びレポート用プログラム
- 任意のツイッターアカウント(複数指定可能)の過去のツイート最大１００件をチェックし、Buzzっている、もしくは炎上している可能性があればSlackへレポートを発出する。仕組みは、monitor.py内のスクリプト及びコメント参照
- 本プログラムをタスクスケジューラ（Windows）、cron（Unix,Linux）で任意のスケジュールで実行すれば自動監視が可能となる。
- 注意点として、一度レポートが発出されたツイートは今後レポートされない。つまり、追跡レポート機能は備わっていない。当該機能追加は追加開発により可能。
- 用いたTwitterAPIは、GET /2/users/:id/tweets, GET /2/tweets/:id, GET statuses/retweets/:id
- Slackへのレポート発信は、SlackのWebhookURLを通じて行う。
- （注意）本プログラムを使用するためには、envファイルにTwitterAPI認証情報及びSlack WebhookURLを記述しなければならない。認証情報等は各人で取得しなければならない。
  -  なお、Bemonitored.txt及びReportedTWT.txtはpickleモジュールで変換して記述してあるので、単純にファイルを開くだけでは認証情報読み取り不可。pickle使えば復元できるので気休め程度だけど。
