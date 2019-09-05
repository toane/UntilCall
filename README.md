install requirements:

```
python -m pip install -r requirements.txt
```

start celery broker and backend

```
redis-server --port 6666
redis-server --port 7777
```

start celery worker

```python
celery -A tasks worker
```

start server

```python
python main.py
```
run tests

```python
python -m pytest tests.py
```

download and process an image

```
curl http://127.0.0.1:5555/download/https://media.istockphoto.com/photos/rainbow-in-watercolor-picture-id669409776
```

browse images

```
curl http://127.0.0.1:5555/catalogue
```
check an image in a browser:

```
http://127.0.0.1:5555/watch/5d812ce075653eb61dccc06a526a98cf/bw
http://127.0.0.1:5555/watch/5d812ce075653eb61dccc06a526a98cf/color
```

view job history in a browser:

```
xdg-open html/index.html
```