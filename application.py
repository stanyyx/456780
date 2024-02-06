import os
import cv2
import time
from flask import Flask, request, jsonify, send_file
from flask.views import MethodView
import celery
from celery.result import AsyncResult
from cv2 import dnn_superres
import importlib
importlib.reload(celery)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'files'
celery = celery.Celery(app.name,
    backend='redis://localhost:6379/1',
    broker='redis://localhost:6379/2',
)
celery.conf.update(app.config)


class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)


celery.Task = ContextTask


@celery.task()
def upscale(input_path: str, output_path: str, model_path: str = 'EDSR_x2.pb') -> None:
    """
    :param input_path: путь к изображению для апскейла
    :param output_path:  путь к выходному файлу
    :param model_path: путь к ИИ модели
    :return:
    """

    scaler = dnn_superres.DnnSuperResImpl_create()
    scaler.readModel(model_path)
    scaler.setModel("edsr", 2)
    image = cv2.imread(input_path)
    result = scaler.upsample(image)
    cv2.imwrite(output_path, result)


def get_file_name(file: str):
    return file[len(app.config['UPLOAD_FOLDER']) + 1:]

class Upscaling(MethodView):
    def post(self):
        while True:
            orig_file, res_file = self.save_image()
            task = upscale.delay(orig_file, res_file)
            return jsonify({
                'task_id': task.id,
                'file_name': get_file_name(res_file)
            })

    def get(self, task_id):
        while True:
            task = AsyncResult(task_id, app=celery)
            return jsonify({
                'status': task.status,
            })


    def save_image(self):
        image = request.files.get('file')
        extension, name = image.filename.split('.')[-1], image.filename.split('.')[0]
        orig_file = os.path.join('files', f'{name}.{extension}')
        res_file = os.path.join('files', f'{name}_upscaled.{extension}')
        image.save(orig_file)
        image.save(res_file)
        return orig_file, res_file


class Upscaled(MethodView):
    def get(self, file_name):
        return send_file(path_or_file=os.path.join(app.config['UPLOAD_FOLDER'], file_name))


upscaling = Upscaling.as_view('upscaling')
upscaled = Upscaled.as_view('upscaled')
app.add_url_rule('/upscaling/', view_func=upscaling, methods=['POST'])
app.add_url_rule('/upscaling/<string:task_id>/', view_func=upscaling, methods=['GET'])
app.add_url_rule('/upscaled/<string:file_name>/', view_func=upscaled, methods=['GET'])


if __name__ == '__main__':
    app.run()
    
    
#celery run
#celery -A application.celery worker  --loglevel=info --pool=solo
