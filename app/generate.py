from openai import AsyncOpenAI
import yaml

with open('text.yaml', 'r') as file:  # открываем yaml файл с данными
  config1 = yaml.safe_load(file)

AI_TOKEN = config1['AI']['AI_TOKEN']
client = AsyncOpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=AI_TOKEN,
)

async def ai_generate(text: str):
  completion = await client.chat.completions.create(
    model="deepseek/deepseek-r1-0528:free",
    messages=[
      {
        "role": "user",
        "content": text
      }
    ]
  )
  print(completion)
  return completion.choices[0].message.content
