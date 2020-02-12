import json
import traceback
import threading
from channels.generic.websocket import WebsocketConsumer
from channels.exceptions import StopConsumer
from asgiref.sync import async_to_sync
from apps.web import models
from django.db import transaction
import os
from utils.repository import GitRepository
from django.conf import settings
import shutil
from utils.ssh import SSHProxy


def init_diagram_record(task_object, consumer, task_id):
    try:
        diagram_object_list = []
        with transaction.atomic():

            start_object = models.Diagram.objects.create(task=task_object, text='开始')
            diagram_object_list.append(start_object)

            download_object = models.Diagram.objects.create(task=task_object, text='下载', parent=start_object)
            diagram_object_list.append(download_object)

            zip_object = models.Diagram.objects.create(task=task_object, text='打包', parent=download_object)
            diagram_object_list.append(zip_object)

            deploy_server_list = models.DeployServer.objects.filter(deploy=task_object)
            for row in deploy_server_list:
                row.status = 2
                row.save()
                server_object = models.Diagram.objects.create(task=task_object, text=row.server.hostname,
                                                              parent=zip_object, deploy_record=row)
                diagram_object_list.append(server_object)

        diagram_data_list = []
        for item in diagram_object_list:
            temp = {
                "key": str(item.id),
                "text": item.text,
                "color": item.status,
            }
            if item.parent:
                temp['parent'] = str(item.parent_id)
            diagram_data_list.append(temp)
        consumer.group_send_init(task_id, diagram_data_list)
        return True
    except Exception as e:
        msg = "【初始化图表】失败。\n具体原因：%s" % traceback.format_exc()
        consumer.group_send_log(task_id, msg)


def retry_init_diagram_record(task_object, consumer, task_id):
    exists = models.Diagram.objects.filter(task=task_object).exists()
    if not exists:
        return init_diagram_record(task_object, consumer, task_id)

    return True


def do_success(diagram_object, success_log, consumer, task_id):
    success_color = "green"
    diagram_object.status = success_color
    diagram_object.log = success_log
    diagram_object.save()

    consumer.group_send_update(task_id, {'key': str(diagram_object.id), 'color': success_color})
    consumer.group_send_log(task_id, success_log)


def do_error(diagram_object, error_log, consumer, task_id):
    error_color = "red"
    diagram_object.status = error_color
    diagram_object.log = error_log
    diagram_object.save()

    consumer.group_send_update(task_id, {'key': str(diagram_object.id), 'color': error_color})
    consumer.group_send_log(task_id, error_log)
    consumer.group_send_close(task_id)  # 关闭所有链接


def deploy_start(task_object, consumer, task_id, retry=False):
    process_start_object = models.Diagram.objects.filter(task=task_object, text='开始').first()
    if retry and process_start_object.status == 'green':
        return True
    try:
        success_log = "【开始发布】成功"
        do_success(process_start_object, success_log, consumer, task_id)
        return True
    except Exception as e:
        error_log = "【开始发布】失败。\n具体原因：%s" % traceback.format_exc()
        do_error(process_start_object, error_log, consumer, task_id)


def deploy_download(task_object, consumer, task_id, retry=False):
    process_download_object = models.Diagram.objects.filter(task=task_object, text='下载').first()
    if retry and process_download_object.status == 'green':
        return True
    try:
        with transaction.atomic():
            # 2.2.1 拉代码
            project_repo = task_object.env.project.repo
            project_name = task_object.env.project.title
            local_project_path = os.path.join(settings.HG_DEPLOY_BASE_PATH,
                                              project_name,
                                              task_object.env.env,
                                              task_object.uid)
            repo_object = GitRepository(local_project_path, project_repo)

            # 2.2.2 如果是基于tag进行发布
            if task_object.tag:
                repo_object.change_to_tag(task_object.tag)
            else:
                # 2.2.3 如果是基于commit发布
                repo_object.change_to_commit(task_object.branch, task_object.commit)

            success_log = "【下载代码】成功"
            do_success(process_download_object, success_log, consumer, task_id)

            return True
    except Exception as e:
        error_log = "【下载代码】失败。\n具体原因：%s" % traceback.format_exc()
        do_error(process_download_object, error_log, consumer, task_id)


def deploy_zip(task_object, consumer, task_id, retry=False):
    zip_object = models.Diagram.objects.filter(task=task_object, text='打包').first()
    if retry and zip_object.status == 'green':
        return os.path.join(settings.HG_ZIP_BASE_PATH,
                            task_object.env.project.title,
                            task_object.env.env,
                            task_object.uid + '.zip')
    try:
        with transaction.atomic():

            zip_file_path = shutil.make_archive(
                # base_name="code/www",  # 压缩包文件路劲
                base_name=os.path.join(settings.HG_ZIP_BASE_PATH,
                                       task_object.env.project.title,
                                       task_object.env.env,
                                       task_object.uid),
                # 压缩包文件路劲
                format='zip',  # “zip”, “tar”
                root_dir=os.path.join(settings.HG_DEPLOY_BASE_PATH,
                                      task_object.env.project.title,
                                      task_object.env.env,
                                      task_object.uid)
                # 被压缩的文件件
            )
            success_log = "【打包】成功"
            do_success(zip_object, success_log, consumer, task_id)

            return zip_file_path
    except Exception as e:
        error_log = "【打包】失败。\n具体原因：%s" % traceback.format_exc()
        do_error(zip_object, error_log, consumer, task_id)


def deploy_upload(zip_file_path, task_object, consumer, task_id, retry=False):
    rsa_object = models.Rsa.objects.filter(status=1).first()
    deploy_server_list = models.DeployServer.objects.filter(deploy=task_object)
    is_all_success = True
    for row in deploy_server_list:
        host_object = models.Diagram.objects.filter(task=task_object, deploy_record=row).first()
        if retry and host_object.status == 'green':
            continue
        try:
            with transaction.atomic():
                with SSHProxy(row.server.hostname, 22, rsa_object.user, rsa_object.private_key) as proxy:
                    proxy.command("mkdir %s" % task_object.env.path)
                    proxy.upload(zip_file_path, os.path.join(task_object.env.path, task_object.uid + '.zip'))
                row.status = 4
                row.save()

            success_log = '【服务器%s 上传代码】 成功' % row.server.hostname
            do_success(host_object, success_log, consumer, task_id)
        except Exception as e:
            row.status = 3
            row.save()
            error_log = "【服务器%s 上传代码】失败。\n具体原因：%s" % (row.server.hostname, traceback.format_exc())
            do_error(host_object, error_log, consumer, task_id)
            is_all_success = False

    return is_all_success


class DeployConsumer(WebsocketConsumer):

    def group_send_init(self, task_id, data):
        async_to_sync(self.channel_layer.group_send)(task_id, {'type': 'xxx.ooo',
                                                               'message': {'code': 'init',
                                                                           'data': data}})

    def group_send_error(self, task_id, msg):
        async_to_sync(self.channel_layer.group_send)(task_id, {'type': 'xxx.ooo',
                                                               'message': {'code': 'error',
                                                                           'msg': msg}})

    def group_send_update(self, task_id, data):
        async_to_sync(self.channel_layer.group_send)(task_id, {'type': 'xxx.ooo',
                                                               'message': {'code': 'update',
                                                                           'data': data}})

    def group_send_log(self, task_id, data):
        async_to_sync(self.channel_layer.group_send)(task_id, {'type': 'xxx.ooo',
                                                               'message': {'code': 'log',
                                                                           'data': data}})

    def group_send_close(self, task_id):
        async_to_sync(self.channel_layer.group_send)(task_id, {'type': 'xxx.ooo', 'message': {'code': 'close'}})

    # websocket
    def websocket_connect(self, message):
        task_id = self.scope['url_route']['kwargs'].get('task_id')
        task_object = models.DeployTask.objects.filter(id=task_id).first()
        self.accept()
        # 1. 去数据库中获取现在任务的所有记录以生成图标
        diagram_object_list = models.Diagram.objects.filter(task=task_object)
        diagram_data_list = []
        for item in diagram_object_list:
            temp = {
                "key": str(item.id),
                "text": item.text,
                "color": item.status,
            }
            if item.parent:
                temp['parent'] = str(item.parent_id)
            diagram_data_list.append(temp)

            self.send(text_data=json.dumps({'code': 'log', 'data': item.log}))
        # 2. 将数据返还给用户
        self.send(text_data=json.dumps({'code': 'init', 'data': diagram_data_list}))

        # 3. 判断发布任务的状态，如果发布成功，则断开websocket链接。
        if task_object.status == 3:
            self.close()  # 告诉客户端，我要和你断开连接。
            raise StopConsumer()  # 我先自杀

        # 把自己加到 task_id 群里，以接受以后发来的消息。
        async_to_sync(self.channel_layer.group_add)(task_id, self.channel_name)

    def websocket_receive(self, message):
        # "deploy",表示第一次发布
        # "retry_deploy",表示重新发布
        deploy_type = json.loads(message['text']).get('type')
        if deploy_type not in ['deploy', 'retry_deploy']:
            self.send(json.dumps({'code': 'error', 'msg': '发布类型错误。'}))
            return

        # 1. 用于点击发布，处理那些重复点击的问题。
        task_id = self.scope['url_route']['kwargs'].get('task_id')
        with transaction.atomic():
            task_object = models.DeployTask.objects.filter(id=task_id).select_for_update().first()
            # 正在发布中，提示无需重复操作。
            if task_object.status == 2:
                self.send(json.dumps({'code': 'error', 'msg': '正在发布中，无需重复操作。'}))
                return
            if task_object.status == 3:
                self.send(json.dumps({'code': 'error', 'msg': '已发布成功，无需重复操作。'}))
                return
            # 发布失败、未发布
            task_object.status = 2
            task_object.save()

        # 2. 生成图标记录

        if deploy_type == 'deploy':
            init_diagram_status = init_diagram_record(task_object, self, task_id)
            if not init_diagram_status:
                return
        else:
            retry_init_diagram_status = retry_init_diagram_record(task_object, self, task_id)
            if not retry_init_diagram_status:
                return

        # 3. 去发布
        def task(retry):
            # 3.1 处理开始
            start_status = deploy_start(task_object, self, task_id, retry)
            if not start_status:
                return

            # 3.2 处理下载
            download_status = deploy_download(task_object, self, task_id, retry)
            if not download_status:
                return

            # 3.3 打包代码
            zip_file_path = deploy_zip(task_object, self, task_id, retry)
            if not zip_file_path:
                return

            # 3.4 上传代码
            is_all_success = deploy_upload(zip_file_path, task_object, self, task_id, retry)
            if is_all_success:
                task_object.status = 3
            else:
                task_object.status = 4
            task_object.save()

        if deploy_type == 'deploy':
            retry = False
        else:
            retry = True
        deploy_thread = threading.Thread(target=task, args=(retry,))
        deploy_thread.start()

    def xxx_ooo(self, event):
        message = event['message']
        if message.get('close'):
            self.close()
        else:
            self.send(json.dumps(message))

    def websocket_disconnect(self, message):
        task_id = self.scope['url_route']['kwargs'].get('task_id')
        async_to_sync(self.channel_layer.group_discard)(task_id, self.channel_name)
        raise StopConsumer()
