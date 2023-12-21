import logging
from pcs.common.base import BaseController
from pcs.common.sql_condition import Sc
from pcs.common.response import Response
from pcs.common.enum.common_enum import ProcessStatus
from pcs.video.tasks import video_add
from pcs.utils.download_file import M3u8Parser


logger = logging.getLogger(__name__)


class VideoController(BaseController):
    def query_all_video(self, query_condition):
        qc = query_condition.get('query_params') or []
        sc = Sc.parse2sc(qc)
        if not sc.valid:
            return Response.error(sc.invalid_msg)

        video_t = self.get_table_obj('VideoTable')
        row_count, user_result = video_t.paginate_query(sc)

        return Response.pagination(user_result, row_count)

    def query_video_info(self, query_data):
        video_id = query_data.get("video_id")
        video_t = self.get_table_obj('VideoTable')
        video_detail_t = self.get_table_obj('VideoDetailTable')

        sc = Sc([("=", "id", video_id)])
        video_result = video_t.query(sc)
        if not video_result:
            return Response.error("没有获取到视频信息")

        video_data = video_result[0]

        sc = Sc([( "=", "video_id", video_id)])
        video_detail_result = video_detail_t.query(sc)
        video_data["video_details"] = video_detail_result

        return Response.json_data(video_data)

    def query_video_detail(self, query_data):
        video_detail_id = query_data.get("video_detail_id")
        t = self.get_table_obj('VideoDetailTable')

        sc = Sc([("=", "id", video_detail_id)])
        video_detail_result = t.query(sc)
        if not video_detail_result:
            return Response.error("没有获取到视频明细信息")

        return Response.json_data(video_detail_result[0])

    def add_video(self, create_data):
        t = self.get_table_obj('VideoTable')
        log_t = self.get_table_obj('VideoLogTable')
        video_name = create_data.get("video_name")

        res = t.query(Sc([( "=", "video_name", video_name)]), ["id"])
        if res:
            return Response.error("该视频已存在该" % video_name)

        video_id = t.create(create_data)
        log_t.add_log(video_id, "创建", "创建视频成功")

        return Response.success()

    def update_video_info(self, update_data):
        video_t = self.get_table_obj('VideoTable')
        log_t = self.get_table_obj('VideoLogTable')

        video_id = update_data.pop("id", None)
        video_name = update_data.get("video_name") or ""
        if not video_id:
            return Response.error("不存在该视频")

        if not video_name:
            return Response.error("视频名称不可未空")

        res = video_t.query(Sc([( "=", "video_name", video_name)]), ["id"])
        if res and res[0].get("id") != video_id:
            return Response.error("已存在相同视频")

        video_t.write(update_data, Sc([( "=", "id", video_id)]))
        log_t.add_log(video_id, "更新", "更新视频成功")

        return Response.success()

    def download_video(self, json_data):
        video_name = json_data.get("video_name")
        video_url_list = json_data.get("url_list")
        url_type = json_data.get("url_type")
        params = json_data.get("params") or {}
        ignore_exist_url = params.get("ignore_exist_url") or False

        download_t = self.get_table_obj('VideoDownloadTable')
        download_res = download_t.query(Sc([( "=", "video_name", video_name)]), ["id", "video_url"])
        if download_res:
            return Response.error("视频[%s]已存在该URL" % video_name)

        exist_url = [r.get("video_url") for r in download_res if r.get("video_url") in video_url_list]
        if exist_url and not ignore_exist_url:
            if not ignore_exist_url:
                return Response.error("视频[%s]已存在该URL[%s]" % (video_name, ",".join(exist_url)))
            else:
                video_url_list = [v for v in video_url_list if v not in exist_url]

        if url_type == 'm3u8':
            res = self.__m3u8_video_download(video_name, video_url_list, params)
        elif url_type == 'magnet':
            res = self.__magnet_video_download(video_name, video_url_list, params)
        else:
            return Response.error("无法下载该视频类型: " % url_type)

        if not res.success:
            return Response.error(res.msg)

        return Response.success()

    def __m3u8_video_download(self, video_name, video_urls, params):
        download_m3u8_detail_t = self.get_table_obj('VideoDownloadM3u8DetailsTable')
        download_t = self.get_table_obj('VideoDownloadTable')

        ignore_failure = params.pop("ignore_failure", False) or False
        for video_url in video_urls:
            parser = M3u8Parser(video_url, params)
            m3u8_url_details = parser.parse()
            if not m3u8_url_details:
                if not ignore_failure:
                    return self.return_failure("URL[%s]: 未获取到正确的m3u8视频资源" % video_url)
                continue

            download_data = {
                "video_name": video_name, "video_url": video_url, "download_status": ProcessStatus.WaitStart.value,
                "parse_status": ProcessStatus.WaitStart.value, "video_url_type": 'm3u8'
            }

            download_t.create(download_data)

            download_detail_data = [
                {
                    "m3u8_url": m.get('m3u8_url'), "local_path": m.get('local_path'),
                    "download_status": ProcessStatus.WaitStart.value
                }
                for m in m3u8_url_details
            ]
            download_m3u8_detail_t.batch_create(download_detail_data)

        return self.return_ok()

    def __magnet_video_download(self, video_name, video_url_list, params):
        return self.return_ok()