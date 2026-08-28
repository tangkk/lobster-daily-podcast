# -*- coding:utf-8 -*-
import websocket, hashlib, base64, hmac, json, os, ssl, _thread as thread
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
class Ws_Param(object):
    def __init__(self,APPID,APIKey,APISecret,Text,Voice,Speed=50,Volume=50,Pitch=50):
        self.APPID=APPID; self.APIKey=APIKey; self.APISecret=APISecret; self.Text=Text; self.Voice=Voice; self.CommonArgs={"app_id":APPID,"status":2}; self.BusinessArgs={"tts":{"vcn":Voice,"volume":int(Volume),"rhy":0,"speed":int(Speed),"pitch":int(Pitch),"bgs":0,"reg":0,"rdn":0,"audio":{"encoding":"lame","sample_rate":24000,"channels":1,"bit_depth":16,"frame_size":0}}}; self.Data={"text":{"encoding":"utf8","compress":"raw","format":"plain","status":2,"seq":0,"text":base64.b64encode(Text.encode()).decode()}}
def auth(url,key,secret):
    host=url.split('://',1)[1].split('/',1)[0]; path='/' + url.split('://',1)[1].split('/',1)[1]; date=format_date_time(mktime(datetime.now().timetuple())); origin=f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"; sig=base64.b64encode(hmac.new(secret.encode(),origin.encode(),hashlib.sha256).digest()).decode(); au=base64.b64encode(f'api_key="{key}", algorithm="hmac-sha256", headers="host date request-line", signature="{sig}"'.encode()).decode(); return url+'?'+urlencode({'host':host,'date':date,'authorization':au})
def run_once(requrl,out_path,voice,text,speed=50,volume=50,pitch=50):
    appid=os.environ['XFYUN_APPID']; key=os.environ['XFYUN_API_KEY']; secret=os.environ['XFYUN_API_SECRET']; p=Ws_Param(appid,key,secret,text,voice,speed,volume,pitch); done={'ok':False,'err':None}
    def msg(ws,m):
        o=json.loads(m); code=o['header'].get('code',-1)
        if code!=0: done['err']=str(o); ws.close(); return
        if 'payload' in o and 'audio' in o['payload']:
            a=o['payload']['audio'].get('audio','')
            if a: open(out_path,'ab').write(base64.b64decode(a))
            if o['payload']['audio'].get('status')==2: done['ok']=True; ws.close()
    def op(ws): thread.start_new_thread(lambda: ws.send(json.dumps({'header':p.CommonArgs,'parameter':p.BusinessArgs,'payload':p.Data},ensure_ascii=False)),())
    w=websocket.WebSocketApp(auth(requrl,key,secret),on_message=msg,on_error=lambda ws,e: done.update(err=str(e))); w.on_open=op; w.run_forever(sslopt={'cert_reqs':ssl.CERT_NONE});
    if done['err'] or not done['ok']: raise RuntimeError(done['err'] or 'TTS did not complete')
def load_profile(name):
    path=os.path.join(os.path.dirname(__file__),'voice_profiles',name+'.json'); return json.load(open(path,encoding='utf-8')) if os.path.exists(path) else {}
