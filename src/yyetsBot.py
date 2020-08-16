# -*- coding: utf-8 -*-
import requests
import config

import random
import json

logger = config.setup_log()


def show_resource(name):
    """
    搜索资源用的
    :param name:
    :return:
    """
    url = "http://pc.zmzapi.com/index.php"

    params = {
        "g": "api/pv3",
        "m": "index",
        "accesskey": "519f9cab85c8059d17544947k361a827",
        "a": "search",
        "k": "{}".format(name)
    }
    headers = {
        'User-Agent': '{}'.format(random.choice(config.UserAgent))
    }

    response = requests.request("GET", url, params=params, headers=headers)
    logger.info("查询内容:{}，返回结果:{}".format(name, response.text))
    text = json.loads(response.text)
    # 处理返回数据
    if len(text['data']) == 0:
        logger.warning("查询内容:{}，返回结果空，查询无结果".format(name))
        return None
    else:
        data = []
        for item in text['data']:
            poster_url = item.get('poster')
            id = item.get('id')
            cnname = item.get('cnname')
            channel_cn = item.get('channel_cn')
            data.append([id, poster_url, cnname, channel_cn])
        return data


def search_resource(video_id):
    """
    这里根据ID查询资源信息，获取包含了剧集，下载链接信息
    :param video_id:
    :return:
    """
    url = "http://pc.zmzapi.com/index.php"

    params = {
        "g": "api/pv3",
        "m": "index",
        "client": "5",
        "accesskey": "519f9cab85c8059d17544947k361a827",
        "a": "resource",
        "id": "{}".format(video_id)
    }
    headers = {
        'User-Agent': '{}'.format(random.choice(config.UserAgent))
    }

    response = requests.request("GET", url, params=params, headers=headers)
    text = json.loads(response.text)
    # 处理返回数据
    if text['status'] != 1:
        logger.warning("查询ID:{}，无下载资源提供".format(video_id))
        return None
    else:
        return text['data'].get('list')


def search_top_resource(top_num):
    """
    这里根据ID查询资源信息，获取包含了剧集，下载链接信息
    :param video_id:
    :return:
    """
    url = "http://pc.zmzapi.com/index.php"

    params = {
        "g": "api/pv3",
        "m": "index",
        "client": "5",
        "accesskey": "519f9cab85c8059d17544947k361a827",
        "a": "hot",
        "limit": "{}".format(top_num)
    }
    headers = {
        'User-Agent': '{}'.format(random.choice(config.UserAgent))
    }

    response = requests.request("GET", url, params=params, headers=headers)
    text = json.loads(response.text)
    # 处理返回数据
    if text['status'] != 1:
        logger.warning("搜索top{}无结果，返回如下信息:{}".format(top_num, response.text))
        return None
    else:
        return text['data']


def download_poster(name):
    """
    下载视频海报
    :param name:
    :return:
    """
    try:
        data = show_resource(name)
        if data is not None:
            img_data = []
            for i in data:
                id = i[0]
                poster_url = i[1]
                cnname = i[2]
                channel_cn = i[3]
                headers = {
                    'User-Agent': '{}'.format(random.choice(config.UserAgent))
                }
                response = requests.request("GET", poster_url, headers=headers, verify=False)
                if response.status_code == 200:
                    img_data.append([id, channel_cn, cnname, response.content])
                    logger.info("资源类型:{},资源名称:{} 提交下载任务正常".format(channel_cn, cnname))
                else:
                    logger.warning("提交下载任务异常，返回结果:{}".format(response.text))
            return img_data
        else:
            logger.warning("搜索资源无结果")
            return None
    except Exception as e:
        logger.exception("下载海报出错，抛出异常:{}".format(e))
        return None


def get_season_count(videoID):
    """
    获取季数
    :param id:
    :return:
    """
    try:
        data = search_resource(videoID)
        # 这里做下区分，由于韩剧这里的season固定是101，而美剧日剧则是真实的季数
        check = data[0].get('season')
        if check == "101":
            season_count = 1
        else:
            season_count = check
        logger.info("资源ID:{}，季数:{}".format(videoID, season_count))
        return season_count
    except Exception as e:
        logger.exception('资源ID:{}，获取季数失败，抛出异常:{}'.format(videoID, e))


def get_episode_count(seasonCount, videoID):
    """
    获取当季集数
    :param seasonCount:
    :param videoID:
    :return:
    """
    try:
        data = search_resource(videoID)
        if data is None:
            logger.warning('资源ID:{}，无下载资源提供'.format(videoID))
            return None
        else:
            for item in data:
                if item.get('season') == seasonCount or item.get('season') == "101":
                    episodeCount = item.get('episodes')[0].get('episode')
                    logger.info(
                        '视频ID:{}，季数:{}，集数:{}'.format(videoID, seasonCount, episodeCount))
                    return episodeCount
                else:
                    pass
    except Exception as e:
        logger.exception('资源ID:{}，获取集数失败，抛出异常:{}'.format(videoID, e))


def get_tv_link(videoID, seasonCount, episodeCount):
    """
    获取对应剧集的下载链接
    :param videoID:
    :param seasonCount:
    :param episodeCount:
    :return:
    """
    try:
        data = search_resource(videoID)
        if data is None:
            logger.warning('资源ID:{}，无下载资源提供'.format(videoID))
            return None
        else:
            for item in data:
                if item.get('season') == seasonCount or item.get('season') == "101":
                    episodes = item.get('episodes')
                    for i in episodes:
                        if i.get('episode') == episodeCount:
                            return iter_video_link('tv', i.get('files'))
                        else:
                            pass
                else:
                    logger.error('资源ID:{}，查无剧集'.format(videoID))
    except Exception as e:
        logger.exception('资源ID:{}，获取电视剧下载链接失败，抛出异常:{}'.format(videoID, e))


def iter_video_link(files_type, files):
    """
    批量获取对应集数电视剧，为了兼容老电视剧，同时也获取了电驴链接
    暂时没想到什么好方式兼容获取电影下载链接的方式，先用这个粗糙的方式获取吧
    :param files:
    :return:
    """
    try:
        if files_type == "tv":
            if "MP4" in files or "HR-HDTV" in files:
                videos = ''
                if "MP4" in files:
                    videos = files.get('MP4')
                elif "HR-HDTV" in files:
                    videos = files.get('HR-HDTV')

                videos_info = []
                for i in videos:
                    if i.get('way_name') == "磁力":
                        name = i.get('name')
                        size = i.get('size')
                        way_name = i.get('way_name')
                        address = i.get('address')
                        logger.info(
                            "资源名称:{},文件大小:{},下载类型:{},下载链接:{}".format(name, size, way_name, address))
                        videos_info.append([name, size, way_name, address])
                    elif i.get('way_name') == "电驴":
                        name = i.get('name')
                        size = i.get('size')
                        way_name = i.get('way_name')
                        address = i.get('address')
                        logger.info(
                            "资源名称:{},文件大小:{},下载类型:{},下载链接:{}".format(name, size, way_name, address))
                        videos_info.append([name, size, way_name, address])
                return videos_info
        elif files_type == "movie":
            for item in files:
                item_file = item.get('files')
                if "MP4" in item_file or "HR-HDTV" in item_file:
                    videos = ''
                    if "MP4" in item_file:
                        videos = item_file.get('MP4')
                    elif "HR-HDTV" in item_file:
                        videos = item_file.get('HR-HDTV')
                    videos_info = []
                    for i in videos:
                        if i.get('way_name') == "磁力":
                            name = i.get('name')
                            size = i.get('size')
                            way_name = i.get('way_name')
                            address = i.get('address')
                            logger.info(
                                "资源名称:{},文件大小:{},下载类型:{},下载链接:{}".format(name, size, way_name, address))
                            videos_info.append([name, size, way_name, address])
                        elif i.get('way_name') == "电驴":
                            name = i.get('name')
                            size = i.get('size')
                            way_name = i.get('way_name')
                            address = i.get('address')
                            logger.info(
                                "资源名称:{},文件大小:{},下载类型:{},下载链接:{}".format(name, size, way_name, address))
                            videos_info.append([name, size, way_name, address])
                    return videos_info
        else:
            return None
    except Exception as e:
        logger.exception('循环获取下载链接失败，抛出异常:{}'.format(e))


def get_movie_link(videoID):
    """
    获取下电影下载链接
    :param videoID:
    :return:
    """
    try:
        data = search_resource(videoID)
        if data is None:
            logger.warning('资源ID:{}，无下载资源提供'.format(videoID))
            return None
        else:
            for item in data:
                return iter_video_link('movie', item.get('episodes'))
    except Exception as e:
        logger.exception('资源ID:{}，获取电影下载链接失败，抛出异常:{}'.format(videoID, e))


def get_top_list(top_type, top_num):
    """
    获取下排行影视
    :param top_type:
    :param top_num:
    :return:
    """
    data = search_top_resource(top_num)
    if data is None:
        return None
    else:
        top_list = []
        if top_type == "总榜":
            total_list = data.get('total_list')
            for i in range(len(total_list)):
                cnname = str(i + 1) + ". " + str(total_list[i].get('cnname'))
                print(cnname)
                top_list.append(cnname)
        elif top_type == "本月":
            movie_list = data.get('movie_list')
            for i in range(len(movie_list)):
                cnname = str(i + 1) + ". " + str(movie_list[i].get('cnname'))
                top_list.append(cnname)
        elif top_type == "电影":
            movie_total = data.get('movie_total')
            for i in range(len(movie_total)):
                cnname = str(i + 1) + ". " + str(movie_total[i].get('cnname'))
                top_list.append(cnname)
        elif top_type == "日剧":
            japan_list = data.get('japan_list')
            for i in range(len(japan_list)):
                cnname = str(i + 1) + ". " + str(japan_list[i].get('cnname'))
                top_list.append(cnname)
        elif top_type == "新剧":
            new_list = data.get('new_list')
            for i in range(len(new_list)):
                cnname = str(i + 1) + ". " + str(new_list[i].get('cnname'))
                top_list.append(cnname)
        elif top_type == "今日":
            today_list = data.get('today_list')
            for i in range(len(today_list)):
                cnname = str(i + 1) + ". " + str(today_list[i].get('cnname'))
                top_list.append(cnname)
        return '\n'.join(top_list)


if __name__ == '__main__':
    name = "神盾局"
    tv_video_id = "30675"
    mv_video_id = "38178"
    seasonCount = "1"
    episodeCount = "8"
    # get_season_count(tv_video_id)
    # get_tv_link(tv_video_id, seasonCount, episodeCount)
    # get_episode_count(seasonCount, tv_video_id)
    # search_resource(tv_video_id)
    get_top_list("总榜", "5")
