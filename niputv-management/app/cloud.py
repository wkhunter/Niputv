# -*- coding: utf-8 -*-
from app import db
import re
from qiniu import Auth, put_file, etag, urlsafe_base64_encode, BucketManager, PersistentFop, build_op, op_save
import qiniu.config
from app.Database.db_videofile import Bangumi_video

access_key = ''
secret_key = ''

#通用
def Get_UploadToken(bucket_name, key, outtime):
    q = Auth(access_key, secret_key)
    token = q.upload_token(bucket_name, key, int(outtime))
    return token

def Get_coverupload_token(bucket_name, key, outtime):
    q = Auth(access_key, secret_key)
    token = q.upload_token(bucket_name, key, int(outtime))
    return token

def bangumi_cover_transcoding(key,sizi):
    q = Auth(access_key, secret_key)
    
    #要转码的文件所在的空间和文件名。
    bucket = 'cover-cache'

    #转码是使用的队列名称。
    #pipeline = 'mpsdemo'

    #要进行转码的转码操作。
    if sizi == 'min':
        fops = 'imageView2/2/w/450/h/600/format/jpg/q/75|imageslim'
        newkey = 'bangumi/cover/' + key
    else:
        fops = 'imageView2/2/w/120/h/160/format/jpg/q/75|imageslim'
        newkey = 'bangumi/cover/min/' + key
    #可以对转码后的文件进行使用saveas参数自定义命名，当然也可以不指定文件会默认命名并保存在当前空间
    saveas_key = urlsafe_base64_encode('video-cover:'+ newkey)

    fops = fops+'|saveas/'+saveas_key
    pfop = PersistentFop(q, bucket)#, pipeline

    ops = []
    ops.append(fops)
    ret, info = pfop.execute(key, ops, 1)
    print(info)

def video_transcoding(key, pxtype):

    if pxtype == '360p':
        video_sizi = '640x360'
        video_kbps = '250k'
        video_mp3kbps = '128k'

    if pxtype == '480p':
        video_sizi = '852x480'
        video_kbps = '550k'
        video_mp3kbps = '192k'

    if pxtype == '720p':
        video_sizi = '1280x720'
        video_kbps = '850k'
        video_mp3kbps = '230k'

    if pxtype == '1080p':
        video_sizi = '1920x1080'
        video_kbps = '1000k'
        video_mp3kbps = '320k'

    if pxtype == '2k':
        video_sizi = '2560x1440'
        video_kbps = '3200k'
        video_mp3kbps = '320k'

    if pxtype == '4k':
        video_sizi = '3840x2160'
        video_kbps = '4000k'
        video_mp3kbps = '320k'

    q = Auth(access_key, secret_key)

    #要转码的文件所在的空间和文件名。
    bucket = 'video-cache'
    key = str(key)
    filekey = str(key)

    #转码是使用的队列名称。
    pipeline = 'transcoding'

    #要进行转码的转码操作。
    fops = 'avthumb/mp4/s/'+ video_sizi +'/vb/'+ video_kbps +'/ab/'+ video_mp3kbps +'/acodec/libmp3lame'

    #生成新的文件名
    name = key.split(".")[0]
    key_tpye = key.split(".")[1]
    key = name + '-' + pxtype + '.'+ 'mp4'

    #可以对转码后的文件进行使用saveas参数自定义命名，当然也可以不指定文件会默认命名并保存在当前空间
    saveas_key = urlsafe_base64_encode('video-store:' + "bangumi/" + key)

    fops = fops+'|saveas/'+saveas_key
    pfop = PersistentFop(q, bucket, pipeline)
    ops = []
    ops.append(fops)
    ret, info = pfop.execute(filekey, ops, 1)
    print(info)
    #assert ret['persistentId'] is not None

def generate_videoabbreviation_cover(coverkey,videokey):
    q = Auth(access_key, secret_key)
    bucket = 'video-cache'
    key = videokey

    #要进行转码的转码操作。
    fops = 'vframe/jpg/offset/20/w/300/h/168'
    #可以对转码后的文件进行使用saveas参数自定义命名，当然也可以不指定文件会默认命名并保存在当前空间
    saveas_key = urlsafe_base64_encode('video-cover:'+ 'bangumi/video/cover/' +coverkey+'.jpg')
    fops = fops+'|saveas/'+saveas_key
    pfop = PersistentFop(q, bucket)
    ops = []
    ops.append(fops)
    ret, info = pfop.execute(key, ops, 1)
    return coverkey+'.jpg'

#删除视频
def del_bangumivideo_filekey(key):

    #获取该视频
    videodata = Bangumi_video.query.filter_by(filekey = key).first()

    if(videodata):

        filename = videodata.filekey
        ftype = filename.split('.')[-1]
        fname = filename.split(".")[0]
        fname = 'bangumi/' + fname
        q = Auth(access_key, secret_key)
        bucket = BucketManager(q)
        bucket_name = 'video-store' #需要删除的储存桶
        
        del_360 = ''
        del_480 = ''
        del_720 = ''
        del_1080 = ''
        del_2k = ''
        del_4k = ''

        if videodata.clear360 == 1:
            del_360 = fname + '-360p.mp4'
            ret, info = bucket.delete(bucket_name, del_360)
            
        if videodata.clear480 == 1:
            del_480 = fname + '-480p.mp4'
            ret, info = bucket.delete(bucket_name, del_480)

        if videodata.clear720 == 1:
            del_720 = fname + '-720p.mp4'
            ret, info = bucket.delete(bucket_name, del_720)

        if videodata.clear1080 == 1:
            del_1080 = fname + '-1080p.mp4'
            ret, info = bucket.delete(bucket_name, del_1080)

        db.session.delete(videodata)
        db.session.commit()

def del_bangumi_cover(key):
    q = Auth(access_key, secret_key)
    bucket = BucketManager(q)
    bucket_name = 'video-cover' #需要删除的储存桶
    key1 = 'bangumi/cover/' + key
    key2 = 'bangumi/cover/min' + key
    ret, info = bucket.delete(bucket_name, key1)
    ret, info = bucket.delete(bucket_name, key2)