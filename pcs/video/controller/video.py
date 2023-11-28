import logging
from pcs.common.base import BaseController
from pcs.common.sql_condition import Sc
from pcs.common.response import Response
from pcs.video.tasks import video_add
from pcs.celery_app import ad_add


logger = logging.getLogger(__name__)


class VideoController(BaseController):
    def query_all_video(self, query_condition):
        qc = query_condition.get('query_params') or []
        sc = Sc.parse2sc(qc)
        if not sc.valid:
            return Response.error(sc.invalid_msg)

        video_t = self.get_table_obj('VideoTable')
        row_count, user_result = video_t.paginate_query(sc)

        a = video_add.delay()
        b = ad_add.delay()

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

        t.create(create_data)

        return Response.success()

    def update_video_info(self, update_data):
        t = self.get_table_obj('VideoTable')

        video_id = update_data.pop("id", None)

        sc = Sc([("=", "id", video_id)])
        t.write(update_data, sc)

        return Response.success()
