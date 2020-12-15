import aiohttp
import asyncio
import uvicorn
import json
from fastai import *
from fastai.imports import *
from fastai.vision import *
from io import BytesIO
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles

# Project root path
path = Path(__file__).parent

# Model file path
model_filepath = "models/model.pth"

# Load classes info from JSON
with open(path / 'classes/sushi.json') as json_file:
    classes = json.load(json_file)
classes = map(lambda classe: classe['en'], classes)
classes = sorted(classes)

# If model not present, download it from its dropbox repo
export_file_url = f'https://www.dropbox.com/s/k9wqc1p5lkgrav8/model.pth?raw=1'
async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f:
                f.write(data)

# Initialize Starlette app
app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))

# Learning setup (dependent of your library!)
async def setup_learner():
    if not os.path.isfile(path / model_filepath):
        print("No model stored in the project. Uploading from Dropbox...")
        await download_file(export_file_url, path / model_filepath)
        print("Model uploaded and stored!")
    try:
        print("Model learning setup")
        data_bunch = ImageDataBunch.single_from_classes(path, classes, ds_tfms=get_transforms(), size=224).normalize(imagenet_stats)
        learn = cnn_learner(data_bunch, models.resnet34, pretrained=False)
        learn.load("model")

        return learn
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise

loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
loop.close()

# Route to the homepage
@app.route('/')
async def homepage(request):
    html_file = path / 'view/index.html'
    return HTMLResponse(html_file.open().read())

# Route to the analyzer
@app.route('/analyze', methods=['POST'])
async def analyze(request):

    # Get the uploaded image and store it in img
    img_data = await request.form()
    img_bytes = await (img_data['file'].read())
    img = open_image(BytesIO(img_bytes))

    # Predict the image classe according to the model (dependent of your library!)
    prediction = learn.predict(img)
    print('prediction:', f'{str(prediction[0])} with {round(prediction[2][prediction[1].item()].item() * 100)}%')
    details = {}
    for index, each_class in enumerate(classes):
        details[each_class] = round(prediction[2][index].item() * 100)
    print('prediction details:',details)

    # Build the json file with analysis results
    json_response = {
        'result': str(prediction[0]),
        'resultPct': round(prediction[2][prediction[1].item()].item() * 100),
        'details': details
    }
    print(json_response)

    return JSONResponse(json_response)

# Initialize the starlette web app when python 'app/server.py serve' is run
if __name__ == '__main__':
    if 'serve' in sys.argv:
        uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level="info")
