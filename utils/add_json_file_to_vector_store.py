
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI()

def create_file(client, file_path):
    with open(file_path, "rb") as file_content:
        result = client.files.create(
            file=file_content,
            purpose="assistants"
        )
    return result.id

vector_store = client.vector_stores.create(
    name="knowledge_base"
)
print(vector_store.id)

client.vector_stores.files.create(
    vector_store_id=vector_store.id,
    file_id=create_file(client, "model_context/wcag_rules.json")
)

result = client.vector_stores.files.list(
    vector_store_id=vector_store.id
)
print(result)