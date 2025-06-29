import requests
import openai
from bs4 import BeautifulSoup

# Step 1: Search Google Custom Search
def google_search(query, api_key, cse_id):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": api_key,
        "cx": cse_id,
        "num": 10  # Number of results
    }
    response = requests.get(url, params=params)
    results = response.json()
    snippets = [item['snippet'] for item in results.get('items', [])]
    return "\n".join(snippets)

# Step 2: Send results to Azure OpenAI
def ask_azure_openai(prompt, azure_endpoint, azure_api_key, deployment_name):
    headers = {
        "api-key": azure_api_key,
        "Content-Type": "application/json"
    }
    data = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    }
    url = f"{azure_endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version=2024-02-15-preview"
    response = requests.post(url, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]

def fetch_full_text(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        # This gets all text, but you may want to refine this for main content
        text = soup.get_text(separator='\n', strip=True)
        return text
    except Exception as e:
        return f"Error fetching {url}: {e}"

# Usage
GOOGLE_API_KEY = "AIzaSyC2XD5jyl_tCs9b0h0tHwPXvbCy6TlrYNI"
GOOGLE_CSE_ID = "12b0c23528bcf42a3"
AZURE_ENDPOINT = "https://ngtdazureaihub1570085143.services.ai.azure.com/"
AZURE_API_KEY = "8EHWQ96vkKRQwmFIlS3EvmL5fNdLxN5A4oFPm4WY1R64gzcGcZxNJQQJ99BDACHrzpqXJ3w3AAAAACOGA3wK"
DEPLOYMENT_NAME = "gpt-4o"
query = "Winner of world test championship 2025"
search_results = google_search(query, GOOGLE_API_KEY, GOOGLE_CSE_ID)

prompt = f"Based on the following web search results, answer the question: {query}\n\n{search_results}"
# print(search_results)

search_results = search_results.get('items', [])
for item in search_results:
    url = item.get('link')
    print(f"Fetching: {url}")
    full_text = fetch_full_text(url)
    print(full_text[:1000])  # Print first 1000 chars for brevity
answer = ask_azure_openai(prompt, AZURE_ENDPOINT, AZURE_API_KEY, DEPLOYMENT_NAME)
# print(search_results)
# print(answer)