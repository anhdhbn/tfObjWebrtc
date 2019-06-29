import object_detection_api
import os
from PIL import Image
from flask import Flask, request, Response
from werkzeug.utils import secure_filename

from flask_ngrok import run_with_ngrok
import cv2
import numpy

app = Flask(__name__)
run_with_ngrok(app)

# for CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST') # Put any other methods you need here
    return response


# @app.route('/')
# def index():
#     return Response('Tensor Flow object detection')


# @app.route('/local')
# def local():
#     return Response(open('./static/local.html').read(), mimetype="text/html")
@app.route('/')
def local():
    return Response(open('./static/index.html').read(), mimetype="text/html")


@app.route('/video')
def remote():
    return Response(open('./static/video.html').read(), mimetype="text/html")


@app.route('/test')
def test():
    PATH_TO_TEST_IMAGES_DIR = 'object_detection/test_images'  # cwh
    TEST_IMAGE_PATHS = [os.path.join(PATH_TO_TEST_IMAGES_DIR, 'image{}.jpg'.format(i)) for i in range(1, 3)]

    image = Image.open(TEST_IMAGE_PATHS[0])
    objects = object_detection_api.get_objects(image)

    return objects


@app.route('/image', methods=['POST'])
def image():
    try:
        image_file = request.files['image']  # get the image
        # print("image_file", image_file)
        # Set an image confidence threshold value to limit returned data
        threshold = request.form.get('threshold')
        if threshold is None:
            threshold = 0.5
        else:
            threshold = float(threshold)
        # img = cv2.imdecode(numpy.fromstring(request.files['file'].read(), numpy.uint8), cv2.IMREAD_UNCHANGED)
        # print("img", img)
        # finally run the image through tensor flow object detection`
        image_object = Image.open(image_file)
        # print("image_object", image_object)
        objects = object_detection_api.get_objects(image_object, threshold)
        print("objects", objects)
        # return objects
        return objects

    except Exception as e:
        print('POST /image error: %e' % e)
        return e


if __name__ == '__main__':
	# without SSL
    # import threading
    # threading.Thread(target=app.run, kwargs={'host':'0.0.0.0','port':80}).start() 
    # app.run(debug=True, host='0.0.0.0')
    app.run()
	# with SSL
    #app.run(debug=True, host='0.0.0.0', ssl_context=('ssl/server.crt', 'ssl/server.key'))
