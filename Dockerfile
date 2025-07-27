FROM fnproject/python:3.9

WORKDIR /function
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

RUN python -c "from paddleocr import PaddleOCR; PaddleOCR(use_angle_cls=True, lang='japan', use_gpu=False)"
COPY func.py .

ENV PYTHONPATH=/function
ENTRYPOINT ["python", "-m", "fdk", "func.py", "handle"]