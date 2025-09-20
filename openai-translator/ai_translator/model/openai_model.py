import requests
import simplejson
import time
import os
import openai

try:
    from .model import Model
except ImportError:  # pragma: no cover - fallback for direct execution
    from model import Model
try:
    from ..utils import LOG
except ImportError:  # pragma: no cover - fallback for direct execution
    from utils import LOG
from openai import OpenAI

class OpenAIModel(Model):
    def __init__(self, model: str, api_key: str):
        self.model = model
        os.environ	[	"OPENAI_API_KEY"	] = "sk-Y9P2ZYbyYK0HNbjBjj5s6yddubVCZ36WqCbXEVcYXSQMiaEm"
        # 这里将官方的接口访问地址替换成便携AI聚合API的入口地址
        os.environ["OPENAI_BASE_URL"] = "https://www.dmxapi.com/v1"
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )

    def make_request(self, prompt):
        attempts = 0
        while attempts < 3:
            try:
                if self.model == "gpt-4o-mini":
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    translation = response.choices[0].message.content.strip()
                else:
                    response = self.client.completions.create(
                        model=self.model,
                        prompt=prompt,
                        max_tokens=150,
                        temperature=0
                    )
                    translation = response.choices[0].text.strip()

                return translation, True
            except openai.RateLimitError as e:
                attempts += 1
                if attempts < 3:
                    LOG.warning("Rate limit reached. Waiting for 60 seconds before retrying.")
                    time.sleep(60)
                else:
                    raise Exception("Rate limit reached. Maximum attempts exceeded.")
            except openai.APIConnectionError as e:
                print("The server could not be reached")
                print(e.__cause__)  # an underlying Exception, likely raised within httpx.
            except requests.exceptions.Timeout as e:
                print("Request timed out")
                print(e)
            except openai.APIStatusError as e:
                print("Another non-200-range status code was received")
                print(e.status_code)
                print(e.response)
            except Exception as e:
                raise Exception(f"发生了未知错误：{e}")
        return "", False
