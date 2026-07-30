# GPT 图片生成接口使用

## 1. 图片生成

```python
import os
from pathlib import Path

from dotenv import load_dotenv

from pipeline.gpt_image_client import GPTImageClient


load_dotenv(".env")

client = GPTImageClient(
    api_key=os.environ["GPT_IMAGE_API_KEY"],
    base_url=os.environ["GPT_IMAGE_BASE_URL"],
    model=os.environ.get("GPT_IMAGE_MODEL", "gpt-image-2"),
)

image_bytes = client.generate(
    prompt="一片暖色阳光照射的森林，电影感插画",
    size="1536x1024",
    quality="high",
    output_format="png",
)

Path("publish/test/generated.png").write_bytes(image_bytes)
```

## 2. 图片编辑

单张参考图：

```python
image_bytes = client.edit(
    prompt="保持人物身份和服装不变，将背景替换为森林",
    images=["publish/test/cy.png"],
    size="1536x1024",
    quality="high",
    output_format="png",
)

Path("publish/test/edited.png").write_bytes(image_bytes)
```

多张参考图：

```python
image_bytes = client.edit(
    prompt="将两张参考图中的人物生成在同一张森林合影中",
    images=[
        "publish/test/cy.png",
        "publish/test/中里毅2.png",
    ],
    size="1536x1024",
    quality="high",
    output_format="png",
)

Path("publish/test/group_portrait.png").write_bytes(image_bytes)
```

## 3. 接口

环境变量：

```dotenv
GPT_IMAGE_API_KEY=你的接口密钥
GPT_IMAGE_BASE_URL=https://你的接口域名
GPT_IMAGE_MODEL=gpt-image-2
```

初始化：

```python
client = GPTImageClient(
    api_key="接口密钥",
    base_url="https://你的接口域名",
    model="gpt-image-2",
    timeout=300,
    attempts=4,
)
```

图片生成接口：

```text
POST /v1/images/generations
```

```python
client.generate(
    prompt="图片提示词",
    size="1024x1024",
    quality="high",
    output_format="png",
)
```

图片编辑接口：

```text
POST /v1/images/edits
Content-Type: multipart/form-data
```

```python
client.edit(
    prompt="图片编辑提示词",
    images=["参考图1.png", "参考图2.png"],
    size="1536x1024",
    quality="high",
    output_format="png",
    max_edge=2048,
    max_upload_bytes=8 * 1024 * 1024,
)
```

接口返回值：

```python
image_bytes: bytes
```
